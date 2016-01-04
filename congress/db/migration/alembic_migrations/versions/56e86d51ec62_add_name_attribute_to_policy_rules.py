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

"""Add name attribute to policy rules

Revision ID: 56e86d51ec62
Revises: 532e9e1f0f3a
Create Date: 2015-01-14 13:08:53.945019

"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

# revision identifiers, used by Alembic.
revision = '56e86d51ec62'
down_revision = '532e9e1f0f3a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('policy_rules',
                  sa.Column('name', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('policy_rules', 'name')
