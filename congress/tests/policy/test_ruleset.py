# Copyright (c) 2014 VMware, Inc. All rights reserved.
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

from congress.policy import compile
from congress.policy.ruleset import RuleSet
from congress.tests import base


class TestRuleSet(base.TestCase):
    def setUp(self):
        super(TestRuleSet, self).setUp()
        self.ruleset = RuleSet()

    def test_empty_ruleset(self):
        self.assertFalse('p' in self.ruleset)
        self.assertEqual([], self.ruleset.keys())

    def test_clear_ruleset(self):
        rule1 = compile.parse1('p(x,y) :- q(x), r(y)')
        self.ruleset.add_rule('p', rule1)
        self.ruleset.clear()

        self.assertFalse('p' in self.ruleset)
        self.assertEqual([], self.ruleset.keys())

    def test_add_rule(self):
        rule1 = compile.parse1('p(x,y) :- q(x), r(y)')
        self.assertTrue(self.ruleset.add_rule('p', rule1))
        self.assertTrue('p' in self.ruleset)
        self.assertEqual([rule1], self.ruleset.get_rules('p'))
        self.assertEqual(['p'], self.ruleset.keys())

    def test_add_existing_rule(self):
        rule1 = compile.parse1('p(x,y) :- q(x), r(y)')
        self.assertTrue(self.ruleset.add_rule('p', rule1))
        self.assertTrue('p' in self.ruleset)
        self.assertEqual([rule1], self.ruleset.get_rules('p'))
        self.assertEqual(['p'], self.ruleset.keys())

        self.assertFalse(self.ruleset.add_rule('p', rule1))
        self.assertTrue('p' in self.ruleset)
        self.assertEqual([rule1], self.ruleset.get_rules('p'))
        self.assertEqual(['p'], self.ruleset.keys())

    def test_add_rules_with_same_head(self):
        rule1 = compile.parse1('p(x,y) :- q(x), r(y)')
        rule2 = compile.parse1('p(x,y) :- s(x), t(y)')

        self.assertTrue(self.ruleset.add_rule('p', rule1))
        self.assertTrue('p' in self.ruleset)
        self.assertEqual([rule1], self.ruleset.get_rules('p'))
        self.assertEqual(['p'], self.ruleset.keys())

        self.assertTrue(self.ruleset.add_rule('p', rule2))
        self.assertTrue('p' in self.ruleset)
        self.assertTrue(rule1 in self.ruleset.get_rules('p'))
        self.assertTrue(rule2 in self.ruleset.get_rules('p'))
        self.assertEqual(['p'], self.ruleset.keys())

    def test_add_rules_with_different_head(self):
        rule1 = compile.parse1('p1(x,y) :- q(x), r(y)')
        rule2 = compile.parse1('p2(x,y) :- s(x), t(y)')

        self.assertTrue(self.ruleset.add_rule('p1', rule1))
        self.assertTrue(self.ruleset.add_rule('p2', rule2))

        self.assertTrue('p1' in self.ruleset)
        self.assertEqual([rule1], self.ruleset.get_rules('p1'))
        self.assertTrue('p1' in self.ruleset.keys())

        self.assertTrue('p2' in self.ruleset)
        self.assertEqual([rule2], self.ruleset.get_rules('p2'))
        self.assertTrue('p2' in self.ruleset.keys())

    def test_discard_rule(self):
        rule1 = compile.parse1('p(x,y) :- q(x), r(y)')
        self.assertTrue(self.ruleset.add_rule('p', rule1))
        self.assertTrue('p' in self.ruleset)
        self.assertEqual([rule1], self.ruleset.get_rules('p'))

        self.assertTrue(self.ruleset.discard_rule('p', rule1))
        self.assertFalse('p' in self.ruleset)
        self.assertEqual([], self.ruleset.keys())

    def test_discard_nonexistent_rule(self):
        rule1 = compile.parse1('p(x,y) :- q(x), r(y)')
        self.assertFalse(self.ruleset.discard_rule('p', rule1))
        self.assertFalse('p' in self.ruleset)
        self.assertEqual([], self.ruleset.keys())

    def test_discard_rules_with_same_head(self):
        rule1 = compile.parse1('p(x,y) :- q(x), r(y)')
        rule2 = compile.parse1('p(x,y) :- s(x), t(y)')
        self.assertTrue(self.ruleset.add_rule('p', rule1))
        self.assertTrue(self.ruleset.add_rule('p', rule2))
        self.assertTrue('p' in self.ruleset)
        self.assertTrue(rule1 in self.ruleset.get_rules('p'))
        self.assertTrue(rule2 in self.ruleset.get_rules('p'))

        self.assertTrue(self.ruleset.discard_rule('p', rule1))
        self.assertTrue(self.ruleset.discard_rule('p', rule2))
        self.assertFalse('p' in self.ruleset)
        self.assertEqual([], self.ruleset.keys())

    def test_discard_rules_with_different_head(self):
        rule1 = compile.parse1('p1(x,y) :- q(x), r(y)')
        rule2 = compile.parse1('p2(x,y) :- s(x), t(y)')
        self.assertTrue(self.ruleset.add_rule('p1', rule1))
        self.assertTrue(self.ruleset.add_rule('p2', rule2))
        self.assertTrue('p1' in self.ruleset)
        self.assertTrue('p2' in self.ruleset)
        self.assertTrue(rule1 in self.ruleset.get_rules('p1'))
        self.assertTrue(rule2 in self.ruleset.get_rules('p2'))

        self.assertTrue(self.ruleset.discard_rule('p1', rule1))
        self.assertTrue(self.ruleset.discard_rule('p2', rule2))
        self.assertFalse('p1' in self.ruleset)
        self.assertFalse('p2' in self.ruleset)
        self.assertEqual([], self.ruleset.keys())
