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

"""poliy name uniqueness

Revision ID: aabe895bbd4d
Revises: 01e78af70b91
Create Date: 2016-11-04 13:55:05.064012

"""

# revision identifiers, used by Alembic.
revision = 'aabe895bbd4d'
down_revision = '01e78af70b91'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('policiesdeleted',
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('deleted_at', sa.DateTime(), nullable=True),
                    sa.Column('deleted', sa.String(length=36),
                              server_default='', nullable=True),
                    sa.Column('name', sa.String(length=255), nullable=False),
                    sa.Column('abbreviation', sa.String(length=5),
                              nullable=False),
                    sa.Column('description', sa.Text(), nullable=False),
                    sa.Column('owner', sa.Text(), nullable=False),
                    sa.Column('kind', sa.Text(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    mysql_engine='InnoDB')

    # copy all rows from table:policies to table:policiesdeleted
    # table:policiesdeleted used as temporary space while we recreate
    # table:policies with the right column:name type to support index/unique
    # recreate table rather than ALTER to generically support most backends
    try:
        op.execute(
            "INSERT INTO policiesdeleted "
            "SELECT * FROM policies")
    except Exception:
        # if copying of rows fail (likely because a name is longer than 255
        # stop upgrade and cleanup
        op.drop_table('policiesdeleted')
        raise

    # drop and recreate table:policies
    op.drop_table('policies')
    op.create_table('policies',
                    sa.Column('id', sa.String(length=36), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('deleted_at', sa.DateTime(), nullable=True),
                    sa.Column('deleted', sa.String(length=36),
                              server_default='', nullable=True),
                    sa.Column('name', sa.String(length=255), nullable=False),
                    sa.Column('abbreviation', sa.String(length=5),
                              nullable=False),
                    sa.Column('description', sa.Text(), nullable=False),
                    sa.Column('owner', sa.Text(), nullable=False),
                    sa.Column('kind', sa.Text(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    mysql_engine='InnoDB')

    # copy non-(soft)deleted rows back into table:policies
    op.execute("INSERT INTO policies "
               "SELECT * FROM policiesdeleted WHERE deleted = ''")

    # delete non-(soft)deleted rows from table:policiesdeleted
    op.execute("DELETE FROM policiesdeleted WHERE deleted = ''")

    op.create_unique_constraint(None, 'policies', ['name'])


def downgrade():
    # drop and recreate table:policies with right column:name type
    # using table:policiesdeleted as temporary work space

    op.execute("INSERT INTO policiesdeleted SELECT * FROM policies")
    op.drop_table('policies')
    # op.drop_constraint(None, 'policies', type_='unique')
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

    # move all rows (deleted or not) into table:policies
    op.execute("INSERT INTO policies SELECT * FROM policiesdeleted")
    op.drop_table('policiesdeleted')
