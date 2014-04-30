"""Migration for upgrades testing fuel_5_1

Revision ID: 12d8dfb6d412
Revises: 4f21f21e2672
Create Date: 2014-04-30 15:25:49.769207

"""

# revision identifiers, used by Alembic.
revision = '12d8dfb6d412'
down_revision = '1a1504d469f8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('nodes', sa.Column('uuuuuupgrade_field', sa.String(length=36), nullable=True))


def downgrade():
    op.drop_column('nodes', 'uuuuuupgrade_field')
