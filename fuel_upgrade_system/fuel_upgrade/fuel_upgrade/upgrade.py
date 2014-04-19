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

import glob
import logging
import os
import time
import traceback

from copy import deepcopy

import requests

from docker import Client

from fuel_upgrade.config import config
from fuel_upgrade import errors
from fuel_upgrade import utils
from fuel_upgrade.utils import exec_cmd
from fuel_upgrade.utils import get_request
from fuel_upgrade.utils import topological_sorting
from fuel_upgrade.supervisor_client import SupervisorClient

logger = logging.getLogger(__name__)


class DockerUpgrader(object):
    """Docker management system for upgrades
    """

    def __init__(self, update_path):
        """Initializes docker upgrade object

        :param update_path: path with files for update
        """
        self.update_path = update_path
        self.working_directory = os.path.join(
            config.working_directory, config.version)

        utils.create_dir_if_not_exists(self.working_directory)

        self.docker_client = Client(
            base_url=config.docker['url'],
            version=config.docker['api_version'],
            timeout=config.docker['http_timeout'])

        self.supervisor = SupervisorClient()

    def upgrade(self):
        """Method with upgarde logic
        """
        self.supervisor.stop_all_services()
        self.stop_fuel_containers()
        self.upload_images()
        self.run_post_build_actions()
        self.stop_fuel_containers()
        self.create_containers()
        self.stop_fuel_containers()
        self.generate_configs()
        self.switch_to_new_configs()

        # Reload configs and run new services
        self.supervisor.restart_and_wait()

    def upload_images(self):
        """Uploads images to docker
        """
        logger.info(u'Start image uploading')
        self.remove_new_release_images()

        for image in self.new_release_images:
            logger.debug(u'Try to upload docker image {0}'.format(image))

            docker_image = image['docker_image']
            if not os.path.exists(docker_image):
                logger.warn(u'Cannot find docker image "{0}"'.format(docker_image))
                continue
            # TODO(eli): maybe it will be better to
            # use docker api here, but in this case
            # we need extra dependencies here to
            # uncompress containers
            utils.exec_cmd(u'xz -dkc "{0}" | docker load'.format(
                docker_image, image['name']))

    def backup(self):
        """We don't need to backup containers
        because we don't remove current version.
        As result here we run backup of database.
        """
        pass
        # self.backup_db()

    def create_containers(self):
        """Create containers in the right order
        """
        logger.info(u'Started containers creation')
        graph = self.build_dependencies_graph(self.new_release_containers)
        logger.debug(u'Built dependencies graph {0}'.format(graph))
        containers_to_creation = topological_sorting(graph)
        logger.debug(u'Resolved creation order {0}'.format(
            containers_to_creation))

        for container_id in containers_to_creation:
            container = self.container_by_id(container_id)
            logger.debug(u'Started  {0}'.format(container))

            volumes_from = []
            if container.get('volumes_from'):
                for container_id in container.get('volumes_from'):
                    volume_container = self.container_by_id(container_id)
                    volumes_from.append(volume_container['container_name'])

            links = []
            if container.get('links'):
                for container_link in container.get('links'):
                    link_container = self.container_by_id(container_link['id'])
                    links.append((link_container['container_name'], container_link['alias']))

            created_container = self.create_container(
                container['image_name'],
                name=container.get('container_name'),
                volumes=container.get('volumes'),
                volumes_from=','.join(volumes_from),
                detach=False)

            self.start_container(
                created_container,
                port_bindings=container.get('port_bindings'),
                links=links,
                binds=container.get('binds'))

    @classmethod
    def build_dependencies_graph(cls, containers):
        """Builds graph which based on
        `volumes_from` and `link` parameters
        of container.

        :returns: dict where keys are nodes and
                  values are lists of dependencies
        """
        graph = {}
        for container in containers:
            graph[container['id']] = list(set(
                container.get('volumes_from', []) +
                [link['id'] for link in container.get('links', [])]))

        return graph

    def generate_configs(self):
        """Generates supervisor configs
        and saves them to configs directory
        """
        configs = []

        for container in self.new_release_containers:
            params = {
                'service_name': container['id'],
                'command': u'docker start -a {0}'.format(
                    container['container_name'])
            }
            configs.append(params)

        self.supervisor.generate_configs(configs)

    def switch_to_new_configs(self):
        """Switches supervisor to new configs
        """
        self.supervisor.switch_to_new_configs()

    def volumes_dependencies(self, container):
        """Get list of `volumes` dependencies

        :param contaienr: dict with information about container
        """
        return self.dependencies_names(container, 'volumes_from')

    def link_dependencies(self, container):
        """Get list of `link` dependencies

        :param contaienr: dict with information about container
        """
        return self.dependencies_names(container, 'link')

    def dependencies_names(self, container, key):
        """Returns list of dependencies for specified key

        :param contaienr: dict with information about container
        :param key: key which will be used for dependencies retrieving

        :returns: list of container names
        """
        names = []
        if container.get(key):
            for container_id in container.get(key):
                container = self.container_by_id(container_id)
                names.append(container['container_name'])

        return names

    def backup_db(self):
        """Backup postgresql database
        """
        logger.debug(u'Backup database')
        pg_dump_path = os.path.join(self.working_directory, 'pg_dump_all.sql')
        if os.path.exists(pg_dump_path):
            logger.info(u'Database backup exists "{0}", '
                        'do nothing'.format(pg_dump_path))
            return

        try:
            exec_cmd(u"su postgres -c 'pg_dumpall' > '{0}'".format(pg_dump_path))
        except errors.ExecutedErrorNonZeroExitCode:
            if os.path.exists(pg_dump_path):
                logger.info(u'Remove postgresql dump file because '
                            'it failed {0}'.format(pg_dump_path))
                os.remove(pg_dump_path)
            raise

    def stop_fuel_containers(self):
        """Use docker API to shutdown containers
        """
        containers = self.docker_client.containers(limit=-1)
        containers_to_stop = filter(
            lambda c: c['Image'].startswith(config.image_prefix),
            containers)

        for container in containers_to_stop:
            logger.debug(u'Stop container: {0}'.format(container))

            try:
                self.docker_client.stop(
                    container['Id'], config.docker['stop_container_timeout'])
            except requests.exceptions.Timeout:
                # NOTE(eli): docker use SIGTERM signal
                # to stop container if timeout expired
                # docker use SIGKILL to stop container.
                # Here we just want to make sure that
                # container was stopped.
                logger.warn(
                    u'Couldn\'t stop ctonainer, try '
                    'to stop it again: {0}'.format(container))
                self.docker_client.stop(
                    container['Id'], config.docker['stop_container_timeout'])

    def run_post_build_actions(self):
        """Run db migration for installed services
        """
        logger.info(u'Run data container')
        data_container = self.container_by_id('data')
        binded_volumes = dict([(v, v) for v in data_container['volumes']])
        self.run(
            data_container['image_name'],
            name=data_container['container_name'],
            volumes=data_container['volumes'],
            command=data_container['post_build_command'],
            binds=binded_volumes,
            detach=True)

        logger.info(u'Run postgresql container')
        pg_container = self.container_by_id('postgresql')
        self.run(
            pg_container['image_name'],
            volumes_from=data_container['container_name'],
            ports=pg_container['ports'],
            port_bindings=pg_container['port_bindings'],
            detach=True)

        logger.info(u'Run db migration for nailgun')
        nailgun_container = self.container_by_id('nailgun')
        self.run(
            nailgun_container['image_name'],
            command=nailgun_container['post_build_command'],
            retry_interval=2,
            retries_count=3)

    def run(self, image_name, **kwargs):
        """Run container from image, accepts the
        same parameters as `docker run` command.
        """
        retries = [None]
        retry_interval = kwargs.pop('retry_interval', 0)
        retries_count = kwargs.pop('retries_count', 0)
        if retry_interval and retries_count:
            retries = [retry_interval] * retries_count

        params = deepcopy(kwargs)
        start_command_keys = [
            'lxc_conf', 'port_bindings', 'binds',
            'publish_all_ports', 'links', 'privileged']

        start_params = {}
        for start_command_key in start_command_keys:
            start_params[start_command_key] = params.pop(
                start_command_key, None)

        container = self.create_container(image_name, **params)
        self.start_container(container, **start_params)

        if not params.get('detach'):
            for interval in retries:
                logs = self.docker_client.logs(container['Id'], stream=True)
                for log_line in logs:
                    logger.debug(log_line.rstrip())

                exit_code = self.docker_client.wait(container['Id'])
                if exit_code == 0:
                    break

                if interval is not None:
                    logger.warn(u'Failed to run container "{0}": {1}'.format(
                        container['Id'], start_params))
                    time.sleep(interval)
                    self.docker_client.start(container['Id'], **start_params)
            else:
                if exit_code > 0:
                    raise errors.DockerExecutedErrorNonZeroExitCode(
                        u'Failed to execute migraion command "{0}" '
                        'exit code {1} container id {2}'.format(
                            params.get('command'), exit_code, container['Id']))

        return container

    def start_container(self, container, **params):
        """Start containers

        :param container: container name
        :param params: dict of arguments for container starting
        """
        logger.debug(u'Start container "{0}": {1}'.format(
            container['Id'], params))
        self.docker_client.start(container['Id'], **params)

    def create_container(self, image_name, **params):
        """Create container

        :param image_name: name of image
        :param params: parameters format equals to
                       create_container call of docker
                       client
        """
        # We have to delete container because we cannot
        # have several containers with the same name
        if params.get('name') is not None:
            self._delete_container_if_exist(params.get('name'))

        logger.debug(u'Create container from image {0}: {1}'.format(
            image_name, params))

        return self.docker_client.create_container(image_name, **params)

    @property
    def new_release_containers(self):
        """Returns list of dicts with information
        for new containers.
        """
        new_containers = []

        for container in config.containers:
            new_container = deepcopy(container)
            new_container['image_name'] = self.make_image_name(
                container['from_image'])
            new_container['container_name'] = u'{0}{1}_{2}'.format(
                config.container_prefix, container['id'], config.version)
            new_containers.append(new_container)

        return new_containers

    @property
    def new_release_images(self):
        """Returns list of dicts with information
        for new images.
        """
        new_images = []

        for image in config.images:
            new_image = deepcopy(image)
            new_image['name'] = self.make_image_name(
                image['id'])
            new_image['docker_image'] = os.path.join(
                self.update_path,
                image['id'] + '.' + config.images_extension)
            new_image['docker_file'] = os.path.join(
                self.update_path, image['id'])

            new_images.append(new_image)

        return new_images

    def make_image_name(self, name):
        return u'{0}{1}_{2}'.format(
            config.image_prefix, name, config.version)

    def container_by_id(self, container_id):
        """Get container from new release by id

        :param container_id: id of container
        """
        return filter(
            lambda c: c['id'] == container_id,
            self.new_release_containers)[0]

    def remove_new_release_images(self):
        """We need to remove images for current release
        because this script can be run several times
        and we have to delete images before images
        building
        """
        image_names = [c['name'] for c in self.new_release_images]
        for image in image_names:
            self._delete_containers_for_image(image)
            if self.docker_client.images(name=image):
                logger.info(u'Remove image for new version {0}'.format(
                    container))
                self.docker_client.remove_image(image)

    def _delete_container_if_exist(self, container_id):
        """Deletes docker container if it exists

        :param container_id: id of container
        """
        found_containers = filter(
            lambda c: u'/{0}'.format(container_id) in c['Names'],
            self.docker_client.containers(all=True))

        for container in found_containers:
            logger.debug(u'Delete container {0}'.format(container))
            self.docker_client.remove_container(container['Id'])

    def _delete_containers_for_image(self, image):
        """Deletes docker containers for specified image

        :param image: name of image
        """
        all_containers = self.docker_client.containers(all=True)

        containers = filter(
            # NOTE(eli) :We must use convertation to
            # str because in some cases Image is integer
            lambda c: str(c.get('Image')).startswith(image),
            all_containers)

        for container in containers:
            logger.debug(u'Try to stop container {0} which '
                         'depends on image {1}'.format(container['Id'], image))
            self.docker_client.stop(container['Id'])
            logger.debug(u'Delete container {0} which '
                         'depends on image {1}'.format(container['Id'], image))
            self.docker_client.remove_container(container['Id'])


