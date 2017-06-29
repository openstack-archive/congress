# Copyright (c) 2017 VMware, Inc. All rights reserved.
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

import copy

from oslo_db import exception as db_exc
from oslo_log import log as logging

from congress.datalog import compile
from congress.db import db_library_policies
from congress.dse2 import data_service
from congress import exception

LOG = logging.getLogger(__name__)


class LibraryService (data_service.DataService):
    def __init__(self, name):
        data_service.DataService.__init__(self, name)
        self.name = name
        self.add_rpc_endpoint(DseLibraryServiceEndpoints(self))

    def create_policy(self, policy_dict):
        policy_dict = copy.deepcopy(policy_dict)
        policy_name = policy_dict['name']

        # check name is valid
        if not compile.string_is_servicename(policy_name):
            raise exception.PolicyException(
                'name `%s` is not a valid policy name' % policy_name)

        # make defaults
        if 'kind' not in policy_dict:
            policy_dict['kind'] = 'nonrecursive'
        if 'abbreviation' not in policy_dict:
            policy_dict['abbreviation'] = policy_name[:5]
        if 'description' not in policy_dict:
            policy_dict['description'] = ''

        try:
            # Note(thread-safety): blocking call
            policy = db_library_policies.add_policy(policy_dict=policy_dict)
            return policy.to_dict()
        except db_exc.DBError:
            LOG.exception('Creating a new library policy failed.')
            raise

    def get_policies(self, include_rules=True):
        return [p.to_dict(include_rules)
                for p in db_library_policies.get_policies()]

    def get_policy(self, id_, include_rules=True):
        # Note(thread-safety): blocking call
        policy = db_library_policies.get_policy(id_)
        return policy.to_dict(include_rules)

    def delete_all_policies(self):
        # Note(thread-safety): blocking call
        db_library_policies.delete_policies()

    def delete_policy(self, id_):
        # Note(thread-safety): blocking call
        db_object = db_library_policies.get_policy(id_)
        db_library_policies.delete_policy(id_)
        return db_object.to_dict(include_rules=True)

    def replace_policy(self, id_, policy_dict):
        policy_name = policy_dict['name']

        # check name is valid
        if not compile.string_is_servicename(policy_name):
            raise exception.PolicyException(
                "Policy name %s is not a valid service name" % policy_name)

        # make defaults
        if 'kind' not in policy_dict:
            policy_dict['kind'] = 'nonrecursive'
        if 'abbreviation' not in policy_dict:
            policy_dict['abbreviation'] = policy_name[:5]
        if 'description' not in policy_dict:
            policy_dict['description'] = ''

        # Note(thread-safety): blocking call
        policy = db_library_policies.replace_policy(
            id_, policy_dict=policy_dict)
        return policy.to_dict()


class DseLibraryServiceEndpoints(object):
    """RPC endpoints exposed by LibraryService."""

    def __init__(self, data_service):
        self.data_service = data_service

    def create_policy(
            self, context, policy_dict):
        return self.data_service.create_policy(
            policy_dict)

    def get_policies(self, context, include_rules=True):
        return self.data_service.get_policies(include_rules)

    def get_policy(self, context, id_, include_rules=True):
        return self.data_service.get_policy(id_, include_rules)

    def delete_all_policies(self, context):
        return self.data_service.delete_all_policies()

    def delete_policy(self, context, id_):
        return self.data_service.delete_policy(id_)

    def replace_policy(self, context, id_, policy_dict):
        return self.data_service.replace_policy(id_, policy_dict)
