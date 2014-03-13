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
from mock import patch

from fuel_upgrade.tests.base import BaseTestCase
from fuel_upgrade.utils import exec_cmd


class TestUtils(BaseTestCase):

    def test_exec_cmd_executes_sucessfuly(self):
        cmd = 'some command'

        process_mock = mock.Mock()
        with patch.object(
                subprocess, 'Popen', return_value=process_mock) as popen_mock:

            exec_cmd(cmd)

        popen_mock

    def test_exec_cmd_raises_error_in_case_of_non_zero_exit_code(self):
        self.assertEquals(byte_to_megabyte(0), 0)
        self.assertEquals(byte_to_megabyte(1048576), 1)


    def test_calculate_free_space(self):
        dev_info = mock.Mock()
        dev_info.f_bsize = 1048576
        dev_info.f_bavail = 2
        with patch.object(os, 'statvfs', return_value=dev_info) as st_mock:
            self.assertEquals(calculate_free_space('/tmp/dir/file'), 2)

        st_mock.assert_called_once_with('/tmp/dir')

    def test_calculate_md5sum(self):
        open_mock = mock.MagicMock(return_value=FakeFile('fake file content'))
        file_path = '/tmp/file'

        with mock.patch('__builtin__.open', open_mock):
            self.assertEquals(
                calculate_md5sum(file_path),
                '199df6f47108545693b5c9cb5344bf13')

        open_mock.assert_called_once_with(file_path, 'rb')

    def test_download_file(self):
        content = 'Some content'
        fake_src = StringIO(content)
        fake_file = FakeFile('')
        file_mock = mock.MagicMock(return_value=fake_file)

        src_path = 'http://0.0.0.0:80/tmp/file'
        dst_path = '/tmp/file'

        with mock.patch('urllib2.urlopen', return_value=fake_src) as url_fake:
            with mock.patch('__builtin__.open', file_mock):
                download_file(src_path, dst_path)

        file_mock.assert_called_once_with(dst_path, 'wb')
        url_fake.assert_called_once_with(src_path)
        self.assertEquals(fake_file.getvalue(), content)
