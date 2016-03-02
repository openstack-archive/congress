# Copyright (c) 2015 OpenStack Foundation
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

# set test to run as distributed arch
from oslo_config import cfg
cfg.CONF.distributed_architecture = True

import mock
from oslo_utils import uuidutils

from congress.api import error_codes
from congress.api import policy_model
from congress.api import rule_model
from congress.api import webservice
from congress.tests import base
from congress.tests import helper
from congress.tests2.api import base as api_base


class TestPolicyModel(base.SqlTestCase):
    def setUp(self):
        super(TestPolicyModel, self).setUp()

        self.policy_model = policy_model.PolicyModel('api-policy',
                                                     policy_engine='engine')
        self.rule_api = rule_model.RuleModel('api-rule',
                                             policy_engine='engine')
        services = api_base.setup_config([self.policy_model, self.rule_api])
        self.node = services['node']
        self.engine = services['engine']
        self.initial_policies = set(self.engine.policy_names())
        # Add default policy
        self.policy_model.add_item({'name': 'classification'}, {})
        self._add_test_policy()

    def _add_test_policy(self):
        test_policy = {
            "name": "test-policy",
            "description": "test policy description",
            "kind": "nonrecursive",
            "abbreviation": "abbr"
        }
        test_policy_id, obj = self.policy_model.add_item(test_policy, {})
        test_policy["id"] = test_policy_id
        test_policy["owner_id"] = obj["owner_id"]

        test_policy2 = {
            "name": "test-policy2",
            "description": "test policy2 description",
            "kind": "nonrecursive",
            "abbreviation": "abbr2"
        }
        test_policy_id, obj = self.policy_model.add_item(test_policy2, {})
        test_policy2["id"] = test_policy_id
        test_policy2["owner_id"] = obj["owner_id"]

        self.policy = test_policy
        self.policy2 = test_policy2

        # add action theory
        action_policy = {
            "name": "action",
            "description": "action description",
            "kind": "action",
            "abbreviation": "abbr2"
        }
        action_policy_id, obj = self.policy_model.add_item(action_policy, {})
        action_policy["id"] = action_policy_id
        action_policy["owner_id"] = obj["owner_id"]
        self.action_policy = action_policy

    def test_in_mem_and_db_policies(self):
        ret = self.policy_model.get_items({})
        db = [p['name'] for p in ret['results']]
        mem = self.engine.policy_names()
        new_memory = set(mem) - self.initial_policies
        new_db = set(db) - self.initial_policies
        self.assertEqual(new_memory, new_db)

    def test_get_items(self):
        ret = self.policy_model.get_items({})
        self.assertTrue(all(p in ret['results']
                            for p in [self.policy, self.policy2]))

    def test_get_item(self):
        expected_ret = self.policy
        ret = self.policy_model.get_item(self.policy["id"], {})
        self.assertEqual(expected_ret, ret)

    def test_get_invalid_item(self):
        self.assertRaises(KeyError, self.policy_model.get_item,
                          'invalid-id', {})

    @mock.patch('oslo_utils.uuidutils.generate_uuid')
    def test_add_item(self, patched_gen_uuid):
        test = {
            "name": "test",
            "description": "test description",
            "kind": "nonrecursive",
            "abbreviation": "abbr"
        }
        patched_gen_uuid.return_value = 'uuid'
        uuidutils.generate_uuid = mock.Mock()
        uuidutils.generate_uuid.return_value = 'uuid'
        expected_ret1 = 'uuid'
        expected_ret2 = {
            'id': 'uuid',
            'name': test['name'],
            'owner_id': 'user',
            'description': test['description'],
            'abbreviation': test['abbreviation'],
            'kind': test['kind']
        }

        policy_id, policy_obj = self.policy_model.add_item(test, {})
        self.assertEqual(expected_ret1, policy_id)
        self.assertEqual(expected_ret2, policy_obj)

    def test_add_item_with_id(self):
        test = {
            "name": "test",
            "description": "test description",
            "kind": "nonrecursive",
            "abbreviation": "abbr"
        }

        self.assertRaises(webservice.DataModelException,
                          self.policy_model.add_item, test, {}, 'id')

    def test_add_item_without_name(self):
        test = {
            "description": "test description",
            "kind": "nonrecursive",
            "abbreviation": "abbr"
        }

        self.assertRaises(webservice.DataModelException,
                          self.policy_model.add_item, test, {})

    def test_add_item_with_long_abbreviation(self):
        test = {
            "name": "test",
            "description": "test description",
            "kind": "nonrecursive",
            "abbreviation": "123456"
        }
        try:
            self.policy_model.add_item(test, {})
            self.fail("DataModelException should been raised.")
        except webservice.DataModelException as e:
            error_key = 'policy_abbreviation_error'
            self.assertEqual(error_codes.get_num(error_key), e.error_code)
            self.assertEqual(error_codes.get_desc(error_key), e.description)
            self.assertEqual(error_codes.get_http(error_key),
                             e.http_status_code)

    def test_delete_item(self):
        expected_ret = self.policy
        policy_id = self.policy['id']

        ret = self.policy_model.delete_item(policy_id, {})
        self.assertEqual(expected_ret, ret)
        self.assertRaises(KeyError, self.policy_model.get_item,
                          self.policy['id'], {})

        # check that deleting the policy also deletes the rules
        self.assertRaises(webservice.DataModelException,
                          self.rule_api.get_items,
                          {}, {'policy_id': policy_id})

    def test_simulate_action(self):
        context = {
            'policy_id': self.action_policy['name']
        }
        action_rule1 = {
            'rule': 'action("q")',
        }
        action_rule2 = {
            'rule': 'p+(x):- q(x)'
        }
        self.rule_api.add_item(action_rule1, {}, context=context)
        self.rule_api.add_item(action_rule2, {}, context=context)

        request_body = {
            'query': 'p(x)',
            'action_policy': self.action_policy['name'],
            'sequence': 'q(1)'
        }
        request = helper.FakeRequest(request_body)
        expected_ret = {
            'result': [
                "p(1)"
            ]
        }

        ret = self.policy_model.simulate_action({}, context, request)
        self.assertEqual(expected_ret, ret)

    def test_simulate_with_delta(self):
        context = {
            'policy_id': self.action_policy['name']
        }
        action_rule1 = {
            'rule': 'action("q")',
        }
        action_rule2 = {
            'rule': 'p+(x):- q(x)'
        }
        self.rule_api.add_item(action_rule1, {}, context=context)
        self.rule_api.add_item(action_rule2, {}, context=context)

        request_body = {
            'query': 'p(x)',
            'action_policy': self.action_policy['name'],
            'sequence': 'q(1)'
        }
        request = helper.FakeRequest(request_body)
        params = {
            'delta': 'true'
        }
        expected_ret = {
            'result': [
                "p+(1)"
            ]
        }

        ret = self.policy_model.simulate_action(params, context, request)
        self.assertEqual(expected_ret, ret)

    def test_simulate_with_trace(self):
        context = {
            'policy_id': self.action_policy['name']
        }
        action_rule1 = {
            'rule': 'action("q")',
        }
        action_rule2 = {
            'rule': 'p+(x):- q(x)'
        }
        self.rule_api.add_item(action_rule1, {}, context=context)
        self.rule_api.add_item(action_rule2, {}, context=context)

        request_body = {
            'query': 'p(x)',
            'action_policy': self.action_policy['name'],
            'sequence': 'q(1)'
        }
        request = helper.FakeRequest(request_body)
        params = {
            'trace': 'true'
        }
        expected_ret = {
            'result': [
                "p(1)"
            ],
            'trace': "trace strings"
        }

        ret = self.policy_model.simulate_action(params, context, request)
        # check response's keys equal expected_ret's key
        self.assertTrue(all(key in expected_ret.keys() for key in ret.keys()))
        self.assertEqual(expected_ret['result'], ret['result'])
        self.assertTrue(len(ret['trace']) > 10)

    def test_simulate_with_delta_and_trace(self):
        context = {
            'policy_id': self.action_policy['name']
        }
        action_rule1 = {
            'rule': 'action("q")',
        }
        action_rule2 = {
            'rule': 'p+(x):- q(x)'
        }
        self.rule_api.add_item(action_rule1, {}, context=context)
        self.rule_api.add_item(action_rule2, {}, context=context)

        request_body = {
            'query': 'p(x)',
            'action_policy': self.action_policy['name'],
            'sequence': 'q(1)'
        }
        request = helper.FakeRequest(request_body)
        params = {
            'trace': 'true',
            'delta': 'true'
        }
        expected_ret = {
            'result': [
                "p+(1)"
            ],
            'trace': "trace strings"
        }

        ret = self.policy_model.simulate_action(params, context, request)
        # check response's keys equal expected_ret's key
        self.assertTrue(all(key in expected_ret.keys() for key in ret.keys()))
        self.assertEqual(expected_ret['result'], ret['result'])
        self.assertTrue(len(ret['trace']) > 10)

    def test_simulate_invalid_policy(self):
        context = {
            'policy_id': 'invalid-policy'
        }
        request_body = {
            'query': 'p(x)',
            'action_policy': self.action_policy['name'],
            'sequence': 'q(1)'
        }
        request = helper.FakeRequest(request_body)

        self.assertRaises(webservice.DataModelException,
                          self.policy_model.simulate_action,
                          {}, context, request)

    def test_simulate_invalid_sequence(self):
        context = {
            'policy_id': self.action_policy['name']
        }
        action_rule = {
            'rule': 'w(x):-z(x)',
        }
        self.rule_api.add_item(action_rule, {}, context=context)

        request_body = {
            'query': 'w(x)',
            'action_policy': self.action_policy['name'],
            'sequence': 'z(1)'
        }
        request = helper.FakeRequest(request_body)

        self.assertRaises(webservice.DataModelException,
                          self.policy_model.simulate_action,
                          {}, context, request)

    def test_simulate_policy_errors(self):
        def check_err(params, context, request, emsg):
            try:
                self.policy_model.simulate_action(params, context, request)
                self.assertFail()
            except webservice.DataModelException as e:
                self.assertIn(emsg, str(e))

        context = {
            'policy_id': self.action_policy['name']
        }

        # Missing query
        body = {'action_policy': self.action_policy['name'],
                'sequence': 'q(1)'}
        check_err({}, context, helper.FakeRequest(body),
                  'Simulate requires parameters')

        # Invalid query
        body = {'query': 'p(x',
                'action_policy': self.action_policy['name'],
                'sequence': 'q(1)'}
        check_err({}, context, helper.FakeRequest(body),
                  'Parse failure')

        # Multiple querys
        body = {'query': 'p(x) q(x)',
                'action_policy': self.action_policy['name'],
                'sequence': 'q(1)'}
        check_err({}, context, helper.FakeRequest(body),
                  'more than 1 rule')

        # Missing action_policy
        body = {'query': 'p(x)',
                'sequence': 'q(1)'}
        check_err({}, context, helper.FakeRequest(body),
                  'Simulate requires parameters')

        # Missing sequence
        body = {'query': 'p(x)',
                'action_policy': self.action_policy['name']}
        check_err({}, context, helper.FakeRequest(body),
                  'Simulate requires parameters')

        # Syntactically invalid sequence
        body = {'query': 'p(x)',
                'action_policy': self.action_policy['name'],
                'sequence': 'q(1'}
        check_err({}, context, helper.FakeRequest(body),
                  'Parse failure')

        # Semantically invalid sequence
        body = {'query': 'p(x)',
                'action_policy': self.action_policy['name'],
                'sequence': 'r(1)'}  # r is not an action
        check_err({}, context, helper.FakeRequest(body),
                  'non-action, non-update')

    def test_policy_api_model_error(self):
        """Test the policy api model."""

        # add policy without name
        self.assertRaises(webservice.DataModelException,
                          self.policy_model.add_item, {}, {})

        # add policy with bad ID
        self.assertRaises(webservice.DataModelException,
                          self.policy_model.add_item, {'name': '7*7'}, {})
        self.assertRaises(webservice.DataModelException,
                          self.policy_model.add_item,
                          {'name': 'p(x) :- q(x)'}, {})

        # add policy with invalid 'kind'
        self.assertRaises(webservice.DataModelException,
                          self.policy_model.add_item,
                          {'kind': 'nonexistent', 'name': 'alice'}, {})

        # add existing policy
        self.policy_model.add_item({'name': 'Test1'}, {})
        self.assertRaises(KeyError, self.policy_model.add_item,
                          {'name': 'Test1'}, {})

        # delete non-existent policy
        self.assertRaises(KeyError, self.policy_model.delete_item,
                          'noexist', {})

        # delete system-maintained policy
        policies = self.policy_model.get_items({})['results']
        class_policy = [p for p in policies if p['name'] == 'classification']
        class_policy = class_policy[0]
        self.assertRaises(KeyError, self.policy_model.delete_item,
                          class_policy['id'], {})
