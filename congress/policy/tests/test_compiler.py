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

import unittest

from congress.policy import compile
from congress.tests import helper


class TestParser(unittest.TestCase):

    def test_column_references_lowlevel(self):
        """Test column-references with low-level checks."""
        # do the first one the painful way, to ensure the parser
        #   is doing something reasonable.
        ms = compile.ModuleSchemas()
        ms['nova'] = compile.Schema({'q': ('id', 'name', 'status')})
        code = ("p(x) :- nova:q(id=x)")
        actual = compile.parse(code, ms)
        self.assertEqual(len(actual), 1)
        rule = actual[0]
        self.assertEqual(len(rule.heads), 1)
        self.assertEqual(rule.head.table, "p")
        self.assertEqual(len(rule.head.arguments), 1)
        self.assertEqual(rule.head.arguments[0].name, 'x')
        self.assertEqual(len(rule.body), 1)
        lit = rule.body[0]
        self.assertFalse(lit.is_negated())
        self.assertEqual(lit.table, "nova:q")
        self.assertEqual(len(lit.arguments), 3)
        self.assertEqual(lit.arguments[0].name, 'x')
        self.assertNotEqual(lit.arguments[0].name, lit.arguments[1].name)
        self.assertNotEqual(lit.arguments[0].name, lit.arguments[2].name)
        self.assertNotEqual(lit.arguments[1].name, lit.arguments[2].name)

    def test_column_references_atom(self):
        """Test column references occurring in a single atom in a rule."""
        ms = compile.ModuleSchemas()
        ms['nova'] = compile.Schema({'q': ('id', 'name', 'status')})

        # Multiple column names
        code = ("p(x) :- nova:q(id=x, status=y)")
        actual = compile.parse(code, ms)
        correct = "p(x) :- nova:q(x, w, y)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Multiple column names')

        # Multiple column numbers
        code = ("p(x) :- nova:q(0=x, 1=y, 2=z)")
        actual = compile.parse(code, ms)
        correct = "p(x) :- nova:q(x, y, z)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Multiple column numbers')

        # Mix column names and numbers
        code = ("p(x) :- nova:q(id=x, 2=y)")
        actual = compile.parse(code, ms)
        correct = "p(x) :- nova:q(x, w, y)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Mix names and numbers')

        # Object constants
        code = ("p(x) :- nova:q(id=3, 2=2)")
        actual = compile.parse(code, ms)
        correct = "p(x) :- nova:q(3, w, 2)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Object constants')

        # Out of order
        code = ("p(x, y) :- nova:q(status=y, id=x)")
        actual = compile.parse(code, ms)
        correct = "p(x, y) :- nova:q(x, z, y)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Out of order')

        # Out of order with numbers
        code = ("p(x, y) :- nova:q(1=y, 0=x)")
        actual = compile.parse(code, ms)
        correct = "p(x, y) :- nova:q(x, y, z)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Out of order with numbers')

        # Positional plus named
        code = ("p(x, y) :- nova:q(x, status=y)")
        actual = compile.parse(code, ms)
        correct = "p(x, y) :- nova:q(x, z, y)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Positional plus named')

        # Positional plus named 2
        code = ("p(x, y, z) :- nova:q(x, y, 2=z)")
        actual = compile.parse(code, ms)
        correct = "p(x, y, z) :- nova:q(x, y, z)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Positional plus named 2')

        # Pure positional (different since we are providing schema)
        code = ("p(x, y, z) :- nova:q(x, y, z)")
        actual = compile.parse(code, ms)
        correct = "p(x, y, z) :- nova:q(x, y, z)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Pure positional')

        # Pure positional (without schema)
        code = ("p(x) :- nova:q(x, y, z)")
        actual = compile.parse(code, compile.ModuleSchemas())
        correct = "p(x) :- nova:q(x, y, z)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Pure positional without schema')

    def test_column_references_atom_errors(self):
        """Test invalid column references occurring in a single atom."""
        ms = compile.ModuleSchemas()
        ms['nova'] = compile.Schema({'q': ('id', 'name', 'status'),
                                     'r': ('id', 'age', 'weight')})

        def check_err(code, errmsg, msg):
            try:
                compile.parse(code, ms)
                self.fail("Error should have been thrown but was not: " + msg)
            except compile.CongressException as e:
                emsg = "Err message '{}' should include '{}'".format(
                    str(e), errmsg)
                self.assertTrue(errmsg in str(e), msg + ": " + emsg)

        check_err(
            'p(x) :- q(id=x, 0=y)',
            'columns for table q have not been declared',
            'Missing schema')

        check_err(
            'p(x) :- nova:q(id=x, birthday=y)',
            'column name birthday does not exist',
            'Unknown column name')

        check_err(
            'p(x) :- nova:q(id=x, status=x, id=y)',
            'two values for column name id',
            'Multiple values for column name')

        check_err(
            'p(x) :- nova:q(4=y)',
            'column number 4 is too large',
            'Large column number')

        check_err(
            'p(x) :- nova:q(4=y, id=w, 4=z)',
            'two values for column number 4',
            'Multiple values for column number')

        check_err(
            'p(x) :- nova:q(id=x, 0=y)',
            'column was given two values by reference parameters',
            'Conflict between name and number references')

        check_err(
            'p(x) :- nova:q(x, y, id=z)',
            'already provided by position arguments',
            'Conflict between name and position')

        check_err(
            'p(x) :- nova:q(x, y, 1=z)',
            '1 is already provided by position arguments',
            'Conflict between name and position')

        check_err(
            'p(x) :- nova:q(x, 1=z, y)',
            'positional parameter after a reference parameter',
            'Positional parameter after reference parameter')

    def test_column_references_multiple_atoms(self):
        """Test column references occurring in multiple atoms in a rule."""
        ms = compile.ModuleSchemas()
        ms['nova'] = compile.Schema({'q': ('id', 'name', 'status'),
                                     'r': ('id', 'age', 'weight')})

        # Multiple atoms
        code = ("p(x) :- nova:q(id=x, 2=y), nova:r(id=x)")
        actual = compile.parse(code, ms)
        correct = "p(x) :- nova:q(x, x0, y), nova:r(x, y0, y1)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Multiple atoms')

        # Multiple atoms sharing column name but different variables
        code = ("p(x) :- nova:q(id=x), nova:r(id=y)")
        actual = compile.parse(code, ms)
        correct = "p(x) :- nova:q(x, x0, x1), nova:r(y, y0, y1)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Multiple atoms shared column name')

        # Multiple atoms, same table
        code = ("p(x) :- nova:q(id=x, 2=y), nova:q(id=x)")
        actual = compile.parse(code, ms)
        correct = "p(x) :- nova:q(x, x0, y), nova:q(x, y0, y1)"
        eq = helper.datalog_same(helper.pol2str(actual), correct)
        self.assertTrue(eq, 'Multiple atoms, same table')


