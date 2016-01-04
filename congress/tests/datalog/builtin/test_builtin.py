#! /usr/bin/python
#
# Copyright (c) 2014 IBM, Inc. All rights reserved.
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
from congress.datalog.builtin import congressbuiltin
from congress.datalog import compile
from congress import exception
from congress.policy_engines import agnostic
from congress.tests import base
from congress.tests import helper

LOG = logging.getLogger(__name__)

addmap = {
    'comparison': [
        {'func': 'f(x,y)', 'num_inputs': 2,
         'code': lambda x, y: x if x > y else y}],
    'newcategory': [
        {'func': 'g(x,y)', 'num_inputs': 2, 'code': lambda x, y: x + y}]}


append_builtin = {'arithmetic': [{'func': 'div(x,y)',
                                  'num_inputs': 2,
                                  'code': 'lambda x,y: x / y'}]}


class TestBuiltins(base.TestCase):
    def setUp(self):
        super(TestBuiltins, self).setUp()
        self.cbcmap = congressbuiltin.CongressBuiltinCategoryMap(
            congressbuiltin._builtin_map)
        self.predl = self.cbcmap.builtin('lt')

    def test_add_and_delete_map(self):
        cbcmap_before = self.cbcmap
        self.cbcmap.add_map(append_builtin)
        self.cbcmap.delete_map(append_builtin)
        self.assertTrue(self.cbcmap.mapequal(cbcmap_before))

    def test_add_map_only(self):
        self.cbcmap.add_map(append_builtin)
        predl = self.cbcmap.builtin('div')
        self.assertNotEqual(predl, None)
        self.cbcmap.add_map(addmap)
        predl = self.cbcmap.builtin('max')
        self.assertNotEqual(predl, None)

    def test_add_and_delete_builtin(self):
        cbcmap_before = self.cbcmap
        self.cbcmap.add_map(append_builtin)
        self.cbcmap.delete_builtin('arithmetic', 'div', 2)
        self.assertTrue(self.cbcmap.mapequal(cbcmap_before))

    def test_string_pred_string(self):
        predstring = str(self.predl)
        self.assertNotEqual(predstring, 'ltc(x,y')

    def test_add_and_delete_to_category(self):
        cbcmap_before = self.cbcmap
        arglist = ['x', 'y', 'z']
        pred = congressbuiltin.CongressBuiltinPred('testfunc', arglist, 1,
                                                   lambda x: not x)
        self.cbcmap.insert_to_category('arithmetic', pred)
        self.cbcmap.delete_from_category('arithmetic', pred)
        self.assertTrue(self.cbcmap.mapequal(cbcmap_before))

    def test_all_checks(self):
        predtotest = self.cbcmap.builtin('lt')
        self.assertTrue(self.cbcmap.builtin_is_registered(predtotest))

    def test_eval_builtin(self):
        predl = self.cbcmap.builtin('plus')
        result = predl.code(1, 2)
        self.assertEqual(result, 3)
        predl = self.cbcmap.builtin('gt')
        result = predl.code(1, 2)
        self.assertEqual(result, False)


