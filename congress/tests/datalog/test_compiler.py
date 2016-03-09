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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import copy

from congress.datalog import analysis
from congress.datalog import base as datalogbase
from congress.datalog import compile
from congress.datalog import utility
from congress import exception
from congress.policy_engines import agnostic
from congress.tests import base
from congress.tests import helper


class TestParser(base.TestCase):

    def test_tablename(self):
        """Test correct parsing of tablenames."""
        p = compile.parse1('p(1)')
        self.assertEqual(p.table.table, 'p')
        self.assertIsNone(p.table.modal)
        self.assertIsNone(p.table.service)

        p = compile.parse1('nova:p(1)')
        self.assertEqual(p.table.table, 'p')
        self.assertIsNone(p.table.modal)
        self.assertEqual(p.table.service, 'nova')

        p = compile.parse1('execute[nova:p(1)]')
        self.assertEqual(p.table.table, 'p')
        self.assertEqual(p.table.modal, 'execute')
        self.assertEqual(p.table.service, 'nova')

    def test_rule_hash(self):
        """Test whether rules are properly hashed."""
        s = set()
        p = compile.parse1('p(x) :- q(x), s(x,y)')
        s.add(p)
        q = compile.parse1('p(x) :- q(x), s(x,y)')
        s.discard(q)
        self.assertEqual(s, set())

    def test_event_equality(self):
        r1 = compile.parse1('p(x) :- q(x)')
        r2 = compile.parse1('p(x) :- q(x)')
        e1 = compile.Event(formula=r1, target='alice', insert=True)
        e2 = compile.Event(formula=r2, target='alice', insert=True)
        self.assertEqual(e1, e2)

    def test_event_facts(self):
        # insert
        event = compile.parse('insert[p(1) :- true]')
        self.assertEqual(len(event), 1)
        event = event[0]
        fact = compile.parse1('p(1) :- true')
        self.assertEqual(event.formula, fact)
        self.assertEqual(event.insert, True)
        self.assertIsNone(event.target)

        # delete
        event = compile.parse('delete[p(1) :- true]')
        self.assertEqual(len(event), 1)
        event = event[0]
        fact = compile.parse1('p(1) :- true')
        self.assertEqual(event.formula, fact)
        self.assertEqual(event.insert, False)
        self.assertIsNone(event.target)

        # insert with policy
        event = compile.parse('insert[p(1) :- true; "policy"]')
        self.assertEqual(len(event), 1)
        event = event[0]
        fact = compile.parse1('p(1) :- true')
        self.assertEqual(event.formula, fact)
        self.assertEqual(event.insert, True)
        self.assertEqual(event.target, "policy")

    def test_event_rules(self):
        """Test modal operators."""
        # a rule we use a few times
        pqrule = compile.parse1('p(x) :- q(x)')

        # rule-level modal (with insert)
        event = compile.parse('insert[p(x) :- q(x)]')
        self.assertEqual(len(event), 1)
        event = event[0]
        self.assertEqual(event.formula, pqrule)
        self.assertEqual(event.insert, True)
        self.assertIsNone(event.target)

        # rule-level modal with delete
        event = compile.parse('delete[p(x) :- q(x)]')
        self.assertEqual(len(event), 1)
        event = event[0]
        self.assertEqual(event.formula, pqrule)
        self.assertEqual(event.insert, False)
        self.assertIsNone(event.target)

        # embedded modals
        event = compile.parse('insert[execute[p(x)] :- q(x)]')
        self.assertEqual(len(event), 1)
        event = event[0]
        rule = compile.parse1('execute[p(x)] :- q(x)')
        self.assertEqual(event.formula, rule)
        self.assertEqual(event.insert, True)
        self.assertIsNone(event.target)

        # rule-level modal with policy name
        event = compile.parse('insert[p(x) :- q(x); "policy"]')
        self.assertEqual(len(event), 1)
        event = event[0]
        self.assertEqual(event.formula, pqrule)
        self.assertEqual(event.insert, True)
        self.assertEqual(event.target, "policy")

    def test_modal_execute(self):
        # modal rule
        rule = compile.parse('execute[p(x)] :- q(x)')
        self.assertEqual(len(rule), 1)
        rule = rule[0]
        self.assertEqual(rule.head.table.modal, 'execute')

        # modal rule with namespace
        rule = compile.parse('execute[nova:disconnectNetwork(x)] :- q(x)')
        self.assertEqual(len(rule), 1)
        rule = rule[0]
        self.assertEqual(rule.head.table.modal, 'execute')

        # modal query
        rule = compile.parse('execute[p(x)]')
        self.assertEqual(len(rule), 1)
        rule = rule[0]
        self.assertEqual(rule.table.modal, 'execute')

    def test_update_rules(self):
        rule = compile.parse1('insert[p(x)] :- q(x)')
        self.assertEqual(rule.head.table.modal, 'insert')

        rule = compile.parse1('insert[p(x)] :- execute[q(x)]')
        self.assertEqual(rule.head.table.modal, 'insert')

    def test_modal_failures(self):
        self.assertRaises(exception.PolicyException, compile.parse1,
                          'insert[p(x) :- q(x)')
        self.assertRaises(exception.PolicyException, compile.parse1,
                          'insert[insert[p(x)] :- q(x)')
        self.assertRaises(exception.PolicyException, compile.parse1,
                          'nonexistent[insert[p(x)] :- q(x)]')
        self.assertRaises(exception.PolicyException, compile.parse1,
                          'insert[nonexistent[p(x)] :- q(x)]')


