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
from oslo_log import log as logging

from congress.datalog import base as datalog_base
from congress.datalog import compile
from congress.datalog import nonrecursive
from congress.policy_engines import agnostic
from congress.tests import base
from congress.tests import helper

LOG = logging.getLogger(__name__)

NREC_THEORY = 'non-recursive theory'
DB_THEORY = 'database'


class TestRuntime(base.TestCase):
    def prep_runtime(self, code=None, msg=None, target=None):
        # compile source
        if msg is not None:
            LOG.debug(msg)
        if code is None:
            code = ""
        if target is None:
            target = NREC_THEORY
        run = agnostic.Runtime()
        run.create_policy(NREC_THEORY,
                          kind=datalog_base.NONRECURSIVE_POLICY_TYPE)
        run.create_policy(DB_THEORY,
                          kind=datalog_base.DATABASE_POLICY_TYPE)
        run.debug_mode()
        run.insert(code, target=target)
        return run

    def check_equal(self, actual_string, correct_string, msg):
        self.assertTrue(helper.datalog_equal(
            actual_string, correct_string, msg))

    def test_indexing(self):
        th = NREC_THEORY
        run = self.prep_runtime('')
        for i in range(10):
            run.insert('r(%d)' % i, th)

        run.insert('s(5)', th)
        run.insert('p(x) :- r(x), s(x)', th)
        ans = 'p(5)'
        self.check_equal(run.select('p(5)', th), ans, 'Indexing')

    def test_insert(self):
        """Test ability to insert/delete sentences."""
        th = NREC_THEORY

        # insert single atom
        run = self.prep_runtime('')
        run.insert('p(1)', th)
        self.check_equal(run.content(th), 'p(1)', 'Atomic insertion')

        # insert collection of atoms
        run = self.prep_runtime('')
        run.insert('p(1)', th)
        run.insert('p(2)', th)
        run.insert('r(3,4)', th)
        run.insert('q(1,2,3)', th)
        run.insert('q(4,5,6)', th)
        ans = 'p(1) p(2) r(3,4) q(1,2,3) q(4,5,6)'
        self.check_equal(run.content(th), ans, 'Multiple atomic insertions')

        # insert collection of rules
        run = self.prep_runtime('')
        run.insert('p(x) :- q(x), r(x)', th)
        run.insert('p(x) :- r(x), s(x,y)', th)
        run.insert('s(x,y) :- t(x,v), m(v,y)', th)
        ans = ('p(x) :- q(x), r(x) '
               'p(x) :- r(x), s(x,y) '
               's(x,y) :- t(x,v), m(v,y) ')
        self.check_equal(run.content(th), ans, 'Rules')

        # insert rules and data
        run.insert('r(1)', th)
        run.insert('r(2)', th)
        run.insert('m(2,3)', th)
        run.insert('p(x) :- q(x), r(x)', th)
        run.insert('p(x) :- r(x), s(x,y)', th)
        run.insert('s(x,y) :- t(x,v), m(v,y)', th)
        ans = ('r(1) r(2) m(2,3) '
               'p(x) :- q(x), r(x) '
               'p(x) :- r(x), s(x,y) '
               's(x,y) :- t(x,v), m(v,y)')
        self.check_equal(run.content(th), ans, 'Rules')

        # insert modal rule
        run = self.prep_runtime('')
        run.insert('execute[p(x)] :- q(x), r(x)', th)
        run.insert('execute[p(x)] :- r(x), s(x, y)', th)
        run.insert('s(x,y) :- t(x, v), m(v, y)', th)
        ans = ('execute[p(x)] :- q(x), r(x) '
               'execute[p(x)] :- r(x), s(x, y) '
               's(x,y) :- t(x,v), m(v, y) ')
        self.check_equal(run.content(th), ans, 'Rules')

        # insert values for modal rule
        run.insert('r(1)', th)
        run.insert('r(2)', th)
        run.insert('m(2,3)', th)
        run.insert('execute[p(x)] :- q(x), r(x)', th)
        run.insert('execute[p(x)] :- r(x), s(x,y)', th)
        run.insert('s(x,y) :- t(x,v), m(v,y)', th)
        ans = ('r(1) r(2) m(2,3) '
               'execute[p(x)] :- q(x), r(x) '
               'execute[p(x)] :- r(x), s(x,y) '
               's(x,y) :- t(x,v), m(v,y)')
        self.check_equal(run.content(th), ans, 'Rules')

        # recursion
        run = self.prep_runtime("", "** Non-recursive Recursion **")
        permitted, changes = run.insert("p(x) :- p(x)", th)
        self.assertFalse(permitted)
        self.assertEqual(run.content(th), '')

        # non-stratified
        run = self.prep_runtime("", "** Stratification **")
        permitted, changes = run.insert("p(x) :- q(x), not p(x)", th)
        self.assertFalse(permitted)
        self.assertEqual(run.content(th), '')

        # confliction: rule-rule
        run = self.prep_runtime("")
        run.insert("q(x) :- p(x,y)", th)
        permitted, changes = run.insert("q(x,y) :- p(x,y)", th)
        self.assertEqual(len(changes), 1)
        self.assertFalse(permitted)

        # confliction: rule-fact
        run = self.prep_runtime("")
        run.insert("q(x) :- p(x,y)", th)
        permitted, changes = run.insert("q(1,3)", th)
        self.assertEqual(len(changes), 1)
        self.assertFalse(permitted)

        # confliction: fact-rule
        run = self.prep_runtime("")
        run.insert("q(1,3)", th)
        permitted, changes = run.insert("q(x) :- p(x,y)", th)
        self.assertEqual(len(changes), 1)
        self.assertFalse(permitted)

        # confliction: fact-rule
        run = self.prep_runtime("")
        run.insert("q(1,3)", th)
        permitted, changes = run.insert("q(1)", th)
        self.assertEqual(len(changes), 1)
        self.assertFalse(permitted)

        # confliction: body-confliction
        run = self.prep_runtime("")
        run.insert("q(1,3)", th)
        permitted, changes = run.insert("p(x,y) :- q(x,y,z)", th)
        self.assertEqual(len(changes), 1)
        self.assertFalse(permitted)

        # confliction: body-confliction1
        run = self.prep_runtime("")
        run.insert("p(x,y) :- q(x,y)", th)
        permitted, changes = run.insert("q(y) :- r(y)", th)
        self.assertEqual(len(changes), 1)
        self.assertFalse(permitted)

        # confliction: body-confliction2
        run = self.prep_runtime("")
        run.insert("p(x) :- q(x)", th)
        permitted, changes = run.insert("r(y) :- q(x,y)", th)
        self.assertEqual(len(changes), 1)
        self.assertFalse(permitted)

    def test_delete(self):
        """Test ability to delete policy statements."""
        th = NREC_THEORY

        # Multiple atoms
        run = self.prep_runtime('', 'Data deletion')
        run.insert('p(1)', th)
        run.insert('p(2)', th)
        run.insert('r(3,4)', th)
        run.insert('q(1,2,3)', th)
        run.insert('q(4,5,6)', th)
        run.delete('q(1,2,3)', th)
        run.delete('p(2)', th)
        ans = ('p(1) r(3,4) q(4,5,6)')
        self.check_equal(run.content(th), ans, 'Multiple atomic deletions')

        # Rules and data
        run = self.prep_runtime('', 'Rule/data deletion')
        run.insert('r(1)', th)
        run.insert('r(2)', th)
        run.insert('m(2,3)', th)
        run.insert('p(x) :- q(x), r(x)', th)
        run.insert('p(x) :- r(x), s(x,y)', th)
        run.insert('s(x,y) :- t(x,v), m(v,y)', th)
        run.delete('r(1)', th)
        run.delete('p(x) :- r(x), s(x,y)', th)

        ans = ('r(2) m(2,3) '
               'p(x) :- q(x), r(x) '
               's(x,y) :- t(x,v), m(v,y)')
        self.check_equal(run.content(th), ans, 'Rule/data deletions')
        run.insert('r(1)', th)
        run.insert('p(y) :- q(y), r(z)', th)
        ans = ('r(1) r(2) m(2,3) '
               'p(x) :- q(x), r(x) '
               'p(y) :- q(y), r(z) '
               's(x,y) :- t(x,v), m(v,y)')
        self.check_equal(run.content(th), ans,
                         'Rule/data inserts after deletes')

        # modal rule deletion
        run = self.prep_runtime('', 'Rule/Modal data deletion')
        run.insert('r(1)', th)
        run.insert('r(2)', th)
        run.insert('m(2,3)', th)
        run.insert('execute[p(x)] :- q(x), r(x)', th)
        run.insert('p(x) :- r(x), s(x,y)', th)
        run.insert('s(x,y) :- t(x,v), m(v,y)', th)
        run.delete('r(1)', th)
        run.delete('execute[p(x)] :- q(x), r(x)', th)
        ans = ('r(2) m(2,3) '
               'p(x) :- r(x), s(x, y) '
               's(x,y) :- t(x,v), m(v,y)')

        self.check_equal(run.content(th), ans, 'Rule/data deletions')
        # non-existent
        run = self.prep_runtime('', 'Nonexistent deletion')
        permitted, changes = run.delete('p(1)', th)
        self.assertEqual(len(changes), 0)

    def test_select(self):
        """Test query functionality, i.e. top-down evaluation."""
        th = NREC_THEORY
        run = self.prep_runtime('')
        run.insert('p(1)', target=th)
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
                         "Monadic, disjunctive rules")
        self.check_equal(run.select('p(x)', target=th), "p(1) p(2)",
                         "Variablized, monadic, disjunctive rules")
        self.check_equal(run.select('p(3)', target=th), "",
                         "False Monadic, disjunctive rules")

        run = self.prep_runtime('p(x) :- q(x), r(x)'
                                'q(1)'
                                'r(1)'
                                'r(2)'
                                'q(2)'
                                'q(3)', target=th)
        self.check_equal(run.select('p(1)', target=th), "p(1)",
                         "Monadic multiple literals in body")
        self.check_equal(run.select('p(x)', target=th), "p(1) p(2)",
                         "Monadic multiple literals in body variablized")
        self.check_equal(run.select('p(3)', target=th), "",
                         "False monadic multiple literals in body")

        run = self.prep_runtime('p(x) :- q(x), r(x)'
                                'q(1)'
                                'r(2)', target=th)
        self.check_equal(run.select('p(x)', target=th), "",
                         "False variablized monadic multiple literals in body")

        # Modal operator in rule
        run = self.prep_runtime('execute[p(x)] :- q(x), r(x)'
                                'q(1)'
                                'r(1)', target=th)
        self.check_equal(run.select('execute[p(x)]',
                                    target=th), "execute[p(1)]",
                         "Modal operator in Rule head")

        run = self.prep_runtime('p(x,y) :- q(x,z), r(z, y)'
                                'q(1,1)'
                                'q(1,2)'
                                'r(1,3)'
                                'r(1,4)'
                                'r(2,5)', target=th)
        self.check_equal(run.select('p(1,3)', target=th), "p(1,3)",
                         "Binary, existential rules 1")
        self.check_equal(run.select('p(x,y)', target=th),
                         "p(1,3) p(1,4) p(1,5)",
                         "Binary, existential rules 2")
        self.check_equal(run.select('p(1,1)', target=th), "",
                         "False binary, existential rules")
        self.check_equal(run.select('p(x,x)', target=th), "",
                         "False binary, variablized, existential rules")

        run = self.prep_runtime('p(x) :- q(x), r(x)'
                                'q(y) :- t(y), s(x)'
                                's(1)'
                                'r(2)'
                                't(2)', target=th)
        self.check_equal(run.select('p(2)', target=th), "p(2)",
                         "Distinct variable namespaces across rules")
        self.check_equal(run.select('p(x)', target=th), "p(2)",
                         "Distinct variable namespaces across rules")

        run = self.prep_runtime('p(x,y) :- q(x,z), r(z,y)'
                                'q(x,y) :- s(x,z), t(z,y)'
                                's(x,y) :- u(x,z), v(z,y)'
                                'u(0,2)'
                                'u(1,2)'
                                'v(2,3)'
                                't(3,4)'
                                'r(4,5)'
                                'r(4,6)', target=th)
        self.check_equal(run.select('p(1,5)', target=th), "p(1,5)",
                         "Tower of existential variables")
        self.check_equal(run.select('p(x,y)', target=th),
                         "p(0,5) p(1,5) p(1,6) p(0,6)",
                         "Tower of existential variables")
        self.check_equal(run.select('p(0,y)', target=th),
                         "p(0,5) p(0,6)",
                         "Tower of existential variables")

        run = self.prep_runtime('p(x) :- q(x), r(z)'
                                'r(z) :- s(z), q(x)'
                                's(1)'
                                'q(x) :- t(x)'
                                't(1)', target=th)
        self.check_equal(run.select('p(x)', target=th), 'p(1)',
                         "Two layers of existential variables")

        # variables
        run = self.prep_runtime('p(x) :- q(x0,x)'
                                'q(1,2)')
        self.check_equal(run.select('p(x)', target=th), 'p(2)',
                         "Using x0 in rule")

    def test_empty(self):
        # full empty
        th = nonrecursive.NonrecursiveRuleTheory()
        th.insert(compile.parse1('p(x) :- q(x)'))
        th.insert(compile.parse1('p(1)'))
        th.insert(compile.parse1('q(2)'))
        th.empty()
        self.assertEqual(len(th.content()), 0)

        # empty with tablenames
        th = nonrecursive.NonrecursiveRuleTheory()
        th.insert(compile.parse1('p(x) :- q(x)'))
        th.insert(compile.parse1('p(1)'))
        th.insert(compile.parse1('q(2)'))
        th.empty(['p'])
        e = helper.datalog_equal(th.content_string(), 'q(2)')
        self.assertTrue(e)

        # empty with invert
        th = nonrecursive.NonrecursiveRuleTheory()
        th.insert(compile.parse1('p(x) :- q(x)'))
        th.insert(compile.parse1('p(1)'))
        th.insert(compile.parse1('q(2)'))
        th.empty(['p'], invert=True)
        correct = ('p(x) :- q(x)   p(1)')
        e = helper.datalog_equal(th.content_string(), correct)
        self.assertTrue(e)

    def test_trace(self):
        """Test tracing during query."""
        # with single theory
        run = self.prep_runtime('')
        run.insert('p(x) :- q(x)', target=NREC_THEORY)
        run.insert('q(1)', target=NREC_THEORY)
        (ans, trace) = run.select('p(x)', target=NREC_THEORY, trace=True)
        self.check_equal(ans, 'p(1) ', "Simple lookup")
        LOG.debug(trace)
        lines = trace.split('\n')
        self.assertEqual(len(lines), 12)

        # with included theory
        run = self.prep_runtime('')
        run.theory[NREC_THEORY].includes.append(run.theory[DB_THEORY])

        run.insert('p(x) :- q(x)', target=NREC_THEORY)
        run.insert('q(1)', target=DB_THEORY)
        (ans, trace) = run.select('p(x)', target=NREC_THEORY, trace=True)
        self.check_equal(ans, 'p(1) ', "Tracing check")
        LOG.debug(trace)
        lines = trace.split('\n')
        self.assertEqual(len(lines), 16)

    def test_abduction(self):
        """Test abduction (computation of policy fragments)."""
        def check(query, code, tablenames, correct, msg, find_all=True):
            # We're interacting directly with the runtime's underlying
            #   theory b/c we haven't yet decided whether Abduce should
            #   be a top-level API call.
            run = self.prep_runtime()
            run.insert(code, target=NREC_THEORY)
            query = helper.str2form(query)
            actual = run.theory[NREC_THEORY].abduce(
                query, tablenames=tablenames, find_all=find_all)
            e = helper.datalog_same(helper.pol2str(actual), correct, msg)
            self.assertTrue(e)

        code = ('p(x) :- q(x), r(x)'
                'q(1)'
                'q(2)')
        check('p(x)', code, ['r'],
              'p(1) :- r(1)  p(2) :- r(2)', "Basic monadic")

        code = ('p(x) :- q(x), r(x)'
                'r(1)'
                'r(2)')
        check('p(x)', code, ['q'],
              'p(1) :- q(1)  p(2) :- q(2)', "Late, monadic binding")

        code = ('p(x) :- q(x)')
        check('p(x)', code, ['q'],
              'p(x) :- q(x)', "No binding")

        code = ('p(x) :- q(x), r(x)'
                'q(x) :- s(x)'
                'r(1)'
                'r(2)')
        check('p(x)', code, ['s'],
              'p(1) :- s(1)  p(2) :- s(2)', "Intermediate table")

        code = ('p(x) :- q(x), r(x)'
                'q(x) :- s(x)'
                'q(x) :- t(x)'
                'r(1)'
                'r(2)')
        check('p(x)', code, ['s', 't'],
              'p(1) :- s(1)  p(2) :- s(2)  p(1) :- t(1)  p(2) :- t(2)',
              "Intermediate, disjunctive table")

        code = ('p(x) :- q(x), r(x)'
                'q(x) :- s(x)'
                'q(x) :- t(x)'
                'r(1)'
                'r(2)')
        check('p(x)', code, ['s'],
              'p(1) :- s(1)  p(2) :- s(2)',
              "Intermediate, disjunctive table, but only some saveable")

        code = ('p(x) :- q(x), u(x), r(x)'
                'q(x) :- s(x)'
                'q(x) :- t(x)'
                'u(1)'
                'u(2)')
        check('p(x)', code, ['s', 't', 'r'],
              'p(1) :- s(1), r(1)  p(2) :- s(2), r(2)'
              'p(1) :- t(1), r(1)  p(2) :- t(2), r(2)',
              "Multiple support literals")

        code = ('p(x) :- q(x,y), s(x), r(y, z)'
                'r(2,3)'
                'r(2,4)'
                's(1)'
                's(2)')
        check('p(x)', code, ['q'],
              'p(1) :- q(1,2)   p(2) :- q(2,2)',
              "Existential variables that become ground")

        code = ('p(x) :- q(x,y), r(y, z)'
                'r(2,3)'
                'r(2,4)')
        check('p(x)', code, ['q'],
              'p(x) :- q(x,2)   p(x) :- q(x,2)',
              "Existential variables that do not become ground")

        code = ('p+(x) :- q(x), r(z)'
                'r(z) :- s(z), q(x)'
                's(1)')
        check('p+(x)', code, ['q'],
              'p+(x) :- q(x), q(x1)',
              "Existential variables with name collision")

    def test_modals(self):
        """Test that the modal operators work properly."""
        run = agnostic.Runtime()
        run.debug_mode()
        run.create_policy("test")
        run.insert('execute[p(x)] :- q(x)', 'test')
        run.insert('q(1)', 'test')
        self.assertTrue(helper.datalog_equal(
            run.select('execute[p(x)]', 'test'),
            'execute[p(1)]'))

    def test_modal_with_theory(self):
        """Test that the modal operators work properly with a theory."""
        run = agnostic.Runtime()
        run.debug_mode()
        run.create_policy("test")
        run.insert('execute[nova:p(x)] :- q(x)', 'test')
        run.insert('q(1)', 'test')
        self.assertTrue(helper.datalog_equal(
            run.select('execute[nova:p(x)]', 'test'),
            'execute[nova:p(1)]'))

    def test_policy_tablenames_filter_modal(self):
        execute_rule = 'execute[nova:servers.pause(x)] :- nova:servers(x)'
        run = self.prep_runtime(execute_rule)
        execute_policy = run.get_target(NREC_THEORY)
        tables = execute_policy.tablenames()
        self.assertEqual({'nova:servers.pause', 'nova:servers'}, set(tables))
        tables = execute_policy.tablenames(include_modal=False)
        self.assertEqual({'nova:servers'}, set(tables))
        tables = execute_policy.tablenames(include_modal=True)
        self.assertEqual({'nova:servers.pause', 'nova:servers'}, set(tables))

    def test_consequences(self):
        """Test computation of all atoms true in a theory."""
        def check(code, correct, msg):
            # We're interacting directly with the runtime's underlying
            #   theory b/c we haven't decided whether consequences should
            #   be a top-level API call.
            run = self.prep_runtime()
            run.insert(code, target=NREC_THEORY)
            actual = run.theory[NREC_THEORY].consequences()
            e = helper.datalog_same(helper.pol2str(actual), correct, msg)
            self.assertTrue(e)

        code = ('p1(x) :- q(x)'
                'q(1)'
                'q(2)')
        check(code, 'p1(1) p1(2) q(1) q(2)', 'Monadic')

        code = ('p1(x) :- q(x)'
                'p2(x) :- r(x)'
                'q(1)'
                'q(2)')
        check(code, 'p1(1) p1(2) q(1) q(2)', 'Monadic with empty tables')


