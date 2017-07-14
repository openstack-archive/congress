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

from congress.db import db_library_policies
from congress.tests import base


class TestDbLibraryPolicies(base.SqlTestCase):

    def setUp(self):
        super(TestDbLibraryPolicies, self).setUp()
        db_library_policies.delete_policies()  # delete preloaded policies

    def test_add_policy_no_name(self):
        self.assertRaises(
            KeyError, db_library_policies.add_policy, {'rules': []})

    def test_add_policy_no_rules(self):
        self.assertRaises(KeyError, db_library_policies.add_policy,
                          {'name': 'policy1'})

    def test_add_policy(self):
        res = db_library_policies.add_policy(
            {'name': 'policy1', 'abbreviation': 'abbr', 'kind': 'database',
             'description': 'descrip', 'rules': [{'rule': 'p(x) :- q(x)',
                                                  'comment': 'test comment',
                                                  'name': 'testname'}]})
        self.assertEqual(res.to_dict(include_rules=True),
                         {'id': res['id'],
                          'abbreviation': 'abbr',
                          'kind': 'database',
                          'name': 'policy1',
                          'description': 'descrip',
                          'rules': [{'rule': 'p(x) :- q(x)',
                                     'comment': 'test comment',
                                     'name': 'testname'}]})

    def test_add_policy_duplicate(self):
        db_library_policies.add_policy(
            {'name': 'policy1', 'abbreviation': 'abbr', 'kind': 'database',
             'description': 'descrip', 'rules': []})
        self.assertRaises(
            KeyError, db_library_policies.add_policy,
            {'name': 'policy1', 'rules': [{'rule': 'p(x) :- q(x)',
                                           'comment': 'test comment',
                                           'name': 'testname'}]})

    def test_get_policy_empty(self):
        res = db_library_policies.get_policies()
        self.assertEqual(res, [])

        self.assertRaises(KeyError, db_library_policies.get_policy,
                          'nosuchpolicy')

        self.assertRaises(KeyError, db_library_policies.get_policy_by_name,
                          'nosuchpolicy')

    def test_create_get_policy(self):
        policy1 = db_library_policies.add_policy(
            {'name': 'policy1', 'abbreviation': 'abbr', 'kind': 'database',
             'description': 'descrip', 'rules': [{'rule': 'p(x) :- q(x)',
                                                  'comment': 'test comment',
                                                  'name': 'testname'}]})

        res = db_library_policies.get_policies()
        self.assertEqual([p.to_dict(include_rules=True) for p in res],
                         [{'id': policy1['id'],
                           'abbreviation': 'abbr',
                           'kind': 'database',
                           'name': 'policy1',
                           'description': 'descrip',
                           'rules': [{'rule': 'p(x) :- q(x)',
                                      'comment': 'test comment',
                                      'name': 'testname'}]}])

        res = db_library_policies.get_policy(policy1['id'])
        self.assertEqual(res.to_dict(include_rules=True),
                         {'id': policy1['id'],
                          'abbreviation': 'abbr',
                          'kind': 'database',
                          'name': 'policy1',
                          'description': 'descrip',
                          'rules': [{'rule': 'p(x) :- q(x)',
                                     'comment': 'test comment',
                                     'name': 'testname'}]})

        res = db_library_policies.get_policy_by_name(policy1['name'])
        self.assertEqual(res.to_dict(include_rules=True),
                         {'id': policy1['id'],
                          'abbreviation': 'abbr',
                          'kind': 'database',
                          'name': 'policy1',
                          'description': 'descrip',
                          'rules': [{'rule': 'p(x) :- q(x)',
                                     'comment': 'test comment',
                                     'name': 'testname'}]})

        self.assertRaises(KeyError, db_library_policies.get_policy,
                          'no_such_policy')

        self.assertRaises(KeyError, db_library_policies.get_policy_by_name,
                          'no_such_policy')

    def test_delete_policy(self):
        db_library_policies.delete_policy('policy1')

        policy1 = db_library_policies.add_policy(
            {'name': 'policy1', 'abbreviation': 'abbr', 'kind': 'database',
             'description': 'descrip', 'rules': [{'rule': 'p(x) :- q(x)',
                                                  'comment': 'test comment',
                                                  'name': 'testname'}]})

        policy2 = db_library_policies.add_policy(
            {'name': 'policy2', 'abbreviation': 'abbr', 'kind': 'database',
             'description': 'descrip', 'rules': [{'rule': 'p(x) :- q(x)',
                                                  'comment': 'test comment',
                                                  'name': 'testname'}]})

        res = db_library_policies.get_policies()
        self.assertEqual(len(res), 2)

        db_library_policies.delete_policy('no_such_policy')

        res = db_library_policies.get_policies()
        self.assertEqual(len(res), 2)

        db_library_policies.delete_policy(policy1['id'])

        res = db_library_policies.get_policies()
        self.assertEqual(len(res), 1)

        db_library_policies.delete_policy(policy2['id'])

        res = db_library_policies.get_policies()
        self.assertEqual(len(res), 0)

    def test_delete_policies(self):
        db_library_policies.delete_policies()
        res = db_library_policies.get_policies()
        self.assertEqual(len(res), 0)

        db_library_policies.add_policy(
            {'name': 'policy1', 'abbreviation': 'abbr', 'kind': 'database',
             'description': 'descrip', 'rules': [{'rule': 'p(x) :- q(x)',
                                                  'comment': 'test comment',
                                                  'name': 'testname'}]})

        db_library_policies.add_policy(
            {'name': 'policy2', 'abbreviation': 'abbr', 'kind': 'database',
             'description': 'descrip', 'rules': [{'rule': 'p(x) :- q(x)',
                                                  'comment': 'test comment',
                                                  'name': 'testname'}]})

        db_library_policies.delete_policies()
        res = db_library_policies.get_policies()
        self.assertEqual(len(res), 0)
