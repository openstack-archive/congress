# Copyright (c) 2013 VMware, Inc. All rights reserved.
#

import unittest
from policy import compile
from policy import runtime
from policy import unify
from policy.runtime import Database
import logging

class TestRuntime(unittest.TestCase):

    def setUp(self):
        pass

    def prep_runtime(self, code, msg=None, target=None):
        # compile source
        if msg is not None:
            logging.debug(msg)
        run = runtime.Runtime()
        run.insert(code, target=target)
        tracer = runtime.Tracer()
        tracer.trace('*')
        run.tracer = tracer
        run.theory[run.CLASSIFY_THEORY].tracer = tracer
        run.theory[run.SERVICE_THEORY].tracer = tracer
        run.theory[run.ACTION_THEORY].tracer = tracer
        return run

    def insert(self, run, alist):
        run.insert(tuple(alist))

    def delete(self, run, alist):
        run.delete(tuple(alist))

    def string_to_database(self, string):
        c = compile.get_compiled([string, '--input_string'])
        database = runtime.Database()
        for atom in c.theory:
            if atom.is_atom():
                database.insert(atom.table,
                    [x.name for x in atom.arguments])
        return database

    def check_db_diffs(self, actual, correct, msg):
        extra = actual - correct
        missing = correct - actual
        extra = [e for e in extra if not e[0].startswith("___")]
        missing = [m for m in missing if not m[0].startswith("___")]
        self.output_diffs(extra, missing, msg)

    def output_diffs(self, extra, missing, msg):
        errmsg = ""
        if len(extra) > 0:
            logging.debug("Extra tuples")
            logging.debug(", ".join([str(x) for x in extra]))
        if len(missing) > 0:
            logging.debug("Missing tuples")
            logging.debug(", ".join([str(x) for x in missing]))
        self.assertTrue(len(extra) == 0 and len(missing) == 0, msg)


    def check(self, run, correct_database_code, msg=None):
        # extract correct answer from correct_database_code
        logging.debug("** Checking: {} **".format(msg))
        correct_database = self.string_to_database(correct_database_code)
        self.check_db_diffs(run.theory[run.CLASSIFY_THEORY].database,
                           correct_database, msg)
        logging.debug("** Finished: {} **".format(msg))

    def check_equal(self, actual_code, correct_code, msg=None):
        logging.debug("** Checking equality: {} **".format(msg))
        actual = compile.get_compiled([actual_code, '--input_string'])
        correct = compile.get_compiled([correct_code, '--input_string'])
        extra = []
        for formula in actual.theory:
            if formula not in correct.theory:
                extra.append(formula)
        missing = []
        for formula in correct.theory:
            if formula not in actual.theory:
                missing.append(formula)
        self.output_diffs(extra, missing, msg)
        logging.debug("** Finished: {} **".format(msg))

    def check_proofs(self, run, correct, msg=None):
        """ Check that the proofs stored in runtime RUN are exactly
        those in CORRECT. """
        # example
        # check_proofs(run, {'q': {(1,):
        #                          Database.ProofCollection([{'x': 1, 'y': 2}])}})

        errs = []
        checked_tables = set()
        for table in run.database.table_names():
            if table in correct:
                checked_tables.add(table)
                for dbtuple in run.database[table]:
                    if dbtuple.tuple in correct[table]:
                        if dbtuple.proofs != correct[table][dbtuple.tuple]:
                            errs.append("For table {} tuple {}\n  "
                                       "Computed: {}\n  "
                                       "Correct: {}".format(table, str(dbtuple),
                                        str(dbtuple.proofs),
                                        str(correct[table][dbtuple.tuple])))
        for table in set(correct.keys()) - checked_tables:
            errs.append("Table {} had a correct answer but did not exist "
                        "in the database".format(table))
        if len(errs) > 0:
