# Copyright (c) 2013 VMware, Inc. All rights reserved.
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

from policy import compile
import unittest


class TestCompiler(unittest.TestCase):

    def setUp(self):
        pass

    def test_foo(self):
        self.assertTrue("a" in "abc", "'a' is a substring of 'abc'")

    def test_type_checkers(self):
        """Test the type checkers, e.g. is_atom, is_rule."""
        atom = compile.Literal("p", [])
        atom2 = compile.Literal("q", [])
        atom3 = compile.Literal("r", [])
        lit = compile.Literal("r", [], negated=True)
        regular_rule = compile.Rule(atom, [atom2, atom3])
        regular_rule2 = compile.Rule(atom, [lit, atom2])
        multi_rule = compile.Rule([atom, atom2], [atom3])
        fake_rule = compile.Rule([atom, 1], [atom2])
        fake_rule2 = compile.Rule(atom, [atom2, 1])

        # is_atom
        self.assertTrue(compile.is_atom(atom))
        self.assertTrue(compile.is_atom(atom2))
        self.assertTrue(compile.is_atom(atom3))
        self.assertFalse(compile.is_atom(lit))
        self.assertFalse(compile.is_atom(regular_rule))
        self.assertFalse(compile.is_atom(regular_rule2))
        self.assertFalse(compile.is_atom(multi_rule))
        self.assertFalse(compile.is_atom(fake_rule))
        self.assertFalse(compile.is_atom(fake_rule2))
        self.assertFalse(compile.is_atom("a string"))

        # is_literal
        self.assertTrue(compile.is_literal(atom))
        self.assertTrue(compile.is_literal(atom2))
        self.assertTrue(compile.is_literal(atom3))
        self.assertTrue(compile.is_literal(lit))
        self.assertFalse(compile.is_literal(regular_rule))
        self.assertFalse(compile.is_literal(regular_rule2))
        self.assertFalse(compile.is_literal(multi_rule))
        self.assertFalse(compile.is_literal(fake_rule))
        self.assertFalse(compile.is_literal(fake_rule2))
        self.assertFalse(compile.is_literal("a string"))

        # is_regular_rule
        self.assertFalse(compile.is_regular_rule(atom))
        self.assertFalse(compile.is_regular_rule(atom2))
        self.assertFalse(compile.is_regular_rule(atom3))
        self.assertFalse(compile.is_regular_rule(lit))
        self.assertTrue(compile.is_regular_rule(regular_rule))
        self.assertTrue(compile.is_regular_rule(regular_rule2))
        self.assertFalse(compile.is_regular_rule(multi_rule))
        self.assertFalse(compile.is_regular_rule(fake_rule))
        self.assertFalse(compile.is_regular_rule(fake_rule2))
        self.assertFalse(compile.is_regular_rule("a string"))

        # is_multi_rule
        self.assertFalse(compile.is_multi_rule(atom))
        self.assertFalse(compile.is_multi_rule(atom2))
        self.assertFalse(compile.is_multi_rule(atom3))
        self.assertFalse(compile.is_multi_rule(lit))
        self.assertFalse(compile.is_multi_rule(regular_rule))
        self.assertFalse(compile.is_multi_rule(regular_rule2))
        self.assertTrue(compile.is_multi_rule(multi_rule))
        self.assertFalse(compile.is_multi_rule(fake_rule))
        self.assertFalse(compile.is_multi_rule(fake_rule2))
        self.assertFalse(compile.is_multi_rule("a string"))

        # is_rule
        self.assertFalse(compile.is_rule(atom))
        self.assertFalse(compile.is_rule(atom2))
        self.assertFalse(compile.is_rule(atom3))
        self.assertFalse(compile.is_rule(lit))
        self.assertTrue(compile.is_rule(regular_rule))
        self.assertTrue(compile.is_rule(regular_rule2))
        self.assertTrue(compile.is_rule(multi_rule))
        self.assertFalse(compile.is_rule(fake_rule))
        self.assertFalse(compile.is_rule(fake_rule2))
        self.assertFalse(compile.is_rule("a string"))

        # is_datalog
        self.assertTrue(compile.is_datalog(atom))
        self.assertTrue(compile.is_datalog(atom2))
        self.assertTrue(compile.is_datalog(atom3))
        self.assertFalse(compile.is_datalog(lit))
        self.assertTrue(compile.is_datalog(regular_rule))
        self.assertTrue(compile.is_datalog(regular_rule2))
        self.assertFalse(compile.is_datalog(multi_rule))
        self.assertFalse(compile.is_datalog(fake_rule))
        self.assertFalse(compile.is_datalog(fake_rule2))
        self.assertFalse(compile.is_datalog("a string"))

        # is_extended_datalog
        self.assertTrue(compile.is_extended_datalog(atom))
        self.assertTrue(compile.is_extended_datalog(atom2))
        self.assertTrue(compile.is_extended_datalog(atom3))
        self.assertFalse(compile.is_extended_datalog(lit))
        self.assertTrue(compile.is_extended_datalog(regular_rule))
        self.assertTrue(compile.is_extended_datalog(regular_rule2))
        self.assertTrue(compile.is_extended_datalog(multi_rule))
        self.assertFalse(compile.is_extended_datalog(fake_rule))
        self.assertFalse(compile.is_extended_datalog(fake_rule2))
        self.assertFalse(compile.is_extended_datalog("a string"))

    def test_rule_validation(self):
        """Test that rules are properly validated."""
        # unsafe var in head
        rule = compile.parse1('p(x) :- q(y)')
        errs = compile.rule_errors(rule)
        self.assertEqual(len(errs), 1)

        # multiple unsafe vars in head
        rule = compile.parse1('p(x,y,z) :- q(w)')
        errs = compile.rule_errors(rule)
        self.assertEqual(len(set([str(x) for x in errs])), 3)

        # unsafe var in negtative literal:
        rule = compile.parse1('p(x) :- q(x), not r(y)')
        errs = compile.rule_errors(rule)
        self.assertEqual(len(set([str(x) for x in errs])), 1)

        # unsafe var in negative literal: ensure head doesn't make safe
        rule = compile.parse1('p(x) :- not q(x)')
        errs = compile.rule_errors(rule)
        self.assertEqual(len(set([str(x) for x in errs])), 1)

        # unsafe var in negative literal:
        #      ensure partial safety not total safety
        rule = compile.parse1('p(x) :- q(x), not r(x,y)')
        errs = compile.rule_errors(rule)
        self.assertEqual(len(set([str(x) for x in errs])), 1)

        # unsafe var in negative literal: ensure double negs doesn't make safe
        rule = compile.parse1('p(x) :- q(x), not r(x,y), not s(x, y)')
        errs = compile.rule_errors(rule)
        self.assertEqual(len(set([str(x) for x in errs])), 1)

    def test_rule_recursion(self):
        rules = compile.parse('p(x) :- q(x), r(x)  q(x) :- r(x) r(x) :- t(x)')
        self.assertFalse(compile.is_recursive(rules))

        rules = compile.parse('p(x) :- p(x)')
        self.assertTrue(compile.is_recursive(rules))

        rules = compile.parse('p(x) :- q(x)  q(x) :- r(x)  r(x) :- p(x)')
        self.assertTrue(compile.is_recursive(rules))

        rules = compile.parse('p(x) :- q(x)  q(x) :- not p(x)')
        self.assertTrue(compile.is_recursive(rules))

        rules = compile.parse('p(x) :- q(x), s(x)  q(x) :- t(x)  s(x) :- p(x)')
        self.assertTrue(compile.is_recursive(rules))

    def test_rule_stratification(self):
        rules = compile.parse('p(x) :- not q(x)')
        self.assertTrue(compile.is_stratified(rules))

        rules = compile.parse('p(x) :- p(x)')
        self.assertTrue(compile.is_stratified(rules))

        rules = compile.parse('p(x) :- q(x)  q(x) :- p(x)')
        self.assertTrue(compile.is_stratified(rules))

        rules = compile.parse('p(x) :- q(x)  q(x) :- not r(x)')
        self.assertTrue(compile.is_stratified(rules))

        rules = compile.parse('p(x) :- not q(x)  q(x) :- not r(x)')
        self.assertTrue(compile.is_stratified(rules))

        rules = compile.parse('p(x) :- not q(x)  '
                              'q(x) :- not r(x)  '
                              'r(x) :- not s(x)')
        self.assertTrue(compile.is_stratified(rules))

        rules = compile.parse('p(x) :- q(x), r(x) '
                              'q(x) :- not t(x) '
                              'r(x) :- not s(x)')
        self.assertTrue(compile.is_stratified(rules))

        rules = compile.parse('p(x) :- not p(x)')
        self.assertFalse(compile.is_stratified(rules))

        rules = compile.parse('p(x) :- q(x)  q(x) :- not p(x)')
        self.assertFalse(compile.is_stratified(rules))

        rules = compile.parse('p(x) :- q(x),r(x)  r(x) :- not p(x)')
        self.assertFalse(compile.is_stratified(rules))

        rules = compile.parse('p(x) :- q(x), r(x) '
                              'q(x) :- not t(x) '
                              'r(x) :- not s(x) '
                              't(x) :- p(x)')
        self.assertFalse(compile.is_stratified(rules))

if __name__ == '__main__':
    unittest.main()
