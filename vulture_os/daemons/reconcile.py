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
__author__ = "Olivier de Régis"
__credits__ = ["Kevin GUILLEMOT"]
__license__ = "GPLv3"
__version__ = "4.0.0"
__maintainer__ = "Vulture OS"
__email__ = "contact@vultureproject.org"
__doc__ = 'Job for OS Monitoring'

# Django system imports
from django.conf import settings
from system.cluster.models import Cluster, Node

# Extern modules imports
import json
from time import sleep
from threading import Thread, Event

# Logger configuration imports
import logging

logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('daemon')

# Redis import
from toolkit.redis.redis_base import RedisBase

# Mongo import
from toolkit.mongodb.mongo_base import MongoBase

def alert_handler(alert, m, r):
    try:
        a = json.loads(alert)
    except json.JSONDecodeError as e:
        logger.error("Alert is not JSON valid : {}".format(e))
        return

    evt_id = a.get("evt_id")
    if evt_id is not None:
        log = r.redis.get(evt_id)
        if log is None:
            logger.warning("No matching log for alert {}. Storing alert without context.".format(evt_id))
        else:
            try:
                log = json.loads(log.decode())
            except json.JSONDecodeError as e:
                logger.error("Context is not JSON valid : {}".format(e))
                return
            a["context"] = log

    r.redis.publish(settings.REDIS_RECONCILIED_CHANNEL, json.dumps(a))
    m.insert("logs", "darwin_alerts", a)
    # query = {"darwin_id": evt_id}
    # newvalue = {"$set": {"darwin_alert_details": a, "darwin_is_alert": True}}
    # m.update_one("logs", query, newvalue)
    return True


class ReconcileJob(Thread):

    def __init__(self, delay):
        super().__init__()
        # The shutdown_flag is a threading.Event object that
        # indicates whether the thread should be terminated.
        self.shutdown_flag = Event()
        self.delay = delay

    def pops(self, m, r):
        redis_list_name = settings.REDIS_LIST

        logger.info("Start pops awaiting alerts.")
        alert = r.redis.rpop(redis_list_name)
        while (alert is not None) and (not self.shutdown_flag.is_set()):
            alert = alert.decode()
            alert_handler(alert, m, r)
            alert = r.redis.rpop(redis_list_name)

    def reconcile(self):
        node = Cluster.get_current_node()
        if not node.is_master_mongo: 
            return False

        m = MongoBase()
        if not m.connect():
            return False
        m.connect_primary()

        r = RedisBase()
        master_node = r.get_master()
        r = RedisBase(node=master_node)

        # Pops alerts produced when vulture was down
        self.pops(m, r)
        if self.shutdown_flag.is_set():
            return True

        redis_channel = settings.REDIS_CHANNEL 
        listener = r.redis.pubsub()
        listener.subscribe([redis_channel])

        logger.info("Start listening {} channel.".format(redis_channel))
        while not self.shutdown_flag.is_set():
            alert = listener.get_message()
            # If we have no messages, the messages is None
            if alert:
                alert = alert['data']
                # Redis can return an int
                try:
                    alert = alert.decode()
                except (UnicodeDecodeError, AttributeError):
                    pass
                # We can have an int
                if isinstance(alert, str):
                    alert_handler(alert, m, r)
            sleep(0.001)  # be nice to the system :)
        return True

    def run(self):
        logger.info("Reconcile job started.")
        try:
            self.reconcile()
        except Exception as e:
            logger.error("Reconcile job failure: {}".format(e))
            logger.info("Resuming ...")

        # Sleep DELAY time, 2 seconds at a time to prevent long sleep when shutdown_flag is set
        cpt = 0
        while not self.shutdown_flag.is_set() and cpt < self.delay:
            sleep(2)
            cpt += 2

        logger.info("Reconcile job stopped.")

    def ask_shutdown(self):
        logger.info("Shutdown asked !")
        self.shutdown_flag.set()