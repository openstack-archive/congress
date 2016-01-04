# Copyright 2015 OpenStack Foundation
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
#

"""add_datasources

Revision ID: 3cee191c4f84
Revises: 56e86d51ec62
Create Date: 2015-02-05 13:30:04.272571

"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

# revision identifiers, used by Alembic.
revision = '3cee191c4f84'
down_revision = '56e86d51ec62'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'datasources',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('driver', sa.String(length=255), nullable=True),
        sa.Column('config', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        mysql_engine='InnoDB')


def downgrade():
    op.drop_table('datasources')