class TestReorder(base.TestCase):
    def check(self, input_string, correct_string, msg):
        rule = compile.parse1(input_string)
        actual = compile.reorder_for_safety(rule)
        correct = compile.parse1(correct_string)
        if correct != actual:
            emsg = "Correct: " + str(correct)
            emsg += "; Actual: " + str(actual)
            self.fail(msg + " :: " + emsg)

    def check_err(self, input_string, unsafe_lit_strings, msg):
        rule = compile.parse1(input_string)
        try:
            compile.reorder_for_safety(rule)
            self.fail("Failed to raise exception for " + input_string)
        except exception.PolicyException as e:
            errmsg = str(e)
            # parse then print to string so string rep same in err msg
            unsafe_lits = [str(compile.parse1(x)) for x in unsafe_lit_strings]
            missing_lits = [m for m in unsafe_lits
                            if m + " (vars" not in errmsg]
            if len(missing_lits) > 0:
                self.fail(
                    "Unsafe literals {} not reported in error: {}".format(
                        ";".join(missing_lits), errmsg))

    def test_reorder_builtins(self):
        self.check("p(x, z) :- q(x, y), plus(x, y, z)",
                   "p(x, z) :- q(x, y), plus(x, y, z)",
                   "No reorder")

        self.check("p(x, z) :- plus(x, y, z), q(x, y)",
                   "p(x, z) :- q(x, y), plus(x, y, z)",
                   "Basic reorder")

        self.check("p(x, z) :- q(x, y), r(w), plus(x, y, z), plus(z, w, y)",
                   "p(x, z) :- q(x, y), r(w), plus(x, y, z), plus(z, w, y)",
                   "Chaining: no reorder")

        self.check("p(x, z) :- q(x, y),  plus(x, y, z), plus(z, w, y), r(w)",
                   "p(x, z) :- q(x, y), plus(x, y, z), r(w), plus(z, w, y)",
                   "Chaining: reorder")

        self.check("p(x) :- lt(t, v), plus(z, w, t), plus(z, u, v), "
                   "   plus(x, y, z), q(y), r(x), s(u), t(w) ",
                   "p(x) :- q(y), r(x), plus(x, y, z), s(u), plus(z, u, v), "
                   "   t(w), plus(z, w, t), lt(t, v)",
                   "Partial-order chaining")

    def test_unsafe_builtins(self):
        # an output
        self.check_err("p(x) :- q(x), plus(x, y, z)",
                       ["plus(x,y,z)"],
                       "Basic Unsafe input")

        self.check_err("p(x) :- q(x), r(z), plus(x, y, z)",
                       ["plus(x,y,z)"],
                       "Basic Unsafe input 2")

        self.check_err("p(x, z) :- plus(x, y, z), plus(z, y, x), "
                       "   plus(x, z, y)",
                       ["plus(x, y, z)", "plus(z, y, x)", "plus(x, z, y)"],
                       "Unsafe with cycle")

        # no outputs
        self.check_err("p(x) :- q(x), lt(x, y)",
                       ["lt(x,y)"],
                       "Basic Unsafe input, no outputs")

        self.check_err("p(x) :- q(y), lt(x, y)",
                       ["lt(x,y)"],
                       "Basic Unsafe input, no outputs 2")

        self.check_err("p(x, z) :- lt(x, y), lt(y, x)",
                       ["lt(x,y)", "lt(y, x)"],
                       "Unsafe with cycle, no outputs")

        # chaining
        self.check_err("p(x) :- q(x, y), plus(x, y, z), plus(z, 3, w), "
                       "    plus(w, t, u)",
                       ["plus(w, t, u)"],
                       "Unsafe chaining")

        self.check_err("p(x) :- q(x, y), plus(x, y, z), plus(z, 3, w), "
                       "   lt(w, t)",
                       ["lt(w, t)"],
                       "Unsafe chaining 2")

    def test_reorder_negation(self):
        self.check("p(x) :- q(x), not u(x), r(y), not s(x, y)",
                   "p(x) :- q(x), not u(x), r(y), not s(x, y)",
                   "No reordering")

        self.check("p(x) :- not q(x), r(x)",
                   "p(x) :- r(x), not q(x)",
                   "Basic")

        self.check("p(x) :- r(x), not q(x, y), s(y)",
                   "p(x) :- r(x), s(y), not q(x,y)",
                   "Partially safe")

        self.check("p(x) :- not q(x, y), not r(x), not r(x, z), "
                   "    t(x, y), u(x), s(z)",
                   "p(x) :- t(x,y), not q(x,y), not r(x), u(x), s(z), "
                   "    not r(x, z)",
                   "Complex")

    def test_unsafe_negation(self):
        self.check_err("p(x) :- not q(x)",
                       ["q(x)"],
                       "Basic")

        self.check_err("p(x) :- not q(x), not r(x)",
                       ["q(x)", "r(x)"],
                       "Cycle")

        self.check_err("p(x) :- not q(x, y), r(y)",
                       ["q(x, y)"],
                       "Partially safe")

    def test_reorder_builtins_negation(self):
        self.check("p(x) :- not q(z), plus(x, y, z), s(x), s(y)",
                   "p(x) :- s(x), s(y), plus(x, y, z), not q(z)",
                   "Basic")

        self.check("p(x) :- not q(z, w), plus(x, y, z), lt(z, w), "
                   "   plus(x, 3, w), s(x, y)",
                   "p(x) :- s(x,y), plus(x, y, z), plus(x, 3, w), "
                   "   not q(z, w), lt(z, w)",
                   "Partial order")

    def test_unsafe_builtins_negation(self):
        self.check_err("p(x) :- plus(x, y, z), not q(x, y)",
                       ['plus(x,y,z)', 'q(x,y)'],
                       'Unsafe cycle')

        self.check_err("p(x) :- plus(x, y, z), plus(z, w, t), not q(z, t),"
                       "    s(x), t(y)",
                       ['plus(z, w, t)', 'q(z, t)'],
                       'Unsafety propagates')