class TestColumnReferences(base.TestCase):

    class SchemaWrapper (object):
        """Placeholder so we don't use the actual policy-engine for tests."""
        def __init__(self, schema):
            self.schema = schema
            self.kind = datalogbase.DATASOURCE_POLICY_TYPE

    def test_column_references_lowlevel(self):
        """Test column-references with low-level checks."""
        # do the first one the painful way, to ensure the parser
        #   is doing something reasonable.
        run = agnostic.Runtime()
        code = ("p(x) :- nova:q(id=x)")
        actual = run.parse(code)
        self.assertEqual(len(actual), 1)
        rule = actual[0]
        self.assertEqual(len(rule.heads), 1)
        self.assertEqual(rule.head.table.table, "p")
        self.assertEqual(len(rule.head.arguments), 1)
        self.assertEqual(rule.head.arguments[0].name, 'x')
        self.assertEqual(len(rule.body), 1)
        lit = rule.body[0]
        self.assertFalse(lit.is_negated())
        self.assertEqual(lit.table.table, "q")
        self.assertIsNone(lit.table.modal)
        self.assertEqual(lit.table.service, 'nova')
        self.assertEqual(len(lit.arguments), 0)
        self.assertEqual(len(lit.named_arguments), 1)
        self.assertTrue('id' in lit.named_arguments)
        self.assertEqual(lit.named_arguments['id'].name, 'x')

    def test_hash(self):
        x = set()
        x.add(compile.parse1('p(x, y) :- nova:q(x, id=y)'))
        x.add(compile.parse1('p(x, y) :- nova:q(x, id=y)'))
        self.assertEqual(len(x), 1)
        self.assertTrue(compile.parse1('p(x, y) :- nova:q(x, id=y)') in x)
        x.discard(compile.parse1('p(x, y) :- nova:q(x, id=y)'))
        self.assertEqual(len(x), 0)

    def test_lessthan(self):
        x = compile.parse1('nova:q(x)')
        y = compile.parse1('nova:q(x, id=y)')
        self.assertLess(x, y)

        x = compile.parse1('nova:q(x)')
        y = compile.parse1('nova:q(x, id=y)')
        self.assertGreaterEqual(y, x)

        x = compile.parse1('nova:q(x, id=w)')
        y = compile.parse1('nova:q(x, id=y)')
        self.assertLess(x, y)

        x = compile.parse1('nova:q(id=x)')
        y = compile.parse1('nova:q(id=y)')
        self.assertLess(x, y)

        x = compile.parse1('nova:q(id=x)')
        y = compile.parse1('nova:q(id=y, status=z)')
        self.assertLess(x, y)

        x = compile.parse1('p(x, y) :- nova:q(x, id=y)')
        y = compile.parse1('p(x, y) :- nova:q(x, id=y, status=z)')
        self.assertLess(x, y)

    def test_column_references_parse_errors(self):
        """Test invalid column references occurring in a single atom."""
        def check_err(code, errmsg, msg):
            try:
                compile.parse(code)
                self.fail("Error should have been thrown but was not: " + msg)
            except exception.PolicyException as e:
                emsg = "Err message '{}' should include '{}'".format(
                    str(e), errmsg)
                self.assertTrue(errmsg in str(e), msg + ": " + emsg)

        check_err(
            'p(x) :- nova:q(id=x, status=x, id=y)',
            'two values for column name id',
            'Multiple values for column name')

        check_err(
            'p(x) :- nova:q(4=y, id=w, 4=z)',
            'two values for column number 4',
            'Multiple values for column number')

        check_err(
            'p(x) :- nova:q(x, 1=z, y)',
            'positional parameter after a reference parameter',
            'Positional parameter after reference parameter')

        check_err(
            'p(x) :- nova:q(x, y, 1=z)',
            '1 is already provided by position arguments',
            'Conflict between name and position')

    def test_column_references_validation_errors(self):
        """Test invalid column references occurring in a single atom."""
        schema = compile.Schema({'q': ('id', 'name', 'status'),
                                 'r': ('id', 'age', 'weight')},
                                complete=True)
        theories = {'nova': self.SchemaWrapper(schema)}

        def check_err(rule, errmsg, msg):
            rule = compile.parse1(rule)
            try:
                rule.eliminate_column_references(theories)
                self.fail("Failed to throw error {}".format(errmsg))
            except (exception.PolicyException,
                    exception.IncompleteSchemaException) as e:
                emsg = "Err messages '{}' should include '{}'".format(
                    str(e), errmsg)
                self.assertTrue(errmsg in str(e), msg + ": " + emsg)

        check_err(
            'p(x) :- nova:missing(id=x)',
            'uses unknown table missing',
            'Unknown table')

        check_err(
            'p(x) :- nova:q(id=x, birthday=y)',
            'column name birthday does not exist',
            'Unknown column name')

        check_err(
            'p(x) :- nova:q(4=y)',
            'column index 4 is too large',
            'Large column number')

        check_err(
            'p(x) :- nova:q(id=x, 0=y)',
            'index 0 references column id, which is also referenced by name',
            'Conflict between name and number references')

        check_err(
            'p(x) :- nova:q(x, y, id=z)',
            'already provided by position',
            'Conflict between name and position')

        theories = {}
        check_err(
            'p(x) :- nova:missing(id=x)',
            'schema is unknown',
            'Missing schema')

    def test_column_references_atom(self):
        """Test column references occurring in a single atom in a rule."""
        def check(code, correct, msg):
            actual = compile.parse1(code).eliminate_column_references(theories)
            eq = helper.datalog_same(str(actual), correct)
            self.assertTrue(eq, msg)

        run = agnostic.Runtime()
        run.create_policy('nova')
        schema = compile.Schema({'q': ('id', 'name', 'status')})
        theories = {'nova': self.SchemaWrapper(schema)}

        # Multiple column names
        code = ("p(x) :- nova:q(id=x, status=y)")
        correct = "p(x) :- nova:q(x, w, y)"
        check(code, correct, 'Multiple column names')

        # Multiple column numbers
        code = ("p(x) :- nova:q(0=x, 1=y, 2=z)")
        correct = "p(x) :- nova:q(x, y, z)"
        check(code, correct, 'Multiple column numbers')

        # Mix column names and numbers
        code = ("p(x) :- nova:q(id=x, 2=y)")
        correct = "p(x) :- nova:q(x, w, y)"
        check(code, correct, 'Mix names and numbers')

        # Object constants
        code = ("p(x) :- nova:q(id=3, 2=2)")
        correct = "p(x) :- nova:q(3, w, 2)"
        check(code, correct, 'Object constants')

        # Out of order
        code = ("p(x, y) :- nova:q(status=y, id=x)")
        correct = "p(x, y) :- nova:q(x, z, y)"
        check(code, correct,  'Out of order')

        # Out of order with numbers
        code = ("p(x, y) :- nova:q(1=y, 0=x)")
        correct = "p(x, y) :- nova:q(x, y, z)"
        check(code, correct, 'Out of order with numbers')

        # Positional plus named
        code = ("p(x, y) :- nova:q(x, status=y)")
        correct = "p(x, y) :- nova:q(x, z, y)"
        check(code, correct, 'Positional plus named')

        # Positional plus named 2
        code = ("p(x, y, z) :- nova:q(x, y, 2=z)")
        correct = "p(x, y, z) :- nova:q(x, y, z)"
        check(code, correct, 'Positional plus named 2')

        # Pure positional (different since we are providing schema)
        code = ("p(x, y, z) :- nova:q(x, y, z)")
        correct = "p(x, y, z) :- nova:q(x, y, z)"
        check(code, correct, 'Pure positional')

        # Pure positional (without schema)
        code = ("p(x) :- nova:q(x, y, z)")
        run.delete_policy('nova')
        correct = "p(x) :- nova:q(x, y, z)"
        check(code, correct, 'Pure positional without schema')

    def test_column_references_multiple_atoms(self):
        """Test column references occurring in multiple atoms in a rule."""
        def check(code, correct, msg):
            actual = compile.parse1(code).eliminate_column_references(theories)
            eq = helper.datalog_same(str(actual), correct)
            self.assertTrue(eq, msg)

        run = agnostic.Runtime()
        run.create_policy('nova')
        schema = compile.Schema({'q': ('id', 'name', 'status'),
                                 'r': ('id', 'age', 'weight')})
        theories = {'nova': self.SchemaWrapper(schema)}

        # Multiple atoms
        code = ("p(x) :- nova:q(id=x, 2=y), nova:r(id=x)")
        correct = "p(x) :- nova:q(x, x0, y), nova:r(x, y0, y1)"
        check(code, correct, 'Multiple atoms')

        # Multiple atoms sharing column name but different variables
        code = ("p(x) :- nova:q(id=x), nova:r(id=y)")
        correct = "p(x) :- nova:q(x, x0, x1), nova:r(y, y0, y1)"
        check(code, correct, 'Multiple atoms shared column name')

        # Multiple atoms, same table
        code = ("p(x) :- nova:q(id=x, 2=y), nova:q(id=x)")
        correct = "p(x) :- nova:q(x, x0, y), nova:q(x, y0, y1)"
        check(code, correct, 'Multiple atoms, same table')

    def test_eliminate_column_references_body_order(self):
        """Test eliminate_column_references preserves order insensitivity."""
        run = agnostic.Runtime()
        run.create_policy('nova')
        schema = compile.Schema({'q': ('id', 'name', 'status'),
                                 'r': ('id', 'age', 'weight')})
        theories = {'nova': self.SchemaWrapper(schema)}

        rule1 = compile.parse1("p(x) :- nova:q(id=x, 2=y), nova:r(id=x)"
                               ).eliminate_column_references(theories)
        rule2 = compile.parse1("p(x) :- nova:r(id=x), nova:q(id=x, 2=y)"
                               ).eliminate_column_references(theories)
        self.assertEqual(rule1, rule2, 'eliminate_column_references failed to '
                                       'preserve order insensitivity')


