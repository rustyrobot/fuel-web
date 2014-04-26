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
import logging
import xmlrpclib
import supervisor.xmlrpc
import stat

from xmlrpclib import Fault

from fuel_upgrade import utils
from fuel_upgrade.config import config

logger = logging.getLogger(__name__)
TEMPLATES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'templates'))

import httplib
import socket


class SupervisorClient(object):

    def __init__(self):
        self.supervisor_template_path = os.path.join(
            TEMPLATES_DIR, 'supervisor.conf')
        self.supervisor_common_template_path = os.path.join(
            TEMPLATES_DIR, 'common.conf')
        self.supervisor_config_dir = os.path.join(
            config.supervisor['configs_prefix'], config.version)

        utils.create_dir_if_not_exists(self.supervisor_config_dir)

    @property
    def supervisor(self):
        """Returns supervisor rpc object
        """
        # TODO(eli): remove dependencies on supervisor
        # implement unix socket connecter
        self.server = xmlrpclib.Server(
            'http://127.0.0.1',
            transport=supervisor.xmlrpc.SupervisorTransport(
                None, None, serverurl=config.supervisor['endpoint']))

        return self.server.supervisor

    def switch_to_new_configs(self):
        """Switch to new version of configs
        for supervisor. Creates symlink on special
        directory.
        """
        current_cfg_path = config.supervisor['current_configs_prefix']
        logger.debug(u'Create symlink from "{0}" to "{1}"'.format(
            self.supervisor_config_dir, current_cfg_path))
        if os.path.exists(current_cfg_path):
            os.remove(current_cfg_path)
            os.symlink(
                self.supervisor_config_dir,
                current_cfg_path)

    def stop_all_services(self):
        """Stops all processes
        """
        logger.info(u'Stop all services')
        self.supervisor.stopAllProcesses()

    def restart_and_wait(self):
        """Restart supervisor and wait untill it will be available
        """
        logger.info(u'Restart supervisor')
        self.stop_fuel_services()
        self.supervisor.restart()

        def get_all_processes():
            try:
                return self.supervisor.getAllProcessInfo()
            except IOError, Fault:
                return False

        all_processes = utils.wait_for_true(
            get_all_processes,
            timeout=config.supervisor['restart_timeout'])

        logger.debug(u'List of supervisor processes {0}'.format(
            all_processes))

    def generate_configs(self, services):
        """Generates supervisor configs for services

        :param services: list of dicts where `service_name`
                         and `command` are required fields
        """
        logger.info(
            u'Generate supervisor configs for services {0}'.format(services))

        for service in services:
            self.generate_config(service)

        names = [service['service_name'] for service in services]

    def generate_cobbler_config(self, container):
        """Generates 

        :param container: dict `service_name` `container_name`
        """
        container_name = container['container_name']
        script_path = os.path.join('/usr/bin', container_name)
        script_template_path = os.path.join(
            TEMPLATES_DIR, 'cobbler_runner')

        utils.render_template_to_file(
            script_template_path,
            script_path,
            {'container_name': container_name})

        self.generate_config({
            'service_name': container['service_name'],
            'command': container_name})

        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)
