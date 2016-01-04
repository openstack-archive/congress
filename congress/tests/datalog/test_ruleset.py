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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from congress.datalog import compile
from congress.datalog import ruleset
from congress.tests import base


class TestRuleSet(base.TestCase):
    def setUp(self):
        super(TestRuleSet, self).setUp()
        self.ruleset = ruleset.RuleSet()

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

    def test_add_fact(self):
        fact1 = compile.Fact('p', (1, 2, 3))
        equivalent_rule = compile.Rule(compile.parse1('p(1,2,3)'), ())

        self.assertTrue(self.ruleset.add_rule('p', fact1))
        self.assertTrue('p' in self.ruleset)
        self.assertEqual([equivalent_rule], self.ruleset.get_rules('p'))
        self.assertEqual(['p'], self.ruleset.keys())

    def test_add_equivalent_rule(self):
        # equivalent_rule could be a fact because it has no body, and is
        # ground.
        equivalent_rule = compile.Rule(compile.parse1('p(1,2,3)'), ())

        self.assertTrue(self.ruleset.add_rule('p', equivalent_rule))
        self.assertTrue('p' in self.ruleset)
        self.assertEqual([equivalent_rule], self.ruleset.get_rules('p'))
        self.assertEqual(['p'], self.ruleset.keys())

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

    def test_discard_fact(self):
        fact = compile.Fact('p', (1, 2, 3))
        equivalent_rule = compile.Rule(compile.parse1('p(1,2,3)'), ())

        self.assertTrue(self.ruleset.add_rule('p', fact))
        self.assertTrue('p' in self.ruleset)
        self.assertEqual([equivalent_rule], self.ruleset.get_rules('p'))

        self.assertTrue(self.ruleset.discard_rule('p', fact))
        self.assertFalse('p' in self.ruleset)
        self.assertEqual([], self.ruleset.keys())

    def test_discard_equivalent_rule(self):
        fact = compile.Fact('p', (1, 2, 3))
        equivalent_rule = compile.Rule(compile.parse1('p(1,2,3)'), ())

        self.assertTrue(self.ruleset.add_rule('p', fact))
        self.assertTrue('p' in self.ruleset)
        self.assertEqual([equivalent_rule], self.ruleset.get_rules('p'))

        self.assertTrue(self.ruleset.discard_rule('p', equivalent_rule))
        self.assertFalse('p' in self.ruleset)
        self.assertEqual([], self.ruleset.keys())

    def test_contains(self):
        fact = compile.Fact('p', (1, 2, 3))
        rule = compile.parse1('p(x) :- q(x)')
        self.ruleset.add_rule('p', fact)
        self.ruleset.add_rule('p', rule)

        # positive tests
        equivalent_fact1 = compile.Fact('p', (1, 2, 3))
        equivalent_fact2 = compile.parse1('p(1,2,3)')
        equivalent_fact3 = compile.Rule(compile.parse1('p(1,2,3)'), ())
        equivalent_rule = compile.parse1('p(x) :- q(x)')
        self.assertTrue(self.ruleset.contains('p', equivalent_fact1))
        self.assertTrue(self.ruleset.contains('p', equivalent_fact2))
        self.assertTrue(self.ruleset.contains('p', equivalent_fact3))
        self.assertTrue(self.ruleset.contains('p', equivalent_rule))

        # negative tests
        nonequiv_fact = compile.parse1('p(4, 5, 6)')
        nonequiv_rule = compile.parse1('p(x) :- r(x)')
        self.assertFalse(self.ruleset.contains('p', nonequiv_fact))
        self.assertFalse(self.ruleset.contains('p', nonequiv_rule))