class TestCompiler(base.TestCase):

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

        # multiple heads with modal
        rule = compile.parse1('execute[p(x)], r(x) :- q(x)')
        errs = compile.rule_errors(rule)
        self.assertEqual(len(set([str(x) for x in errs])), 1)

        # modal in body
        rule = compile.parse1('p(x) :- execute[q(x)]')
        errs = compile.rule_errors(rule)
        self.assertEqual(len(set([str(x) for x in errs])), 1)

        # keywords
        rule = compile.parse1('equal(x) :- q(x)')
        errs = compile.rule_errors(rule)
        self.assertEqual(len(set([str(x) for x in errs])), 1)

    def test_module_schemas(self):
        """Test that rules are properly checked against module schemas."""

        run = agnostic.Runtime()
        run.create_policy('mod1')
        run.create_policy('mod2')
        run.set_schema('mod1', compile.Schema({'p': (1, 2, 3), 'q': (1,)}),
                       complete=True)
        run.set_schema('mod2', compile.Schema({'p': (1,), 'q': (1, 2)}),
                       complete=True)

        def check_err(code_string, theory, emsg, msg, f=compile.rule_errors):
            rule = compile.parse1(code_string)
            errs = f(rule, run.theory, theory)
            self.assertTrue(any(emsg in str(err) for err in errs),
                            msg + ":: Failed to find error message '" + emsg +
                            "' in: " + ";".join(str(e) for e in errs))

        # no errors
        rule = compile.parse1('p(x) :- q(x), mod1:p(x, y, z), mod2:q(x, y), '
                              'mod1:q(t), mod2:p(t)')
        errs = compile.rule_errors(rule, run.theory)
        self.assertEqual(len(errs), 0, "Should not have found any errors")

        # unknown table within module
        check_err('p(x) :- q(x), mod1:r(x), r(x)',
                  'mod3',
                  'unknown table',
                  'Unknown table for rule')

        # wrong number of arguments
        check_err('p(x) :- q(x), mod1:p(x,y,z,w), r(x)',
                  'mod3',
                  'only 3 arguments are permitted',
                  'Wrong number of arguments for rule')

        # same tests for an atom

        # no errors
        atom = compile.parse1('p(1, 2, 2)')
        errs = compile.fact_errors(atom, run.theory, 'mod1')
        self.assertEqual(len(errs), 0, "Should not have found any errors")

        # unknown table within module
        check_err('r(1)',
                  'mod1',
                  'unknown table',
                  'Unknown table for atom',
                  f=compile.fact_errors)

        # wrong number of arguments
        check_err('p(1, 2, 3, 4)',
                  'mod1',
                  'only 3 arguments are permitted',
                  'Wrong number of arguments for atom',
                  f=compile.fact_errors)

        # schema update
        schema = compile.Schema()
        rule1 = compile.parse1('p(x) :- q(x, y)')
        change1 = schema.update(rule1.head, True)
        rule2 = compile.parse1('p(x) :- r(x, y)')
        change2 = schema.update(rule2.head, True)
        self.assertEqual(schema.count['p'], 2)
        schema.revert(change2)
        self.assertEqual(schema.count['p'], 1)
        schema.revert(change1)
        self.assertEqual('p' in schema.count, False)

        schema.update(rule1.head, True)
        schema.update(rule2.head, True)
        change1 = schema.update(rule1.head, False)
        change2 = schema.update(rule2.head, False)
        self.assertEqual('p' in schema.count, False)
        schema.revert(change2)
        self.assertEqual(schema.count['p'], 1)
        schema.revert(change1)
        self.assertEqual(schema.count['p'], 2)

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