#            logging.debug("Check_proof errors:\n{}".format("\n".join(errs)))
            self.fail("\n".join(errs))

    def showdb(self, run):
        logging.debug("Resulting DB: {}".format(
            str(run.theory[run.CLASSIFY_THEORY].database)))

    def test_database(self):
        code = ("")
        run = self.prep_runtime(code, "**** Database tests ****")

        self.check(run, "", "Empty database on init")

        self.insert(run, ['r', 1])
        self.check(run, "r(1)", "Basic insert with no propagations")
        self.insert(run, ['r', 1])
        self.check(run, "r(1)", "Duplicate insert with no propagations")

        self.delete(run, ['r', 1])
        self.check(run, "", "Delete with no propagations")
        self.delete(run, ['r', 1])
        self.check(run, "", "Delete from empty table")

    def test_unary_tables(self):
        """ Test rules for tables with one argument """
        code = ("q(x) :- p(x), r(x)")
        run = self.prep_runtime(code, "**** Basic propagation tests ****")
        self.insert(run, ['r', 1])
        self.insert(run, ['p', 1])
        self.check(run, "r(1) p(1) q(1)", "Insert into base table with 1 propagation")

        self.delete(run, ['r', 1])
        self.check(run, "p(1)", "Delete from base table with 1 propagation")

        # multiple rules
        code = ("q(x) :- p(x), r(x)"
                "q(x) :- s(x)")
        self.insert(run, ['p', 1])
        self.insert(run, ['r', 1])
        self.check(run, "p(1) r(1) q(1)", "Insert: multiple rules")
        self.insert(run, ['s', 1])
        self.check(run, "p(1) r(1) s(1) q(1)", "Insert: duplicate conclusions")

        # body of length 1
        code = ("q(x) :- p(x)")
        run = self.prep_runtime(code, "**** Body length 1 tests ****")

        self.insert(run, ['p', 1])
        self.check(run, "p(1) q(1)", "Insert with body of size 1")
        self.showdb(run)
        self.delete(run, ['p', 1])
        self.showdb(run)
        self.check(run, "", "Delete with body of size 1")

        # existential variables
        code = ("q(x) :- p(x), r(y)")
        run = self.prep_runtime(code, "**** Unary tables with existential ****")
        self.insert(run, ['p', 1])
        self.insert(run, ['r', 2])
        self.insert(run, ['r', 3])
        self.showdb(run)
        self.check(run, "p(1) r(2) r(3) q(1)",
            "Insert with unary table and existential")
        self.delete(run, ['r', 2])
        self.check(run, "p(1) r(3) q(1)",
            "Delete 1 with unary table and existential")
        self.delete(run, ['r', 3])
        self.check(run, "p(1)",
            "Delete all with unary table and existential")


    def test_multi_arity_tables(self):
        """ Test rules whose tables have more than 1 argument """
        code = ("q(x) :- p(x,y)")
        run = self.prep_runtime(code, "**** Multiple-arity table tests ****")

        self.insert(run, ['p', 1, 2])
        self.check(run, "p(1, 2) q(1)", "Insert: existential variable in body of size 1")
        self.delete(run, ['p', 1, 2])
        self.check(run, "", "Delete: existential variable in body of size 1")

        code = ("q(x) :- p(x,y), r(y,x)")
        run = self.prep_runtime(code)
        self.insert(run, ['p', 1, 2])
        self.insert(run, ['r', 2, 1])
        self.check(run, "p(1, 2) r(2, 1) q(1)", "Insert: join in body of size 2")
        self.delete(run, ['p', 1, 2])
        self.check(run, "r(2, 1)", "Delete: join in body of size 2")
        self.insert(run, ['p', 1, 2])
        self.insert(run, ['p', 1, 3])
        self.insert(run, ['r', 3, 1])
        self.check(run, "r(2, 1) r(3,1) p(1, 2) p(1, 3) q(1)",
            "Insert: multiple existential bindings for same head")

        self.delete(run, ['p', 1, 2])
        self.check(run, "r(2, 1) r(3,1) p(1, 3) q(1)",
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
        self.check(run, code, "Insert: larger join")
        self.delete(run, ['t', 1000, 10000])
        code = ("p(1,10) p(1,20) r(10,100) r(20,200) s(100,1000) s(200,2000)"
                "t(2000,20000) "
                "q(1,20000)")
        self.check(run, code, "Delete: larger join")

        code = ("q(x,y) :- p(x,z), p(z,y)")
        run = self.prep_runtime(code)
        self.insert(run, ['p', 1, 2])
        self.insert(run, ['p', 1, 3])
        self.insert(run, ['p', 2, 4])
        self.insert(run, ['p', 2, 5])
        self.check(run, 'p(1,2) p(1,3) p(2,4) p(2,5) q(1,4) q(1,5)',
            "Insert: self-join")
        self.delete(run, ['p', 2, 4])
        self.check(run, 'p(1,2) p(1,3) p(2,5) q(1,5)')

        code = ("q(x,z) :- p(x,y), p(y,z)")
        run = self.prep_runtime(code)
        self.insert(run, ['p', 1, 1])
        self.check(run, 'p(1,1) q(1,1)', "Insert: self-join on same data")

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
        self.check(run, code, "Insert: larger self join")
        self.delete(run, ['p', 1, 1])
        self.delete(run, ['p', 2, 2])
        code = ('       p(1,2)        p(2,3) p(2,4) p(2,5)'
                'p(3,3) p(3,4) p(3,5) p(3,6) p(3,7)'
                '                     q(2,3) q(2,4) q(2,5)'
                'q(3,3) q(3,4) q(3,5) q(3,6) q(3,7)'
                'q(1,3) q(1,4) q(1,5) q(1,6) q(1,7)'
                'q(2,6) q(2,7)')
        self.check(run, code, "Delete: larger self join")

    def test_value_types(self):
        """ Test the different value types """
        # string
        code = ("q(x) :- p(x), r(x)")
        run = self.prep_runtime(code, "String data type")

        self.insert(run, ['r', 'apple'])
        self.check(run, 'r("apple")', "String insert with no propagations")
        self.insert(run, ['r', 'apple'])
        self.check(run, 'r("apple")', "Duplicate string insert with no propagations")

        self.delete(run, ['r', 'apple'])
        self.check(run, "", "Delete with no propagations")
        self.delete(run, ['r', 'apple'])
        self.check(run, "", "Delete from empty table")

        self.insert(run, ['r', 'apple'])
        self.insert(run, ['p', 'apple'])
        self.check(run, 'r("apple") p("apple") q("apple")',
            "String insert with 1 propagation")

        self.delete(run, ['r', 'apple'])
        self.check(run, 'p("apple")', "String delete with 1 propagation")

        # float
        code = ("q(x) :- p(x), r(x)")
        run = self.prep_runtime(code, "Float data type")

        self.insert(run, ['r', 1.2])
        self.check(run, 'r(1.2)', "String insert with no propagations")
        self.insert(run, ['r', 1.2])
        self.check(run, 'r(1.2)', "Duplicate string insert with no propagations")

        self.delete(run, ['r', 1.2])
        self.check(run, "", "Delete with no propagations")
        self.delete(run, ['r', 1.2])
        self.check(run, "", "Delete from empty table")

        self.insert(run, ['r', 1.2])
        self.insert(run, ['p', 1.2])
        self.check(run, 'r(1.2) p(1.2) q(1.2)',
            "String self.insert with 1 propagation")

        self.delete(run, ['r', 1.2])
        self.check(run, 'p(1.2)', "String delete with 1 propagation")

    # def test_proofs(self):
    #     """ Test if the proof computation is performed correctly. """
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

    def test_negation(self):
        """ Test negation """
        # Unary, single join
        code = ("q(x) :- p(x), not r(x)")
        run = self.prep_runtime(code, "Unary, single join")

        self.insert(run, ['p', 2])
        self.check(run, 'p(2) q(2)',
            "Insert into positive literal with propagation")
        self.delete(run, ['p', 2])
        self.check(run, '',
            "Delete from positive literal with propagation")

        self.insert(run, ['r', 2])
        self.check(run, 'r(2)',
            "Insert into negative literal without propagation")
        self.delete(run, ['r', 2])
        self.check(run, '',
            "Delete from negative literal without propagation")

        self.insert(run, ['p', 2])
        self.insert(run, ['r', 2])
        self.check(run, 'p(2) r(2)',
            "Insert into negative literal with propagation")

        self.delete(run, ['r', 2])
        self.check(run, 'q(2) p(2)',
            "Delete from negative literal with propagation")

        # Unary, multiple joins
        code = ("s(x) :- p(x), not r(x), q(y), not t(y)")
        run = self.prep_runtime(code, "Unary, multiple join")
        self.insert(run, ['p', 1])
        self.insert(run, ['q', 2])
        self.check(run, 'p(1) q(2) s(1)',
            'Insert with two negative literals')

        self.insert(run, ['r', 3])
        self.check(run, 'p(1) q(2) s(1) r(3)',
            'Ineffectual insert with 2 negative literals')
        self.insert(run, ['r', 1])
        self.check(run, 'p(1) q(2) r(3) r(1)',
            'Insert into existentially quantified negative literal with propagation. ')
        self.insert(run, ['t', 2])
        self.check(run, 'p(1) q(2) r(3) r(1) t(2)',
            'Insert into negative literal producing extra blocker for proof.')
        self.delete(run, ['t', 2])
        self.check(run, 'p(1) q(2) r(3) r(1)',
            'Delete first blocker from proof')
        self.delete(run, ['r', 1])
        self.check(run, 'p(1) q(2) r(3) s(1)',
            'Delete second blocker from proof')

        # Non-unary
        code = ("p(x, v) :- q(x,z), r(z, w), not s(x, w), u(w,v)")
        run = self.prep_runtime(code, "Non-unary")
        self.insert(run, ['q', 1, 2])
        self.insert(run, ['r', 2, 3])
        self.insert(run, ['r', 2, 4])
        self.insert(run, ['u', 3, 5])
        self.insert(run, ['u', 4, 6])
        self.check(run, 'q(1,2) r(2,3) r(2,4) u(3,5) u(4,6) p(1,5) p(1,6)',
            'Insert with non-unary negative literal')

        self.insert(run, ['s', 1, 3])
        self.check(run, 'q(1,2) r(2,3) r(2,4) u(3,5) u(4,6) s(1,3) p(1,6)',
            'Insert into non-unary negative with propagation')

        self.insert(run, ['s', 1, 4])
        self.check(run, 'q(1,2) r(2,3) r(2,4) u(3,5) u(4,6) s(1,3) s(1,4)',
            'Insert into non-unary with different propagation')

    def test_select(self):
        """ Test the SELECT event handler. """
        code = ("p(x, y) :- q(x), r(y)")
        run = self.prep_runtime(code, "Select")
        self.insert(run, ['q', 1])
        self.insert(run, ['q', 2])
        self.insert(run, ['r', 1])
        self.insert(run, ['r', 2])
        self.check(run, 'q(1) q(2) r(1) r(2) p(1,1) p(1,2) p(2,1) p(2,2)',
            'Prepare for select')
        self.check_equal(run.select('p(x,y)'), 'p(1,1) p(1,2) p(2,1) p(2,2)',
            'Select: bound no args')
        self.check_equal(run.select('p(1,y)'), 'p(1,1) p(1,2)',
            'Select: bound 1st arg')
        self.check_equal(run.select('p(x,2)'), 'p(1,2) p(2,2)',
            'Select: bound 2nd arg')
        self.check_equal(run.select('p(1,2)'), 'p(1,2)',
            'Select: bound 1st and 2nd arg')
        self.check_equal(run.select('query :- q(x), r(y)'),
            'query :- q(1), r(1)'
            'query :- q(1), r(2)'
            'query :- q(2), r(1)'
            'query :- q(2), r(2)')

    def test_modify_rules(self):
        """ Test the functionality for adding and deleting rules *after* data
            has already been entered. """
        run = self.prep_runtime("", "Rule modification")
        run.insert("q(1) r(1) q(2) r(2)")
        self.showdb(run)
        self.check(run, 'q(1) r(1) q(2) r(2)', "Installation")
        run.insert("p(x) :- q(x), r(x)")
        self.check(run, 'q(1) r(1) q(2) r(2) p(1) p(2)', 'Rule insert after data insert')
        run.delete("q(1)")
        self.check(run, 'r(1) q(2) r(2) p(2)', 'Delete after Rule insert with propagation')
        run.insert("q(1)")
        run.delete("p(x) :- q(x), r(x)")
        self.check(run, 'q(1) r(1) q(2) r(2)', "Delete rule")

    def test_recursion(self):
        run = self.prep_runtime('q(x,y) :- p(x,y)'
                                'q(x,y) :- p(x,z), q(z,y)')
        run.insert('p(1,2)')
        run.insert('p(2,3)')
        run.insert('p(3,4)')
        run.insert('p(4,5)')
        self.check(run, 'p(1,2) p(2,3) p(3,4) p(4,5)'
                        'q(1,2) q(2,3) q(1,3) q(3,4) q(2,4) q(1,4) q(4,5) q(3,5) '
                        'q(1,5) q(2,5)',
            'Insert into recursive rules')
        run.delete('p(1,2)')
        self.check(run, 'p(2,3) p(3,4) p(4,5)'
                        'q(2,3) q(3,4) q(2,4) q(4,5) q(3,5) q(2,5)',
            'Delete from recursive rules')

    # TODO(tim): add tests for explanations
    def test_explanations(self):
        """ Test the explanation event handler. """
        run = self.prep_runtime("p(x) :- q(x), r(x)", "Explanations")
        run.insert("q(1) r(1)")
        self.showdb(run)
        logging.debug(run.explain("p(1)"))

        run = self.prep_runtime("p(x) :- q(x), r(x) q(x) :- s(x), t(x)", "Explanations")
        run.insert("s(1) r(1) t(1)")
        self.showdb(run)
        logging.debug(run.explain("p(1)"))
        # self.fail()

    def check_unify(self, atom_string1, atom_string2, msg, change_num):
        """ Check that bi-unification succeeds. """
        logging.debug("** Checking: {} **".format(msg))
        unifier1 = runtime.new_BiUnifier()
        unifier2 = runtime.new_BiUnifier()
        p1 = compile.get_parsed([atom_string1, '--input_string'])[0]
        p2 = compile.get_parsed([atom_string2, '--input_string'])[0]
        changes = unify.bi_unify_atoms(p1, unifier1, p2, unifier2)
        self.assertTrue(p1 != p2)
        p1p = p1.plug_new(unifier1)
        p2p = p2.plug_new(unifier2)
        if not p1p == p2p:
            logging.debug("Failure: bi-unify({}, {}) produced {} and {}".format(
                str(p1), str(p2), str(unifier1), str(unifier2)))
            logging.debug("plug({}, {}) = {}".format(
                str(p1), str(unifier1), str(p1p)))
            logging.debug("plug({}, {}) = {}".format(
                str(p2), str(unifier2), str(p2p)))
            self.fail()
        self.assertTrue(changes is not None)
        if change_num is not None:
            self.assertEqual(len(changes), change_num)
        unify.undo_all(changes)
        self.assertEqual(p1.plug_new(unifier1), p1)
        self.assertEqual(p2.plug_new(unifier2), p2)
        logging.debug("** Finished: {} **".format(msg))

    def check_unify_fail(self, atom_string1, atom_string2, msg):
        """ Check that the bi-unification fails. """
        unifier1 = runtime.new_BiUnifier()
        unifier2 = runtime.new_BiUnifier()
        p1 = compile.get_parsed([atom_string1, '--input_string'])[0]
        p2 = compile.get_parsed([atom_string2, '--input_string'])[0]
        changes = unify.bi_unify_atoms(p1, unifier1, p2, unifier2)
        if changes is not None:
            logging.debug(
                "Failure failure: bi-unify({}, {}) produced {} and {}".format(
                str(p1), str(p2), str(unifier1), str(unifier2)))
            logging.debug("plug({}, {}) = {}".format(
                str(p1), str(unifier1), str(p1.plug_new(unifier1))))
            logging.debug("plug({}, {}) = {}".format(
                str(p2), str(unifier2), str(p2.plug_new(unifier2))))
            self.fail()

    def test_bi_unify(self):
        """ Test the bi-unification routine. """
        self.check_unify("p(x)", "p(1)",
            "Matching", 1)
        self.check_unify("p(x,y)", "p(1,2)",
            "Binary Matching", 2)
        self.check_unify("p(1,2)", "p(x,y)",
            "Binary Matching Reversed", 2)
        self.check_unify("p(1,1)", "p(x,y)",
            "Binary Matching Many-to-1", 2)
        self.check_unify_fail("p(1,2)", "p(x,x)",
            "Binary Matching Failure")
        self.check_unify("p(1,x)", "p(1,y)",
            "Simple Unification", 1)
        self.check_unify("p(1,x)", "p(y,1)",
            "Separate Namespace Unification", 2)
        self.check_unify("p(1,x)", "p(x,2)",
            "Namespace Collision Unification", 2)
        self.check_unify("p(x,y,z)", "p(t,u,v)",
            "Variable-only Unification", 3)
        self.check_unify("p(x,y,y)", "p(t,u,t)",
            "Repeated Variable Unification", 3)
        self.check_unify_fail("p(x,y,y,x,y)", "p(t,u,t,1,2)",
            "Repeated Variable Unification Failure")
        self.check_unify("p(x,y,y)", "p(x,y,x)",
            "Repeated Variable Unification Namespace Collision", 3)
        self.check_unify_fail("p(x,y,y,x,y)", "p(x,y,x,1,2)",
            "Repeated Variable Unification Namespace Collision Failure")



    def test_rule_select(self):
        """ Test top-down evaluation for RuleTheory. """
        th = runtime.Runtime.ACTION_THEORY
        run = self.prep_runtime('p(1)', target=th)
        self.check_equal(run.select('p(1)', target=th), "p(1)",
            "Simple lookup")
        self.check_equal(run.select('p(2)', target=th), "",
            "Failed lookup")
        run = self.prep_runtime('p(1)', target=th)
        self.check_equal(run.select('p(x)', target=th), "p(1)",
            "Variablized lookup")

        run = self.prep_runtime('p(x) :- q(x)'
                                'q(x) :- r(x)'
                                'r(1)', target=th)
        self.check_equal(run.select('p(1)', target=th), "p(1)",
            "Monadic rules")
        self.check_equal(run.select('p(2)', target=th), "",
            "False monadic rules")
        self.check_equal(run.select('p(x)', target=th), "p(1)",
            "Variablized query with monadic rules")

        run = self.prep_runtime('p(x) :- q(x)'
                                'q(x) :- r(x)'
                                'q(x) :- s(x)'
                                'r(1)'
                                's(2)', target=th)
        self.check_equal(run.select('p(1)', target=th), "p(1)",
            "Monadic, disjunctive rules 1")
        self.check_equal(run.select('p(2)', target=th), "p(2)",
            "Monadic, disjunctive rules 2")
        self.check_equal(run.select('p(x)', target=th), "p(1)",
            "Monadic, disjunctive rules 2")
        self.check_equal(run.select('p(3)', target=th), "",
            "False Monadic, disjunctive rules")

        run = self.prep_runtime('p(x) :- q(x), r(x)'
                                'q(1)'
                                'r(1)'
                                'r(2)'
                                'q(2)'
                                'q(3)', target=th)
        self.check_equal(run.select('p(1)', target=th), "p(1)",
            "Multiple literals in body")
        self.check_equal(run.select('p(2)', target=th), "p(2)",
            "Multiple literals in body answer 2")
        self.check_equal(run.select('p(x)', target=th), "p(1)",
            "Multiple literals in body variablized")
        self.check_equal(run.select('p(3)', target=th), "",
            "False multiple literals in body")

        run = self.prep_runtime('p(x) :- q(x), r(x)'
                                'q(1)'
                                'r(2)', target=th)
        self.check_equal(run.select('p(x)', target=th), "",
            "False variablized multiple literals in body")

        run = self.prep_runtime('p(x,y) :- q(x,z), r(z, y)'
                                'q(1,1)'
                                'q(1,2)'
                                'r(1,3)'
                                'r(1,4)'
                                'r(2,5)', target=th)
        self.check_equal(run.select('p(1,3)', target=th), "p(1,3)",
            "Binary, existential rules 1")
        self.check_equal(run.select('p(1,4)', target=th), "p(1,4)",
            "Binary, existential rules 2")
        self.check_equal(run.select('p(1,5)', target=th), "p(1,5)",
            "Binary, existential rules 3")
        self.check_equal(run.select('p(1,1)', target=th), "",
            "False binary, existential rules")

        run = self.prep_runtime('p(x) :- q(x), r(x)'
                            'q(y) :- t(y), s(x)'
                            's(1)'
                            'r(2)'
                            't(2)', target=th)
        self.check_equal(run.select('p(2)', target=th), "p(2)",
            "Distinct variable namespaces across rules")

        run = self.prep_runtime('p(x,y) :- q(x,z), r(z,y)'
                            'q(x,y) :- s(x,z), t(z,y)'
                            's(x,y) :- u(x,z), v(z,y)'
                            'u(1,2)'
                            'v(2,3)'
                            't(3,4)'
                            'r(4,5)', target=th)
        self.check_equal(run.select('p(1,5)', target=th), "p(1,5)",
            "Tower of existential variables")
        self.check_equal(run.select('p(x,y)', target=th), "p(1,5)",
            "Tower of existential variables")


if __name__ == '__main__':
    unittest.main()
