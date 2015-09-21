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

import mock
from oslo_config import cfg
from oslo_utils import uuidutils

from congress.api import error_codes
from congress.api import policy_model
from congress.api import webservice
from congress import harness
from congress.tests import base
from congress.tests import helper


class TestPolicyModel(base.SqlTestCase):
    def setUp(self):
        super(TestPolicyModel, self).setUp()
        # Here we load the fake driver
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])

        self.cage = harness.create(helper.root_path())
        self.engine = self.cage.service_object('engine')
        self.rule_api = self.cage.service_object('api-rule')
        self.policy_model = policy_model.PolicyModel("policy_model", {},
                                                     policy_engine=self.engine)

        self._add_test_policy()

    def tearDown(self):
        super(TestPolicyModel, self).tearDown()

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

    def test_get_items(self):
        ret = self.policy_model.get_items({})
        self.assertTrue(all(p in ret['results']
                            for p in [self.policy, self.policy2]))

    def test_get_item(self):
        expected_ret = self.policy
        ret = self.policy_model.get_item(self.policy["id"], {})
        self.assertEqual(expected_ret, ret)

    def test_get_invalid_item(self):
        expected_ret = None
        ret = self.policy_model.get_item('invalid-id', {})
        self.assertEqual(expected_ret, ret)

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

        ret = self.policy_model.delete_item(self.policy['id'], {})
        self.assertEqual(expected_ret, ret)

        expected_ret = None
        ret = self.policy_model.get_item(self.policy['id'], {})
        self.assertEqual(expected_ret, ret)

    def test_delete_item_invalid_id(self):
        self.assertRaises(KeyError,
                          self.policy_model.delete_item, 'invalid-id', {})

    def test_simulate_action(self):
        context = {
            'policy_id': self.engine.ACTION_THEORY
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
            'action_policy': self.engine.ACTION_THEORY,
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
            'policy_id': self.engine.ACTION_THEORY
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
            'action_policy': self.engine.ACTION_THEORY,
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
            'policy_id': self.engine.ACTION_THEORY
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
            'action_policy': self.engine.ACTION_THEORY,
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
        self.assertTrue(ret['trace'] > 10)

    def test_simulate_invalid_policy(self):
        context = {
            'policy_id': 'invalid-policy'
        }
        request_body = {
            'query': 'p(x)',
            'action_policy': self.engine.ACTION_THEORY,
            'sequence': 'q(1)'
        }
        request = helper.FakeRequest(request_body)

        self.assertRaises(webservice.DataModelException,
                          self.policy_model.simulate_action,
                          {}, context, request)

    def test_simulate_invalid_sequence(self):
        context = {
            'policy_id': self.engine.ACTION_THEORY
        }
        action_rule = {
            'rule': 'w(x):-z(x)',
        }
        self.rule_api.add_item(action_rule, {}, context=context)

        request_body = {
            'query': 'w(x)',
            'action_policy': self.engine.ACTION_THEORY,
            'sequence': 'z(1)'
        }
        request = helper.FakeRequest(request_body)

        self.assertRaises(webservice.DataModelException,
                          self.policy_model.simulate_action,
                          {}, context, request)
