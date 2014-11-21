#    Copyright 2014 Mirantis, Inc.
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

import mock
import yaml

from nailgun.objects import Plugin
from nailgun.objects import PluginCollection
from nailgun.test import base



class TestPluginCollection(base.BaseTestCase):

    def test_all_newest(self):
        for version in ['1.0.0', '2.0.0', '0.0.1']:
            plugin_data = self.env.get_default_plugin_metadata(version=version)
            Plugin.create(plugin_data)

        self.assertEqual(len(PluginCollection.all_newest()), 1)
        plugin = PluginCollection.all_newest()[0]
        self.assertEqual(plugin.version, '2.0.0')