class TestSelectNegation(base.TestCase):
    """Tests for negation within a select() routine."""
    def check(self, run, query_string, correct_string, msg):
        actual_string = run.select(query_string)
        self.assertTrue(helper.datalog_equal(
            actual_string, correct_string, msg))

    def test_monadic(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x), not r(x)'
                   'q(1)'
                   'q(2)'
                   'r(2)')

        self.check(run, 'p(1)', 'p(1)', "Monadic negation")
        self.check(run, 'p(2)', '', "False monadic negation")
        self.check(run, 'p(x)', 'p(1)',
                   "Variablized monadic negation")

    def test_binary(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x,y), r(z), not s(y,z)'
                   'q(1,1)'
                   'q(2,2)'
                   'r(4)'
                   'r(5)'
                   's(1,4)'
                   's(1,5)'
                   's(2,5)')
        self.check(run, 'p(2)', 'p(2)',
                   "Binary negation with existentials")
        self.check(run, 'p(1)', '',
                   "False Binary negation with existentials")
        self.check(run, 'p(x)', 'p(2)',
                   "False Binary negation with existentials")

    def test_depth(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x,y), s(y,z)'
                   's(y,z) :- r(y,w), t(z), not u(w,z)'
                   'q(1,1)'
                   'q(2,2)'
                   'r(1,4)'
                   't(7)'
                   'r(1,5)'
                   't(8)'
                   'u(5,8)')
        self.check(run, 'p(1)', 'p(1)',
                   "Embedded negation with existentials")
        self.check(run, 'p(2)', '',
                   "False embedded negation with existentials")
        self.check(run, 'p(x)', 'p(1)',
                   "False embedded negation with existentials")

    def test_mid_rule(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x), not s(x), r(x)'
                   'q(1) q(2) q(3) q(4) q(5) q(6)'
                   's(1) s(3) s(5)'
                   'r(2) r(6)')
        self.check(run, 'p(x)', 'p(2) p(6)',
                   "Multiple answers with monadic negation in middle of rule")


