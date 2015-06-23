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

import abc
import os
import six

from glob import glob
from importlib import import_module


def get_all_extensions():
    files = glob(os.path.join(os.path.dirname(__file__), '*'))
    dirs = filter(lambda f: os.path.isdir(f), files)
    modules = map(lambda d: os.path.basename(d), dirs)
    [import_module('.{0}'.format(module), 'nailgun.extensions') for module in modules]

    return [klass() for klass in BaseExtension.__subclasses__()]


def get_extension(name, version):
    extensions = filter(
        lambda e: e.name == name and e.version == version,
        get_all_extensions())

    if not extensions:
        raise Exception(
            "Cannot find extension with name {0} "
            "and version {1}".format(name, version))

    return extensions[0]


def extension_call(call_name, env=None, node=None):
    found_extension = None
    if node:
        for extension in node.extensions:
            if call_name in get_extension(**extension).provides:
                found_extension = extension

    if not found_extension and env:
        for extension in env.extensions:
            if call_name in get_extension(**extension).provides:
                found_extension = extension

    if not found_extension:
        raise Exception(
            "Cannot find extension which provides '{0}' for environment "
            "'{1}' and for node '{2}'".format(call_name, env, node))

    extension = get_extension(found_extension['name'], found_extension['version'])

    return getattr(extension, call_name)(env, node)


def extensions_fire_callbacks(method, obj):
    for extension in get_all_extensions():
        getattr(extension, method)(obj)


@six.add_metaclass(abc.ABCMeta)
class BaseExtension(object):

    # A mapping of serializers, by default it is empty,
    # here is an example
    # {
    #     "provisioning": [VolumeManagerSerializer],
    #     "deployment": [],
    #     "any_other_action": []
    # }
    #
    # In the future, code from serializers should be moved
    # to separate module which request data from REST API
    serializers = {}
    # If extension provides API, define here urls in the
    # next format:
    # (r'/new/url', HandlerClass,
    #  r'/new/url_2', HandlerClass2)
    urls = ()

    # TODO(eli): think how to make it non alembic specific
    #
    # If extension has alembic migrations, alembic config
    # should be set
    alembic_config = None

    def on_node_create(self, node):
        """Callback which is fired when node
        gets created in the database
        """

    def on_node_update(self, node):
        """Callback which is fired when node
        gets updated. For example discovery
        update the data about the node.
        """

    def on_node_delete(self, node):
        """Callback which is fired when node
        gets deleted
        """

    def on_environment_create(self, environment):
        """Callback gets executed on environment
        creation, can be used to initialize environment
        specific data.
        """

    def on_environment_update(self, environment):
        """Callback gets executed on environment update
        """

    def on_environment_delete(self, environment):
        """Gets executed on environment deletion
        """

    @abc.abstractproperty
    def name(self):
        """Uniq name of the extension"""

    @abc.abstractproperty
    def version(self):
        """Version of the extension, follow semantic
        versioning schema (http://semver.org/)
        """

    @abc.abstractmethod
    def provides(self):
        """A list of keys which describes what extension provides
        """

    @abc.abstractmethod
    def requires(self):
        """A list of keys which specifies what
        extension require for its work
        """
