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

import logging
import os
import traceback

from docker import Client

from fuel_upgrade import errors
from fuel_upgrade.utils import exec_cmd
from fuel_upgrade.utils import get_request
from fuel_upgrade.config import config

logger = logging.getLogger(__name__)


class DockerUpgrader(object):
    """Puppet implementation of upgrader
    """

    def __init__(self, update_path):
        puppet_modules_path = os.path.join(
            update_path, config.puppet_modules_dir)

        self.puppet_cmd = u'puppet apply --debug --modulepath={0} -e '.format(
            puppet_modules_path)

        self.update_path = update_path
        self.working_directory = os.path.join(
            config.working_directory, config.version)

        if not os.path.isdir(self.working_directory):
            os.makedirs(self.working_directory)

        self.docker_client = Client(
            base_url=config.docker['url'],
            version=config.docker['api_version'],
            timeout=config.docker['http_timeout'])

    def upgrade(self):
        # self._upgrade_master_node()
        self._build_containers()
        self._run_migration()
        # self._shutdown_containers()

    def rollback(self):
        exec_cmd(self.puppet_cmd + '"include rollback"')

    def backup(self):
        """We don't need to backup containers
        because we don't remove current version.
        As result here we just shutdown containers
        and run backup of postgresql.
        """
        self._backup_db()

    def _backup_db(self):
        logger.debug('Backup database')
        pg_dump_path = os.path.join(self.working_directory, 'pg_dump_all.sql')
        exec_cmd("su postgres -c 'pg_dumpall' > {0}".format(pg_dump_path))

    def _shutdown_containers(self):
        """Use docker API to shutdown containers
        """
        containers = self.docker_client.containers(limit=-1)
        containers_to_stop = filter(
            lambda c: c['Image'].startswith(config.container_prefix),
            containers)

        for container in containers_to_stop:
            self.docker_client.stop(
                container['Id'], config.docker['stop_container_timeout'])

    def _upgrade_master_node(self):
        exec_cmd(self.puppet_cmd + '"include master node"')

    def _build_containers(self):
        """Use docker API to build new containers
        """
        self._remove_new_release_images()

        for container in self.new_release_containers:
            logger.info('Start container building "{0}" with name "{1}"'.format(
                container['docker_file'], container['name']))
            self.docker_client.build(
                path=container['docker_file'],
                tag=container['name'],
                nocache=True)

    def _remove_new_release_images(self):
        """We need to remove images for current release
        because this script can be run several times
        and we have to delete images before images
        building
        """
        names = [c['name'] for c in self.new_release_containers]
        for container in names:
            if self.docker_client.images(name=container):
                logger.info('Remove image for new version {0}'.format(
                    container))
                self.docker_client.remove_image(container)

    def _run_migration(self):
        """Get list of containers which were
        installed (it can happen in case if upgrade
        was runned several times).
        Make and return list of containers to creation.
        """
        return

    @property
    def new_release_containers(self):
        """Returns list of dicts with container names
        for new release, fuel/container_name/version
        and paths to Dockerfile.
        """
        container_names = [c[0] for c in config.containers.iteritems()]
        new_containers = []

        for container in container_names:
            new_container = {}
            new_container['name'] = '{0}{1}/{2}'.format(
                config.container_prefix, container, config.version)
            new_container['docker_file'] = os.path.join(
                self.update_path, container)
            new_containers.append(new_container)

        return new_containers


class Upgrade(object):
    """Upgrade logic
    """

    def __init__(self,
                 update_path,
                 working_dir,
                 upgrade_engine,
                 disable_rollback=False):

        logger.debug(
            u'Create Upgrade object with update path "{0}", '
            'working directory "{1}", '
            'upgrade engine "{2}", '
            'disable rollback is "{3}"'.format(
                update_path, working_dir,
                upgrade_engine.__class__.__name__,
                disable_rollback))

        self.update_path = update_path
        self.working_dir = working_dir
        self.upgrade_engine = upgrade_engine
        self.disable_rollback = disable_rollback

    def run(self):
        self.before_upgrade()

        try:
            self.upgrade()
            self.after_upgrade()
        except Exception as exc:
            logger.error(u'Upgrade failed: {0}'.format(exc))
            logger.error(traceback.format_exc())
            if not self.disable_rollback:
                self.rollback()

    def before_upgrade(self):
        logger.debug('Run before upgrade actions')
        self.check_upgrade_opportunity()
        self.make_backup()

    def upgrade(self):
        logger.debug('Run upgrade')
        self.upgrade_engine.upgrade()

    def after_upgrade(self):
        logger.debug('Run after upgrade actions')
        self.run_services()
        self.check_health()

    def make_backup(self):
        logger.debug('Run system backup')
        self.upgrade_engine.backup()

    def check_upgrade_opportunity(self):
        """Sends request to nailgun
        to make sure that there are no
        running tasks
        """
        logger.info('Check upgrade opportunity')
        nailgun = config.endpoints['nailgun']
        tasks_url = 'http://{0}:{1}/api/v1/tasks'.format(
            nailgun['host'], nailgun['port'])

        tasks = get_request(tasks_url)

        running_tasks = filter(
            lambda t: t['status'] == 'running', tasks)

        if running_tasks:
            tasks_msg = ['id={0} cluster={1} name={2}'.format(
                t['id'], t['cluster'], t['name']) for t in running_tasks]

            error_msg = 'Cannot run upgrade, tasks are running: {0}'.format(
                ' '.join(tasks_msg))

            raise errors.CannotRunUpgrade(error_msg)

    def run_services(self):
        logger.debug('Run services')

    def check_health(self):
        logger.debug('Check that upgrade passed correctly')

    def rollback(self):
        logger.debug('Run rollback')
        self.upgrade_engine.rollback()
