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
#

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from oslo_log import log as logging

from congress.datalog import base as datalog_base
from congress.datalog import compile
from congress.policy_engines import agnostic
from congress.tests import base
from congress.tests import helper

LOG = logging.getLogger(__name__)

MAT_THEORY = 'classification test theory'
DB_THEORY = 'database test theory'


class TestRuntime(base.TestCase):
    """Tests for Runtime that are not specific to any theory."""

    def prep_runtime(self, code=None, msg=None, target=None):
        # compile source
        if msg is not None:
            LOG.debug(msg)
        if code is None:
            code = ""
        if target is None:
            target = MAT_THEORY
        run = agnostic.Runtime()
        run.create_policy(MAT_THEORY,
                          kind=datalog_base.MATERIALIZED_POLICY_TYPE)
        run.create_policy(DB_THEORY,
                          kind=datalog_base.DATABASE_POLICY_TYPE)
        # ensure inserts without target go to MAT_THEORY
        run.DEFAULT_THEORY = MAT_THEORY
        run.debug_mode()
        run.insert(code, target=target)
        return run

    def check_equal(self, actual_string, correct_string, msg):
        self.assertTrue(helper.datalog_equal(
            actual_string, correct_string, msg))

    def check_db(self, runtime, correct_string, msg):
        """Check that runtime.theory[DB_THEORY] is equal to CORRECT_STRING."""
        self.check_equal(runtime.theory[DB_THEORY].content_string(),
                         correct_string, msg)

    def check_class(self, runtime, correct_string, msg, tablenames=None):
        """Test MAT_THEORY.

        Check that runtime RUN.theory[MAT_THEORY] is
        equal to CORRECT_STRING.
        """
        actual = runtime.theory[MAT_THEORY].content(tablenames=tablenames)
        actual_string = " ".join(str(x) for x in actual)
        self.check_equal(actual_string, correct_string, msg)

    def showdb(self, run):
        LOG.debug("Resulting DB: %s",
                  run.theory[MAT_THEORY].database | run.theory[DB_THEORY])

    def test_database(self):
        """Test Database with insert/delete."""
        run = self.prep_runtime('')

        self.check_db(run, "", "Empty database on init")

        # set semantics, not bag semantics
        run.insert('r(1)', DB_THEORY)
        self.check_db(run, "r(1)", "Basic insert")
        run.insert('r(1)', DB_THEORY)
        self.check_db(run, "r(1)", "Duplicate insert")

        run.delete('r(1)', DB_THEORY)
        self.check_db(run, "", "Delete")
        run.delete('r(1)', DB_THEORY)
        self.check_db(run, "", "Delete from empty table")

    def test_error_checking(self):
        """Test error-checking on insertion of rules."""
        code = ("p(x) :- q(x)")
        run = self.prep_runtime(code)
        result = run.get_target(MAT_THEORY).policy()
        self.assertEqual(1, len(result))
        self.assertTrue(compile.parse1("p(x) :- q(x)") in result)

        # safety 1
        code = ("p(x) :- not q(x)")
        run = self.prep_runtime("", "** Safety 1 **")
        permitted, changes = run.insert(code, MAT_THEORY)
        self.assertFalse(permitted)

        # safety 2
        code = ("p(x) :- q(y)")
        run = self.prep_runtime("", "** Safety 2 **")
        permitted, changes = run.insert(code, MAT_THEORY)
        self.assertFalse(permitted)

        # TODO(thinrichs): weaken cross-policy recursion restriction
        #   so that we can include recursion within a single theory.
        # recursion into classification theory
        # code = ("p(x) :- p(x)")
        # run = self.prep_runtime("", "** Classification Recursion **")
        # permitted, changes = run.insert(code, MAT_THEORY)
        # self.assertTrue(permitted)

        # stratification into classification theory
        code = ("p(x) :- q(x), not p(x)")
        run = self.prep_runtime("", "** Classification Stratification **")
        permitted, changes = run.insert(code, MAT_THEORY)
        self.assertFalse(permitted)

    def test_basic(self):
        """Materialized Theory: test rule propagation."""
        code = ("q(x) :- p(x), r(x)")
        run = self.prep_runtime(
            code, "**** Materialized Theory: Basic propagation tests ****")
        run.insert('r(1)', MAT_THEORY)
        run.insert('p(1)', MAT_THEORY)
        self.check_class(run, "r(1) p(1) q(1)",
                         "Insert into base table with 1 propagation")

        run.delete('r(1)', MAT_THEORY)
        self.check_class(run, "p(1)",
                         "Delete from base table with 1 propagation")

        # multiple rules
        code = ("q(x) :- p(x), r(x)"
                "q(x) :- s(x)")
        run.insert('p(1)', MAT_THEORY)
        run.insert('r(1)', MAT_THEORY)
        self.check_class(run, "p(1) r(1) q(1)", "Insert: multiple rules")
        run.insert('s(1)', MAT_THEORY)
        self.check_class(run, "p(1) r(1) s(1) q(1)",
                         "Insert: duplicate conclusions")

    def test_short_body(self):
        code = ("q(x) :- p(x)")
        run = self.prep_runtime(
            code, "**** Materialized Theory: Body length 1 tests ****")

        run.insert('p(1)', MAT_THEORY)
        self.check_class(run, "p(1) q(1)", "Insert with body of size 1")
        self.showdb(run)
        run.delete('p(1)', MAT_THEORY)
        self.showdb(run)
        self.check_class(run, "", "Delete with body of size 1")

    def test_existentials(self):
        code = ("q(x) :- p(x), r(y)")
        run = self.prep_runtime(
            code,
            "**** Materialized Theory: Unary tables with existential ****")
        run.insert('p(1)', MAT_THEORY)
        run.insert('r(2)', MAT_THEORY)
        run.insert('r(3)', MAT_THEORY)
        self.showdb(run)
        self.check_class(run, "p(1) r(2) r(3) q(1)",
                         "Insert with unary table and existential")
        run.delete('r(2)', MAT_THEORY)
        self.showdb(run)
        self.check_class(run, "p(1) r(3) q(1)",
                         "Delete 1 with unary table and existential")
        run.delete('r(3)', MAT_THEORY)
        self.check_class(run, "p(1)",
                         "Delete all with unary table and existential")

    def test_nonmonadic(self):
        run = self.prep_runtime(
            "q(x) :- p(x,y)",
            "**** Materialized Theory: Multiple-arity table tests ****")

        run.insert('p(1,2)', MAT_THEORY)
        self.check_class(run, "p(1, 2) q(1)",
                         "Insert: existential variable in body of size 1")
        run.delete('p(1,2)', MAT_THEORY)
        self.check_class(run, "",
                         "Delete: existential variable in body of size 1")

        code = ("q(x) :- p(x,y), r(y,x)")
        run = self.prep_runtime(code)
        run.insert('p(1,2)', MAT_THEORY)
        run.insert('r(2,1)', MAT_THEORY)
        self.check_class(run, "p(1, 2) r(2, 1) q(1)",
                         "Insert: join in body of size 2")
        run.delete('p(1,2)', MAT_THEORY)
        self.check_class(run, "r(2, 1)",
                         "Delete: join in body of size 2")
        run.insert('p(1,2)', MAT_THEORY)
        run.insert('p(1,3)', MAT_THEORY)
        run.insert('r(3,1)', MAT_THEORY)
        self.check_class(
            run, "r(2, 1) r(3,1) p(1, 2) p(1, 3) q(1)",
            "Insert: multiple existential bindings for same head")

        run.delete('p(1,2)', MAT_THEORY)
        self.check_class(
            run, "r(2, 1) r(3,1) p(1, 3) q(1)",
            "Delete: multiple existential bindings for same head")

    def test_larger_join(self):
        code = ("q(x,v) :- p(x,y), r(y,z), s(z,w), t(w,v)")
        run = self.prep_runtime(code)
        run.insert('p(1, 10)', MAT_THEORY)
        run.insert('p(1, 20)', MAT_THEORY)
        run.insert('p(10, 100)', MAT_THEORY)
        run.insert('p(20, 200)', MAT_THEORY)
        run.insert('p(100, 1000)', MAT_THEORY)
        run.insert('p(200, 2000)', MAT_THEORY)
        run.insert('p(1000, 10000)', MAT_THEORY)
        run.insert('p(2000, 20000)', MAT_THEORY)
        run.insert('r(10, 100)', MAT_THEORY)
        run.insert('r(20, 200)', MAT_THEORY)
        run.insert('s(100, 1000)', MAT_THEORY)
        run.insert('s(200, 2000)', MAT_THEORY)
        run.insert('t(1000, 10000)', MAT_THEORY)
        run.insert('t(2000, 20000)', MAT_THEORY)
        code = ("p(1,10) p(1,20) p(10, 100) p(20, 200) p(100, 1000) "
                "p(200, 2000) p(1000, 10000) p(2000, 20000) "
                "r(10,100) r(20,200) s(100,1000) s(200,2000) "
                "t(1000, 10000) t(2000,20000) "
                "q(1,10000) q(1,20000)")
        self.check_class(run, code, "Insert: larger join")
        run.delete('t(1000, 10000)', MAT_THEORY)
        code = ("p(1,10) p(1,20) p(10, 100) p(20, 200) p(100, 1000)  "
                "p(200, 2000) p(1000, 10000) p(2000, 20000) r(10,100) "
                "r(20,200) s(100,1000) s(200,2000) t(2000,20000) "
                "q(1,20000)")
        self.check_class(run, code, "Delete: larger join")

    def test_self_join(self):
        code = ("q(x,y) :- p(x,z), p(z,y)")
        run = self.prep_runtime(code)
        run.insert('p(1,2)', MAT_THEORY)
        run.insert('p(1,3)', MAT_THEORY)
        run.insert('p(2, 4)', MAT_THEORY)
        run.insert('p(2, 5)', MAT_THEORY)
        self.check_class(
            run, 'p(1,2) p(1,3) p(2,4) p(2,5) q(1,4) q(1,5)',
            "Insert: self-join", tablenames=['p', 'q'])
        run.delete('p(2, 4)', MAT_THEORY)
        self.check_class(run, 'p(1,2) p(1,3) p(2,5) q(1,5)', '',
                         tablenames=['p', 'q'])

        code = ("q(x,z) :- p(x,y), p(y,z)")
        run = self.prep_runtime(code)
        run.insert('p(1, 1)', MAT_THEORY)
        self.check_class(
            run, 'p(1,1) q(1,1)', "Insert: self-join on same data",
            tablenames=['p', 'q'])

        code = ("q(x,w) :- p(x,y), p(y,z), p(z,w)")
        run = self.prep_runtime(code)
        run.insert('p(1, 1)', MAT_THEORY)
        run.insert('p(1, 2)', MAT_THEORY)
        run.insert('p(2, 2)', MAT_THEORY)
        run.insert('p(2, 3)', MAT_THEORY)
        run.insert('p(2, 4)', MAT_THEORY)
        run.insert('p(2, 5)', MAT_THEORY)
        run.insert('p(3, 3)', MAT_THEORY)
        run.insert('p(3, 4)', MAT_THEORY)
        run.insert('p(3, 5)', MAT_THEORY)
        run.insert('p(3, 6)', MAT_THEORY)
        run.insert('p(3, 7)', MAT_THEORY)
        code = ('p(1,1) p(1,2) p(2,2) p(2,3) p(2,4) p(2,5)'
                'p(3,3) p(3,4) p(3,5) p(3,6) p(3,7)'
                'q(1,1) q(1,2) q(2,2) q(2,3) q(2,4) q(2,5)'
                'q(3,3) q(3,4) q(3,5) q(3,6) q(3,7)'
                'q(1,3) q(1,4) q(1,5) q(1,6) q(1,7)'
                'q(2,6) q(2,7)')
        self.check_class(run, code, "Insert: larger self join",
                         tablenames=['p', 'q'])
        run.delete('p(1, 1)', MAT_THEORY)
        run.delete('p(2, 2)', MAT_THEORY)
        code = ('       p(1,2)        p(2,3) p(2,4) p(2,5)'
                'p(3,3) p(3,4) p(3,5) p(3,6) p(3,7)'
                '                     q(2,3) q(2,4) q(2,5)'
                'q(3,3) q(3,4) q(3,5) q(3,6) q(3,7)'
                'q(1,3) q(1,4) q(1,5) q(1,6) q(1,7)'
                'q(2,6) q(2,7)')
        self.check_class(run, code, "Delete: larger self join",
                         tablenames=['p', 'q'])

    def test_insert_order(self):
        """Test insert.

        Test that the order in which we change rules
        and data is irrelevant.
        """
        # was actual bug: insert data first, then
        #   insert rule with self-join
        code = ('q(1)'
                'p(x) :- q(x)')
        run = self.prep_runtime(code)
        self.check_class(run, 'p(1) q(1)', "Basic insert order")

        code = ('s(1)'
                'q(1,1)'
                'p(x,y) :- q(x,y), not r(x,y)'
                'r(x,y) :- s(x), s(y)')
        run = self.prep_runtime(code)
        self.check_class(run, 's(1) q(1,1) r(1,1)', "Self-join Insert order",
                         tablenames=['s', 'q', 'r'])

        code = ('q(1)'
                'p(x) :- q(x) '
                'r(x) :- p(x) ')
        run = self.prep_runtime(code)
        self.check_class(run, 'q(1) p(1) r(1)', "Multiple rule insert")
        run.delete('p(x) :- q(x)', MAT_THEORY)
        self.check_class(run, 'q(1)', "Deletion of rule")

    def test_value_types(self):
        """Test the different value types."""
        # string
        code = ("q(x) :- p(x), r(x)")
        run = self.prep_runtime(
            code, "**** Materialized Theory: String data type ****")

        run.insert('r("apple")', MAT_THEORY)
        self.check_class(run, 'r("apple")',
                         "String insert with no propagations")
        run.insert('r("apple")', MAT_THEORY)
        self.check_class(run, 'r("apple")',
                         "Duplicate string insert with no propagations")

        run.delete('r("apple")', MAT_THEORY)
        self.check_class(run, "", "Delete with no propagations")
        run.delete('r("apple")', MAT_THEORY)
        self.check_class(run, "", "Delete from empty table")

        run.insert('r("apple")', MAT_THEORY)
        run.insert('p("apple")', MAT_THEORY)
        self.check_class(run, 'r("apple") p("apple") q("apple")',
                         "String insert with 1 propagation")

        run.delete('r("apple")', MAT_THEORY)
        self.check_class(run, 'p("apple")', "String delete with 1 propagation")

        # float
        code = ("q(x) :- p(x), r(x)")
        run = self.prep_runtime(
            code, "**** Materialized Theory: Float data type ****")

        run.insert('r(1.2)', MAT_THEORY)
        self.check_class(run, 'r(1.2)', "String insert with no propagations")
        run.insert('r(1.2)', MAT_THEORY)
        self.check_class(run, 'r(1.2)',
                         "Duplicate string insert with no propagations")

        run.delete('r(1.2)', MAT_THEORY)
        self.check_class(run, "", "Delete with no propagations")
        run.delete('r(1.2)', MAT_THEORY)
        self.check_class(run, "", "Delete from empty table")

        run.insert('r(1.2)', MAT_THEORY)
        run.insert('p(1.2)', MAT_THEORY)
        self.check_class(run, 'r(1.2) p(1.2) q(1.2)',
                         "String self.insert with 1 propagation")

        run.delete('r(1.2)', MAT_THEORY)
        self.check_class(run, 'p(1.2)', "String delete with 1 propagation")

    def test_negation(self):
        """Test Materialized Theory negation."""
        # Unary, single join
        code = ("q(x) :- p(x), not r(x)")
        run = self.prep_runtime(code,
                                "**** Materialized Theory: Negation ****")

        run.insert('p(2)', MAT_THEORY)
        self.check_class(run, 'p(2) q(2)',
                         "Insert into positive literal with propagation")
        run.delete('p(2)', MAT_THEORY)
        self.check_class(run, '',
                         "Delete from positive literal with propagation")

        run.insert('r(2)', MAT_THEORY)
        self.check_class(run, 'r(2)',
                         "Insert into negative literal without propagation")
        run.delete('r(2)', MAT_THEORY)
        self.check_class(run, '',
                         "Delete from negative literal without propagation")

        run.insert('p(2)', MAT_THEORY)
        run.insert('r(2)', MAT_THEORY)
        self.check_class(run, 'p(2) r(2)',
                         "Insert into negative literal with propagation")

        run.delete('r(2)', MAT_THEORY)
        self.check_class(run, 'q(2) p(2)',
                         "Delete from negative literal with propagation")

        # Unary, multiple joins
        code = ("s(x) :- p(x), not r(x), q(y), not t(y)")
        run = self.prep_runtime(code, "Unary, multiple join")
        run.insert('p(1)', MAT_THEORY)
        run.insert('q(2)', MAT_THEORY)
        self.check_class(run, 'p(1) q(2) s(1)',
                         'Insert with two negative literals')

        run.insert('r(3)', MAT_THEORY)
        self.check_class(run, 'p(1) q(2) s(1) r(3)',
                         'Ineffectual insert with 2 negative literals')
        run.insert('r(1)', MAT_THEORY)
        self.check_class(
            run, 'p(1) q(2) r(3) r(1)',
            'Insert into existentially quantified negative literal '
            'with propagation. ')
        run.insert('t(2)', MAT_THEORY)
        self.check_class(
            run, 'p(1) q(2) r(3) r(1) t(2)',
            'Insert into negative literal producing extra blocker for proof.')
        run.delete('t(2)', MAT_THEORY)
        self.check_class(run, 'p(1) q(2) r(3) r(1)',
                         'Delete first blocker from proof')
        run.delete('r(1)', MAT_THEORY)
        self.check_class(run, 'p(1) q(2) r(3) s(1)',
                         'Delete second blocker from proof')

        # Non-unary
        code = ("p(x, v) :- q(x,z), r(z, w), not s(x, w), u(w,v)")
        run = self.prep_runtime(code, "Non-unary")
        run.insert('q(1, 2)', MAT_THEORY)
        run.insert('r(2, 3)', MAT_THEORY)
        run.insert('r(2, 4)', MAT_THEORY)
        run.insert('u(3, 5)', MAT_THEORY)
        run.insert('u(4, 6)', MAT_THEORY)
        self.check_class(
            run, 'q(1,2) r(2,3) r(2,4) u(3,5) u(4,6) p(1,5) p(1,6)',
            'Insert with non-unary negative literal')

        run.insert('s(1, 3)', MAT_THEORY)
        self.check_class(
            run, 'q(1,2) r(2,3) r(2,4) u(3,5) u(4,6) s(1,3) p(1,6)',
            'Insert into non-unary negative with propagation')

        run.insert('s(1, 4)', MAT_THEORY)
        self.check_class(
            run, 'q(1,2) r(2,3) r(2,4) u(3,5) u(4,6) s(1,3) s(1,4)',
            'Insert into non-unary with different propagation')

    def test_select(self):
        """Materialized Theory: test the SELECT event handler."""
        code = ("p(x, y) :- q(x), r(y)")
        run = self.prep_runtime(code, "**** Materialized Theory: Select ****")
        run.insert('q(1)', MAT_THEORY)
        # self.assertEqual('q(1)', run.select('q(x)'))
        run.insert('q(2)', MAT_THEORY)
        run.insert('r(1)', MAT_THEORY)
        run.insert('r(2)', MAT_THEORY)
        self.check_class(
            run, 'q(1) q(2) r(1) r(2) p(1,1) p(1,2) p(2,1) p(2,2)',
            'Prepare for select')
        self.check_equal(
            run.select('p(x,y)', MAT_THEORY),
            'p(1,1) p(1,2) p(2,1) p(2,2)',
            'Select: bound no args')
        self.check_equal(
            run.select('p(1,y)', MAT_THEORY),
            'p(1,1) p(1,2)',
            'Select: bound 1st arg')
        self.check_equal(
            run.select('p(x,2)', MAT_THEORY),
            'p(1,2) p(2,2)',
            'Select: bound 2nd arg')
        self.check_equal(
            run.select('p(1,2)', MAT_THEORY),
            'p(1,2)',
            'Select: bound 1st and 2nd arg')
        self.check_equal(
            run.select('query :- q(x), r(y)', MAT_THEORY),
            'query :- q(1), r(1)'
            'query :- q(1), r(2)'
            'query :- q(2), r(1)'
            'query :- q(2), r(2)',
            'Select: conjunctive query')

    def test_modify_rules(self):
        """Test rules modification.

        Test the functionality for adding and deleting
        rules *after* data has already been entered.
        """
        run = self.prep_runtime("", "Rule modification")
        run.insert("q(1) r(1) q(2) r(2)", MAT_THEORY)
        self.showdb(run)
        self.check_class(run, 'q(1) r(1) q(2) r(2)', "Installation")
        run.insert("p(x) :- q(x), r(x)", MAT_THEORY)
        self.check_class(
            run,
            'q(1) r(1) q(2) r(2) p(1) p(2)', 'Rule insert after data insert')
        run.delete("q(1)", MAT_THEORY)
        self.check_class(
            run,
            'r(1) q(2) r(2) p(2)', 'Delete after Rule insert with propagation')
        run.insert("q(1)", MAT_THEORY)
        run.delete("p(x) :- q(x), r(x)", MAT_THEORY)
        self.check_class(run, 'q(1) r(1) q(2) r(2)', "Delete rule")

    def test_recursion(self):
        """Materialized Theory: test recursion."""
        self.skipTest('Recursion not currently allowed')
        # TODO(thinrichs): weaken cross-policy recursion restriction
        #   so that we can include recursion within a single theory.
        run = self.prep_runtime('q(x,y) :- p(x,y)'
                                'q(x,y) :- p(x,z), q(z,y)')
        run.insert('p(1,2)', MAT_THEORY)
        run.insert('p(2,3)', MAT_THEORY)
        run.insert('p(3,4)', MAT_THEORY)
        run.insert('p(4,5)', MAT_THEORY)
        self.check_class(
            run, 'p(1,2) p(2,3) p(3,4) p(4,5)'
            'q(1,2) q(2,3) q(1,3) q(3,4) q(2,4) q(1,4) q(4,5) q(3,5) '
            'q(1,5) q(2,5)', 'Insert into recursive rules')
        run.delete('p(1,2)', MAT_THEORY)
        self.check_class(
            run, 'p(2,3) p(3,4) p(4,5)'
            'q(2,3) q(3,4) q(2,4) q(4,5) q(3,5) q(2,5)',
            'Delete from recursive rules')
