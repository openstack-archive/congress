# Copyright (c) 2017 VMware Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import copy

from congress.api import webservice
from congress.db import db_library_policies
from congress.tests.api import base as api_base
from congress.tests import base


class TestLibraryPolicyModel(base.SqlTestCase):
    def setUp(self):
        super(TestLibraryPolicyModel, self).setUp()

        services = api_base.setup_config()
        self.library_policy_model = services['api']['api-library-policy']
        self.node = services['node']
        self.engine = services['engine']

        # clear the library policies loaded on startup
        db_library_policies.delete_policies()

        self._add_test_policy()

    def _add_test_policy(self):
        test_policy = {
            "name": "test_policy",
            "description": "test policy description",
            "kind": "nonrecursive",
            "abbreviation": "abbr",
            "rules": [{"rule": "p(x) :- q(x)", "comment": "test comment",
                       "name": "test name"},
                      {"rule": "p(x) :- q2(x)", "comment": "test comment2",
                       "name": "test name2"}]
        }
        test_policy_id, obj = self.library_policy_model.add_item(
            test_policy, {})
        test_policy["id"] = test_policy_id

        test_policy2 = {
            "name": "test_policy2",
            "description": "test policy2 description",
            "kind": "nonrecursive",
            "abbreviation": "abbr2",
            "rules": []
        }
        test_policy_id, obj = self.library_policy_model.add_item(
            test_policy2, {})
        test_policy2["id"] = test_policy_id

        self.policy = test_policy
        self.policy2 = test_policy2

        self.policy_metadata = copy.deepcopy(test_policy)
        self.policy2_metadata = copy.deepcopy(test_policy2)
        del self.policy_metadata['rules']
        del self.policy2_metadata['rules']

    def test_get_items(self):
        ret = self.library_policy_model.get_items({})
        self.assertTrue(all(p in ret['results']
                            for p in [self.policy,
                                      self.policy2]))

        ret = self.library_policy_model.get_items({'include_rules': 'False'})
        self.assertTrue(all(p in ret['results']
                            for p in [self.policy_metadata,
                                      self.policy2_metadata]))

    def test_get_items_by_name(self):
        ret = self.library_policy_model.get_items(
            {'name': 'no-such-policy'})
        self.assertEqual(ret['results'], [])

        ret = self.library_policy_model.get_items(
            {'name': self.policy['name']})
        self.assertEqual(ret['results'], [self.policy])

    def test_get_item(self):
        expected_ret = self.policy
        ret = self.library_policy_model.get_item(self.policy["id"], {})
        self.assertEqual(expected_ret, ret)

        ret = self.library_policy_model.get_item(self.policy["id"],
                                                 {'include_rules': 'False'})
        del expected_ret['rules']
        self.assertEqual(expected_ret, ret)

    def test_get_invalid_item(self):
        self.assertRaises(KeyError,
                          self.library_policy_model.get_item,
                          'invalid-id', {})

    def test_add_item(self):
        test = {
            "name": "test",
            "description": "test description",
            "kind": "nonrecursive",
            "abbreviation": "abbr",
            "rules": []
        }
        expected_ret = copy.deepcopy(test)
        del expected_ret['rules']

        policy_id, policy_obj = self.library_policy_model.add_item(test, {})
        test['id'] = policy_id
        self.assertEqual(test, policy_obj)

    def test_add_item_duplicate_name(self):
        test = {
            "name": "test_policy",
            "description": "test description",
            "kind": "nonrecursive",
            "abbreviation": "abbr",
            "rules": []
        }
        # duplicate name allowed
        self.assertRaises(KeyError,
                          self.library_policy_model.add_item, test, {})
        ret = self.library_policy_model.get_items({})
        self.assertEqual(len(ret['results']), 2)

    def test_add_item_with_id(self):
        test = {
            "name": "test",
            "description": "test description",
            "kind": "nonrecursive",
            "abbreviation": "abbr",
            "rules": []
        }

        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.add_item, test, {}, 'id')

    def test_add_item_without_name(self):
        test = {
            "description": "test description",
            "kind": "nonrecursive",
            "abbreviation": "abbr"
        }

        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.add_item, test, {})

    def test_add_item_with_long_abbreviation(self):
        test = {
            "name": "test",
            "description": "test description",
            "kind": "nonrecursive",
            "abbreviation": "123456",
            "rules": []
        }
        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.add_item, test, {})

    def test_replace_item_without_name(self):
        test = {
            "description": "test description",
            "kind": "nonrecursive",
            "abbreviation": "abbr"
        }

        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.replace_item,
                          self.policy['id'], test, {})

    def test_replace_item_with_long_abbreviation(self):
        test = {
            "name": "test",
            "description": "test description",
            "kind": "nonrecursive",
            "abbreviation": "123456",
            "rules": []
        }
        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.replace_item,
                          self.policy['id'], test, {})

    def test_delete_item(self):
        # delete non-existent policy
        self.assertRaises(KeyError, self.library_policy_model.delete_item,
                          'no_such_policy', {})

        # delete existing policy
        expected_ret = self.policy
        policy_id = self.policy['id']

        ret = self.library_policy_model.delete_item(policy_id, {})
        self.assertEqual(expected_ret, ret)
        self.assertRaises(KeyError,
                          self.library_policy_model.get_item,
                          self.policy['id'], {})

    def test_policy_api_model_error(self):
        """Test the policy api model."""

        # policy without name
        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.add_item,
                          {'rules': []}, {})

        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.replace_item,
                          self.policy['id'], {'rules': []}, {})

        # policy with bad name
        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.add_item,
                          {'name': '7*7', 'rules': []}, {})
        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.replace_item,
                          self.policy['id'], {'name': '7*7', 'rules': []}, {})

        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.add_item,
                          {'name': 'p(x) :- q(x)'}, {})
        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.replace_item,
                          self.policy['id'], {'name': 'p(x) :- q(x)'}, {})

        # policy with invalid 'kind'
        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.add_item,
                          {'kind': 'nonexistent', 'name': 'alice',
                           'rules': []}, {})
        self.assertRaises(webservice.DataModelException,
                          self.library_policy_model.replace_item,
                          self.policy['id'],
                          {'kind': 'nonexistent', 'name': 'alice',
                           'rules': []}, {})

    def test_replace_item(self):
        replacement_policy = {
            "name": "new_name",
            "description": "new test policy2 description",
            "kind": "nonrecursive",
            "abbreviation": "newab",
            "rules": [{"rule": "r(x) :- c(x)", "comment": "test comment",
                       "name": "test name"}]
        }

        # update non-existent item
        self.assertRaises(KeyError,
                          self.library_policy_model.replace_item, 'no_such_id',
                          replacement_policy, {}, {})

        # update existing item
        self.library_policy_model.replace_item(
            self.policy2['id'], replacement_policy, {}, {})

        replacement_policy_w_id = copy.deepcopy(replacement_policy)
        replacement_policy_w_id['id'] = self.policy2['id']

        ret = self.library_policy_model.get_items({})
        self.assertEqual(len(ret['results']), 2)
        self.assertTrue(all(p in ret['results']
                            for p in [self.policy,
                                      replacement_policy_w_id]))