class DockerInitializer(DockerUpgrader):
    """Logic for docker containers installation
    on new system. Used for development.
    """

    def upgrade(self):
        self.build_images()
        self.run_post_build_actions()
        self.stop_fuel_containers()
        self.create_containers()
        self.stop_fuel_containers()
        self.generate_configs()
        self.switch_to_new_configs()

        # Reload configs and run new services
        self.supervisor.restart_and_wait()

    def build_images(self):
        """Use docker API to build new containers
        """
        self.remove_new_release_images()

        for image in self.new_release_images:
            logger.info(u'Start image building: {0}'.format(image))
            self.docker_client.build(
                path=image['docker_file'],
                tag=image['name'],
                nocache=True)

            # NOTE(eli): 0.10 and early versions of
            # Docker api dont't return correct http
            # response in case of failed build, here
            # we check if build succed and raise error
            # if it failed i.e. image was not created
            if not self.docker_client.images(name=image):
                raise errors.DockerFailedToBuildImageError(
                    u'Failed to build image {0}'.format(image))

    def rollback(self):
        logger.warn(u"DockerInitializer doesn't support rollback")

    def make_backup(self):
        logger.warn(u"DockerInitializer doesn't support rollback")



class Upgrade(object):
    """Upgrade logic
    """

    def __init__(self,
                 update_path,
                 upgrade_engine,
                 disable_rollback=False):

        logger.debug(
            u'Create Upgrade object with update path "{0}", '
            'upgrade engine "{1}", '
            'disable rollback is "{2}"'.format(
                update_path,
                upgrade_engine.__class__.__name__,
                disable_rollback))

        self.update_path = update_path
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
        # self.check_upgrade_opportunity()
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
                t.get('id'),
                t.get('cluster'),
                t.get('name')) for t in running_tasks]

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
