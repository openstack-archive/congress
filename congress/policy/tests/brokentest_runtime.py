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

import os
import unittest

from congress.openstack.common import log as logging
from congress.policy import compile
from congress.policy import runtime
from congress.policy import unify

LOG = logging.getLogger(__name__)

NREC_THEORY = 'non-recursive theory'
DB_THEORY = 'database'
MAT_THEORY = 'materialized'


# This file contains tests that are likely broken.  But the tests
#   are good ones once we get the underlying data structures fixed.
# TODO(thinrichs): fix tests so they are working again.

class TestRuntime(unittest.TestCase):

    def setUp(self):
        pass

    def prep_runtime(self, code=None, msg=None, target=None):
        # compile source
        if msg is not None:
            LOG.debug(msg)
        if code is None:
            code = ""
        if target is None:
            target = MAT_THEORY
        run = runtime.Runtime()
        run.theory[NREC_THEORY] = runtime.NonrecursiveRuleTheory()
        run.theory[DB_THEORY] = runtime.Database()
        run.theory[MAT_THEORY] = runtime.MaterializedViewTheory()
        run.debug_mode()
        run.insert(code, target=target)
        return run

    def check_class(self, run, correct_database_code, msg=None):
        """Check that runtime RUN's MAT_THEORY theory
        has exactly the same contents as CORRECT_DATABASE_CODE.
        """
        self.open(msg)
        db_class = run.theory[MAT_THEORY].database
        # self.showdb(run)
        correct = runtime.string_to_database(correct_database_code)
        self.check_db_diffs(db_class, correct, msg)
        self.close(msg)

    def check_db(self, run, correct_database_code, msg=None):
        """Check that runtime RUN.theory[DB_THEORY] is
        equal to CORRECT_DATABASE_CODE.
        """
        # extract correct answer from correct_database_code
        self.open(msg)
        correct_database = runtime.string_to_database(correct_database_code)
        self.check_db_diffs(run.theory[DB_THEORY],
                            correct_database, msg)
        self.close(msg)

    def check_db_diffs(self, actual, correct, msg):
        extra = actual - correct
        missing = correct - actual
        extra = [e for e in extra if not e[0].startswith("___")]
        missing = [m for m in missing if not m[0].startswith("___")]
        self.output_diffs(extra, missing, msg, actual=actual)

    def output_diffs(self, extra, missing, msg, actual=None):
        if len(extra) > 0:
            LOG.debug("Extra tuples")
            LOG.debug(", ".join([str(x) for x in extra]))
        if len(missing) > 0:
            LOG.debug("Missing tuples")
            LOG.debug(", ".join([str(x) for x in missing]))
        if len(extra) > 0 or len(missing) > 0:
            LOG.debug("Resulting database: {}".format(str(actual)))
        self.assertTrue(len(extra) == 0 and len(missing) == 0, msg)

    def check_equal(self, actual_code, correct_code, msg=None, equal=None):
        def minus(iter1, iter2, invert=False):
            extra = []
            for i1 in iter1:
                found = False
                for i2 in iter2:
                    # for asymmetric equality checks
                    if invert:
                        test_result = equal(i2, i1)
                    else:
                        test_result = equal(i1, i2)
                    if test_result:
                        found = True
                        break
                if not found:
                    extra.append(i1)
            return extra
        if equal is None:
            equal = lambda x, y: x == y
        LOG.debug("** Checking equality: {} **".format(msg))
        actual = compile.parse(actual_code)
        correct = compile.parse(correct_code)
        extra = minus(actual, correct)
        # in case EQUAL is asymmetric, always supply actual as the first arg
        missing = minus(correct, actual, invert=True)
        self.output_diffs(extra, missing, msg)
        LOG.debug("** Finished equality: {} **".format(msg))

    def check_same(self, actual_code, correct_code, msg=None):
        """Checks if ACTUAL_CODE is a variable-renaming of CORRECT_CODE."""
        return self.check_equal(
            actual_code, correct_code, msg=msg,
            equal=lambda x, y: unify.same(x, y) is not None)

    def check_instance(self, actual_code, correct_code, msg=None):
        """Checks if ACTUAL_CODE is an instance of CORRECT_CODE."""
        return self.check_equal(
            actual_code, correct_code, msg=msg,
            equal=lambda x, y: unify.instance(x, y) is not None)

    def check_proofs(self, run, correct, msg=None):
        """Check that the proofs stored in runtime RUN are exactly
        those in CORRECT.
        """
        # example
        # check_proofs(run, {'q': {(1,):
        #              Database.ProofCollection([{'x': 1, 'y': 2}])}})

        errs = []
        checked_tables = set()
        for table in run.database.table_names():
            if table in correct:
                checked_tables.add(table)
                for dbtuple in run.database[table]:
                    if dbtuple.tuple in correct[table]:
                        if dbtuple.proofs != correct[table][dbtuple.tuple]:
                            errs.append(
                                "For table {} tuple {}\n  Computed: {}\n  "
                                "Correct: {}".format(
                                    table, str(dbtuple),
                                    str(dbtuple.proofs),
                                    str(correct[table][dbtuple.tuple])))
        for table in set(correct.keys()) - checked_tables:
            errs.append("Table {} had a correct answer but did not exist "
                        "in the database".format(table))
        if len(errs) > 0:
            # LOG.debug("Check_proof errors:\n{}".format("\n".join(errs)))
            self.fail("\n".join(errs))

    def showdb(self, run):
        LOG.debug("Resulting DB: {}".format(
            str(run.theory[run.CLASSIFY_THEORY].database |
                run.theory[run.DATABASE] |
                run.theory[run.ENFORCEMENT_THEORY].database)))

    def insert(self, run, alist, target=None):
        if target is None:
            target = MAT_THEORY
        run.insert(tuple(alist))

    def delete(self, run, alist):
        run.delete(tuple(alist))

    def test_database(self):
        """Test Database with insert/delete."""
        run = self.prep_runtime('', "**** Database tests ****")

        self.check_db(run, "", "Empty database on init")

        # set semantics, not bag semantics
        self.insert(run, ['r', 1], DB_THEORY)
        self.check_db(run, "r(1)", "Basic insert with no propagations")
        self.insert(run, ['r', 1], DB_THEORY)
        self.check_db(run, "r(1)", "Duplicate insert with no propagations")

        self.delete(run, ['r', 1], DB_THEORY)
        self.check_db(run, "", "Delete with no propagations")
        self.delete(run, ['r', 1], DB_THEORY)
        self.check_db(run, "", "Delete from empty table")

    def test_error_checking(self):
        """Test error-checking on insertion of rules."""
        code = ("p(x) :- q(x)")
        run = self.prep_runtime(code)
        result = run.get_target(MAT_THEORY).policy()
        self.assertTrue(len(result) == 1)
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

        # recursion into classification theory
        code = ("p(x) :- p(x)")
        run = self.prep_runtime("", "** Classification Recursion **")
        permitted, changes = run.insert(code, MAT_THEORY)
        self.assertTrue(permitted)

        # stratification into classification theory
        code = ("p(x) :- q(x), not p(x)")
        run = self.prep_runtime("", "** Classification Stratification **")
        permitted, changes = run.insert(code, MAT_THEORY)
        self.assertFalse(permitted)

    def test_materialized_theory(self):
        """Materialized Theory: test rule propagation."""
        code = ("q(x) :- p(x), r(x)")
        run = self.prep_runtime(
            code, "**** Materialized Theory: Basic propagation tests ****")
        self.insert(run, ['r', 1])
        self.insert(run, ['p', 1])
        self.check_class(run, "r(1) p(1) q(1)",
                         "Insert into base table with 1 propagation")

        self.delete(run, ['r', 1])
        self.check_class(run, "p(1)",
                         "Delete from base table with 1 propagation")

        # multiple rules
        code = ("q(x) :- p(x), r(x)"
                "q(x) :- s(x)")
        self.insert(run, ['p', 1])
        self.insert(run, ['r', 1])
        self.check_class(run, "p(1) r(1) q(1)", "Insert: multiple rules")
        self.insert(run, ['s', 1])
        self.check_class(run, "p(1) r(1) s(1) q(1)",
                         "Insert: duplicate conclusions")

        # body of length 1
        code = ("q(x) :- p(x)")
        run = self.prep_runtime(
            code, "**** Materialized Theory: Body length 1 tests ****")

        self.insert(run, ['p', 1])
        self.check_class(run, "p(1) q(1)", "Insert with body of size 1")
        self.showdb(run)
        self.delete(run, ['p', 1])
        self.showdb(run)
        self.check_class(run, "", "Delete with body of size 1")

        # existential variables
        code = ("q(x) :- p(x), r(y)")
        run = self.prep_runtime(
            code,
            "**** Materialized Theory: Unary tables with existential ****")
        self.insert(run, ['p', 1])
        self.insert(run, ['r', 2])
        self.insert(run, ['r', 3])
        self.showdb(run)
        self.check_class(run, "p(1) r(2) r(3) q(1)",
                         "Insert with unary table and existential")
        self.delete(run, ['r', 2])
        self.showdb(run)
        self.check_class(run, "p(1) r(3) q(1)",
                         "Delete 1 with unary table and existential")
        self.delete(run, ['r', 3])
        self.check_class(run, "p(1)",
                         "Delete all with unary table and existential")

        # non-monadic
        run = self.prep_runtime(
            "q(x) :- p(x,y)",
            "**** Materialized Theory: Multiple-arity table tests ****")

        self.insert(run, ['p', 1, 2])
        self.check_class(run, "p(1, 2) q(1)",
                         "Insert: existential variable in body of size 1")
        self.delete(run, ['p', 1, 2])
        self.check_class(run, "",
                         "Delete: existential variable in body of size 1")

        code = ("q(x) :- p(x,y), r(y,x)")
        run = self.prep_runtime(code)
        self.insert(run, ['p', 1, 2])
        self.insert(run, ['r', 2, 1])
        self.check_class(run, "p(1, 2) r(2, 1) q(1)",
                         "Insert: join in body of size 2")
        self.delete(run, ['p', 1, 2])
        self.check_class(run, "r(2, 1)",
                         "Delete: join in body of size 2")
        self.insert(run, ['p', 1, 2])
        self.insert(run, ['p', 1, 3])
        self.insert(run, ['r', 3, 1])
        self.check_class(
            run, "r(2, 1) r(3,1) p(1, 2) p(1, 3) q(1)",
            "Insert: multiple existential bindings for same head")

        self.delete(run, ['p', 1, 2])
        self.check_class(
            run, "r(2, 1) r(3,1) p(1, 3) q(1)",
            "Delete: multiple existential bindings for same head")

        code = ("q(x,v) :- p(x,y), r(y,z), s(z,w), t(w,v)")
        run = self.prep_runtime(code)
        self.insert(run, ['p', 1, 10])
        self.insert(run, ['p', 1, 20])
        self.insert(run, ['r', 10, 100])
        self.insert(run, ['r', 20, 200])
        self.insert(run, ['s', 100, 1000])
        self.insert(run, ['s', 200, 2000])
        self.insert(run, ['t', 1000, 10000])
        self.insert(run, ['t', 2000, 20000])
        code = ("p(1,10) p(1,20) r(10,100) r(20,200) s(100,1000) s(200,2000)"
                "t(1000, 10000) t(2000,20000) "
                "q(1,10000) q(1,20000)")
        self.check_class(run, code, "Insert: larger join")
        self.delete(run, ['t', 1000, 10000])
        code = ("p(1,10) p(1,20) r(10,100) r(20,200) s(100,1000) s(200,2000)"
                "t(2000,20000) "
                "q(1,20000)")
        self.check_class(run, code, "Delete: larger join")

        code = ("q(x,y) :- p(x,z), p(z,y)")
        run = self.prep_runtime(code)
        self.insert(run, ['p', 1, 2])
        self.insert(run, ['p', 1, 3])
        self.insert(run, ['p', 2, 4])
        self.insert(run, ['p', 2, 5])
        self.check_class(
            run, 'p(1,2) p(1,3) p(2,4) p(2,5) q(1,4) q(1,5)',
            "Insert: self-join")
        self.delete(run, ['p', 2, 4])
        self.check_class(run, 'p(1,2) p(1,3) p(2,5) q(1,5)')

        code = ("q(x,z) :- p(x,y), p(y,z)")
        run = self.prep_runtime(code)
        self.insert(run, ['p', 1, 1])
        self.check_class(run,
                         'p(1,1) q(1,1)', "Insert: self-join on same data")

        code = ("q(x,w) :- p(x,y), p(y,z), p(z,w)")
        run = self.prep_runtime(code)
        self.insert(run, ['p', 1, 1])
        self.insert(run, ['p', 1, 2])
        self.insert(run, ['p', 2, 2])
        self.insert(run, ['p', 2, 3])
        self.insert(run, ['p', 2, 4])
        self.insert(run, ['p', 2, 5])
        self.insert(run, ['p', 3, 3])
        self.insert(run, ['p', 3, 4])
        self.insert(run, ['p', 3, 5])
        self.insert(run, ['p', 3, 6])
        self.insert(run, ['p', 3, 7])
        code = ('p(1,1) p(1,2) p(2,2) p(2,3) p(2,4) p(2,5)'
                'p(3,3) p(3,4) p(3,5) p(3,6) p(3,7)'
                'q(1,1) q(1,2) q(2,2) q(2,3) q(2,4) q(2,5)'
                'q(3,3) q(3,4) q(3,5) q(3,6) q(3,7)'
                'q(1,3) q(1,4) q(1,5) q(1,6) q(1,7)'
                'q(2,6) q(2,7)')
        self.check_class(run, code, "Insert: larger self join")
        self.delete(run, ['p', 1, 1])
        self.delete(run, ['p', 2, 2])
        code = ('       p(1,2)        p(2,3) p(2,4) p(2,5)'
                'p(3,3) p(3,4) p(3,5) p(3,6) p(3,7)'
                '                     q(2,3) q(2,4) q(2,5)'
                'q(3,3) q(3,4) q(3,5) q(3,6) q(3,7)'
                'q(1,3) q(1,4) q(1,5) q(1,6) q(1,7)'
                'q(2,6) q(2,7)')
        self.check_class(run, code, "Delete: larger self join")

        # was actual bug: insert data first, then
        #   insert rule with self-join
        code = ('s(1)'
                'q(1,1)'
                'p(x,y) :- q(x,y), not r(x,y)'
                'r(x,y) :- s(x), s(y)')
        run = self.prep_runtime(code)
        self.check_class(run, 's(1) q(1,1) r(1,1)')

    def test_materialized_value_types(self):
        """Test the different value types."""
        # string
        code = ("q(x) :- p(x), r(x)")
        run = self.prep_runtime(
            code, "**** Materialized Theory: String data type ****")

        self.insert(run, ['r', 'apple'])
        self.check_class(run, 'r("apple")',
                         "String insert with no propagations")
        self.insert(run, ['r', 'apple'])
        self.check_class(run, 'r("apple")',
                         "Duplicate string insert with no propagations")

        self.delete(run, ['r', 'apple'])
        self.check_class(run, "", "Delete with no propagations")
        self.delete(run, ['r', 'apple'])
        self.check_class(run, "", "Delete from empty table")

        self.insert(run, ['r', 'apple'])
        self.insert(run, ['p', 'apple'])
        self.check_class(run, 'r("apple") p("apple") q("apple")',
                         "String insert with 1 propagation")

        self.delete(run, ['r', 'apple'])
        self.check_class(run, 'p("apple")', "String delete with 1 propagation")

        # float
        code = ("q(x) :- p(x), r(x)")
        run = self.prep_runtime(
            code, "**** Materialized Theory: Float data type ****")

        self.insert(run, ['r', 1.2])
        self.check_class(run, 'r(1.2)', "String insert with no propagations")
        self.insert(run, ['r', 1.2])
        self.check_class(run, 'r(1.2)',
                         "Duplicate string insert with no propagations")

        self.delete(run, ['r', 1.2])
        self.check_class(run, "", "Delete with no propagations")
        self.delete(run, ['r', 1.2])
        self.check_class(run, "", "Delete from empty table")

        self.insert(run, ['r', 1.2])
        self.insert(run, ['p', 1.2])
        self.check_class(run, 'r(1.2) p(1.2) q(1.2)',
                         "String self.insert with 1 propagation")

        self.delete(run, ['r', 1.2])
        self.check_class(run, 'p(1.2)', "String delete with 1 propagation")

    # def test_proofs(self):
    #     """Test if the proof computation is performed correctly. """
    #     def check_table_proofs(run, table, tuple_proof_dict, msg):
    #         for tuple in tuple_proof_dict:
    #             tuple_proof_dict[tuple] = \
    #                 Database.ProofCollection(tuple_proof_dict[tuple])
    #         self.check_proofs(run, {table : tuple_proof_dict}, msg)

    #     code = ("q(x) :- p(x,y)")
    #     run = self.prep_runtime(code, "**** Proof tests ****")

    #     self.insert(run, ['p', 1, 2])
    #     check_table_proofs(run, 'q', {(1,): [{u'x': 1, u'y': 2}]},
    #         'Simplest proof test')

    def test_materialized_negation(self):
        """Test Materialized Theory negation."""
        # Unary, single join
        code = ("q(x) :- p(x), not r(x)")
        run = self.prep_runtime(code,
                                "**** Materialized Theory: Negation ****")

        self.insert(run, ['p', 2])
        self.check_class(run, 'p(2) q(2)',
                         "Insert into positive literal with propagation")
        self.delete(run, ['p', 2])
        self.check_class(run, '',
                         "Delete from positive literal with propagation")

        self.insert(run, ['r', 2])
        self.check_class(run, 'r(2)',
                         "Insert into negative literal without propagation")
        self.delete(run, ['r', 2])
        self.check_class(run, '',
                         "Delete from negative literal without propagation")

        self.insert(run, ['p', 2])
        self.insert(run, ['r', 2])
        self.check_class(run, 'p(2) r(2)',
                         "Insert into negative literal with propagation")

        self.delete(run, ['r', 2])
        self.check_class(run, 'q(2) p(2)',
                         "Delete from negative literal with propagation")

        # Unary, multiple joins
        code = ("s(x) :- p(x), not r(x), q(y), not t(y)")
        run = self.prep_runtime(code, "Unary, multiple join")
        self.insert(run, ['p', 1])
        self.insert(run, ['q', 2])
        self.check_class(run, 'p(1) q(2) s(1)',
                         'Insert with two negative literals')

        self.insert(run, ['r', 3])
        self.check_class(run, 'p(1) q(2) s(1) r(3)',
                         'Ineffectual insert with 2 negative literals')
        self.insert(run, ['r', 1])
        self.check_class(
            run, 'p(1) q(2) r(3) r(1)',
            'Insert into existentially quantified negative literal '
            'with propagation. ')
        self.insert(run, ['t', 2])
        self.check_class(
            run, 'p(1) q(2) r(3) r(1) t(2)',
            'Insert into negative literal producing extra blocker for proof.')
        self.delete(run, ['t', 2])
        self.check_class(run, 'p(1) q(2) r(3) r(1)',
                         'Delete first blocker from proof')
        self.delete(run, ['r', 1])
        self.check_class(run, 'p(1) q(2) r(3) s(1)',
                         'Delete second blocker from proof')

        # Non-unary
        code = ("p(x, v) :- q(x,z), r(z, w), not s(x, w), u(w,v)")
        run = self.prep_runtime(code, "Non-unary")
        self.insert(run, ['q', 1, 2])
        self.insert(run, ['r', 2, 3])
        self.insert(run, ['r', 2, 4])
        self.insert(run, ['u', 3, 5])
        self.insert(run, ['u', 4, 6])
        self.check_class(
            run, 'q(1,2) r(2,3) r(2,4) u(3,5) u(4,6) p(1,5) p(1,6)',
            'Insert with non-unary negative literal')

        self.insert(run, ['s', 1, 3])
        self.check_class(
            run, 'q(1,2) r(2,3) r(2,4) u(3,5) u(4,6) s(1,3) p(1,6)',
            'Insert into non-unary negative with propagation')

        self.insert(run, ['s', 1, 4])
        self.check_class(
            run, 'q(1,2) r(2,3) r(2,4) u(3,5) u(4,6) s(1,3) s(1,4)',
            'Insert into non-unary with different propagation')

        # Negation ordering
        code = ("p(x) :- not q(x), r(x)")
        run = self.prep_runtime(code, "Negation ordering")
        self.insert(run, ['r', 1])
        self.insert(run, ['r', 2])
        self.insert(run, ['q', 1])
        self.check_class(
            run, 'r(1) r(2) q(1) p(2)',
            'Reordering negation')

    def test_materialized_select(self):
        """Materialized Theory: test the SELECT event handler."""
        code = ("p(x, y) :- q(x), r(y)")
        run = self.prep_runtime(code, "**** Materialized Theory: Select ****")
        self.insert(run, ['q', 1])
        # self.assertEqual('q(1)', run.select('q(x)'))
        self.insert(run, ['q', 2])
        self.insert(run, ['r', 1])
        self.insert(run, ['r', 2])
        self.check_class(
            run, 'q(1) q(2) r(1) r(2) p(1,1) p(1,2) p(2,1) p(2,2)',
            'Prepare for select')
        self.check_equal(
            run.select('p(x,y)'), 'p(1,1) p(1,2) p(2,1) p(2,2)',
            'Select: bound no args')
        self.check_equal(
            run.select('p(1,y)'), 'p(1,1) p(1,2)',
            'Select: bound 1st arg')
        self.check_equal(
            run.select('p(x,2)'), 'p(1,2) p(2,2)',
            'Select: bound 2nd arg')
        self.check_equal(
            run.select('p(1,2)'), 'p(1,2)',
            'Select: bound 1st and 2nd arg')
        self.check_equal(
            run.select('query :- q(x), r(y)'),
            'query :- q(1), r(1)'
            'query :- q(1), r(2)'
            'query :- q(2), r(1)'
            'query :- q(2), r(2)')

    def test_materialized_modify_rules(self):
        """Materialized Theory: Test the functionality for adding and deleting
        rules *after* data has already been entered.
        """
        run = self.prep_runtime("", "Rule modification")
        run.insert("q(1) r(1) q(2) r(2)")
        self.showdb(run)
        self.check_class(run, 'q(1) r(1) q(2) r(2)', "Installation")
        run.insert("p(x) :- q(x), r(x)")
        self.check_class(
            run,
            'q(1) r(1) q(2) r(2) p(1) p(2)', 'Rule insert after data insert')
        run.delete("q(1)")
        self.check_class(
            run,
            'r(1) q(2) r(2) p(2)', 'Delete after Rule insert with propagation')
        run.insert("q(1)")
        run.delete("p(x) :- q(x), r(x)")
        self.check_class(run, 'q(1) r(1) q(2) r(2)', "Delete rule")

    def test_materialized_recursion(self):
        """Materialized Theory: test recursion."""
        run = self.prep_runtime('q(x,y) :- p(x,y)'
                                'q(x,y) :- p(x,z), q(z,y)')
        run.insert('p(1,2)')
        run.insert('p(2,3)')
        run.insert('p(3,4)')
        run.insert('p(4,5)')
        self.check_class(
            run, 'p(1,2) p(2,3) p(3,4) p(4,5)'
            'q(1,2) q(2,3) q(1,3) q(3,4) q(2,4) q(1,4) q(4,5) q(3,5) '
            'q(1,5) q(2,5)', 'Insert into recursive rules')
        run.delete('p(1,2)')
        self.check_class(
            run, 'p(2,3) p(3,4) p(4,5)'
            'q(2,3) q(3,4) q(2,4) q(4,5) q(3,5) q(2,5)',
            'Delete from recursive rules')

    def open(self, msg):
        LOG.debug("** Started: {} **".format(msg))

    def close(self, msg):
        LOG.debug("** Finished: {} **".format(msg))

     # TODO(tim): add tests for explanations
    def test_materialized_explain(self):
        """Test the explanation event handler."""
        run = self.prep_runtime("p(x) :- q(x), r(x)", "Explanations")
        run.insert("q(1) r(1)")
        self.showdb(run)
        LOG.debug(run.explain("p(1)"))

        run = self.prep_runtime(
            "p(x) :- q(x), r(x) q(x) :- s(x), t(x)", "Explanations")
        run.insert("s(1) r(1) t(1)")
        self.showdb(run)
        LOG.debug(run.explain("p(1)"))
        # self.fail()

    def test_remediation(self):
        """Test remediation computation."""
        def check(action_code, classify_code, query, correct, msg):
            run = self.prep_runtime()
            actth = run.ACTION_THEORY
            clsth = run.CLASSIFY_THEORY
            run.insert(action_code, target=actth)
            run.insert(class_code, target=clsth)
            self.showdb(run)
            self.check_equal(run.remediate(query), correct, msg)

        # simple
        action_code = ('action("a")'
                       'p-(x) :- a(x)')
        class_code = ('err(x) :- p(x)'
                      'p(1)')
        check(action_code, class_code, 'err(1)', 'p-(1) :- a(1)', 'Monadic')

        # rules in action theory
        action_code = ('action("a")'
                       'p-(x) :- q(x)'
                       'q(x) :- a(x)')
        class_code = ('err(x) :- p(x)'
                      'p(1)')
        check(action_code, class_code, 'err(1)', 'p-(1) :- a(1)',
              'Monadic, indirect')

        # multiple conditions in error
        action_code = ('action("a")'
                       'action("b")'
                       'p-(x) :- a(x)'
                       'q-(x) :- b(x)')
        class_code = ('err(x) :- p(x), q(x)'
                      'p(1)'
                      'q(1)')
        check(action_code, class_code, 'err(1)',
              'p-(1) :- a(1)  q-(1) :- b(1)',
              'Monadic, two conditions, two actions')

    def test_simulate(self):
        """Test simulate: the computation of a query given a sequence of
        actions.
        """
        def create(action_code, class_code):
            run = self.prep_runtime()

            actth = run.ACTION_THEORY
            permitted, errors = run.insert(action_code, target=actth)
            self.assertTrue(permitted, "Error in action policy: {}".format(
                runtime.iterstr(errors)))

            clsth = run.CLASSIFY_THEORY
            permitted, errors = run.insert(class_code, target=clsth)
            self.assertTrue(permitted, "Error in classifier policy: {}".format(
                runtime.iterstr(errors)))
            return run

        def check(run, action_sequence, query, correct, original_db, msg):
            actual = run.simulate(query, action_sequence)
            self.check_equal(actual, correct, msg)
            self.check_class(run, original_db, msg)

        # Simple
        action_code = ('p+(x) :- q(x) action("q")')
        classify_code = 'p(2)'  # just some other data present
        run = create(action_code, classify_code)
        action_sequence = 'q(1)'
        check(run, action_sequence, 'p(x)', 'p(1) p(2)',
              classify_code, 'Simple')

        # Noop does not break rollback
        action_code = ('p-(x) :- q(x)'
                       'action("q")')
        classify_code = ('')
        run = create(action_code, classify_code)
        action_sequence = 'q(1)'
        check(run, action_sequence, 'p(x)', '',
              classify_code, "Rollback handles Noop")

        # insertion takes precedence over deletion
        action_code = ('p+(x) :- q(x)'
                       'p-(x) :- r(x)'
                       'action("q")')
        classify_code = ('')
        run = create(action_code, classify_code)
            # ordered so that consequences will be p+(1) p-(1)
        action_sequence = 'q(1), r(1) :- true'
        check(run, action_sequence, 'p(x)', 'p(1)',
              classify_code, "Deletion before insertion")

        # multiple action sequences 1
        action_code = ('p+(x) :- q(x)'
                       'p-(x) :- r(x)'
                       'action("q")'
                       'action("r")')
        classify_code = ('')
        run = create(action_code, classify_code)
        action_sequence = 'q(1) r(1)'
        check(run, action_sequence, 'p(x)', '',
              classify_code, "Multiple actions: inversion from {}")

        # multiple action sequences 2
        action_code = ('p+(x) :- q(x)'
                       'p-(x) :- r(x)'
                       'action("q")'
                       'action("r")')
        classify_code = ('p(1)')
        run = create(action_code, classify_code)
        action_sequence = 'q(1) r(1)'
        check(run, action_sequence, 'p(x)', '',
              classify_code,
              "Multiple actions: inversion from p(1), first is noop")

        # multiple action sequences 3
        action_code = ('p+(x) :- q(x)'
                       'p-(x) :- r(x)'
                       'action("q")'
                       'action("r")')
        classify_code = ('p(1)')
        run = create(action_code, classify_code)
        action_sequence = 'r(1) q(1)'
        check(run, action_sequence, 'p(x)', 'p(1)',
              classify_code,
              "Multiple actions: inversion from p(1), first is not noop")

        # multiple action sequences 4
        action_code = ('p+(x) :- q(x)'
                       'p-(x) :- r(x)'
                       'action("q")'
                       'action("r")')
        classify_code = ('')
        run = create(action_code, classify_code)
        action_sequence = 'r(1) q(1)'
        check(run, action_sequence, 'p(x)', 'p(1)',
              classify_code,
              "Multiple actions: inversion from {}, first is not noop")

        # Action with additional info
        action_code = ('p+(x,z) :- q(x,y), r(y,z)'
                       'action("q") action("r")')
        classify_code = 'p(1,2)'
        run = create(action_code, classify_code)
        action_sequence = 'q(1,2), r(2,3) :- true'
        check(run, action_sequence, 'p(x,y)', 'p(1,2) p(1,3)',
              classify_code, 'Action with additional info')

        # State update
        action_code = ''
        classify_code = 'p(1)'
        run = create(action_code, classify_code)
        action_sequence = 'p+(2)'
        check(run, action_sequence, 'p(x)', 'p(1) p(2)',
              classify_code, 'State update')

        # Rule update
        action_code = ''
        classify_code = 'q(1)'
        run = create(action_code, classify_code)
        action_sequence = 'p+(x) :- q(x)'
        check(run, action_sequence, 'p(x)', 'p(1)',
              classify_code, 'Rule update')

        # action with query
        action_code = ('p+(x, y) :- q(x, y)'
                       'action("q")')
        classify_code = ('r(1)')
        run = create(action_code, classify_code)
        action_sequence = 'q(x, 0) :- r(x)'
        check(run, action_sequence, 'p(x,y)', 'p(1,0)',
              classify_code, 'Action with query')

        # action sequence with results
        action_code = ('p+(id, val) :- create(val)'
                       'p+(id, val) :- update(id, val)'
                       'p-(id, val) :- update(id, newval), p(id, val)'
                       'action("create")'
                       'action("update")'
                       'result(x) :- create(val), p+(x,val)')
        classify_code = 'hasval(val) :- p(x, val)'
        run = create(action_code, classify_code)
        action_sequence = 'create(0)  update(x,1) :- result(x)'
        check(run, action_sequence, 'hasval(x)', 'hasval(1)',
              classify_code, 'Action sequence with results')

    def test_access_control(self):
        """Test access control: whether a given action is permitted."""
        def create(ac_code, class_code):
            run = self.prep_runtime()

            acth = run.ACCESSCONTROL_THEORY
            permitted, errors = run.insert(ac_code, target=acth)
            self.assertTrue(permitted,
                            "Error in access control policy: {}".format(
                                runtime.iterstr(errors)))

            clsth = run.CLASSIFY_THEORY
            permitted, errors = run.insert(class_code, target=clsth)
            self.assertTrue(permitted, "Error in classifier policy: {}".format(
                runtime.iterstr(errors)))
            return run

        def check_true(run, query, support='', msg=None):
            result = run.access_control(query, support)
            self.assertTrue(result,
                            "Error in access control test {}".format(msg))

        def check_false(run, query, support='', msg=None):
            result = run.access_control(query, support)
            self.assertFalse(result,
                             "Error in access control test {}".format(msg))

        # Only checking basic I/O interface for the access_control request.
        # Basic inference algorithms are tested elsewhere.

        # Simple
        ac_code = ('action(x) :- q(x)')
        classify_code = 'q(2)'
        run = create(ac_code, classify_code)
        check_true(run, "action(2)", msg="Simple true action")
        check_false(run, "action(1)", msg="Simple false action")

        # Options
        ac_code = ('action(x, y) :- q(x), options:value(y, "name", name), '
                   'r(name)')
        classify_code = 'q(2) r("alice")'
        run = create(ac_code, classify_code)
        check_true(run, 'action(2,18)', 'options:value(18, "name", "alice")',
                   msg="Single option true")
        check_false(run, 'action(2,18)', 'options:value(18, "name", "bob")',
                    msg="Single option false")

        # Multiple Options
        ac_code = ('action(x, y) :- q(x), options:value(y, "name", name), '
                   'r(name), options:value(y, "age", 30)')
        classify_code = 'q(2) r("alice")'
        run = create(ac_code, classify_code)
        check_true(run, 'action(2,18)', 'options:value(18, "name", "alice") '
                   'options:value(18, "age", 30)', msg="Multiple option true")
        check_false(run, 'action(2, 18)', 'options:value(18, "name", "bob") '
                    'options:value(18, "age", 30)',
                    msg="Multiple option false")

    def test_enforcement(self):
        """Test enforcement.
        """
        def prep_runtime(enforce_theory, action_theory, class_theory):
            run = runtime.Runtime()
            run.insert(enforce_theory, target=run.ENFORCEMENT_THEORY)
            run.insert(action_theory, target=run.ACTION_THEORY)
            run.insert(class_theory, target=run.CLASSIFY_THEORY)
            return run
        enforce = 'act(x) :- p(x)'
        action = 'action("act")'
        run = prep_runtime(enforce, action, "")
        run.insert('p(1)')
        self.check_equal(run.logger.content(), 'act(1)', 'Insert')
        run.logger.empty()
        run.insert('p(1)')
        self.check_equal(run.logger.content(), '', 'Insert again')
        run.insert('p(2)')
        self.check_equal(run.logger.content(), 'act(2)', 'Insert different')
        run.logger.empty()
        run.delete('p(2)')
        self.check_equal(run.logger.content(), '', 'Delete')

    def test_neutron_actions(self):
        """Test our encoding of the Neutron actions.  Use simulation.
        Just the basics.
        """
        def check(query, action_sequence, correct, msg):
            actual = run.simulate(query, action_sequence)
            LOG.debug("Simulate results: {}".format(
                str(actual)))
            self.check_instance(actual, correct, msg)

        full_path = os.path.realpath(__file__)
        path = os.path.dirname(full_path)
        neutron_path = path + "/../../../examples/neutron.action"
        run = runtime.Runtime()
        run.debug_mode()
        permitted, errs = run.load_file(neutron_path, target=run.ACTION_THEORY)
        if not permitted:
            self.assertTrue(permitted, "Error in Neutron file: {}".format(
                "\n".join([str(x) for x in errs])))
            return

        #### Ports
        query = 'neutron:port(x1, x2, x3, x4, x5, x6, x7, x8, x9)'
        acts = 'neutron:create_port("net1", 17), sys:user("tim") :- true'
        correct = ('neutron:port(id, "net1", name, mac, "null",'
                   '"null", z, w, "tim")')
        check(query, acts, correct, 'Simple port creation')

        query = 'neutron:port(x1, x2, x3, x4, x5, x6, x7, x8, x9)'
        # result(uuid): simulation-specific table that holds the results
        #  of the last action invocation
        acts = ('neutron:create_port("net1", 17), sys:user("tim") :- true '
                'neutron:update_port(uuid, 18), sys:user("tim"), '
                '    options:value(18, "name", "tims port") :- result(uuid) ')
        correct = ('neutron:port(id, "net1", "tims port", mac, "null",'
                   '"null", z, w, "tim")')
        check(query, acts, correct, 'Port create, update')

        query = 'neutron:port(x1, x2, x3, x4, x5, x6, x7, x8, x9)'
        # result(uuid): simulation-specific table that holds the results
        #  of the last action invocation
        acts = ('neutron:create_port("net1", 17), sys:user("tim") :- true '
                'neutron:update_port(uuid, 18), sys:user("tim"), '
                '    options:value(18, "name", "tims port") :- result(uuid) '
                'neutron:delete_port(uuid), sys:user("tim")'
                '    :- result(uuid) ')
        correct = ''
        check(query, acts, correct, 'Port create, update, delete')

        #### Networks
        query = ('neutron:network(id, name, status, admin_state, shared,'
                 'tenenant_id)')
        acts = 'neutron:create_network(17), sys:user("tim") :- true'
        correct = 'neutron:network(id, "", status, "true", "true", "tim")'
        check(query, acts, correct, 'Simple network creation')

        query = ('neutron:network(id, name, status, admin_state, '
                 'shared, tenenant_id)')
        acts = ('neutron:create_network(17), sys:user("tim") :- true '
                'neutron:update_network(uuid, 18), sys:user("tim"), '
                '  options:value(18, "admin_state", "false") :- result(uuid)')
        correct = 'neutron:network(id, "", status, "false", "true", "tim")'
        check(query, acts, correct, 'Network creation, update')

        query = ('neutron:network(id, name, status, admin_state, shared, '
                 'tenenant_id)')
        acts = ('neutron:create_network(17), sys:user("tim") :- true '
                'neutron:update_network(uuid, 18), sys:user("tim"), '
                '  options:value(18, "admin_state", "false") :- result(uuid)'
                'neutron:delete_network(uuid) :- result(uuid)')
        correct = ''
        check(query, acts, correct, 'Network creation, update')

        #### Subnets
        query = ('neutron:subnet(id, name, network_id, '
                 'gateway_ip, ip_version, cidr, enable_dhcp, tenant_id)')
        acts = ('neutron:create_subnet("net1", "10.0.0.1/24", 17), '
                'sys:user("tim") :- true')
        correct = ('neutron:subnet(id, "", "net1", gateway_ip, 4, '
                   '"10.0.0.1/24", "true", "tim")')
        check(query, acts, correct, 'Simple subnet creation')

        query = ('neutron:subnet(id, name, network_id, '
                 'gateway_ip, ip_version, cidr, enable_dhcp, tenant_id)')
        acts = ('neutron:create_subnet("net1", "10.0.0.1/24", 17), '
                'sys:user("tim") :- true '
                'neutron:update_subnet(uuid, 17), sys:user("tim"), '
                '   options:value(17, "enable_dhcp", "false") :- result(uuid)')
        correct = ('neutron:subnet(id, "", "net1", gateway_ip, 4, '
                   '"10.0.0.1/24", "false", "tim")')
        check(query, acts, correct, 'Subnet creation, update')

        query = ('neutron:subnet(id, name, network_id, '
                 'gateway_ip, ip_version, cidr, enable_dhcp, tenant_id)')
        acts = ('neutron:create_subnet("net1", "10.0.0.1/24", 17), '
                'sys:user("tim") :- true '
                'neutron:update_subnet(uuid, 17), sys:user("tim"), '
                '   options:value(17, "enable_dhcp", "false") :- result(uuid)'
                'neutron:delete_subnet(uuid) :- result(uuid)')
        correct = ''
        check(query, acts, correct, 'Subnet creation, update, delete')


def str2form(formula_string):
    return compile.parse1(formula_string)


def str2pol(policy_string):
    return compile.parse(policy_string)


def pol2str(policy):
    return " ".join(str(x) for x in policy)


def form2str(formula):
    return str(formula)


if __name__ == '__main__':
    unittest.main()
