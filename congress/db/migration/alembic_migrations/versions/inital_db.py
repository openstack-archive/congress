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

"""initial_db

Revision ID: initial_db
Revises: None

"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

# revision identifiers, used by Alembic.
revision = 'initial_db'
down_revision = None

from congress.db.migration.alembic_migrations import policy_rules_init_opts


def upgrade():
    policy_rules_init_opts.upgrade()


def downgrade():
    policy_rules_init_opts.downgrade()
