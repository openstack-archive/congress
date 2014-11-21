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
import unittest

from congress.openstack.common import log as logging
from congress.policy import runtime
from congress.tests import helper

LOG = logging.getLogger(__name__)

NREC_THEORY = 'non-recursive theory'


class TestRuntime(unittest.TestCase):
    """Tests for Runtime that are not specific to any theory."""

    def setUp(self):
        pass

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

        # TODO(thinrichs): add tests with other types of theories,
        # once we get those other theory types cleaned up.

    def test_get_arity(self):
        run = runtime.Runtime()
        run.debug_mode()
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
        run.theory['th1'] = runtime.NonrecursiveRuleTheory()
        run.theory['th2'] = runtime.NonrecursiveRuleTheory()

        events1 = [runtime.Event(formula=x, insert=True, target='th1')
                   for x in helper.str2pol("p(1) p(2) q(1) q(3)")]
        events2 = [runtime.Event(formula=x, insert=True, target='th2')
                   for x in helper.str2pol("r(1) r(2) t(1) t(4)")]
        run.update(events1 + events2)

        check_equal(run.select('p(x)', 'th1'), 'p(1) p(2)')
        check_equal(run.select('q(x)', 'th1'), 'q(1) q(3)')
        check_equal(run.select('r(x)', 'th2'), 'r(1) r(2)')
        check_equal(run.select('t(x)', 'th2'), 't(1) t(4)')

    def test_initialize(self):
        """Test initialize() functionality of Runtime."""
        run = runtime.Runtime()
        run.insert('p(1) p(2)')
        run.initialize(['p'], ['p(3)', 'p(4)'])
        e = helper.datalog_equal(run.select('p(x)'), 'p(3) p(4)')
        self.assertTrue(e)

    def test_dump_load(self):
        """Test if dumping/loading theories works properly."""
        run = runtime.Runtime()
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
        e = helper.datalog_equal(str(run.theory[run.DEFAULT_THEORY]),
                                 policy, 'Service theory dump/load')
        self.assertTrue(e)

    def test_single_policy(self):
        """Test ability to create/delete single policies."""
        # single policy
        run = runtime.Runtime()
        original = run.get_policy_names()
        run.create_policy('test1')
        run.insert('p(x) :- q(x)', 'test1')
        run.insert('q(1)', 'test1')
        self.assertEqual(
            run.select('p(x)', 'test1'), 'p(1)', 'Policy creation')
        self.assertEqual(
            run.select('p(x)', 'test1'), 'p(1)', 'Policy creation')
        run.delete_policy('test1')
        self.assertEqual(
            set(run.get_policy_names()), set(original), 'Policy deletion')

    def test_multi_policy(self):
        """Test ability to create/delete multiple policies."""
        # multiple policies
        run = runtime.Runtime()
        original = run.get_policy_names()
        run.create_policy('test2')
        run.create_policy('test3')
        self.assertEqual(
            set(run.get_policy_names()),
            set(original + ['test2', 'test3']),
            'Multi policy creation')
        run.delete_policy('test2')
        run.create_policy('test4')
        self.assertEqual(
            set(run.get_policy_names()),
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
        run.create_policy('test1', kind='nonrecursive')
        self.assertTrue(
            isinstance(run.get_policy('test1'),
            runtime.NonrecursiveRuleTheory),
            'Nonrecursive policy addition')
        run.create_policy('test2', kind='action')
        self.assertTrue(
            isinstance(run.get_policy('test2'),
            runtime.ActionTheory),
            'Action policy addition')

    def test_policy_errors(self):
        """Test errors for multiple policies."""
        # errors
        run = runtime.Runtime()
        self.assertRaises(KeyError, run.create_policy,
                          runtime.Runtime.DEFAULT_THEORY)
        self.assertRaises(KeyError, run.delete_policy, 'nonexistent')
        self.assertRaises(KeyError, run.get_policy, 'nonexistent')


class TestSimulate(unittest.TestCase):
    DEFAULT_THEORY = 'test_default'
    ACTION_THEORY = 'test_action'

    def prep_runtime(self, code=None, msg=None, target=None):
        if code is None:
            code = ""
        if target is None:
            target = self.DEFAULT_THEORY
        run = runtime.Runtime()
        run.theory[self.DEFAULT_THEORY] = runtime.NonrecursiveRuleTheory(
            name="default", abbr="Def")
        run.theory[self.ACTION_THEORY] = runtime.ActionTheory(
            name="action", abbr="Act")
        run.debug_mode()
        run.insert(code, target=target)
        return run

    def create(self, action_code, class_code):
        run = self.prep_runtime()

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
