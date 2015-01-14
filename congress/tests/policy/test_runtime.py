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

import os

from congress.openstack.common import log as logging
from congress.policy.base import ACTION_POLICY_TYPE
from congress.policy.base import DATABASE_POLICY_TYPE
from congress.policy.base import MATERIALIZED_POLICY_TYPE
from congress.policy.base import NONRECURSIVE_POLICY_TYPE
from congress.policy import runtime
from congress.tests import base
from congress.tests import helper

LOG = logging.getLogger(__name__)

NREC_THEORY = 'non-recursive theory'


class TestRuntime(base.TestCase):
    """Tests for Runtime that are not specific to any theory."""

    def check_equal(self, actual_string, correct_string, msg):
        self.assertTrue(helper.datalog_equal(
            actual_string, correct_string, msg))

    def test_theory_inclusion(self):
        """Test evaluation routines when one theory includes another."""
        # spread out across inclusions
        th1 = runtime.NonrecursiveRuleTheory()
        th2 = runtime.NonrecursiveRuleTheory()
        th3 = runtime.NonrecursiveRuleTheory()
        th1.includes.append(th2)
        th2.includes.append(th3)

        th1.insert(helper.str2form('p(x) :- q(x), r(x), s(2)'))
        th2.insert(helper.str2form('q(1)'))
        th1.insert(helper.str2form('r(1)'))
        th3.insert(helper.str2form('s(2)'))

        self.check_equal(
            helper.pol2str(th1.select(helper.str2form('p(x)'))),
            'p(1)', 'Data spread across inclusions')

    def test_get_arity(self):
        th = runtime.NonrecursiveRuleTheory()
        th.insert(helper.str2form('q(x) :- p(x)'))
        th.insert(helper.str2form('p(x) :- s(x)'))
        self.assertEqual(th.get_arity('p'), 1)
        self.assertEqual(th.get_arity('q'), 1)
        self.assertIsNone(th.get_arity('s'))
        self.assertIsNone(th.get_arity('missing'))

    def test_multi_policy_update(self):
        """Test updates that apply to multiple policies."""
        def check_equal(actual, correct):
            e = helper.datalog_equal(actual, correct)
            self.assertTrue(e)

        run = runtime.Runtime()
        run.create_policy('th1')
        run.create_policy('th2')

        events1 = [runtime.Event(formula=x, insert=True, target='th1')
                   for x in helper.str2pol("p(1) p(2) q(1) q(3)")]
        events2 = [runtime.Event(formula=x, insert=True, target='th2')
                   for x in helper.str2pol("r(1) r(2) t(1) t(4)")]
        run.update(events1 + events2)

        check_equal(run.select('p(x)', 'th1'), 'p(1) p(2)')
        check_equal(run.select('q(x)', 'th1'), 'q(1) q(3)')
        check_equal(run.select('r(x)', 'th2'), 'r(1) r(2)')
        check_equal(run.select('t(x)', 'th2'), 't(1) t(4)')

    def test_initialize_tables(self):
        """Test initialize_tables() functionality of Runtime."""
        run = runtime.Runtime()
        run.create_policy('test')
        run.insert('p(1) p(2)')
        run.initialize_tables(['p'], ['p(3)', 'p(4)'])
        e = helper.datalog_equal(run.select('p(x)'), 'p(3) p(4)')
        self.assertTrue(e)

    def test_dump_load(self):
        """Test if dumping/loading theories works properly."""
        run = runtime.Runtime()
        run.create_policy('test')
        run.debug_mode()
        policy = ('p(4,"a","bcdef ghi", 17.1) '
                  'p(5,"a","bcdef ghi", 17.1) '
                  'p(6,"a","bcdef ghi", 17.1)')
        run.insert(policy)

        full_path = os.path.realpath(__file__)
        path = os.path.dirname(full_path)
        path = os.path.join(path, "snapshot")
        run.dump_dir(path)
        run = runtime.Runtime()
        run.load_dir(path)
        e = helper.datalog_equal(run.theory['test'].content_string(),
                                 policy, 'Service theory dump/load')
        self.assertTrue(e)

    def test_single_policy(self):
        """Test ability to create/delete single policies."""
        # single policy
        run = runtime.Runtime()
        original = run.policy_names()
        run.create_policy('test1')
        run.insert('p(x) :- q(x)', 'test1')
        run.insert('q(1)', 'test1')
        self.assertEqual(
            run.select('p(x)', 'test1'), 'p(1)', 'Policy creation')
        self.assertEqual(
            run.select('p(x)', 'test1'), 'p(1)', 'Policy creation')
        run.delete_policy('test1')
        self.assertEqual(
            set(run.policy_names()), set(original), 'Policy deletion')

    def test_multi_policy(self):
        """Test ability to create/delete multiple policies."""
        # multiple policies
        run = runtime.Runtime()
        original = run.policy_names()
        run.create_policy('test2')
        run.create_policy('test3')
        self.assertEqual(
            set(run.policy_names()),
            set(original + ['test2', 'test3']),
            'Multi policy creation')
        run.delete_policy('test2')
        run.create_policy('test4')
        self.assertEqual(
            set(run.policy_names()),
            set(original + ['test3', 'test4']),
            'Multiple policy deletion')
        run.insert('p(x) :- q(x)  q(1)', 'test4')
        self.assertEqual(
            run.select('p(x)', 'test4'),
            'p(1)',
            'Multipolicy deletion select')

    def test_policy_types(self):
        """Test types for multiple policies."""
        # policy types
        run = runtime.Runtime()
        run.create_policy('test1', kind=NONRECURSIVE_POLICY_TYPE)
        self.assertTrue(isinstance(run.policy_object('test1'),
                        runtime.NonrecursiveRuleTheory),
                        'Nonrecursive policy addition')
        run.create_policy('test2', kind=ACTION_POLICY_TYPE)
        self.assertTrue(isinstance(run.policy_object('test2'),
                        runtime.ActionTheory),
                        'Action policy addition')
        run.create_policy('test3', kind=DATABASE_POLICY_TYPE)
        self.assertTrue(isinstance(run.policy_object('test3'),
                        runtime.Database),
                        'Database policy addition')
        run.create_policy('test4', kind=MATERIALIZED_POLICY_TYPE)
        self.assertTrue(isinstance(run.policy_object('test4'),
                        runtime.MaterializedViewTheory),
                        'Materialized policy addition')

    def test_policy_errors(self):
        """Test errors for multiple policies."""
        # errors
        run = runtime.Runtime()
        run.create_policy('existent')
        self.assertRaises(KeyError, run.create_policy, 'existent')
        self.assertRaises(KeyError, run.delete_policy, 'nonexistent')
        self.assertRaises(KeyError, run.policy_object, 'nonexistent')