class TestCompiler(unittest.TestCase):

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

    def test_module_schemas(self):
        """Test that rules are properly checked against module schemas."""

        modules = compile.ModuleSchemas(
            {'mod1': compile.Schema({'p': (1, 2, 3), 'q': (1,)}),
             'mod2': compile.Schema({'p': (1,), 'q': (1, 2)})})

        def check_err(code_string, emsg, msg, f=compile.rule_errors):
            rule = compile.parse1(code_string)
            errs = f(rule, modules)
            self.assertTrue(any(emsg in str(err) for err in errs),
                    msg + ":: Failed to find error message '" + emsg +
                    "' in: " + ";".join(str(e) for e in errs))

        # no errors
        rule = compile.parse1('p(x) :- q(x), mod1:p(x, y, z), mod2:q(x, y), '
                              'mod1:q(t), mod2:p(t)')
        errs = compile.rule_errors(rule, modules)
        self.assertEqual(len(errs), 0, "Should not have found any errors")

        # unknown module
        check_err('p(x) :- q(x), mod3:q(x), r(x)',
                  'unknown module',
                  'Unknown module for rule')

        # unknown table within module
        check_err('p(x) :- q(x), mod1:r(x), r(x)',
                  'unknown table',
                  'Unknown table for rule')

        # wrong number of arguments
        check_err('p(x) :- q(x), mod1:p(x,y,z,w), r(x)',
                  'only 3 arguments are permitted',
                  'Wrong number of arguments for rule')

        # same tests for an atom

        # no errors
        atom = compile.parse1('mod1:p(1, 2, 2)')
        errs = compile.fact_errors(atom, modules)
        self.assertEqual(len(errs), 0, "Should not have found any errors")

        # unknown module
        check_err('mod3:q(1)',
                  'unknown module',
                  'Unknown module for atom',
                  f=compile.fact_errors)

        # unknown table within module
        check_err('mod1:r(1)',
                  'unknown table',
                  'Unknown table for atom',
                  f=compile.fact_errors)

        # wrong number of arguments
        check_err('mod1:p(1, 2, 3, 4)',
                  'only 3 arguments are permitted',
                  'Wrong number of arguments for atom',
                  f=compile.fact_errors)

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
