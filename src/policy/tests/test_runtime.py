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
        def prep_runtime(code):
            # compile source
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
            # extract correct answer from code, represented as a Database
            print "** Creating correct Database **"
            c = compile.Compiler()
            c.read_source(input_string=correct_database_code)
            correct = c.theory
            correct_database = runtime.Database()
            for atom in correct:
                correct_database.insert(atom.table,
                    tuple([x.name for x in atom.arguments]))
            print str(correct_database)

            # compute diffs; should be empty
            extra = run.database - correct_database
            missing = correct_database - run.database
            errmsg = ""
            if len(extra) > 0:
                print "Extra tuples"
                print ", ".join([str(x) for x in extra])
            if len(missing) > 0:
                print "Missing tuples"
                print ", ".join([str(x) for x in missing])
            self.assertTrue(len(extra) == 0 and len(missing) == 0, msg)


        code = ("q(x) :- p(x), r(x)")
        run = prep_runtime(code)
        check(run, "", "Empty database on init")
        logging.debug("** Next test phase **")

        insert(run, ['r', 1])
        check(run, "r(1)", "Basic insert should Insert into base table with no propagations")
        logging.debug("** Next test phase **")

        delete(run, ['r', 1])
        check(run, "", "Delete from base table after insert")
        logging.debug("** Next test phase **")

        insert(run, ['r', 1])
        insert(run, ['p', 1])
        check(run, "r(1) p(1) q(1)", "Insert into base table with 1 propagation")
        logging.debug("** Next test phase **")

        delete(run, ['r', 1])
        check(run, "p(1)", "Delete from base table with 1 propagation")

        # body of length 1
        # existential variables
        # multiple rules
        # negation

if __name__ == '__main__':
    unittest.main()
