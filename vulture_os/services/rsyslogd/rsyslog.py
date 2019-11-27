#!/home/vlt-os/env/bin/python
"""This file is part of Vulture OS.

Vulture OS is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Vulture OS is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Vulture OS.  If not, see http://www.gnu.org/licenses/.
"""
__author__ = "Kevin GUILLEMOT"
__credits__ = []
__license__ = "GPLv3"
__version__ = "4.0.0"
__maintainer__ = "Vulture OS"
__email__ = "contact@vultureproject.org"
__doc__ = 'Rsyslog service wrapper utils'

# Django system imports
from django.conf import settings

# Django project imports
from services.service import Service
from services.frontend.models import Frontend
from services.rsyslogd.models import RsyslogSettings
from system.cluster.models import Cluster
from system.config.models import write_conf
from toolkit.mongodb.mongo_base import MongoBase

# Required exceptions imports
from django.core.exceptions import ObjectDoesNotExist
from services.exceptions import ServiceError
from subprocess import CalledProcessError
from system.exceptions import VultureSystemError

# Extern modules imports
from jinja2 import Environment, FileSystemLoader
from re import search as re_search
from subprocess import check_output, PIPE

# Logger configuration imports
import logging
logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('services')


JINJA_PATH = "/home/vlt-os/vulture_os/services/rsyslogd/config/"
RSYSLOG_PATH = "/usr/local/etc/rsyslog.d"
INPUTS_PATH = RSYSLOG_PATH + "/00-system.conf"

RSYSLOG_PERMS = "640"
RSYSLOG_OWNER = "vlt-os:wheel"


class RsyslogService(Service):
    """ HAProxy service class wrapper """

    def __init__(self):
        super().__init__()
        self.model = RsyslogSettings
        self.service_name = "rsyslogd"
        self.friendly_name = "Logging"

        self.config_file = "rsyslog_inputs.conf"
        self.owners = RSYSLOG_OWNER
        self.perms = RSYSLOG_PERMS
        self.jinja_template = {
            'tpl_name': self.config_file,
            'tpl_path': INPUTS_PATH,  # Set inputs conf as general conf file
        }

    def __str__(self):
        return "Rsyslog Service"

    # Status inherited from Service class


def configure_node(node_logger):
    """ Generate and write netdata conf files """
    result = ""

    node = Cluster.get_current_node()
    global_config = Cluster.get_global_config()

    """ For each Jinja templates """
    jinja2_env = Environment(loader=FileSystemLoader(JINJA_PATH))
    for template_name in jinja2_env.list_templates():
        """ Perform only "rsyslog_template_*.conf" templates """
        match = re_search("^rsyslog_template_([^\.]+)\.conf$", template_name)
        if not match:
            continue
        template = jinja2_env.get_template(template_name)
        template_path = "{}/05-tpl-01-{}.conf".format(RSYSLOG_PATH, match.group(1))
        """ Generate and write the conf depending on all nodes, and current node """
        write_conf(node_logger, [template_path, template.render({'node': node,
                                                                 'global_config': global_config}),
                                 RSYSLOG_OWNER, RSYSLOG_PERMS])
        result += "Rsyslog template '{}' written.\n".format(template_path)

    """ PF configuration for Rsyslog """
    pf_template = jinja2_env.get_template("pf.conf")
    write_conf(node_logger, ["{}/pf.conf".format(RSYSLOG_PATH),
                             pf_template.render({'mongodb_uri': MongoBase.get_replicaset_uri()}),
                             RSYSLOG_OWNER, RSYSLOG_PERMS])
    result += "Rsyslog configuration 'pf.conf' written.\n"

    result += configure_pstats(node_logger)

    """ If this method has been called, there is a reason - a Node has been modified
          so we need to restart Rsyslog because at least PF conf has been changed 
    """
    # if Frontend.objects.filter(enable_logging=True).count() > 0:
    #    node_logger.debug("Logging enabled, reload of Rsyslog needed.")
    restart_service(node_logger)
    node_logger.info("Rsyslog service restarted.")
    result += "Rsyslogd service restarted."

    return result


def configure_pstats(node_logger):
    """ Pstats configuration """
    node = Cluster.get_current_node()
    jinja2_env = Environment(loader=FileSystemLoader(JINJA_PATH))
    pstats_template = jinja2_env.get_template("pstats.conf")
    write_conf(node_logger, ["{}/pstats.conf".format(RSYSLOG_PATH),
                             pstats_template.render({'node': node}),
                             RSYSLOG_OWNER, RSYSLOG_PERMS])
    return "Rsyslog configuration 'pstats.conf' written.\n"


def build_conf(node_logger, frontend_id=None):
    """ Generate conf of rsyslog inputs, based on all frontends LOG
    ruleset of frontend
    outputs of all frontends
    :param node_logger: Logger sent to all API requests
    :param frontend_id: The name of the frontend in conf file
    :return: 
    """
    result = ""
    """ Firstly, try to retrieve Frontend with given id """
    if frontend_id:
        try:
            frontend = Frontend.objects.get(pk=frontend_id)
            """ Generate ruleset conf of asked frontend """
            frontend_conf = frontend.generate_rsyslog_conf()
            """ And write-it """
            write_conf(node_logger, [frontend.get_rsyslog_filename(), frontend_conf, RSYSLOG_OWNER, RSYSLOG_PERMS])
            result += "Frontend '{}' conf written.\n".format(frontend_id)
        except ObjectDoesNotExist:
            raise VultureSystemError("Frontend with id {} not found, failed to generate conf.".format(frontend_id),
                                     "build rsyslog conf", traceback=" ")

    """ Generate inputs configutation """
    service = RsyslogService()
    """ If frontend was given we cannot check if its conf has changed to restart service
     and if reload_conf is True, conf has changed so restart service
    """
    if service.reload_conf() or frontend_id:
        result += "Rsyslog conf updated. Restarting service."
        result += service.restart()
    else:
        result += "Rsyslog conf hasn't changed."
    return result


def reload_service(node_logger):
    # Do not handle exceptions here, they are handled by process_message
    service = RsyslogService()

    # Warning : can raise ServiceError
    result = service.reload()
    node_logger.info("Rsyslogd service reloaded : {}".format(result))

    return result


def restart_service(node_logger):
    """ Only way (for the moment) to reload config """
    # Do not handle exceptions here, they are handled by process_message
    service = RsyslogService()

    # Warning : can raise ServiceError
    result = service.restart()
    node_logger.info("Rsyslogd service restarted : {}".format(result))

    return result


def start_service(node_logger):
    """ Only way (for the moment) to reload config """
    # Do not handle exceptions here, they are handled by process_message
    service = RsyslogService()

    # Warning : can raise ServiceError
    result = service.start()
    node_logger.info("Rsyslogd service started : {}".format(result))

    return result


def delete_conf(node_logger, filename):
    try:
        check_output(["/bin/rm", "{}/{}".format(RSYSLOG_PATH, filename)], stderr=PIPE).decode('utf8')
        # Return message to API request, that will be saved into MessageQueue result
        return "'{}' successfully deleted.".format(filename)

    except CalledProcessError as e:
        """ Command raise if permission denied or file does not exists """
        stdout = e.stdout.decode('utf8')
        stderr = e.stderr.decode('utf8')
        # logger.exception("Failed to delete frontend filename '{}': {}".format(frontend_filename, stderr or stdout))
        raise ServiceError("'{}' : {}".format(filename, (stderr or stdout)), "rsyslogd",
                           "delete rsyslog conf file")
