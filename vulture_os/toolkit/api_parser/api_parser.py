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
__credits__ = []
__license__ = "GPLv3"
__version__ = "4.0.0"
__maintainer__ = "Vulture OS"
__email__ = "contact@vultureproject.org"
__doc__ = 'API Parser'


import logging

from system.config.models import Config
from django.conf import settings

logging.config.dictConfig(settings.LOG_SETTINGS)
logger = logging.getLogger('gui')


class NodeNotInstalled(Exception):
    pass


class ApiParser:
    def __init__(self):
        try:
            config = Config.objects.get()
        except Config.DoesNotExist:
            raise NodeNotInstalled()

        self.customer_name = config.customer_name
