# -*- coding: utf-8 -*-

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

from fuel_upgrade import errors
from fuel_upgrade.tests.base import BaseTestCase
from fuel_upgrade.supervisor_client import SupervisorClient


@mock.patch('fuel_upgrade.supervisor_client.os')
class TestSupervisorClient(BaseTestCase):

    def setUp(self):
        self.utils_patcher = mock.patch('fuel_upgrade.supervisor_client.utils')
        self.utils_mock_class = self.utils_patcher.start()
        self.utils_mock = mock.MagicMock()
        self.utils_mock_class.return_value = self.utils_mock

        self.supervisor = SupervisorClient(self.fake_config)
        type(self.supervisor).supervisor = mock.PropertyMock()

        self.new_version_supervisor_path = '/etc/supervisord.d/9999'
        self.previous_version_supervisor_path = '/etc/supervisord.d/0'

    def tearDown(self):
        self.utils_patcher.stop()

    def test_switch_to_new_configs(self, os_mock):
        self.supervisor.switch_to_new_configs()
        print self.utils_mock
        self.utils_mock.symlink.assert_called_once_with(
            self.new_version_supervisor_path,
            self.fake_config.supervisor['current_configs_prefix'])

    def test_switch_to_previous_configs(self, os_mock):
        self.supervisor.switch_to_previous_configs()
        self.utils_mock.symlink.assert_called_once_with(
            self.previous_version_supervisor_path,
            self.fake_config.supervisor['current_configs_prefix'])

    # def test_stop_all_services(self):
    #     pass

    # def test_restart_and_wait(self):
    #     pass

    # def test_generate_configs(self):
    #     pass

    # def test_generate_config(self):
    #     pass

    # def test_generate_cobbler_config(self):
    #     pass
