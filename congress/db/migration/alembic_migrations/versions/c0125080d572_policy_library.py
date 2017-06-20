# Copyright 2017 OpenStack Foundation
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

"""policy library

Revision ID: c0125080d572
Revises: aabe895bbd4d
Create Date: 2017-06-21 13:20:14.529313

"""

# revision identifiers, used by Alembic.
revision = 'c0125080d572'
down_revision = 'aabe895bbd4d'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'library_policies',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True),
        sa.Column('abbreviation', sa.String(length=5), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('kind', sa.Text(), nullable=False),
        sa.Column('rules', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        mysql_engine='InnoDB'
    )


def downgrade():
    op.drop_table('library_policies')
