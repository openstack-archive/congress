# Copyright 2016 OpenStack Foundation
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

"""add datasource data persistence

Revision ID: 01e78af70b91
Revises: 3cee191c4f84
Create Date: 2016-07-29 17:02:40.026610

"""

# revision identifiers, used by Alembic.
revision = '01e78af70b91'
down_revision = '3cee191c4f84'

from alembic import op
import sqlalchemy as sa


def upgrade():
    if op.get_bind().engine.dialect.name == 'mysql':
        # NOTE: Specify a length long enough to choose MySQL
        # LONGTEXT
        text_type = sa.Text(length=1000000000)
    else:
        text_type = sa.Text()

    op.create_table(
        'dstabledata',
        sa.Column('ds_id', sa.String(length=36), nullable=False),
        sa.Column('tablename', sa.String(length=255), nullable=False),
        sa.Column('tabledata', text_type, nullable=False),
        sa.PrimaryKeyConstraint('ds_id', 'tablename'),
        mysql_engine='InnoDB')


def downgrade():
    op.drop_table('dstabledata')
