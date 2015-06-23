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


from nailgun.db import db
from ..models.volumes import NodeVolumes


# TODO(eli): Should we use here NailgunObject?
class VolumesObject(object):

    @classmethod
    def get_model_by_node_id(cls, node_id):
        models = db().query(NodeVolumes).filter_by(node_id=node_id).all()
        if models:
            return models[0]

        return None

    @classmethod
    def get_volumes_by_node_id(cls, node_id):
        volume_db = cls.get_model_by_node_id(node_id)
        if volume_db:
            return volume_db.volumes

        return None

    @classmethod
    def generate_default_volumes(cls, node):
        return cls.volume_manager_for_node(node).gen_volumes_info()

    @classmethod
    def reset_volumes(cls, node):
        # TODO Check that there is no other entries for this node
        cls.update_or_create_entry(node.id, cls.generate_default_volumes(node), node.meta.get('disks', []))

    @classmethod
    def update_or_create_entry(cls, node_id, volumes, disks):
        volume_db = cls.get_model_by_node_id(node_id)

        if volume_db:
            volume_db.volumes = volumes
            volume_db.disks = disks
            db().flush()

        volumes = NodeVolumes(
            node_id=node_id,
            volumes=volumes,
            disks=disks)
        db().add(volumes)
        db().flush()

    @classmethod
    def volume_manager_for_node(cls, node):
        from ..manager import VolumeManager
        return VolumeManager(node)

    @classmethod
    def set_volumes(cls, node, volumes_data):
        cls.update_or_create_entry(node.id, volumes_data, node.meta.get('disks', []))
        volume_db = cls.get_model_by_node_id(node.id)
        volume_db.volumes = volumes_data
        db().flush()
