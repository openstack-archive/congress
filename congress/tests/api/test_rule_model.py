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

import mock
from oslo_config import cfg

from congress.api import rule_model
from congress.api import webservice
from congress.datalog import compile
from congress import harness
from congress.tests import base
from congress.tests import helper


class TestRuleModel(base.SqlTestCase):
    def setUp(self):
        super(TestRuleModel, self).setUp()
        # Here we load the fake driver
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])

        self.cage = harness.create(helper.root_path())
        self.engine = self.cage.service_object('engine')
        self.rule_model = rule_model.RuleModel("rule_model", {},
                                               policy_engine=self.engine)
        self.context = {'policy_id': 'action'}
        self._add_test_rule()

    def tearDown(self):
        super(TestRuleModel, self).tearDown()

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

    @mock.patch.object(rule_model.RuleModel, 'policy_name')
    def test_add_rule_with_invalid_policy(self, policy_name_mock):
        test_rule = {'rule': 'p()', 'name': 'test'}
        policy_name_mock.return_value = 'invalid'
        self.assertRaises(webservice.DataModelException,
                          self.rule_model.add_item,
                          test_rule, {})

    def test_add_rule_using_schema(self):
        engine = self.engine
        engine.create_policy('beta')
        engine.set_schema(
            'beta', compile.Schema({'q': ("name", "status", "year")}))
        # insert/retrieve rule with column references
        # just testing that no errors are thrown--correctness tested elsewhere
        # Assuming that api-models are pass-throughs to functionality
        (id1, _) = self.rule_model.add_item(
            {'rule': 'p(x) :- beta:q(name=x)'},
            {}, context=self.context)
        self.rule_model.get_item(id1, {}, context=self.context)

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

    def test_rule_api_model_errors(self):
        """Test syntax errors.

        Test that syntax errors thrown by the policy runtime
        are returned properly to the user so they can see the
        error messages.
        """
        # lexer error
        with self.assertRaisesRegexp(
                webservice.DataModelException,
                "Lex failure"):
            self.rule_model.add_item({'rule': 'p#'}, {}, context=self.context)

        # parser error
        with self.assertRaisesRegexp(
                webservice.DataModelException,
                "Parse failure"):
            self.rule_model.add_item({'rule': 'p('}, {}, context=self.context)

        # single-rule error: safety in the head
        with self.assertRaisesRegexp(
                webservice.DataModelException,
                "Variable x found in head but not in body"):
            # TODO(ramineni):check for action
            self.context = {'policy_id': 'classification'}
            self.rule_model.add_item({'rule': 'p(x,y) :- q(y)'}, {},
                                     context=self.context)

        # multi-rule error: recursion through negation
        self.rule_model.add_item({'rule': 'p(x) :- q(x), not r(x)'}, {},
                                 context=self.context)
        with self.assertRaisesRegexp(
                webservice.DataModelException,
                "Rules are recursive"):
            self.rule_model.add_item({'rule': 'r(x) :- q(x), not p(x)'}, {},
                                     context=self.context)

        self.rule_model.add_item({'rule': 'p(x) :- q(x)'}, {},
                                 context=self.context)
        # duplicate rules
        with self.assertRaisesRegexp(
                webservice.DataModelException,
                "Rule already exists"):
            self.rule_model.add_item({'rule': 'p(x) :- q(x)'}, {},
                                     context=self.context)
