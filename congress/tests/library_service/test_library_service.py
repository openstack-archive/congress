# Copyright 2017 VMware Inc. All rights reserved.
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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import copy

from congress import exception
from congress.library_service import library_service
from congress.tests import base


class TestLibraryService(base.SqlTestCase):

    def setUp(self):
        super(TestLibraryService, self).setUp()
        self.library = library_service.LibraryService('lib-test')
        self.library.delete_all_policies()  # clear pre-loaded library policies

        self.policy1 = {'name': 'policy1', 'abbreviation': 'abbr',
                        'kind': 'database', 'description': 'descrip',
                        'rules': [{'rule': 'p(x) :- q(x)',
                                   'comment': 'test comment',
                                   'name': 'testname'}]}

        self.policy2 = {'name': 'policy2', 'abbreviation': 'abbr',
                        'kind': 'database', 'description': 'descrip',
                        'rules': [{'rule': 'p(x) :- q(x)',
                                   'comment': 'test comment',
                                   'name': 'testname'}]}

        self.policy1_meta = copy.deepcopy(self.policy1)
        self.policy2_meta = copy.deepcopy(self.policy2)
        del self.policy1_meta['rules']
        del self.policy2_meta['rules']

    def test_create_policy_no_name(self):
        self.assertRaises(exception.InvalidPolicyInput,
                          self.library.create_policy, {'rules': []})

    def test_create_policy_no_rules(self):
        self.assertRaises(exception.InvalidPolicyInput,
                          self.library.create_policy, {'name': 'policy1'})

    def test_create_policy_other_schema_violations(self):
        # name too long (255 limit)
        policy_item = {
            'name': 'policy2', 'abbreviation': 'abbr',
            'kind': 'database', 'description': 'descrip',
            'rules': [{
                'rule': 'p(x) :- q(x)',
                'comment': 'test comment',
                'name':
                    '111111111111111111111111111111111111111111111111111111111'
                    '111111111111111111111111111111111111111111111111111111111'
                    '111111111111111111111111111111111111111111111111111111111'
                    '111111111111111111111111111111111111111111111111111111111'
                    '11111111111111111111111111111'}]}
        self.assertRaises(exception.InvalidPolicyInput,
                          self.library.create_policy, policy_item)

        # comment too long (255 limit)
        policy_item = {
            'name': 'policy2', 'abbreviation': 'abbr',
            'kind': 'database', 'description': 'descrip',
            'rules': [{
                'rule': 'p(x) :- q(x)',
                'comment':
                    '111111111111111111111111111111111111111111111111111111111'
                    '111111111111111111111111111111111111111111111111111111111'
                    '111111111111111111111111111111111111111111111111111111111'
                    '111111111111111111111111111111111111111111111111111111111'
                    '11111111111111111111111111111',
                'name': 'testname'}]}
        self.assertRaises(exception.InvalidPolicyInput,
                          self.library.create_policy, policy_item)

        # rule item missing 'rule' property
        policy_item = {
            'name': 'policy2', 'abbreviation': 'abbr',
            'kind': 'database', 'description': 'descrip',
            'rules': [{
                'comment': 'test comment',
                'name': 'testname'}]}
        self.assertRaises(exception.InvalidPolicyInput,
                          self.library.create_policy, policy_item)

    def test_create_policy_bad_name(self):
        self.assertRaises(exception.PolicyException,
                          self.library.create_policy,
                          {'name': 'disallowed-hyphen', 'rules': []})

    def test_create_policy_default(self):
        res = self.library.create_policy({'name': 'policy1', 'rules': []})
        self.assertEqual(res, {'id': res['id'], 'abbreviation': 'polic',
                               'kind': 'nonrecursive', 'name': 'policy1',
                               'description': '', 'rules': []})

    def test_create_policy(self):
        policy_obj = self.library.create_policy(self.policy1)
        self.policy1['id'] = policy_obj['id']
        self.assertEqual(policy_obj, self.policy1)

    def test_create_policy_duplicate(self):
        self.library.create_policy({'name': 'policy1', 'rules': []})
        self.assertRaises(KeyError, self.library.create_policy,
                          {'name': 'policy1', 'rules': []})
        res = self.library.get_policies()
        self.assertEqual(len(res), 1)

    def test_get_policy_empty(self):
        res = self.library.get_policies()
        self.assertEqual(res, [])

        self.assertRaises(KeyError, self.library.get_policy,
                          'nosuchpolicy')

        self.assertRaises(KeyError, self.library.get_policy_by_name,
                          'nosuchpolicy')

    def test_create_get_policy(self):
        policy_obj = self.library.create_policy(self.policy1)
        self.policy1['id'] = policy_obj['id']
        self.policy1_meta['id'] = policy_obj['id']
        res = self.library.get_policies()
        self.assertEqual(res, [self.policy1])

        res = self.library.get_policy(policy_obj['id'])
        self.assertEqual(res, self.policy1)

        res = self.library.get_policy_by_name(policy_obj['name'])
        self.assertEqual(res, self.policy1)

        res = self.library.get_policies(include_rules=True)
        self.assertEqual(res, [self.policy1])

        res = self.library.get_policy(policy_obj['id'], include_rules=False)
        self.assertEqual(res, self.policy1_meta)

        res = self.library.get_policy_by_name(policy_obj['name'],
                                              include_rules=False)
        self.assertEqual(res, self.policy1_meta)

        self.assertRaises(KeyError, self.library.get_policy, 'no_such_policy')

        self.assertRaises(KeyError, self.library.get_policy_by_name,
                          'no_such_policy')

    def test_delete_policy(self):
        self.assertRaises(KeyError, self.library.delete_policy,
                          'policy1')

        policy_obj = self.library.create_policy(self.policy1)
        self.policy1['id'] = policy_obj['id']

        policy_obj = self.library.create_policy(self.policy2)
        self.policy2['id'] = policy_obj['id']

        res = self.library.get_policies()
        self.assertEqual(len(res), 2)
        self.assertTrue(all(p in res
                            for p in [self.policy1, self.policy2]))

        self.assertRaises(KeyError, self.library.delete_policy,
                          'no_such_policy')

        res = self.library.delete_policy(self.policy1['id'])
        self.assertEqual(res, self.policy1)

        res = self.library.get_policies()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0], self.policy2)

        res = self.library.delete_policy(self.policy2['id'])
        self.assertEqual(res, self.policy2)

        res = self.library.get_policies()
        self.assertEqual(len(res), 0)

    def test_delete_policies(self):
        self.library.delete_all_policies()
        res = self.library.get_policies()
        self.assertEqual(len(res), 0)

        self.library.create_policy(
            {'name': 'policy1', 'abbreviation': 'abbr', 'kind': 'database',
             'description': 'descrip', 'rules': [{'rule': 'p(x) :- q(x)',
                                                  'comment': 'test comment',
                                                  'name': 'testname'}]})

        self.library.create_policy(
            {'name': 'policy2', 'abbreviation': 'abbr', 'kind': 'database',
             'description': 'descrip', 'rules': [{'rule': 'p(x) :- q(x)',
                                                  'comment': 'test comment',
                                                  'name': 'testname'}]})

        self.library.delete_all_policies()
        res = self.library.get_policies()
        self.assertEqual(len(res), 0)

    def test_replace_policy(self):
        policy1 = self.library.create_policy(
            {'name': 'policy1', 'abbreviation': 'abbr', 'kind': 'database',
             'description': 'descrip', 'rules': [{'rule': 'p(x) :- q(x)',
                                                  'comment': 'test comment',
                                                  'name': 'testname'}]})

        policy2 = self.library.create_policy(
            {'name': 'policy2', 'abbreviation': 'abbr', 'kind': 'database',
             'description': 'descrip', 'rules': [{'rule': 'p(x) :- q(x)',
                                                  'comment': 'test comment',
                                                  'name': 'testname'}]})

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
                          self.library.replace_policy, 'no_such_id',
                          replacement_policy)

        # update existing item
        self.library.replace_policy(policy2['id'], replacement_policy)

        replacement_policy_w_id = copy.deepcopy(replacement_policy)
        replacement_policy_w_id['id'] = policy2['id']

        ret = self.library.get_policies()
        self.assertEqual(len(ret), 2)
        self.assertTrue(all(p in ret
                            for p in [policy1,
                                      replacement_policy_w_id]))
