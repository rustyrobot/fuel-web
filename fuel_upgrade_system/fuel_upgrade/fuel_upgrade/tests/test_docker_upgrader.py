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
from fuel_upgrade.upgrade import DockerUpgrader


@mock.patch('fuel_upgrade.upgrade.utils.exec_cmd')
class TestDockerUpgrader(BaseTestCase):

    def setUp(self):
        # NOTE (eli): mocking doesn't work correctly
        # when we try to patch docker client with
        # class decorator, it's the reason why
        # we have to do it explicitly
        self.docker_patcher = mock.patch('fuel_upgrade.upgrade.Client')
        self.docker_mock_class = self.docker_patcher.start()
        self.docker_mock = mock.MagicMock()
        self.docker_mock_class.return_value = self.docker_mock

        self.supervisor_patcher = mock.patch('fuel_upgrade.upgrade.SupervisorClient')
        self.supervisor_class = self.supervisor_patcher.start()
        self.supervisor_mock = mock.MagicMock()
        self.supervisor_class.return_value = self.supervisor_mock

        self.update_path = '/tmp/new_update'
        with mock.patch('os.makedirs'):
            self.upgrader = DockerUpgrader(
                self.update_path, self.fake_config)

    def tearDown(self):
        self.docker_patcher.stop()
        self.supervisor_patcher.stop()

    @mock.patch('fuel_upgrade.upgrade.time.sleep')
    def test_run_with_retries(self, sleep, _):
        image_name = 'test_image'
        retries_count = 3

        with self.assertRaises(errors.DockerExecutedErrorNonZeroExitCode):
            self.upgrader.run(
                image_name,
                retry_interval=1,
                retries_count=retries_count)

        self.assertEquals(sleep.call_count, retries_count)
        self.called_once(self.docker_mock.create_container)

    def test_run_without_errors(self, exec_cmd):
        image_name = 'test_image'
        self.docker_mock.wait.return_value = 0

        self.upgrader.run(image_name)

        self.called_once(self.docker_mock.create_container)
        self.called_once(self.docker_mock.logs)
        self.called_once(self.docker_mock.start)
        self.called_once(self.docker_mock.wait)


    def mock_methods(self, obj, methods):
        for method in methods:
            setattr(obj, method, mock.MagicMock())
        
    def test_upgrade(self, _):
        mocked_methods = [
            'stop_fuel_containers',
            'upload_images',
            'run_post_build_actions',
            'create_containers',
            'generate_configs',
            'switch_to_new_configs']

        self.mock_methods(self.upgrader, mocked_methods)
        self.upgrader.upgrade()

        # Check that all methods was called once
        # except stop_fuel_containers method
        for method in mocked_methods[1:-1]:
            self.called_once(getattr(self.upgrader, method))

        self.called_times(self.upgrader.stop_fuel_containers, 3)

        self.called_once(self.supervisor_mock.stop_all_services)
        self.called_once(self.supervisor_mock.restart_and_wait)

    def test_rollback(self, _):
        self.upgrader.stop_fuel_containers = mock.MagicMock()
        self.upgrader.rollback()

        self.called_times(self.upgrader.stop_fuel_containers, 1)
        self.called_once(self.supervisor_mock.switch_to_previous_configs)
        self.called_once(self.supervisor_mock.stop_all_services)
        self.called_once(self.supervisor_mock.restart_and_wait)

    def test_stop_fuel_containers(self, _):
        non_fuel_images = [
            'first_image_1.0', 'second_image_2.0', 'third_image_2.0']
        fuel_images = [
            'fuel/image_1.0', 'fuel/image_2.0']

        all_images = [{'Image': v, 'Id': i}
                      for i, v in enumerate(non_fuel_images + fuel_images)]

        self.docker_mock.containers.return_value = all_images
        self.upgrader.stop_fuel_containers()
        self.assertEquals(
            self.docker_mock.stop.call_args_list, [((3, 10),), ((4, 10),)])

