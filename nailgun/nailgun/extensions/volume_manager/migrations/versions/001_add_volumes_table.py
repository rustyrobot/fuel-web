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

"""volume_manager_1_0_0

Revision ID: 1a1504d469f999
Revises: None
Create Date: 2015-06-19 16:16:44.513714

"""

# revision identifiers, used by Alembic.
revision = '1a1504d469f999'
down_revision = None

from alembic import op
import sqlalchemy as sa

from nailgun.db.sqlalchemy.models.fields import JSON


def upgrade():
    op.create_table(
        'volume_manager_1_0_0_node_volumes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('volumes', JSON(), nullable=True),
        sa.Column('disks', JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'))


def downgrade():
    op.drop_table('volume_manager_1_0_0_node_volumes')
