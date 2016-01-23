# Copyright 2014 OpenStack Foundation
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

"""add_policy

Revision ID: 532e9e1f0f3a
Revises: initial_db
Create Date: 2014-12-18 14:52:20.402861

"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

# revision identifiers, used by Alembic.
revision = '532e9e1f0f3a'
down_revision = 'initial_db'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('policies',
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('deleted_at', sa.DateTime(), nullable=True),
                    sa.Column('deleted', sa.String(length=36),
                              server_default='', nullable=True),
                    sa.Column('name', sa.Text(), nullable=False),
                    sa.Column('abbreviation', sa.String(length=5),
                              nullable=False),
                    sa.Column('description', sa.Text(), nullable=False),
                    sa.Column('owner', sa.Text(), nullable=False),
                    sa.Column('kind', sa.Text(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    mysql_engine='InnoDB')


def downgrade():
    op.drop_table('policies')
