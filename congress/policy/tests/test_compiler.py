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
