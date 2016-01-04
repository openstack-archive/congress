# Copyright (c) 2014 OpenStack Foundation.
# All Rights Reserved.
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

"""
The module provides all database models at current HEAD.

Its purpose is to create comparable metadata with current database schema.
Based on this comparison database can be healed with healing migration.

"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from congress.db import datasources  # noqa
from congress.db import db_policy_rules  # noqa
from congress.db import model_base


def get_metadata():
    return model_base.BASE.metadata
