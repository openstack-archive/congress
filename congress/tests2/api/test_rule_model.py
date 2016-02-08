# Copyright 2015 NEC Corporation.  All rights reserved.
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

from oslo_config import cfg
cfg.CONF.distributed_architecture = True

from oslo_config import cfg

from congress.api import policy_model
from congress.api import rule_model
from congress.tests import base
from congress.tests import helper

from congress.dse2.dse_node import DseNode
from congress.policy_engines.agnostic import Dse2Runtime


class TestRuleModel(base.SqlTestCase):
    def setUp(self):
        super(TestRuleModel, self).setUp()
        # Here we load the fake driver
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])

        result = self.create_services()
        self.node = result['node']
        self.engine = result['engine']
        self.rule_model = result['api_rule']
        self.policy_model = result['api_policy']
        self.action_policy = self._add_action_policy()
        self.context = {'policy_id': self.action_policy["name"]}
        self._add_test_rule()

    def create_services(self):
        messaging_config = helper.generate_messaging_config()
        node = DseNode(messaging_config, "testnode", [])

        engine = Dse2Runtime('engine')
        api_rule = rule_model.RuleModel('api-rule', policy_engine='engine')
        api_policy = policy_model.PolicyModel(
            'api-policy', policy_engine='engine')
        node.register_service(engine)
        node.register_service(api_rule)
        node.register_service(api_policy)
        node.start()
        return {'node': node, 'engine': engine,
                'api_rule': api_rule, 'api_policy': api_policy}

    def tearDown(self):
        super(TestRuleModel, self).tearDown()
        self.node.stop()
        self.node.wait()

    def _add_action_policy(self):
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
        return action_policy

    def _add_test_rule(self):
        test_rule1 = {
            "rule": "p(x) :- q(x)",
            "name": "test-rule1",
            "comment": "test-comment"
        }
        test_rule2 = {
            "rule": 'p(x) :- q(x), not r(x)',
            "name": "test-rule2",
            "comment": "test-comment-2"
        }
        test_rule_id, obj = self.rule_model.add_item(test_rule1, {},
                                                     context=self.context)
        test_rule1["id"] = test_rule_id
        self.rule1 = test_rule1

        test_rule_id, obj = self.rule_model.add_item(test_rule2, {},
                                                     context=self.context)
        test_rule2["id"] = test_rule_id
        self.rule2 = test_rule2

    # TODO(dse2): Enable this test once exceptions are properly returned
    # @mock.patch.object(rule_model.RuleModel, 'policy_name')
    # def test_add_rule_with_invalid_policy(self, policy_name_mock):
    #     test_rule = {'rule': 'p()', 'name': 'test'}
    #     policy_name_mock.return_value = 'invalid'
    #     self.assertRaises(webservice.DataModelException,
    #                       self.rule_model.add_item,
    #                       test_rule, {})

    # TODO(dse2): Fix this test; it must create a 'beta' service on the dse
    #   so that when it subscribes, the snapshot can be returned.
    #   Or fix the subscribe() implementation so that we can subscribe before
    #   the service has been created.
    # def test_add_rule_using_schema(self):
    #     engine = self.engine
    #     engine.create_policy('beta')
    #     engine.set_schema(
    #         'beta', compile.Schema({'q': ("name", "status", "year")}))
    #     # insert/retrieve rule with column references
    #     # testing that no errors are thrown--correctness tested elsewhere
    #     # Assuming that api-models are pass-throughs to functionality
    #     (id1, _) = self.rule_model.add_item(
    #         {'rule': 'p(x) :- beta:q(name=x)'},
    #         {}, context=self.context)
    #     self.rule_model.get_item(id1, {}, context=self.context)

    def test_get_items(self):
        ret = self.rule_model.get_items({}, context=self.context)
        self.assertTrue(all(p in ret['results']
                            for p in [self.rule1, self.rule2]))

    def test_get_item(self):
        expected_ret = self.rule1
        ret = self.rule_model.get_item(self.rule1["id"], {},
                                       context=self.context)
        self.assertEqual(expected_ret, ret)

    def test_get_invalid_item(self):
        expected_ret = None
        ret = self.rule_model.get_item('invalid-id', {}, context=self.context)
        self.assertEqual(expected_ret, ret)

    def test_delete_item(self):
        expected_ret = self.rule1

        ret = self.rule_model.delete_item(self.rule1['id'], {},
                                          context=self.context)
        self.assertEqual(expected_ret, ret)

        expected_ret = None
        ret = self.rule_model.get_item(self.rule1['id'], {},
                                       context=self.context)
        self.assertEqual(expected_ret, ret)

    # TODO(dse2): Enable these tests once exceptions properly returned
    # def test_rule_api_model_errors(self):
    #     """Test syntax errors.

    #     Test that syntax errors thrown by the policy runtime
    #     are returned properly to the user so they can see the
    #     error messages.
    #     """
    #     # lexer error
    #     with self.assertRaisesRegexp(
    #             webservice.DataModelException,
    #             "Lex failure"):
    #         self.rule_model.add_item({'rule': 'p#'}, {},
    #                                  context=self.context)

    #     # parser error
    #     with self.assertRaisesRegexp(
    #             webservice.DataModelException,
    #             "Parse failure"):
    #         self.rule_model.add_item({'rule': 'p('}, {},
    #                                  context=self.context)

    #     # single-rule error: safety in the head
    #     with self.assertRaisesRegexp(
    #             webservice.DataModelException,
    #             "Variable x found in head but not in body"):
    #         # TODO(ramineni):check for action
    #         self.context = {'policy_id': 'classification'}
    #         self.rule_model.add_item({'rule': 'p(x,y) :- q(y)'}, {},
    #                                  context=self.context)

    #     # multi-rule error: recursion through negation
    #     self.rule_model.add_item({'rule': 'p(x) :- q(x), not r(x)'}, {},
    #                              context=self.context)
    #     with self.assertRaisesRegexp(
    #             webservice.DataModelException,
    #             "Rules are recursive"):
    #         self.rule_model.add_item({'rule': 'r(x) :- q(x), not p(x)'}, {},
    #                                  context=self.context)

    #     self.rule_model.add_item({'rule': 'p(x) :- q(x)'}, {},
    #                              context=self.context)
    #     # duplicate rules
    #     with self.assertRaisesRegexp(
    #             webservice.DataModelException,
    #             "Rule already exists"):
    #         self.rule_model.add_item({'rule': 'p(x) :- q(x)'}, {},
    #                                  context=self.context)
