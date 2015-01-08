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

from congress.openstack.common import log as logging
from congress.policy.base import DATABASE_POLICY_TYPE
from congress.policy.base import NONRECURSIVE_POLICY_TYPE
from congress.policy import runtime
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
        run = runtime.Runtime()
        run.create_policy(NREC_THEORY, kind=NONRECURSIVE_POLICY_TYPE)
        run.create_policy(DB_THEORY, kind=DATABASE_POLICY_TYPE)
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
        run.insert('p(3,4)', th)
        run.insert('q(1,2,3)', th)
        run.insert('q(4,5,6)', th)
        ans = 'p(1) p(2) p(3,4) q(1,2,3) q(4,5,6)'
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

    def test_delete(self):
        """Test ability to delete policy statements."""
        th = NREC_THEORY

        # Multiple atoms
        run = self.prep_runtime('', 'Data deletion')
        run.insert('p(1)', th)
        run.insert('p(2)', th)
        run.insert('p(3,4)', th)
        run.insert('q(1,2,3)', th)
        run.insert('q(4,5,6)', th)
        run.delete('q(1,2,3)', th)
        run.delete('p(2)', th)
        ans = ('p(1) p(3,4) q(4,5,6)')
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

        # Negation
        run = self.prep_runtime('p(x) :- q(x), not r(x)'
                                'q(1)'
                                'q(2)'
                                'r(2)', target=th)
        self.check_equal(
            run.select('p(1)', target=th), "p(1)", "Monadic negation")
        self.check_equal(
            run.select('p(2)', target=th), "", "False monadic negation")
        self.check_equal(
            run.select('p(x)', target=th), "p(1)",
            "Variablized monadic negation")

        run = self.prep_runtime('p(x) :- q(x,y), r(z), not s(y,z)'
                                'q(1,1)'
                                'q(2,2)'
                                'r(4)'
                                'r(5)'
                                's(1,4)'
                                's(1,5)'
                                's(2,5)', target=th)
        self.check_equal(
            run.select('p(2)', target=th), "p(2)",
            "Binary negation with existentials")
        self.check_equal(
            run.select('p(1)', target=th), "",
            "False Binary negation with existentials")
        self.check_equal(
            run.select('p(x)', target=th), "p(2)",
            "False Binary negation with existentials")

        run = self.prep_runtime('p(x) :- q(x,y), s(y,z)'
                                's(y,z) :- r(y,w), t(z), not u(w,z)'
                                'q(1,1)'
                                'q(2,2)'
                                'r(1,4)'
                                't(7)'
                                'r(1,5)'
                                't(8)'
                                'u(5,8)', target=th)
        self.check_equal(
            run.select('p(1)', target=th), "p(1)",
            "Embedded negation with existentials")
        self.check_equal(
            run.select('p(2)', target=th), "",
            "False embedded negation with existentials")
        self.check_equal(
            run.select('p(x)', target=th), "p(1)",
            "False embedded negation with existentials")

        # variables
        run = self.prep_runtime('p(x) :- q(x0,x)'
                                'q(1,2)')
        self.check_equal(run.select('p(x)', target=th), 'p(2)',
                         "Using x0 in rule")

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
        self.assertEqual(len(lines), 10)

        # with included theory
        run = self.prep_runtime('')
        run.theory[NREC_THEORY].includes.append(run.theory[DB_THEORY])

        run.insert('p(x) :- q(x)', target=NREC_THEORY)
        run.insert('q(1)', target=DB_THEORY)
        (ans, trace) = run.select('p(x)', target=NREC_THEORY, trace=True)
        self.check_equal(ans, 'p(1) ', "Multiple theory lookup")
        LOG.debug(trace)
        lines = trace.split('\n')
        self.assertEqual(len(lines), 14)

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

    def test_dependency_graph(self):
        """Test that dependency graph gets updated correctly."""
        run = runtime.Runtime()
        run.debug_mode()

        run.create_policy('test')
        self.assertEqual(len(run.policy_object('test').dependency_graph), 0)

        run.insert('p(x) :- q(x), nova:q(x)', target='test')
        g = run.policy_object('test').dependency_graph
        self.assertEqual(len(g), 4)

        run.insert('p(x) :- s(x)', target='test')
        g = run.policy_object('test').dependency_graph
        self.assertEqual(len(g), 5)

        run.insert('q(x) :- nova:r(x)', target='test')
        g = run.policy_object('test').dependency_graph
        self.assertEqual(len(g), 7)

        run.delete('p(x) :- q(x), nova:q(x)', target='test')
        g = run.policy_object('test').dependency_graph
        self.assertEqual(len(g), 6)

        run.update([runtime.Event(helper.str2form('p(x) :- q(x), nova:q(x)'),
                                  target='test')])
        g = run.policy_object('test').dependency_graph
        self.assertEqual(len(g), 7)
