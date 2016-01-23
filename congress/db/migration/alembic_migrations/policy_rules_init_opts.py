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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'policy_rules',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('rule', sa.Text, nullable=False),
        sa.Column('comment', sa.String(length=255), nullable=False),
        sa.Column('policy_name', sa.String(length=255), nullable=False),
        sa.Column('deleted', sa.String(length=36), server_default="",
                  nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'))


def downgrade():
    op.drop_table('policy_rules')
