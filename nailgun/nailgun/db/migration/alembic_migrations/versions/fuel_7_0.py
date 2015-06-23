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

"""Fuel 7.0 migration

Revision ID: 37608259014
Revises: 1b1d4016375d
Create Date: 2015-06-19 11:35:19.872214

"""

# revision identifiers, used by Alembic.
revision = '37608259014'
down_revision = '37608259013'

from alembic import op
from oslo.serialization import jsonutils
import six
import sqlalchemy as sa
from sqlalchemy.sql import text

from nailgun.db.sqlalchemy.models import fields


def upgrade():
    upgrade_schema()
    upgrade_data()


def downgrade():
    downgrade_data()
    downgrade_schema()


def upgrade_schema():
    connection = op.get_bind()

    op.add_column(
        'nodes',
        sa.Column('extensions', fields.JSON(), nullable=True))
    op.add_column(
        'clusters',
        sa.Column('extensions', fields.JSON(), nullable=True))


def downgrade_schema():
    op.drop_column('nodes', 'extensions')
    op.drop_column('clusters', 'extensions')
    

def upgrade_data():
    pass

def downgrade_data():
    pass