class TestMultipolicyRules(base.TestCase):
    def test_external(self):
        """Test ability to write rules that span multiple policies."""
        # External theory
        run = runtime.Runtime()
        run.create_policy('test1')
        run.insert('q(1)', target='test1')
        run.insert('q(2)', target='test1')
        run.create_policy('test2')
        run.insert('p(x) :- test1:q(x)', target='test2')
        actual = run.select('p(x)', target='test2')
        e = helper.db_equal(actual, 'p(1) p(2)')
        self.assertTrue(e, "Basic")

    def test_multi_external(self):
        """Test multiple rules that span multiple policies."""
        run = runtime.Runtime()
        run.debug_mode()
        run.create_policy('test1')
        run.create_policy('test2')
        run.create_policy('test3')
        run.insert('p(x) :- test2:p(x)', target='test1')
        run.insert('p(x) :- test3:p(x)', target='test1')
        run.insert('p(1)', target='test2')
        run.insert('p(2)', target='test3')
        actual = run.select('p(x)', target='test1')
        e = helper.db_equal(actual, 'p(1) p(2)')
        self.assertTrue(e, "Multiple external rules with multiple policies")

    def test_external_current(self):
        """Test ability to write rules that span multiple policies."""
        # External theory plus current theory
        run = runtime.Runtime()
        run.create_policy('test1')
        run.insert('q(1)', target='test1')
        run.insert('q(2)', target='test1')
        run.create_policy('test2')
        run.insert('p(x) :- test1:q(x), r(x)', target='test2')
        run.insert('r(1)', target='test2')
        run.insert('r(2)', target='test2')
        actual = run.select('p(x)', target='test2')
        e = helper.db_equal(actual, 'p(1) p(2)')
        self.assertTrue(e, "Mixing external theories with current theory")

    def test_ignore_local(self):
        """Test ability to write rules that span multiple policies."""
        # Local table ignored
        run = runtime.Runtime()
        run.create_policy('test1')
        run.insert('q(1)', target='test1')
        run.insert('q(2)', target='test1')
        run.create_policy('test2')
        run.insert('p(x) :- test1:q(x), r(x)', target='test2')
        run.insert('q(3)', 'test2')
        run.insert('r(1)', target='test2')
        run.insert('r(2)', target='test2')
        run.insert('r(3)', target='test2')
        actual = run.select('p(x)', target='test2')
        e = helper.db_equal(actual, 'p(1) p(2)')
        self.assertTrue(e, "Local table ignored")

    def test_local(self):
        """Test ability to write rules that span multiple policies."""
        # Local table used
        run = runtime.Runtime()
        run.create_policy('test1')
        run.insert('q(1)', target='test1')
        run.insert('q(2)', target='test1')
        run.create_policy('test2')
        run.insert('p(x) :- test1:q(x), q(x)', target='test2')
        run.insert('q(2)', 'test2')
        actual = run.select('p(x)', target='test2')
        e = helper.db_equal(actual, 'p(2)')
        self.assertTrue(e, "Local table used")

    def test_multiple_external(self):
        """Test ability to write rules that span multiple policies."""
        # Multiple external theories
        run = runtime.Runtime()
        run.create_policy('test1')
        run.insert('q(1)', target='test1')
        run.insert('q(2)', target='test1')
        run.insert('q(3)', target='test1')
        run.create_policy('test2')
        run.insert('q(1)', target='test2')
        run.insert('q(2)', target='test2')
        run.insert('q(4)', target='test2')
        run.create_policy('test3')
        run.insert('p(x) :- test1:q(x), test2:q(x)', target='test3')
        actual = run.select('p(x)', target='test3')
        e = helper.db_equal(actual, 'p(1) p(2)')
        self.assertTrue(e, "Multiple external theories")

    def test_multiple_levels_external(self):
        """Test ability to write rules that span multiple policies."""
        # Multiple levels of external theories
        run = runtime.Runtime()
        run.debug_mode()
        run.create_policy('test1')
        run.insert('p(x) :- test2:q(x), test3:q(x)', target='test1')
        run.insert('s(3) s(1) s(2) s(4)', target='test1')
        run.create_policy('test2')
        run.insert('q(x) :- test4:r(x)', target='test2')
        run.create_policy('test3')
        run.insert('q(x) :- test1:s(x)', target='test3')
        run.create_policy('test4')
        run.insert('r(1)', target='test4')
        run.insert('r(2)', target='test4')
        run.insert('r(5)', target='test4')
        actual = run.select('p(x)', target='test1')
        e = helper.db_equal(actual, 'p(1) p(2)')
        self.assertTrue(e, "Multiple levels of external theories")

    def test_multi_policy_errors(self):
        """Test errors arising from rules in multiple policies."""
        run = runtime.Runtime()
        run.debug_mode()
        run.create_policy('test1')

        # policy in head of rule
        (permitted, errors) = run.insert('test2:p(x) :- q(x)', 'test1')
        self.assertFalse(permitted)
        self.assertTrue("should not reference any policy" in str(errors[0]))

        # policy in head of fact
        (permitted, errors) = run.insert('test2:p(1)', 'test1')
        self.assertFalse(permitted)
        self.assertTrue("should not reference any policy" in str(errors[0]))

        # recursion across policies
        run.insert('p(x) :- test2:q(x)', target='test1')
        run.create_policy('test2')
        (permit, errors) = run.insert('q(x) :- test1:p(x)', target='test2')
        self.assertFalse(permit, "Recursion across theories should fail")
        self.assertEqual(len(errors), 1)
        self.assertTrue("Rules are recursive" in str(errors[0]))

    def test_dependency_graph(self):
        """Test that dependency graph gets updated correctly."""
        run = runtime.Runtime()
        run.debug_mode()
        g = run.global_dependency_graph

        run.create_policy('test')

        run.insert('p(x) :- q(x), nova:q(x)', target='test')
        self.assertTrue(g.edge_in('test:p', 'nova:q', False))
        self.assertTrue(g.edge_in('test:p', 'test:q', False))

        run.insert('p(x) :- s(x)', target='test')
        self.assertTrue(g.edge_in('test:p', 'nova:q', False))
        self.assertTrue(g.edge_in('test:p', 'test:q', False))
        self.assertTrue(g.edge_in('test:p', 'test:s', False))

        run.insert('q(x) :- nova:r(x)', target='test')
        self.assertTrue(g.edge_in('test:p', 'nova:q', False))
        self.assertTrue(g.edge_in('test:p', 'test:q', False))
        self.assertTrue(g.edge_in('test:p', 'test:s', False))
        self.assertTrue(g.edge_in('test:q', 'nova:r', False))

        run.delete('p(x) :- q(x), nova:q(x)', target='test')
        self.assertTrue(g.edge_in('test:p', 'test:s', False))
        self.assertTrue(g.edge_in('test:q', 'nova:r', False))

        run.update([runtime.Event(helper.str2form('p(x) :- q(x), nova:q(x)'),
                                  target='test')])
        self.assertTrue(g.edge_in('test:p', 'nova:q', False))
        self.assertTrue(g.edge_in('test:p', 'test:q', False))
        self.assertTrue(g.edge_in('test:p', 'test:s', False))
        self.assertTrue(g.edge_in('test:q', 'nova:r', False))