class TestArity(base.TestCase):
    def test_regular_parsing(self):
        th = nonrecursive.NonrecursiveRuleTheory()
        th.insert(compile.parse1('p(x) :- q(x, y)'))
        th.insert(compile.parse1('execute[r(x)] :- t(x, y)'))
        th.insert(compile.parse1('execute[nova:s(x, y)] :- u(x, y)'))
        th.insert(compile.parse1('execute[nova:noargs()] :- true'))
        self.assertEqual(th.arity('p'), 1)
        self.assertIsNone(th.arity('q'))
        self.assertIsNone(th.arity('r'))
        self.assertIsNone(th.arity('nova:s'))
        self.assertEqual(th.arity('r', modal='execute'), 1)
        self.assertEqual(th.arity('nova:s', modal='execute'), 2)
        self.assertEqual(th.arity('nova:noargs', modal='execute'), 0)

    def test_no_split_parsing(self):
        th = nonrecursive.NonrecursiveRuleTheory()
        th.insert(compile.parse1('nova:v(x, y) :- u(x, y)',
                                 use_modules=False))

        self.assertEqual(th.arity('nova:v'), 2)
        self.assertIsNone(th.arity('nova:v', modal='insert'))
        th.insert(compile.parse1('insert[neutron:v(x, y, z)] :- u(x, y)',
                                 use_modules=False))
        self.assertEqual(th.arity('nova:v'), 2)
        self.assertEqual(th.arity('neutron:v', modal='insert'), 3)

    def test_schema(self):
        th = nonrecursive.NonrecursiveRuleTheory(name='alice')
        th.schema = compile.Schema({'p': ('id', 'status', 'name')})
        self.assertEqual(th.arity('p'), 3)
        self.assertEqual(th.arity('alice:p'), 3)