class TestDependencyGraph(base.TestCase):

    def test_nodes_edges(self):
        g = compile.RuleDependencyGraph()

        # first insertion
        g.formula_insert(compile.parse1('p(x), q(x) :- r(x), s(x)'))
        self.assertTrue(g.node_in('p'))
        self.assertTrue(g.node_in('q'))
        self.assertTrue(g.node_in('r'))
        self.assertTrue(g.node_in('s'))
        self.assertTrue(g.edge_in('p', 'r', False))
        self.assertTrue(g.edge_in('p', 's', False))
        self.assertTrue(g.edge_in('q', 'r', False))
        self.assertTrue(g.edge_in('q', 's', False))
        self.assertFalse(g.has_cycle())

        # another insertion
        g.formula_insert(compile.parse1('r(x) :- t(x)'))
        self.assertTrue(g.node_in('p'))
        self.assertTrue(g.node_in('q'))
        self.assertTrue(g.node_in('r'))
        self.assertTrue(g.node_in('s'))
        self.assertTrue(g.edge_in('p', 'r', False))
        self.assertTrue(g.edge_in('p', 's', False))
        self.assertTrue(g.edge_in('q', 'r', False))
        self.assertTrue(g.edge_in('q', 's', False))
        self.assertTrue(g.node_in('t'))
        self.assertTrue(g.edge_in('r', 't', False))
        self.assertFalse(g.has_cycle())

        # 3rd insertion, creating a cycle
        g.formula_insert(compile.parse1('t(x) :- p(x)'))
        self.assertTrue(g.edge_in('t', 'p', False))
        self.assertTrue(g.has_cycle())

        # deletion
        g.formula_delete(compile.parse1('p(x), q(x) :- r(x), s(x)'))
        self.assertTrue(g.node_in('p'))
        self.assertTrue(g.node_in('r'))
        self.assertTrue(g.node_in('t'))
        self.assertTrue(g.edge_in('r', 't', False))
        self.assertTrue(g.edge_in('t', 'p', False))
        self.assertFalse(g.has_cycle())

        # double-insertion
        g.formula_insert(compile.parse1('p(x) :- q(x), r(x)'))
        g.formula_insert(compile.parse1('p(1) :- r(1)'))
        self.assertTrue(g.has_cycle())

        # deletion -- checking for bag semantics
        g.formula_delete(compile.parse1('p(1) :- r(1)'))
        self.assertTrue(g.has_cycle())
        g.formula_delete(compile.parse1('p(x) :- q(x), r(x)'))
        self.assertFalse(g.has_cycle())

        # update
        g.formula_update([
            compile.Event(compile.parse1('a(x) :- b(x)')),
            compile.Event(compile.parse1('b(x) :- c(x)')),
            compile.Event(compile.parse1('c(x) :- a(x)'))])
        self.assertTrue(g.has_cycle())
        g.formula_update([
            compile.Event(compile.parse1('c(x) :- a(x)'), insert=False)])
        self.assertFalse(g.has_cycle())

        # cycle enumeration
        g = compile.RuleDependencyGraph()
        g.formula_insert(compile.parse1('p(x) :- q(x), r(x)'))
        g.formula_insert(compile.parse1('q(x) :- t(x), not s(x)'))
        g.formula_insert(compile.parse1('t(x) :- t(x), p(x), q(x)'))
        self.assertTrue(g.has_cycle())
        self.assertEqual(len(g.cycles()), 3)
        expected_cycle_set = set([
            utility.Cycle(['p', 'q', 't', 'p']),
            utility.Cycle(['q', 't', 'q']),
            utility.Cycle(['t', 't'])
        ])
        actual_cycle_set = set([
            utility.Cycle(g.cycles()[0]),
            utility.Cycle(g.cycles()[1]),
            utility.Cycle(g.cycles()[2])
        ])
        self.assertEqual(expected_cycle_set, actual_cycle_set)

    def test_dependencies(self):
        g = compile.RuleDependencyGraph()
        g.formula_insert(compile.parse1('p(x) :- q(x), r(x)'))
        g.formula_insert(compile.parse1('q(x) :- t(x), not s(x)'))
        self.assertEqual(g.dependencies('p'), set(['p', 'q', 'r', 't', 's']))
        self.assertEqual(g.dependencies('q'), set(['q', 't', 's']))
        self.assertEqual(g.dependencies('r'), set(['r']))
        self.assertEqual(g.dependencies('t'), set(['t']))
        self.assertEqual(g.dependencies('s'), set(['s']))

        # cyclic case
        g = compile.RuleDependencyGraph()
        g.formula_insert(compile.parse1('p(x) :- q(x), r(x)'))
        g.formula_insert(compile.parse1('q(x) :- t(x), not s(x)'))
        g.formula_insert(compile.parse1('t(x) :- t(x), p(x), q(x)'))
        self.assertEqual(g.dependencies('p'), set(['p', 'q', 'r', 't', 's']))
        self.assertEqual(g.dependencies('q'), set(['p', 'q', 'r', 't', 's']))
        self.assertEqual(g.dependencies('r'), set(['r']))
        self.assertEqual(g.dependencies('t'), set(['p', 'q', 'r', 't', 's']))
        self.assertEqual(g.dependencies('s'), set(['s']))

        g = compile.RuleDependencyGraph(head_to_body=False)
        g.formula_insert(compile.parse1('p(x) :- q(x), r(x)'))
        g.formula_insert(compile.parse1('q(x) :- t(x), not s(x)'))
        self.assertEqual(g.dependencies('p'), set(['p']))
        self.assertEqual(g.dependencies('q'), set(['q', 'p']))
        self.assertEqual(g.dependencies('r'), set(['r', 'p']))
        self.assertEqual(g.dependencies('t'), set(['t', 'q', 'p']))
        self.assertEqual(g.dependencies('s'), set(['s', 'q', 'p']))

    def test_modal_index(self):
        m = analysis.ModalIndex()
        m.add('execute', 'p')
        self.assertEqual(set(m.tables('execute')), set(['p']))
        m.add('execute', 'q')
        self.assertEqual(set(m.tables('execute')), set(['p', 'q']))
        m.remove('execute', 'q')
        self.assertEqual(set(m.tables('execute')), set(['p']))
        m.add('execute', 'q')
        m.add('execute', 'q')
        m.remove('execute', 'q')
        self.assertEqual(set(m.tables('execute')), set(['p', 'q']))
        m.remove('execute', 'q')
        self.assertEqual(set(m.tables('execute')), set(['p']))
        m.add('foo', 'p')
        self.assertEqual(set(m.tables('foo')), set(['p']))
        self.assertEqual(set(m.tables('bar')), set())
        self.assertEqual(set(m.tables('execute')), set(['p']))

    def test_modal_index_composition(self):
        m = analysis.ModalIndex()
        m.add('execute', 'p')
        m.add('execute', 'q')
        m.add('execute', 'r')
        m.add('foo', 'r')
        m.add('foo', 's')

        n = analysis.ModalIndex()
        n.add('execute', 'p')
        n.add('execute', 'alpha')
        n.add('foo', 'r')
        n.add('bar', 'beta')

        n_plus_m = analysis.ModalIndex()
        n_plus_m.add('execute', 'p')
        n_plus_m.add('execute', 'p')
        n_plus_m.add('execute', 'q')
        n_plus_m.add('execute', 'r')
        n_plus_m.add('execute', 'alpha')
        n_plus_m.add('foo', 'r')
        n_plus_m.add('foo', 's')
        n_plus_m.add('foo', 'r')
        n_plus_m.add('bar', 'beta')

        m_copy = copy.copy(m)
        m_copy += n
        self.assertEqual(m_copy, n_plus_m)

        m_minus_n = analysis.ModalIndex()
        m_minus_n.add('execute', 'q')
        m_minus_n.add('execute', 'r')
        m_minus_n.add('foo', 's')

        m_copy = copy.copy(m)
        m_copy -= n
        self.assertEqual(m_copy, m_minus_n)

    def test_modals(self):
        g = compile.RuleDependencyGraph()
        g.formula_insert(compile.parse1('p(x) :- q(x)'))
        g.formula_insert(compile.parse1('q(x) :- r(x)'))
        g.formula_insert(compile.parse1('execute[p(x)] :- q(x)'))
        chgs = g.formula_insert(compile.parse1('execute[r(x)] :- q(x)'))
        g.formula_insert(compile.parse1('insert[s(x)] :- q(x)'))
        self.assertEqual(set(g.tables_with_modal('execute')), set(['p', 'r']))
        g.undo_changes(chgs)
        self.assertEqual(set(g.tables_with_modal('execute')), set(['p']))
        chgs = g.formula_delete(compile.parse1('execute[p(x)] :- q(x)'))
        self.assertEqual(set(g.tables_with_modal('execute')), set())
        g.undo_changes(chgs)
        self.assertEqual(set(g.tables_with_modal('execute')), set(['p']))