class TestSimulate(base.TestCase):
    DEFAULT_THEORY = 'test_default'
    ACTION_THEORY = 'test_action'

    def prep_runtime(self, code=None, msg=None, target=None, theories=None):
        if code is None:
            code = ""
        if target is None:
            target = self.DEFAULT_THEORY
        run = runtime.Runtime()
        run.create_policy(self.DEFAULT_THEORY)
        run.create_policy(self.ACTION_THEORY, kind='action')
        if theories:
            for theory in theories:
                run.create_policy(theory)
        run.debug_mode()
        run.insert(code, target=target)
        return run

    def create(self, action_code, class_code, theories=None):
        run = self.prep_runtime(theories=theories)

        actth = self.ACTION_THEORY
        permitted, errors = run.insert(action_code, target=actth)
        self.assertTrue(permitted, "Error in action policy: {}".format(
            runtime.iterstr(errors)))

        defth = self.DEFAULT_THEORY
        permitted, errors = run.insert(class_code, target=defth)
        self.assertTrue(permitted, "Error in classifier policy: {}".format(
            runtime.iterstr(errors)))

        return run

    def check(self, run, action_sequence, query, correct, msg, delta=False):
        original_db = str(run.theory[self.DEFAULT_THEORY])
        actual = run.simulate(
            query, self.DEFAULT_THEORY, action_sequence,
            self.ACTION_THEORY, delta=delta)
        e = helper.datalog_equal(actual, correct)
        self.assertTrue(e, msg + " (Query results not correct)")
        e = helper.db_equal(
            str(run.theory[self.DEFAULT_THEORY]), original_db)
        self.assertTrue(e, msg + " (Rollback failed)")

    def test_multipolicy_state_1(self):
        """Test update sequence affecting datasources."""
        run = self.prep_runtime(theories=['nova', 'neutron'])
        run.insert('p(x) :- nova:p(x)', self.DEFAULT_THEORY)
        sequence = 'nova:p+(1) neutron:p+(2)'
        self.check(run, sequence, 'p(x)', 'p(1)', 'Separate theories')

    def test_multipolicy_state_2(self):
        """Test update sequence affecting datasources."""
        run = self.prep_runtime(theories=['nova', 'neutron'])
        run.insert('p(x) :- neutron:p(x)', self.DEFAULT_THEORY)
        run.insert('p(x) :- nova:p(x)', self.DEFAULT_THEORY)
        sequence = 'nova:p+(1) neutron:p+(2)'
        self.check(run, sequence, 'p(x)', 'p(1) p(2)', 'Separate theories 2')

    def test_multipolicy_state_3(self):
        """Test update sequence affecting datasources."""
        run = self.prep_runtime(theories=['nova', 'neutron'])
        run.insert('p(x) :- neutron:p(x)', self.DEFAULT_THEORY)
        run.insert('p(x) :- nova:p(x)', self.DEFAULT_THEORY)
        run.insert('p(1)', 'nova')
        sequence = 'nova:p+(1) neutron:p+(2)'
        self.check(run, sequence, 'p(x)', 'p(1) p(2)', 'Separate theories 3')
        self.check(run, '', 'p(x)', 'p(1)', 'Existing data separate theories')

    def test_multipolicy_action_sequence(self):
        """Test sequence updates with actions that impact multiple policies."""
        action_code = ('nova:p+(x) :- q(x)'
                       'neutron:p+(y) :- q(x), plus(x, 1, y)'
                       'action("q")')
        classify_code = 'p(x) :- nova:p(x)  p(3)'
        run = self.create(action_code, classify_code,
                          theories=['nova', 'neutron'])
        action_sequence = 'q(1)'
        self.check(run, action_sequence, 'p(x)', 'p(1) p(2) p(3)',
                   'Multi-policy actions')

    def test_action_sequence(self):
        """Test sequence updates with actions."""

        # Simple
        action_code = ('p+(x) :- q(x) action("q")')
        classify_code = 'p(2)'  # just some other data present
        run = self.create(action_code, classify_code)
        action_sequence = 'q(1)'
        self.check(run, action_sequence, 'p(x)', 'p(1) p(2)', 'Simple')

        # Noop does not break rollback
        action_code = ('p-(x) :- q(x)'
                       'action("q")')
        classify_code = ('')
        run = self.create(action_code, classify_code)
        action_sequence = 'q(1)'
        self.check(run, action_sequence, 'p(x)', '',
                   "Rollback handles Noop")

        # Add and delete
        action_code = ('action("act") '
                       'p+(x) :- act(x) '
                       'p-(y) :- act(x), r(x, y) ')
        classify_code = 'p(2) r(1, 2)'
        run = self.create(action_code, classify_code)
        action_sequence = 'act(1)'
        self.check(run, action_sequence, 'p(x)', 'p(1)', 'Add and delete')

        # insertion takes precedence over deletion
        action_code = ('p+(x) :- q(x)'
                       'p-(x) :- r(x)'
                       'action("q")')
        classify_code = ('')
        run = self.create(action_code, classify_code)
        # ordered so that consequences will be p+(1) p-(1)
        action_sequence = 'q(1), r(1) :- true'
        self.check(run, action_sequence, 'p(x)', 'p(1)',
                   "Deletion before insertion")

        # multiple action sequences 1
        action_code = ('p+(x) :- q(x)'
                       'p-(x) :- r(x)'
                       'action("q")'
                       'action("r")')
        classify_code = ('')
        run = self.create(action_code, classify_code)
        action_sequence = 'q(1) r(1)'
        self.check(run, action_sequence, 'p(x)', '',
                   "Multiple actions: inversion from {}")

        # multiple action sequences 2
        action_code = ('p+(x) :- q(x)'
                       'p-(x) :- r(x)'
                       'action("q")'
                       'action("r")')
        classify_code = ('p(1)')
        run = self.create(action_code, classify_code)
        action_sequence = 'q(1) r(1)'
        self.check(run, action_sequence, 'p(x)', '',
                   "Multiple actions: inversion from p(1), first is noop")

        # multiple action sequences 3
        action_code = ('p+(x) :- q(x)'
                       'p-(x) :- r(x)'
                       'action("q")'
                       'action("r")')
        classify_code = ('p(1)')
        run = self.create(action_code, classify_code)
        action_sequence = 'r(1) q(1)'
        self.check(run, action_sequence, 'p(x)', 'p(1)',
                   "Multiple actions: inversion from p(1), first is not noop")

        # multiple action sequences 4
        action_code = ('p+(x) :- q(x)'
                       'p-(x) :- r(x)'
                       'action("q")'
                       'action("r")')
        classify_code = ('')
        run = self.create(action_code, classify_code)
        action_sequence = 'r(1) q(1)'
        self.check(run, action_sequence, 'p(x)', 'p(1)',
                   "Multiple actions: inversion from {}, first is not noop")

        # Action with additional info
        action_code = ('p+(x,z) :- q(x,y), r(y,z)'
                       'action("q") action("r")')
        classify_code = 'p(1,2)'
        run = self.create(action_code, classify_code)
        action_sequence = 'q(1,2), r(2,3) :- true'
        self.check(run, action_sequence, 'p(x,y)', 'p(1,2) p(1,3)',
                   'Action with additional info')

    def test_state_rule_sequence(self):
        """Test state and rule update sequences."""
        # State update
        action_code = ''
        classify_code = 'p(1)'
        run = self.create(action_code, classify_code)
        action_sequence = 'p+(2)'
        self.check(run, action_sequence, 'p(x)', 'p(1) p(2)',
                   'State update')

        # Rule update
        action_code = ''
        classify_code = 'q(1)'
        run = self.create(action_code, classify_code)
        action_sequence = 'p+(x) :- q(x)'
        self.check(run, action_sequence, 'p(x)', 'p(1)',
                   'Rule update')

    def test_complex_sequence(self):
        """Test more complex sequences of updates."""
        # action with query
        action_code = ('p+(x, y) :- q(x, y)'
                       'action("q")')
        classify_code = ('r(1)')
        run = self.create(action_code, classify_code)
        action_sequence = 'q(x, 0) :- r(x)'
        self.check(run, action_sequence, 'p(x,y)', 'p(1,0)',
                   'Action with query')

        # action sequence with results
        action_code = ('p+(id, val) :- create(val)'
                       'p+(id, val) :- update(id, val)'
                       'p-(id, val) :- update(id, newval), p(id, val)'
                       'action("create")'
                       'action("update")'
                       'result(x) :- create(val), p+(x,val)')
        classify_code = 'hasval(val) :- p(x, val)'
        run = self.create(action_code, classify_code)
        action_sequence = 'create(0)  update(x,1) :- result(x)'
        self.check(run, action_sequence, 'hasval(x)', 'hasval(1)',
                   'Action sequence with results')

    def test_delta(self):
        """Test when asking for changes in query."""

        # Add
        action_code = ('action("q") '
                       'p+(x) :- q(x) ')
        classify_code = 'p(2)'  # just some other data present
        run = self.create(action_code, classify_code)
        action_sequence = 'q(1)'
        self.check(run, action_sequence, 'p(x)', 'p+(1)', 'Add',
                   delta=True)

        # Delete
        action_code = ('action("q") '
                       'p-(x) :- q(x) ')
        classify_code = 'p(1) p(2)'  # p(2): just some other data present
        run = self.create(action_code, classify_code)
        action_sequence = 'q(1)'
        self.check(run, action_sequence, 'p(x)', 'p-(1)', 'Delete',
                   delta=True)

        # Add and delete
        action_code = ('action("act") '
                       'p+(x) :- act(x) '
                       'p-(y) :- act(x), r(x, y) ')
        classify_code = 'p(2) r(1, 2) p(3)'  # p(3): just other data present
        run = self.create(action_code, classify_code)
        action_sequence = 'act(1)'
        self.check(run, action_sequence, 'p(x)', 'p+(1) p-(2)',
                   'Add and delete', delta=True)

    def test_key_value_schema(self):
        """Test action of key/value updates."""
        action_code = (
            'action("changeAttribute")'
            'server_attributes+(uid, name, newvalue) :- '
            'changeAttribute(uid, name, newvalue) '
            'server_attributes-(uid, name, oldvalue) :- '
            ' changeAttribute(uid, name, newvalue), '
            ' server_attributes(uid, name, oldvalue)')
        policy = 'error(uid) :- server_attributes(uid, name, 0)'

        run = self.create(action_code, policy)
        seq = 'changeAttribute(101, "cpu", 0)'
        self.check(run, seq, 'error(x)', 'error(101)',
                   'Basic error')

        run = self.create(action_code, policy)
        seq = 'changeAttribute(101, "cpu", 1)'
        self.check(run, seq, 'error(x)', '',
                   'Basic non-error')

        data = ('server_attributes(101, "cpu", 1)')
        run = self.create(action_code, policy + data)
        seq = 'changeAttribute(101, "cpu", 0)'
        self.check(run, seq, 'error(x)', 'error(101)',
                   'Overwrite existing to cause error')

        data = ('server_attributes(101, "cpu", 0)')
        run = self.create(action_code, policy + data)
        seq = 'changeAttribute(101, "cpu", 1)'
        self.check(run, seq, 'error(x)', '',
                   'Overwrite existing to eliminate error')

        data = ('server_attributes(101, "cpu", 0)'
                'server_attributes(101, "disk", 0)')
        run = self.create(action_code, policy + data)
        seq = 'changeAttribute(101, "cpu", 1)'
        self.check(run, seq, 'error(x)', 'error(101)',
                   'Overwrite existing but still error')