class TestInstances(base.TestCase):
    """Tests for Runtime's delegation functionality."""
    def check(self, rule, data, correct, possibilities=None):
        rule = compile.parse1(rule, use_modules=False)
        data = compile.parse(data, use_modules=False)
        possibilities = possibilities or ''
        possibilities = compile.parse(possibilities, use_modules=False)
        possibilities = [compile.Rule(x, []) for x in possibilities]
        poss = {}
        for rule_lit in possibilities:
            if rule_lit.head.tablename() not in poss:
                poss[rule_lit.head.tablename()] = set([rule_lit])
            else:
                poss[rule_lit.head.tablename()].add(rule_lit)

        th = nonrecursive.MultiModuleNonrecursiveRuleTheory()
        th.debug_mode()
        for lit in data:
            th.insert(lit)
        result = th.instances(rule, poss)
        actual = " ".join(str(x) for x in result)
        e = helper.datalog_equal(actual, correct)
        self.assertTrue(e)

    def test_basic(self):
        rule = 'p(x) :- r(x)'
        data = 'r(1) r(2)'
        correct = ('p(1) :- r(1) '
                   'p(2) :- r(2)')
        self.check(rule, data, correct)

    def test_multiple_literals(self):
        rule = 'p(x) :- r(x), s(x)'
        data = 'r(1) r(2) r(3) s(2) s(3)'
        correct = ('p(2) :- r(2), s(2) '
                   'p(3) :- r(3), s(3)')
        self.check(rule, data, correct)

    def test_grounded(self):
        rule = 'p(x) :- t(5), r(x), s(x)'
        data = 'r(1) r(2) r(3) s(2) s(3)'
        correct = ('p(2) :- t(5), r(2), s(2) '
                   'p(3) :- t(5), r(3), s(3)')
        self.check(rule, data, correct)

    def test_builtins(self):
        rule = 'p(x, z) :- r(x), s(y), plus(x, y, z)'
        data = 'r(1) s(2) s(3)'
        correct = ('p(1, z) :- r(1), s(2), plus(1, 2, z) '
                   'p(1, z) :- r(1), s(3), plus(1, 3, z)')
        self.check(rule, data, correct)

    def test_builtins_reordered(self):
        rule = 'p(x, z) :- r(x), plus(x, y, z), s(y)'
        data = 'r(1) s(2) s(3)'
        correct = ('p(1, z) :- r(1), plus(1, 2, z), s(2) '
                   'p(1, z) :- r(1), plus(1, 3, z), s(3)')
        self.check(rule, data, correct)

    def test_modules(self):
        # Nonstandard here in that for instances, we are assuming all the
        #   data that we need is in the current policy, even if it references
        #   a different policy explicitly.
        rule = 'p(x) :- nova:r(x)'
        data = 'nova:r(1) nova:r(2)'
        correct = ('p(1) :- nova:r(1) '
                   'p(2) :- nova:r(2)')
        self.check(rule, data, correct)

    def test_possibilities(self):
        rule = 'p(x) :- q(x)'
        data = 'q(1) q(5)'
        poss = 'q(2) q(3)'
        correct = ('p(2) :- q(2) '
                   'p(3) :- q(3) ')
        self.check(rule, data, correct, poss)
