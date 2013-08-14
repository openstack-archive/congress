# Copyright (c) 2013 VMware, Inc. All rights reserved.
#

import unittest
from policy import compile
from policy import runtime
import logging

class TestRuntime(unittest.TestCase):

    def setUp(self):
        pass

    def test_runtime(self):
        def prep_runtime(code, msg=None):
            # compile source
            if msg is not None:
                logging.debug(msg)
            c = compile.Compiler()
            c.read_source(input_string=code)
            c.compute_delta_rules()
            run = runtime.Runtime(c.delta_rules)
            tracer = runtime.Tracer()
            tracer.trace('*')
            run.tracer = tracer
            run.database.tracer = tracer
            return run

        def insert(run, list):
            run.insert(list[0], tuple(list[1:]))

        def delete(run, list):
            run.delete(list[0], tuple(list[1:]))

        def check(run, correct_database_code, msg=None):
            # extract correct answer from correct_database_code
            logging.debug("** Checking {} **".format(msg))
            c = compile.Compiler()
            c.read_source(input_string=correct_database_code)
            correct = c.theory
            correct_database = runtime.Database()
            for atom in correct:
                correct_database.insert(atom.table,
                    [x.name for x in atom.arguments])

            # compute diffs; should be empty
            extra = run.database - correct_database
            missing = correct_database - run.database
            errmsg = ""
            if len(extra) > 0:
                logging.debug("Extra tuples")
                logging.debug(", ".join([str(x) for x in extra]))
            if len(missing) > 0:
                logging.debug("Missing tuples")
                logging.debug(", ".join([str(x) for x in missing]))
            self.assertTrue(len(extra) == 0 and len(missing) == 0, msg)
            logging.debug(str(run.database))
            logging.debug("** Finished {} **".format(msg))

        def showdb(run):
            logging.debug("Resulting DB: " + str(run.database))


        # basic tests
        code = ("q(x) :- p(x), r(x)")
        run = prep_runtime(code, "**** Basic tests ****")

        check(run, "", "Empty database on init")

        insert(run, ['r', 1])
        check(run, "r(1)", "Basic insert with no propagations")
        insert(run, ['r', 1])
        check(run, "r(1)", "Duplicate insert with no propagations")

        delete(run, ['r', 1])
        check(run, "", "Delete with no propagations")
        delete(run, ['r', 1])
        check(run, "", "Delete from empty table")

        insert(run, ['r', 1])
        insert(run, ['p', 1])
        check(run, "r(1) p(1) q(1)", "Insert into base table with 1 propagation")
        showdb(run)

        delete(run, ['r', 1])
        check(run, "p(1)", "Delete from base table with 1 propagation")
        showdb(run)

        # multiple rules
        code = ("q(x) :- p(x), r(x)"
                "q(x) :- s(x)")
        insert(run, ['p', 1])
        insert(run, ['r', 1])
        showdb(run)
        check(run, "p(1) r(1) q(1)", "Insert: multiple rules")
        insert(run, ['s', 1])
        showdb(run)
        check(run, "p(1) r(1) s(1) q(1)", "Insert: duplicate conclusions")

        # body of length 1
        code = ("q(x) :- p(x)")
        run = prep_runtime(code, "**** Body length 1 tests ****")

        insert(run, ['p', 1])
        check(run, "p(1) q(1)", "Insert with body of size 1")

        delete(run, ['p', 1])
        check(run, "", "Delete with body of size 1")

        # existential variables
        code = ("q(x) :- p(x,y)")
        run = prep_runtime(code, "**** Existential variable tests ****")

        insert(run, ['p', 1, 2])
        check(run, "p(1, 2) q(1)", "Insert: existential variable in body of size 1")
        delete(run, ['p', 1, 2])
        check(run, "", "Delete: existential variable in body of size 1")

        code = ("q(x) :- p(x,y), r(y,x)")
        run = prep_runtime(code)
        insert(run, ['p', 1, 2])
        showdb(run)
        insert(run, ['r', 2, 1])
        showdb(run)
        check(run, "p(1, 2) r(2, 1) q(1)", "Insert: join in body of size 2")
        delete(run, ['p', 1, 2])
        showdb(run)
        check(run, "r(2, 1)", "Delete: join in body of size 2")
        insert(run, ['p', 1, 2])
        showdb(run)
        insert(run, ['p', 1, 3])
        showdb(run)
        insert(run, ['r', 3, 1])
        showdb(run)
        check(run, "r(2, 1) r(3,1) p(1, 2) p(1, 3) q(1)",
            "Insert: multiple existential bindings for same head")

        delete(run, ['p', 1, 2])
        check(run, "r(2, 1) r(3,1) p(1, 3) q(1)",
            "Delete: multiple existential bindings for same head")

        code = ("q(x,v) :- p(x,y), r(y,z), s(z,w), t(w,v)")
        run = prep_runtime(code)
        insert(run, ['p', 1, 10])
        insert(run, ['p', 1, 20])
        insert(run, ['r', 10, 100])
        insert(run, ['r', 20, 200])
        insert(run, ['s', 100, 1000])
        insert(run, ['s', 200, 2000])
        insert(run, ['t', 1000, 10000])
        insert(run, ['t', 2000, 20000])
        code = ("p(1,10) p(1,20) r(10,100) r(20,200) s(100,1000) s(200,2000)"
                "t(1000, 10000) t(2000,20000) "
                "q(1,10000) q(1,20000)")
        check(run, code, "Insert: larger join")
        delete(run, ['t', 1000, 10000])
        code = ("p(1,10) p(1,20) r(10,100) r(20,200) s(100,1000) s(200,2000)"
                "t(2000,20000) "
                "q(1,20000)")
        check(run, code, "Delete: larger join")

        code = ("q(x,y) :- p(x,z), p(z,y)")
        run = prep_runtime(code)
        insert(run, ['p', 1, 2])
        insert(run, ['p', 1, 3])
        insert(run, ['p', 2, 4])
        insert(run, ['p', 2, 5])
        check(run, 'p(1,2) p(1,3) p(2,4) p(2,5) q(1,4) q(1,5)',
            "Insert: self-join")
        delete(run, ['p', 2, 4])
        check(run, 'p(1,2) p(1,3) p(2,5) q(1,5)')

        code = ("q(x,w) :- p(x,y), p(y,z), p(z,w)")
        run = prep_runtime(code)
        insert(run, ['p', 1, 1])
        insert(run, ['p', 1, 2])
        insert(run, ['p', 2, 2])
        insert(run, ['p', 2, 3])
        insert(run, ['p', 2, 4])
        insert(run, ['p', 2, 5])
        insert(run, ['p', 3, 3])
        insert(run, ['p', 3, 4])
        insert(run, ['p', 3, 5])
        insert(run, ['p', 3, 6])
        insert(run, ['p', 3, 7])
        code = ('p(1,1) p(1,2) p(2,2) p(2,3) p(2,4) p(2,5)'
                'p(3,3) p(3,4) p(3,5) p(3,6) p(3,7)'
                'q(1,1) q(1,2) q(2,2) q(2,3) q(2,4) q(2,5)'
                'q(3,3) q(3,4) q(3,5) q(3,6) q(3,7)'
                'q(1,3) q(1,4) q(1,5) q(1,6) q(1,7)'
                'q(2,6) q(2,7)')
        check(run, code, "Insert: larger self join")
        delete(run, ['p', 1, 1])
        delete(run, ['p', 2, 2])
        code = ('       p(1,2)        p(2,3) p(2,4) p(2,5)'
                'p(3,3) p(3,4) p(3,5) p(3,6) p(3,7)'
                '                     q(2,3) q(2,4) q(2,5)'
                'q(3,3) q(3,4) q(3,5) q(3,6) q(3,7)'
                'q(1,3) q(1,4) q(1,5) q(1,6) q(1,7)'
                'q(2,6) q(2,7)')
        check(run, code, "Delete: larger self join")

        # Value types: string
        code = ("q(x) :- p(x), r(x)")
        run = prep_runtime(code, "String data type")

        insert(run, ['r', 'apple'])
        check(run, 'r("apple")', "String insert with no propagations")
        insert(run, ['r', 'apple'])
        check(run, 'r("apple")', "Duplicate string insert with no propagations")

        delete(run, ['r', 'apple'])
        check(run, "", "Delete with no propagations")
        delete(run, ['r', 'apple'])
        check(run, "", "Delete from empty table")

        insert(run, ['r', 'apple'])
        insert(run, ['p', 'apple'])
        check(run, 'r("apple") p("apple") q("apple")',
            "String insert with 1 propagation")
        showdb(run)

        delete(run, ['r', 'apple'])
        check(run, 'p("apple")', "String delete with 1 propagation")
        showdb(run)

        # Value types: floats
        code = ("q(x) :- p(x), r(x)")
        run = prep_runtime(code, "Float data type")

        insert(run, ['r', 1.2])
        check(run, 'r(1.2)', "String insert with no propagations")
        insert(run, ['r', 1.2])
        check(run, 'r(1.2)', "Duplicate string insert with no propagations")

        delete(run, ['r', 1.2])
        check(run, "", "Delete with no propagations")
        delete(run, ['r', 1.2])
        check(run, "", "Delete from empty table")

        insert(run, ['r', 1.2])
        insert(run, ['p', 1.2])
        check(run, 'r(1.2) p(1.2) q(1.2)',
            "String insert with 1 propagation")
        showdb(run)

        delete(run, ['r', 1.2])
        check(run, 'p(1.2)', "String delete with 1 propagation")
        showdb(run)

        # negation

if __name__ == '__main__':
    unittest.main()