NREC_THEORY = 'non-recursive theory test'
MAT_THEORY = 'materialized view theory test'


class TestTheories(base.TestCase):
    def prep_runtime(self, code=None, msg=None, target=None):
        # compile source
        if msg is not None:
            LOG.debug(msg)
        if code is None:
            code = ""
        if target is None:
            target = NREC_THEORY
        run = agnostic.Runtime()
        run.create_policy(NREC_THEORY, abbr="NRT",
                          kind=datalog_base.NONRECURSIVE_POLICY_TYPE)
        run.create_policy(MAT_THEORY, abbr="MAT",
                          kind=datalog_base.MATERIALIZED_POLICY_TYPE)
        run.debug_mode()
        run.insert(code, target=target)
        return run

    def check_equal(self, actual_string, correct_string, msg):
        self.assertTrue(helper.datalog_equal(
            actual_string, correct_string, msg))

    def test_materialized_builtins(self):
        self.test_builtins(MAT_THEORY)

    def test_builtins(self, th=NREC_THEORY):
        """Test the mechanism that implements builtins."""
        run = self.prep_runtime()
        run.insert('p(x) :- q(x,y), plus(x,y,z), r(z)'
                   'q(1,2)'
                   'q(2,3)'
                   'r(3)'
                   'r(5)', target=th)
        self.check_equal(run.select('p(x)', target=th), "p(1) p(2)", "Plus")
        run.delete('r(5)', target=th)
        self.check_equal(run.select('p(x)', target=th), "p(1)", "Plus")

        run = self.prep_runtime()
        run.insert('p(x) :- q(x,y), minus(x,y,z), r(z)'
                   'q(2,1)'
                   'q(3,1)'
                   'r(1)'
                   'r(4)', target=th)
        self.check_equal(run.select('p(x)', target=th), "p(2)", "Minus")
        run.delete('r(4)', target=th)
        run.insert('r(2)', target=th)
        self.check_equal(run.select('p(x)', target=th), "p(2) p(3)", "Minus")

        run = self.prep_runtime()
        run.insert('p(x, z) :- q(x,y), plus(x,y,z)'
                   'q(1,2)'
                   'q(2,3)', target=th)
        self.check_equal(run.select('p(x, y)', target=th),
                         "p(1, 3) p(2, 5)", "Plus")

        run = self.prep_runtime()
        run.insert('m(x) :- j(x,y), lt(x,y)'
                   'j(1,2)'
                   'j(3,2)', target=th)
        self.check_equal(run.select('m(x)', target=th), 'm(1)', "LT")

        run = self.prep_runtime()
        run.insert('m(x) :- j(x,y), lt(x,y), r(y)'
                   'j(1,2)'
                   'j(2,3)'
                   'j(3,2)'
                   'r(2)', target=th)
        self.check_equal(run.select('m(x)', target=th), 'm(1)', "LT 2")

        run = self.prep_runtime()
        run.insert('p(x,z) :- q(x), plus(x,1,z)'
                   'q(3)'
                   'q(5)', target=th)
        self.check_equal(run.select('p(x,z)', target=th),
                         'p(3, 4) p(5,6)', "Bound input")

        run = self.prep_runtime()
        run.insert('p(x) :- q(x), plus(x,1,5)'
                   'q(4)'
                   'q(5)', target=th)
        self.check_equal(run.select('p(x)', target=th),
                         'p(4)', "Bound output")

        run = self.prep_runtime()
        run.insert('p(x, z) :- plus(x,y,z), q(x), r(y)'
                   'q(4)'
                   'r(5)', target=th)
        self.check_equal(run.select('p(x, y)', target=th),
                         'p(4, 9)',
                         "Reordering")

        run = self.prep_runtime()
        run.insert('p(x, z) :- plus(x,y,z), q(x), q(y)'
                   'q(4)'
                   'q(5)', target=th)
        self.check_equal(run.select('p(x, y)', target=th),
                         'p(4, 9) p(4, 8) p(5, 9) p(5, 10)',
                         "Reordering with self joins")

    def test_materialized_builtins_content(self):
        self.test_builtins_content(MAT_THEORY)

    def test_builtins_content(self, th=NREC_THEORY):
        """Test the content of the builtins, not the mechanism."""
        def check_true(code, msg):
            run = self.prep_runtime('')
            run.insert(code, target=th)
            self.check_equal(
                run.select('p(x)', target=th),
                'p(1)',
                msg)

        def check_false(code, msg):
            th = NREC_THEORY
            run = self.prep_runtime('')
            run.insert(code, target=th)
            self.check_equal(
                run.select('p(x)', target=th),
                '',
                msg)

        #
        # Numbers
        #

        # int
        code = 'p(1) :- int(2,2)'
        check_true(code, "int")

        code = 'p(1) :- int(2.3, 2)'
        check_true(code, "int")

        code = 'p(1) :- int(2, 3.3)'
        check_false(code, "int")

        # float
        code = 'p(1) :- float(2,2.0)'
        check_true(code, "float")

        code = 'p(1) :- float(2.3,2.3)'
        check_true(code, "float")

        code = 'p(1) :- float(2,3.3)'
        check_false(code, "int")

        # plus
        code = 'p(1) :- plus(2,3,5)'
        check_true(code, "plus")

        code = 'p(1) :- plus(2,3,1)'
        check_false(code, "plus")

        # minus
        code = 'p(1) :- minus(5, 3, 2)'
        check_true(code, "minus")

        code = 'p(1) :- minus(5, 3, 6)'
        check_false(code, "minus")

        # minus negative: negative numbers should not be supported
        # code = 'p(1) :- minus(3, 5, x)'
        # check_false(code, "minus")

        # times
        code = 'p(1) :- mul(3, 5, 15)'
        check_true(code, "multiply")

        code = 'p(1) :- mul(2, 5, 1)'
        check_false(code, "multiply")

        # divides
        code = 'p(1) :- div(10, 2, 5)'
        check_true(code, "divides")

        code = 'p(1) :- div(10, 4, 2)'
        check_true(code, "integer divides")

        code = 'p(1) :- div(10, 4.0, 2.5)'
        check_true(code, "float divides")

        code = 'p(1) :- div(10.0, 3, 3.3)'
        check_false(code, "divides")

        #
        # Comparison
        #

        # less than
        code = 'p(1) :- lt(1, 3)'
        check_true(code, "lessthan")

        code = 'p(1) :- lt(5, 2)'
        check_false(code, "lessthan")

        # less than equal
        code = 'p(1) :- lteq(1, 3)'
        check_true(code, "lessthaneq")

        code = 'p(1) :- lteq(3, 3)'
        check_true(code, "lessthaneq")

        code = 'p(1) :- lteq(4, 3)'
        check_false(code, "lessthaneq")

        # greater than
        code = 'p(1) :- gt(9, 5)'
        check_true(code, "greaterthan")

        code = 'p(1) :- gt(5, 9)'
        check_false(code, "greaterthan")

        # greater than equal
        code = 'p(1) :- gteq(10, 5)'
        check_true(code, "greaterthaneq")

        code = 'p(1) :- gteq(10, 10)'
        check_true(code, "greaterthaneq")

        code = 'p(1) :- gteq(5, 20)'
        check_false(code, "greaterthaneq")

        # equal
        code = 'p(1) :- equal(5, 5)'
        check_true(code, "equal")

        code = 'p(1) :- equal(5, 7)'
        check_false(code, "equal")

        # max
        code = 'p(1) :- max(3, 4, 4)'
        check_true(code, "max")

        code = 'p(1) :- max(3, 7, 3)'
        check_false(code, "max")

        #
        # Strings
        #

        # len
        code = 'p(1) :- len("abcde", 5)'
        check_true(code, "Len")

        code = 'p(1) :- len("abcde", 7)'
        check_false(code, "Len")

        # concat
        code = 'p(1) :- concat("abc", "def", "abcdef")'
        check_true(code, "concat")

        code = 'p(1) :- concat("abc", "def", "zxy")'
        check_false(code, "concat")

        #
        # Datetime
        # We should make some of these more robust but can't do
        #   that with the safety restrictions in place at the time
        #   of writing.
        #

        # lessthan
        code = ('p(1) :- datetime_lt('
                '"Jan 1, 2014 10:00:00", "2014-01-02 10:00:00")')
        check_true(code, "True datetime_lt")

        code = ('p(1) :- datetime_lt('
                '"2014-01-03 10:00:00", "Jan 2, 2014 10:00:00")')
        check_false(code, "False datetime_lt")

        # lessthanequal
        code = ('p(1) :- datetime_lteq('
                '"Jan 1, 2014 10:00:00", "2014-01-02 10:00:00")')
        check_true(code, "True datetime_lteq")

        code = ('p(1) :- datetime_lteq('
                '"Jan 1, 2014 10:00:00", "2014-01-01 10:00:00")')
        check_true(code, "True datetime_lteq")

        code = ('p(1) :- datetime_lteq('
                '"2014-01-02 10:00:00", "Jan 1, 2014 10:00:00")')
        check_false(code, "False datetime_lteq")

        # greaterthan
        code = ('p(1) :- datetime_gt('
                '"Jan 5, 2014 10:00:00", "2014-01-02 10:00:00")')
        check_true(code, "True datetime_gt")

        code = ('p(1) :- datetime_gt('
                '"2014-01-03 10:00:00", "Feb 2, 2014 10:00:00")')
        check_false(code, "False datetime_gt")

        # greaterthanequal
        code = ('p(1) :- datetime_gteq('
                '"Jan 5, 2014 10:00:00", "2014-01-02 10:00:00")')
        check_true(code, "True datetime_gteq")

        code = ('p(1) :- datetime_gteq('
                '"Jan 5, 2014 10:00:00", "2014-01-05 10:00:00")')
        check_true(code, "True datetime_gteq")

        code = ('p(1) :- datetime_gteq('
                '"2014-01-02 10:00:00", "Mar 1, 2014 10:00:00")')
        check_false(code, "False datetime_gteq")

        # equal
        code = ('p(1) :- datetime_equal('
                '"Jan 5, 2014 10:00:00", "2014-01-05 10:00:00")')
        check_true(code, "True datetime_equal")

        code = ('p(1) :- datetime_equal('
                '"Jan 5, 2014 10:00:00", "2014-01-02 10:00:00")')
        check_false(code, "False datetime_equal")

        # plus
        code = ('p(1) :- datetime_plus('
                '"Jan 5, 2014 10:00:00", 3600, "2014-01-05 11:00:00")')
        check_true(code, "True datetime_plus")

        code = ('p(1) :- datetime_plus('
                '"Jan 5, 2014 10:00:00", "1:00:00", "2014-01-05 11:00:00")')
        check_true(code, "True datetime_plus")

        code = ('p(1) :- datetime_plus('
                '"Jan 5, 2014 10:00:00", 3600, "2014-01-05 12:00:00")')
        check_false(code, "False datetime_plus")

        # minus
        code = ('p(1) :- datetime_minus('
                '"Jan 5, 2014 10:00:00", "25:00:00", "2014-01-04 09:00:00")')
        check_true(code, "True datetime_minus")

        code = ('p(1) :- datetime_minus('
                '"Jan 5, 2014 10:00:00", 3600, "2014-01-05 09:00:00")')
        check_true(code, "True datetime_minus")

        code = ('p(1) :- datetime_minus('
                '"Jan 5, 2014 10:00:00", "9:00:00", "Jan 4, 2014 10:00:00")')
        check_false(code, "False datetime_minus")

        # to_seconds
        code = ('p(1) :- datetime_to_seconds('
                '"Jan 1, 1900 1:00:00", 3600)')
        check_true(code, "True datetime_to_seconds")

        code = ('p(1) :- datetime_to_seconds('
                '"Jan 1, 1900 1:00:00", 3601)')
        check_false(code, "False datetime_to_seconds")

        # extract_time
        code = ('p(1) :- extract_time('
                '"Jan 1, 1900 1:00:00", "01:00:00")')
        check_true(code, "True extract_time")

        code = ('p(1) :- extract_time('
                '"Jan 1, 1900 1:00:00", "02:00:00")')
        check_false(code, "False extract_time")

        # extract_date
        code = ('p(1) :- extract_date('
                '"Jan 1, 1900 1:00:00", "1900-01-01")')
        check_true(code, "True extract_date")

        code = ('p(1) :- extract_date('
                '"Jan 1, 1900 1:00:00", "2000-01-01")')
        check_false(code, "False extract_date")

        # pack_datetime
        code = ('p(1) :- pack_datetime(2000, 1, 1, 10, 5, 6, '
                '"2000-1-1 10:5:6")')
        check_true(code, "True pack_datetime")

        code = ('p(1) :- pack_datetime(2000, 1, 1, 10, 5, 6, '
                '"2000-1-1 10:5:20")')
        check_false(code, "False pack_datetime")

        # pack_date
        code = ('p(1) :- pack_date(2000, 1, 1, '
                '"2000-1-1")')
        check_true(code, "True pack_date")

        code = ('p(1) :- pack_date(2000, 1, 1, '
                '"2000-1-2")')
        check_false(code, "False pack_date")

        # pack_time
        code = ('p(1) :- pack_time(5, 6, 7, '
                '"5:6:7")')
        check_true(code, "True pack_time")

        code = ('p(1) :- pack_time(5, 6, 7, '
                '"10:6:7")')
        check_false(code, "False pack_time")

        # unpack_datetime
        code = ('p(1) :- unpack_datetime("2000-1-1 10:5:6", '
                '2000, 1, 1, 10, 5, 6)')
        check_true(code, "True unpack_datetime")

        code = ('p(1) :- unpack_datetime("2000-1-1 10:5:6", '
                '2000, 1, 1, 12, 5, 6)')
        check_false(code, "False unpack_datetime")

        # unpack_date
        code = ('p(1) :- unpack_date("2000-1-1 10:5:6", '
                '2000, 1, 1)')
        check_true(code, "True unpack_date")

        code = ('p(1) :- unpack_date("2000-1-1 10:5:6", '
                '2000, 1, 5)')
        check_false(code, "False unpack_date")

        # unpack_time
        code = ('p(1) :- unpack_time("2000-1-1 10:5:6", '
                '10, 5, 6)')
        check_true(code, "True unpack_time")

        code = ('p(1) :- unpack_time("2000-1-1 10:5:6", '
                '12, 5, 6)')
        check_false(code, "False unpack_time")

        # unpack_time
        code = 'p(1) :- now(x)'
        check_true(code, "True unpack_time")
