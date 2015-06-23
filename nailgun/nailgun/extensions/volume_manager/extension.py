# -*- coding: utf-8 -*-

#    Copyright 2015 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

from nailgun.extensions.base import BaseExtension

# The extension itself can be not only in Nailgun
# it can be in different module, lets use relative
# imports, to make migration easier
from .manager import VolumeManager
from .urls import urls

from .objects.volumes import VolumesObject


from alembic import config as alembic_config

from nailgun.db.sqlalchemy import db_str

ALEMBIC_CONFIG = alembic_config.Config(
    os.path.join(os.path.dirname(__file__), 'alembic.ini'))
ALEMBIC_CONFIG.set_main_option(
    'script_location', os.path.join(os.path.dirname(__file__), 'migrations'))

ALEMBIC_CONFIG.set_main_option('sqlalchemy.url', db_str)


class VolumeManagerExtension(BaseExtension):

    name = "volume_manager"
    version = "1.0.0-alpha"

    requires = []
    provides = ['volumes_for_node', 'calc_glance_cache_size']
    urls = urls
    alembic_config = ALEMBIC_CONFIG

    def volumes_for_node(self, _, node):
        return VolumesObject.get_volumes_by_node_id(node.id)

    def calc_glance_cache_size(self, _, node):
        volume_manager.calc_glance_cache_size(VolumeManager(node).gen_volumes_info())

    def on_node_creation(self, node):
        """Generate default volumes layout for disks.
        """
        return VolumesObject.reset_volumes(node)

    def on_node_update(self, node):
        """Regenerate the disks if node is not provisioned
        and new disk was added/removed.
        """
        return VolumesObject.reset_volumes(node)
