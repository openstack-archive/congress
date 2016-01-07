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
import mock
from oslo_log import log as logging

from congress.datalog import base as datalog_base
from congress.datalog import compile
from congress.datalog import database
from congress.datalog import materialized
from congress.datalog import nonrecursive
from congress.datalog import utility
from congress.db import db_policy_rules
from congress import exception
from congress.policy_engines import agnostic
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
        th1 = nonrecursive.NonrecursiveRuleTheory()
        th2 = nonrecursive.NonrecursiveRuleTheory()
        th3 = nonrecursive.NonrecursiveRuleTheory()
        th1.includes.append(th2)
        th2.includes.append(th3)

        th1.insert(helper.str2form('p(x) :- q(x), r(x), s(2)'))
        th2.insert(helper.str2form('q(1)'))
        th1.insert(helper.str2form('r(1)'))
        th3.insert(helper.str2form('s(2)'))

        self.check_equal(
            helper.pol2str(th1.select(helper.str2form('p(x)'))),
            'p(1)', 'Data spread across inclusions')

    def test_multi_policy_update(self):
        """Test updates that apply to multiple policies."""
        def check_equal(actual, correct):
            e = helper.datalog_equal(actual, correct)
            self.assertTrue(e)

        run = agnostic.Runtime()
        run.create_policy('th1')
        run.create_policy('th2')

        events1 = [compile.Event(formula=x, insert=True, target='th1')
                   for x in helper.str2pol("p(1) p(2) q(1) q(3)")]
        events2 = [compile.Event(formula=x, insert=True, target='th2')
                   for x in helper.str2pol("r(1) r(2) t(1) t(4)")]
        run.update(events1 + events2)

        check_equal(run.select('p(x)', 'th1'), 'p(1) p(2)')
        check_equal(run.select('q(x)', 'th1'), 'q(1) q(3)')
        check_equal(run.select('r(x)', 'th2'), 'r(1) r(2)')
        check_equal(run.select('t(x)', 'th2'), 't(1) t(4)')

    def test_initialize_tables(self):
        """Test initialize_tables() functionality of agnostic."""
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(1) p(2)')
        facts = [compile.Fact('p', (3,)), compile.Fact('p', (4,))]
        run.initialize_tables(['p'], facts)
        e = helper.datalog_equal(run.select('p(x)'), 'p(3) p(4)')
        self.assertTrue(e)

    def test_single_policy(self):
        """Test ability to create/delete single policies."""
        # single policy
        run = agnostic.Runtime()
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
        run = agnostic.Runtime()
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
        run = agnostic.Runtime()
        run.create_policy('test1', kind=datalog_base.NONRECURSIVE_POLICY_TYPE)
        self.assertIsInstance(run.policy_object('test1'),
                              nonrecursive.NonrecursiveRuleTheory,
                              'Nonrecursive policy addition')
        run.create_policy('test2', kind=datalog_base.ACTION_POLICY_TYPE)
        self.assertIsInstance(run.policy_object('test2'),
                              nonrecursive.ActionTheory,
                              'Action policy addition')
        run.create_policy('test3', kind=datalog_base.DATABASE_POLICY_TYPE)
        self.assertIsInstance(run.policy_object('test3'),
                              database.Database,
                              'Database policy addition')
        run.create_policy('test4', kind=datalog_base.MATERIALIZED_POLICY_TYPE)
        self.assertIsInstance(run.policy_object('test4'),
                              materialized.MaterializedViewTheory,
                              'Materialized policy addition')

    def test_policy_errors(self):
        """Test errors for multiple policies."""
        # errors
        run = agnostic.Runtime()
        run.create_policy('existent')
        self.assertRaises(KeyError, run.create_policy, 'existent')
        self.assertRaises(KeyError, run.delete_policy, 'nonexistent')
        self.assertRaises(KeyError, run.policy_object, 'nonexistent')

    def test_wrong_arity_index(self):
        run = agnostic.Runtime()
        run.create_policy('test1')
        run.insert('p(x) :- r(x), q(y, x)')
        run.insert('r(1)')
        run.insert('q(1,1)')
        # run query first to build index
        self.assertTrue(helper.datalog_equal(run.select('p(x)'), 'p(1)'))
        # next insert causes an exceptions since the thing we indexed on
        #   doesn't exist
        permitted, errs = run.insert('q(5)')
        self.assertFalse(permitted)
        self.assertEqual(len(errs), 1)
        self.assertIsInstance(errs[0], exception.PolicyException)
        # double-check that the error didn't result in an inconsistent state
        self.assertEqual(run.select('q(5)'), '')

    def test_get_tablename(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x)')
        run.insert('q(x) :- r(x)')
        run.insert('execute[nova:disconnect(x, y)] :- s(x, y)')
        tables = run.get_tablename('test', 'p')
        self.assertEqual({'p'}, set(tables))

        tables = run.get_tablename('test', 't')
        self.assertIsNone(tables)

        tables = run.get_tablenames('test')
        self.assertEqual({'p', 'q', 'r', 's'}, set(tables))

        tables = run.get_tablename('test', 'nova:disconnect')
        self.assertIsNone(tables)

    def test_tablenames(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x,y)')
        run.insert('q(x,y) :- r(x,y)')
        run.insert('t(x) :- q(x,y), r(x,z), equal(y, z)')
        run.insert('execute[nova:disconnect(x, y)] :- s(x, y)')
        tables = run.tablenames()
        self.assertEqual({'p', 'q', 'r', 's', 't', 'nova:disconnect'},
                         set(tables))
        tables = run.tablenames(include_builtin=True)
        self.assertEqual({'p', 'q', 'r', 's', 't', 'nova:disconnect', 'equal'},
                         set(tables))
        tables = run.tablenames(body_only=True)
        self.assertEqual({'q', 'r', 's'}, set(tables))
        tables = run.tablenames(include_modal=False)
        self.assertEqual({'p', 'q', 'r', 's', 't'}, set(tables))

    @mock.patch.object(db_policy_rules, 'add_policy', side_effect=Exception())
    def test_persistent_create_policy_with_db_exception(self, mock_add):
        run = agnostic.Runtime()
        with mock.patch.object(run, 'delete_policy') as mock_delete:
            policy_name = 'test_policy'
            self.assertRaises(exception.PolicyException,
                              run.persistent_create_policy,
                              policy_name)
            mock_add.assert_called_once_with(mock.ANY,
                                             policy_name,
                                             policy_name[:5],
                                             mock.ANY,
                                             'user',
                                             'nonrecursive')
            mock_delete.assert_called_once_with(policy_name)

    def test_tablenames_theory_name(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.create_policy('test2')
        run.insert('p(x) :- q(x)', 'test')
        run.insert('r(x) :- s(x)', 'test2')

        tables = run.tablenames()
        self.assertEqual(set(tables), set(['p', 'q', 'r', 's']))

        tables = run.tablenames(theory_name='test')
        self.assertEqual(set(tables), set(['p', 'q']))


class TestArity(base.TestCase):
    def test_same_table_diff_policies(self):
        run = agnostic.Runtime()
        run.create_policy('alice')
        run.create_policy('bob')
        run.insert('p(x) :- q(x, y)', 'alice')
        run.insert('p(x, y) :- r(x, y, z)', 'bob')
        self.assertEqual(1, run.arity('p', 'alice'))
        self.assertEqual(2, run.arity('p', 'bob'))

    def test_complex_table(self):
        run = agnostic.Runtime()
        run.create_policy('alice')
        run.create_policy('bob')
        run.insert('p(x) :- q(x, y)', 'alice')
        run.insert('p(x, y) :- r(x, y, z)', 'bob')
        self.assertEqual(1, run.arity('alice:p', 'bob'))
        self.assertEqual(1, run.arity('alice:p', 'alice'))

    def test_modals(self):
        run = agnostic.Runtime()
        run.create_policy('alice')
        run.insert('execute[nova:p(x)] :- q(x, y)', 'alice')
        self.assertEqual(1, run.arity('nova:p', 'alice', 'execute'))


class TestTriggerRegistry(base.TestCase):
    def setUp(self):
        super(TestTriggerRegistry, self).setUp()
        self.f = lambda tbl, old, new: old

    def test_trigger(self):
        trigger1 = agnostic.Trigger('table', 'policy', self.f)
        trigger2 = agnostic.Trigger('table', 'policy', self.f)
        trigger3 = agnostic.Trigger('table2', 'policy', self.f)
        trigger4 = agnostic.Trigger('table', 'policy', lambda x: x)

        s = set()
        s.add(trigger1)
        s.add(trigger2)
        s.add(trigger3)
        s.add(trigger4)
        self.assertEqual(4, len(s))
        s.discard(trigger1)
        self.assertEqual(3, len(s))
        s.discard(trigger2)
        self.assertEqual(2, len(s))
        s.discard(trigger3)
        self.assertEqual(1, len(s))
        s.discard(trigger4)
        self.assertEqual(0, len(s))

    def test_register(self):
        g = compile.RuleDependencyGraph()
        reg = agnostic.TriggerRegistry(g)

        # register
        p_trigger = reg.register_table('p', 'alice', self.f)
        triggers = reg.relevant_triggers(['alice:p'])
        self.assertEqual(triggers, set([p_trigger]))

        # register 2nd table
        q_trigger = reg.register_table('q', 'alice', self.f)
        p_triggers = reg.relevant_triggers(['alice:p'])
        self.assertEqual(p_triggers, set([p_trigger]))
        q_triggers = reg.relevant_triggers(['alice:q'])
        self.assertEqual(q_triggers, set([q_trigger]))

        # register again with table p
        p2_trigger = reg.register_table('p', 'alice', self.f)
        p_triggers = reg.relevant_triggers(['alice:p'])
        self.assertEqual(p_triggers, set([p_trigger, p2_trigger]))
        q_triggers = reg.relevant_triggers(['alice:q'])
        self.assertEqual(q_triggers, set([q_trigger]))

    def test_unregister(self):
        g = compile.RuleDependencyGraph()
        reg = agnostic.TriggerRegistry(g)
        p_trigger = reg.register_table('p', 'alice', self.f)
        q_trigger = reg.register_table('q', 'alice', self.f)
        self.assertEqual(reg.relevant_triggers(['alice:p']),
                         set([p_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:q']),
                         set([q_trigger]))
        # unregister p
        reg.unregister(p_trigger)
        self.assertEqual(reg.relevant_triggers(['alice:p']), set())
        self.assertEqual(reg.relevant_triggers(['alice:q']),
                         set([q_trigger]))
        # unregister q
        reg.unregister(q_trigger)
        self.assertEqual(reg.relevant_triggers(['alice:p']), set())
        self.assertEqual(reg.relevant_triggers(['alice:q']), set())
        # unregister nonexistent trigger
        self.assertRaises(KeyError, reg.unregister, p_trigger)
        self.assertEqual(reg.relevant_triggers(['alice:p']), set())
        self.assertEqual(reg.relevant_triggers(['alice:q']), set())

    def test_basic_dependency(self):
        g = compile.RuleDependencyGraph()
        reg = agnostic.TriggerRegistry(g)
        g.formula_insert(compile.parse1('p(x) :- q(x)'), 'alice')
        # register p
        p_trigger = reg.register_table('p', 'alice', self.f)
        self.assertEqual(reg.relevant_triggers(['alice:q']), set([p_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:p']), set([p_trigger]))

        # register q
        q_trigger = reg.register_table('q', 'alice', self.f)
        self.assertEqual(reg.relevant_triggers(['alice:q']),
                         set([p_trigger, q_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:p']),
                         set([p_trigger]))

    def test_complex_dependency(self):
        g = compile.RuleDependencyGraph()
        reg = agnostic.TriggerRegistry(g)
        g.formula_insert(compile.parse1('p(x) :- q(x)'), 'alice')
        g.formula_insert(compile.parse1('q(x) :- r(x), s(x)'), 'alice')
        g.formula_insert(compile.parse1('r(x) :- t(x, y), u(y)'), 'alice')
        g.formula_insert(compile.parse1('separate(x) :- separate2(x)'),
                         'alice')
        g.formula_insert(compile.parse1('notrig(x) :- notrig2(x)'), 'alice')
        p_trigger = reg.register_table('p', 'alice', self.f)
        sep_trigger = reg.register_table('separate', 'alice', self.f)

        # individual tables
        self.assertEqual(reg.relevant_triggers(['alice:p']), set([p_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:q']), set([p_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:r']), set([p_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:s']), set([p_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:t']), set([p_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:u']), set([p_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:notrig']), set())
        self.assertEqual(reg.relevant_triggers(['alice:notrig2']), set([]))
        self.assertEqual(reg.relevant_triggers(['alice:separate']),
                         set([sep_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:separate2']),
                         set([sep_trigger]))

        # groups of tables
        self.assertEqual(reg.relevant_triggers(['alice:p', 'alice:q']),
                         set([p_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:separate', 'alice:p']),
                         set([p_trigger, sep_trigger]))
        self.assertEqual(reg.relevant_triggers(['alice:notrig', 'alice:p']),
                         set([p_trigger]))

        # events: data
        event = compile.Event(compile.parse1('q(1)'), target='alice')
        self.assertEqual(reg.relevant_triggers([event]), set([p_trigger]))

        event = compile.Event(compile.parse1('u(1)'), target='alice')
        self.assertEqual(reg.relevant_triggers([event]), set([p_trigger]))

        event = compile.Event(compile.parse1('separate2(1)'), target='alice')
        self.assertEqual(reg.relevant_triggers([event]), set([sep_trigger]))

        event = compile.Event(compile.parse1('notrig2(1)'), target='alice')
        self.assertEqual(reg.relevant_triggers([event]), set([]))

        # events: rules
        event = compile.Event(compile.parse1('separate(x) :- q(x)'),
                              target='alice')
        self.assertEqual(reg.relevant_triggers([event]), set([sep_trigger]))

        event = compile.Event(compile.parse1('notrig(x) :- q(x)'),
                              target='alice')
        self.assertEqual(reg.relevant_triggers([event]), set([]))

        event = compile.Event(compile.parse1('r(x) :- q(x)'), target='alice')
        self.assertEqual(reg.relevant_triggers([event]), set([p_trigger]))

        # events: multiple rules and data
        event1 = compile.Event(compile.parse1('r(x) :- q(x)'), target='alice')
        event2 = compile.Event(compile.parse1('separate2(1)'), target='alice')
        self.assertEqual(reg.relevant_triggers([event1, event2]),
                         set([p_trigger, sep_trigger]))

        event1 = compile.Event(compile.parse1('r(x) :- q(x)'), target='alice')
        event2 = compile.Event(compile.parse1('notrigger2(1)'), target='alice')
        self.assertEqual(reg.relevant_triggers([event1, event2]),
                         set([p_trigger]))

    def test_triggers_by_table(self):
        t1 = agnostic.Trigger('p', 'alice', lambda x: x)
        t2 = agnostic.Trigger('p', 'alice', lambda x, y: x)
        t3 = agnostic.Trigger('q', 'alice', lambda x: x)
        triggers = [t1, t2, t3]
        table_triggers = agnostic.TriggerRegistry.triggers_by_table(triggers)
        self.assertTrue(len(table_triggers), 2)
        self.assertEqual(set(table_triggers[('p', 'alice', None)]),
                         set([t1, t2]))
        self.assertEqual(set(table_triggers[('q', 'alice', None)]),
                         set([t3]))

    def test_modals(self):
        g = compile.RuleDependencyGraph()
        reg = agnostic.TriggerRegistry(g)

        # register
        p_trigger = reg.register_table('p', 'alice', self.f, modal='exec')
        triggers = reg.relevant_triggers(['alice:p'])
        self.assertEqual(triggers, set([p_trigger]))

        # register 2nd table
        q_trigger = reg.register_table('q', 'alice', self.f)
        p_triggers = reg.relevant_triggers(['alice:p'])
        self.assertEqual(p_triggers, set([p_trigger]))
        q_triggers = reg.relevant_triggers(['alice:q'])
        self.assertEqual(q_triggers, set([q_trigger]))


class TestTriggers(base.TestCase):
    class MyObject(object):
        """A class with methods that have side-effects."""

        def __init__(self):
            self.value = 0
            self.equals = False

        def increment(self):
            """Used for counting number of times function invoked."""
            self.value += 1

        def equal(self, realold, realnew, old, new):
            """Used for checking if function is invoked with correct args."""
            self.equals = (realold == old and realnew == new)

    def test_empty(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.insert('p(1)')
        self.assertEqual(1, obj.value)

    def test_empty2(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(1)')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.delete('p(1)')
        self.assertEqual(1, obj.value)

    def test_empty3(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(1)')
        run.delete('p(1)')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.delete('p(1)')
        self.assertEqual(0, obj.value)

    def test_nochange(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(1)')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.insert('p(1)')
        self.assertEqual(0, obj.value)

    def test_batch_change(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        p1 = compile.parse1('p(1)')
        result = run.update([compile.Event(p1, target='test')])
        self.assertTrue(result[0], ("Update failed with errors: " +
                                    ";".join(str(x) for x in result[1])))
        self.assertEqual(1, obj.value)

    def test_dependency(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x)')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.insert('q(1)')
        self.assertEqual(1, obj.value)

    def test_dependency_batch_insert(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.insert('q(1)   p(x) :- q(x)')
        self.assertEqual(1, obj.value)

    def test_dependency_batch(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x)')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        rule = compile.parse1('q(x) :- r(x)')
        data = compile.parse1('r(1)')
        run.update([compile.Event(rule, target='test'),
                    compile.Event(data, target='test')])
        self.assertEqual(1, obj.value)

    def test_dependency_batch_delete(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x)')
        run.insert('q(x) :- r(x)')
        run.insert('r(1)')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.delete('q(x) :- r(x)')
        self.assertEqual(1, obj.value)

    def test_multi_dependency(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x)')
        run.insert('q(x) :- r(x), s(x)')
        run.insert('s(1)')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.insert('r(1)')
        self.assertEqual(1, obj.value)

    def test_negation(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x), not r(x)')
        run.insert('q(1)')
        run.insert('q(2)')
        run.insert('r(2)')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.insert('r(1)')
        self.assertEqual(1, obj.value)
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.delete('r(1)')
        self.assertEqual(3, obj.value)

    def test_anti_dependency(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x)')
        run.insert('r(1)')
        run.register_trigger('r', lambda tbl, old, new: obj.increment())
        run.insert('q(1)')
        self.assertEqual(0, obj.value)

    def test_old_new_correctness(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x)')
        run.insert('q(x) :- r(x), not s(x)')
        run.insert('r(1) r(2) r(3)')
        run.insert('s(2)')
        oldp = set(compile.parse('p(1) p(3)'))
        newp = set(compile.parse('p(1) p(2)'))
        run.register_trigger('p',
                             lambda tbl, old, new:
                             obj.equal(oldp, newp, old, new))
        run.update([compile.Event(compile.parse1('s(3)')),
                    compile.Event(compile.parse1('s(2)'), insert=False)])
        self.assertTrue(obj.equals)

    def test_unregister(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        trigger = run.register_trigger('p',
                                       lambda tbl, old, new: obj.increment())
        run.insert('p(1)')
        self.assertEqual(1, obj.value)
        run.unregister_trigger(trigger)
        self.assertEqual(1, obj.value)
        run.insert('p(2)')
        self.assertEqual(1, obj.value)
        self.assertRaises(KeyError, run.unregister_trigger, trigger)
        self.assertEqual(1, obj.value)

    def test_sequence(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.insert('p(x) :- q(x)')
        run.insert('q(1)')
        self.assertEqual(1, obj.value)

    def test_delete_data(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.create_policy('test')
        run.register_trigger('p', lambda tbl, old, new: obj.increment())
        run.insert('p(x) :- q(x, y), equal(y, 1)')
        run.insert('q(1, 1)')
        self.assertEqual(1, obj.value)
        run.delete('q(1, 1)')
        self.assertEqual(2, obj.value)

    def test_multi_policies(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.debug_mode()
        run.create_policy('alice')
        run.create_policy('bob')
        run.register_trigger('p',
                             lambda tbl, old, new: obj.increment(), 'alice')
        run.insert('p(x) :- bob:q(x)', target='alice')
        run.insert('q(1)', target='bob')
        self.assertEqual(1, obj.value)
        run.delete('q(1)', target='bob')
        self.assertEqual(2, obj.value)

    def test_modal(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.debug_mode()
        run.create_policy('alice')
        run.register_trigger('p', lambda tbl, old, new:
                             obj.increment(), 'alice', 'execute')
        run.insert('execute[p(x)] :- q(x)')
        self.assertEqual(0, obj.value)
        run.insert('q(1)')
        self.assertEqual(1, obj.value)
        run.insert('q(2)')
        self.assertEqual(2, obj.value)

    def test_initialize(self):
        obj = self.MyObject()
        run = agnostic.Runtime()
        run.debug_mode()
        run.create_policy('alice')
        run.register_trigger('p', lambda tbl, old, new:
                             obj.increment(), 'alice', 'execute')
        run.insert('execute[p(x)] :- q(x)')
        self.assertEqual(obj.value, 0)
        run.initialize_tables(['q'], [compile.Fact('q', [1])], 'alice')
        self.assertEqual(obj.value, 1)


class TestMultipolicyRules(base.TestCase):
    def test_external(self):
        """Test ability to write rules that span multiple policies."""
        # External theory
        run = agnostic.Runtime()
        run.create_policy('test1')
        run.insert('q(1)', target='test1')
        run.insert('q(2)', target='test1')
        run.create_policy('test2')
        run.insert('p(x) :- test1:q(x)', target='test2')
        actual = run.select('p(x)', target='test2')
        e = helper.db_equal('p(1) p(2)', actual)
        self.assertTrue("Basic", e)

    def test_multi_external(self):
        """Test multiple rules that span multiple policies."""
        run = agnostic.Runtime()
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
        self.assertTrue("Multiple external rules with multiple policies", e)

    def test_external_current(self):
        """Test ability to write rules that span multiple policies."""
        # External theory plus current theory
        run = agnostic.Runtime()
        run.create_policy('test1')
        run.insert('q(1)', target='test1')
        run.insert('q(2)', target='test1')
        run.create_policy('test2')
        run.insert('p(x) :- test1:q(x), r(x)', target='test2')
        run.insert('r(1)', target='test2')
        run.insert('r(2)', target='test2')
        actual = run.select('p(x)', target='test2')
        e = helper.db_equal(actual, 'p(1) p(2)')
        self.assertTrue("Mixing external theories with current theory", e)

    def test_ignore_local(self):
        """Test ability to write rules that span multiple policies."""
        # Local table ignored
        run = agnostic.Runtime()
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
        self.assertTrue("Local table ignored", e)

    def test_local(self):
        """Test ability to write rules that span multiple policies."""
        # Local table used
        run = agnostic.Runtime()
        run.create_policy('test1')
        run.insert('q(1)', target='test1')
        run.insert('q(2)', target='test1')
        run.create_policy('test2')
        run.insert('p(x) :- test1:q(x), q(x)', target='test2')
        run.insert('q(2)', 'test2')
        actual = run.select('p(x)', target='test2')
        e = helper.db_equal(actual, 'p(2)')
        self.assertTrue("Local table used", e)

    def test_multiple_external(self):
        """Test ability to write rules that span multiple policies."""
        # Multiple external theories
        run = agnostic.Runtime()
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
        run = agnostic.Runtime()
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

    def test_multipolicy_head(self):
        """Test SELECT with different policy in the head."""
        run = agnostic.Runtime()
        run.debug_mode()
        run.create_policy('test1', kind='action')
        run.create_policy('test2', kind='action')
        (permitted, errors) = run.insert('test2:p+(x) :- q(x)', 'test1')
        self.assertTrue(permitted, "modals with policy names must be allowed")
        run.insert('q(1)', 'test1')
        run.insert('p(2)', 'test2')
        actual = run.select('test2:p+(x)', 'test1')
        e = helper.db_equal(actual, 'test2:p+(1)')
        self.assertTrue(e, "Policy name in the head")

    def test_multipolicy_normal_errors(self):
        """Test errors arising from rules in multiple policies."""
        run = agnostic.Runtime()
        run.debug_mode()
        run.create_policy('test1')

        # policy in head of rule
        (permitted, errors) = run.insert('test2:p(x) :- q(x)', 'test1')
        self.assertFalse(permitted)
        self.assertTrue("should not reference any policy" in str(errors[0]))

        # policy in head of rule with update
        (permitted, errors) = run.insert('test2:p+(x) :- q(x)', 'test1')
        self.assertFalse(permitted)
        self.assertTrue("should not reference any policy" in str(errors[0]))

        # policy in head of rule with update
        (permitted, errors) = run.insert('test2:p-(x) :- q(x)', 'test1')
        self.assertFalse(permitted)
        self.assertTrue("should not reference any policy" in str(errors[0]))

        # policy in head of fact
        (permitted, errors) = run.insert('test2:p(1)', 'test1')
        self.assertFalse(permitted)
        self.assertTrue("should not reference any policy" in str(errors[0]))

        # policy in head of fact
        (permitted, errors) = run.insert('test2:p+(1)', 'test1')
        self.assertFalse(permitted)
        self.assertTrue("should not reference any policy" in str(errors[0]))

        # policy in head of fact
        (permitted, errors) = run.insert('test2:p-(1)', 'test1')
        self.assertFalse(permitted)
        self.assertTrue("should not reference any policy" in str(errors[0]))

        # recursion across policies
        run.insert('p(x) :- test2:q(x)', target='test1')
        run.create_policy('test2')
        (permit, errors) = run.insert('q(x) :- test1:p(x)', target='test2')
        self.assertFalse(permit, "Recursion across theories should fail")
        self.assertEqual(len(errors), 1)
        self.assertTrue("Rules are recursive" in str(errors[0]))

    def test_multipolicy_action_errors(self):
        """Test errors arising from rules in action policies."""
        run = agnostic.Runtime()
        run.debug_mode()
        run.create_policy('test1', kind='action')

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
        run = agnostic.Runtime()
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

        run.update([compile.Event(helper.str2form('p(x) :- q(x), nova:q(x)'),
                                  target='test')])
        self.assertTrue(g.edge_in('test:p', 'nova:q', False))
        self.assertTrue(g.edge_in('test:p', 'test:q', False))
        self.assertTrue(g.edge_in('test:p', 'test:s', False))
        self.assertTrue(g.edge_in('test:q', 'nova:r', False))

    def test_negation(self):
        """Test that negation when applied to a different policy works."""
        run = agnostic.Runtime()
        run.debug_mode()
        run.create_policy('alpha')
        run.create_policy('beta')
        run.insert('p(x) :- beta:q(x), not beta:q(x)', 'alpha')
        run.insert('q(1)', 'beta')
        self.assertEqual(run.select('p(x)', 'alpha'), '')

    def test_built_in(self):
        """Test that built_in function works."""
        run = agnostic.Runtime()
        run.debug_mode()
        run.create_policy('alpha')
        run.create_policy('beta')
        run.create_policy('sigma')
        run.insert('p(x1, x2) :- '
                   'beta:q(x1), sigma:r(x2), not equal(x1, x2)', 'alpha')
        run.insert('q(1)', 'beta')
        run.insert('r(1)', 'sigma')
        run.insert('r(3)', 'sigma')
        self.assertEqual(run.select('p(x1,x2)', 'alpha'), 'p(1, 3)')

    def test_schema_check(self):
        """Test that schema check in multiple policies works."""
        run = agnostic.Runtime()
        run.debug_mode()
        run.create_policy('alpha')
        run.create_policy('beta')
        run.insert('p(x,y) :- beta:q(x,y)', 'alpha')
        permitted, changes = run.insert('q(x) :- r(x)', 'beta')
        self.assertFalse(permitted)
        self.assertEqual(len(changes), 1)

    def test_same_rules(self):
        """Test that same rule insertion can be correctly dealt with."""
        run = agnostic.Runtime()
        run.debug_mode()
        policy = 'alpha'
        run.create_policy(policy)
        rulestr = 'p(x,y) :- q(x,y)'
        rule = compile.parse1(rulestr)
        run.insert(rulestr, policy)
        self.assertTrue(rule in run.policy_object(policy))
        self.assertTrue(
            rule.head.table.table in run.policy_object(policy).schema)
        run.insert(rulestr, policy)
        run.delete(rulestr, policy)
        self.assertFalse(rule in run.policy_object(policy))
        self.assertFalse(
            rule.head.table.table in run.policy_object(policy).schema)


class TestSelect(base.TestCase):
    def test_no_dups(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x)')
        run.insert('p(x) :- r(x)')
        run.insert('q(1)')
        run.insert('r(1)')
        self.assertEqual(run.select('p(x)'), 'p(1)')


class TestPolicyCreationDeletion(base.TestCase):
    def test_policy_creation_after_ref(self):
        """Test ability to write rules that span multiple policies."""
        # Local table used
        run = agnostic.Runtime()
        run.create_policy('test1')
        run.insert('p(x) :- test2:q(x)', 'test1')
        run.create_policy('test2')
        run.insert('q(1)', 'test2')
        actual = run.select('p(x)', 'test1')
        e = helper.db_equal(actual, 'p(1)')
        self.assertTrue(e, "Creation after reference")

    def test_policy_deletion_after_ref(self):
        """Test ability to write rules that span multiple policies."""
        # Local table used
        run = agnostic.Runtime()
        run.create_policy('test1')
        run.insert('p(x) :- test2:q(x)', 'test1')
        # ensuring this code runs, without causing an error
        run.create_policy('test2')
        run.delete_policy('test2')
        # add the policy back, this time checking for dangling refs
        run.create_policy('test2')
        self.assertRaises(exception.DanglingReference, run.delete_policy,
                          'test2', disallow_dangling_refs=True)

    def test_policy_deletion_dependency_graph(self):
        """Ensure dependency graph is properly updated when deleting policy."""
        run = agnostic.Runtime()
        run.create_policy('alice')
        run.insert('p(x) :- q(x)')
        LOG.info("graph: \n%s", run.global_dependency_graph)
        self.assertTrue(run.global_dependency_graph.edge_in(
            'alice:p', 'alice:q', False))
        # don't delete rules first--just delete policy
        run.delete_policy('alice')
        self.assertEqual(len(run.global_dependency_graph), 0)


class TestDependencyGraph(base.TestCase):
    def test_fact_insert(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        facts = [compile.Fact('p', [1])]
        run.initialize_tables([], facts)
        self.assertFalse(run.global_dependency_graph.node_in('test:p'))

    def test_atom_insert(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(1)')
        self.assertFalse(run.global_dependency_graph.node_in('test:p'))

    def test_rule_noop(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('q(1) :- p(1)')
        run.delete('q(2) :- p(2)')
        self.assertTrue(run.global_dependency_graph.node_in('test:p'))
        self.assertTrue(run.global_dependency_graph.node_in('test:q'))
        self.assertTrue(run.global_dependency_graph.edge_in(
            'test:q', 'test:p', False))

    def test_atom_deletion(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('q(x) :- p(x)')
        run.delete('p(1)')
        run.delete('p(1)')
        # actually just testing that no error is thrown
        self.assertFalse(run.global_dependency_graph.has_cycle())


class TestSimulate(base.TestCase):
    DEFAULT_THEORY = 'test_default'
    ACTION_THEORY = 'test_action'

    def prep_runtime(self, code=None, msg=None, target=None, theories=None):
        if code is None:
            code = ""
        if target is None:
            target = self.DEFAULT_THEORY
        run = agnostic.Runtime()
        run.create_policy(self.DEFAULT_THEORY, abbr='default')
        run.create_policy(self.ACTION_THEORY, abbr='action', kind='action')
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
            utility.iterstr(errors)))

        defth = self.DEFAULT_THEORY
        permitted, errors = run.insert(class_code, target=defth)
        self.assertTrue(permitted, "Error in classifier policy: {}".format(
            utility.iterstr(errors)))

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
                       'ceilometer:p+(y) :- q(x), plus(x, 5, y)'
                       'action("q")')
        classify_code = 'p(x) :- nova:p(x)  p(x) :- neutron:p(x) p(3)'
        run = self.create(action_code, classify_code,
                          theories=['nova', 'neutron', 'ceilometer'])
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

    def test_delta_add(self):
        """Test when asking for changes in query."""
        action_code = ('action("q") '
                       'p+(x) :- q(x) ')
        classify_code = 'p(2)'  # just some other data present
        run = self.create(action_code, classify_code)
        action_sequence = 'q(1)'
        self.check(run, action_sequence, 'p(x)', 'p+(1)', 'Add',
                   delta=True)

    def test_delta_delete(self):
        """Test when asking for changes in query."""
        action_code = ('action("q") '
                       'p-(x) :- q(x) ')
        classify_code = 'p(1) p(2)'  # p(2): just some other data present
        run = self.create(action_code, classify_code)
        action_sequence = 'q(1)'
        self.check(run, action_sequence, 'p(x)', 'p-(1)', 'Delete',
                   delta=True)

    def test_delta_add_delete(self):
        """Test when asking for changes in query."""
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

    def test_duplicates(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x)')
        run.insert('p(x) :- r(x)')
        run.insert('q(1)')
        run.insert('r(1)')
        self.assertEqual(run.simulate('p(x)', 'test', '', 'test'), 'p(1)')


class TestActionExecution(base.TestCase):
    class FakeCage(object):
        def __init__(self, name):
            self.name = name

        def service_object(self, name):
            if self.name == name:
                return self
            else:
                return None

    def test_insert_rule_insert_data(self):
        args = {}
        args['d6cage'] = TestActionExecution.FakeCage('test')
        args['rootdir'] = None
        args['log_actions_only'] = True
        run = agnostic.DseRuntime(
            name='test', keys='', inbox=None, datapath=None, args=args)

        run.request = mock.Mock()
        run.request.return_value = 'mocked request'

        run.create_policy('test')
        run.debug_mode()
        run.insert('execute[p(x)] :- q(x)')
        self.assertEqual(len(run.logger.messages), 0, "Improper action logged")
        run.insert('q(1)')
        self.assertEqual(len(run.logger.messages), 1, "No action logged")
        self.assertEqual(run.logger.messages[0], 'Executing test:p(1)')

        expected_args = ('test', 'p')
        expected_kwargs = {'args': {'positional': [1]}}
        args, kwargs = run.request.call_args_list[0]

        self.assertEqual(expected_args, args)
        self.assertEqual(expected_kwargs, kwargs)

    def test_insert_data_insert_rule(self):
        args = {}
        args['d6cage'] = TestActionExecution.FakeCage('test')
        args['rootdir'] = None
        args['log_actions_only'] = True
        run = agnostic.DseRuntime(
            name='test', keys='', inbox=None, datapath=None, args=args)

        run.request = mock.Mock()
        run.request.return_value = 'mocked request'

        run.create_policy('test')
        run.debug_mode()
        run.insert('q(1)')
        self.assertEqual(len(run.logger.messages), 0, "Improper action logged")
        run.insert('execute[p(x)] :- q(x)')
        self.assertEqual(len(run.logger.messages), 1, "No action logged")
        self.assertEqual(run.logger.messages[0], 'Executing test:p(1)')

        expected_args = ('test', 'p')
        expected_kwargs = {'args': {'positional': [1]}}
        args, kwargs = run.request.call_args_list[0]

        self.assertEqual(expected_args, args)
        self.assertEqual(expected_kwargs, kwargs)

    def test_insert_data_insert_rule_delete_data(self):
        args = {}
        args['d6cage'] = TestActionExecution.FakeCage('test')
        args['rootdir'] = None
        args['log_actions_only'] = True
        run = agnostic.DseRuntime(
            name='test', keys='', inbox=None, datapath=None, args=args)

        run.request = mock.Mock()
        run.request.return_value = 'mocked request'

        run.create_policy('test')
        run.debug_mode()
        run.insert('q(1)')
        self.assertEqual(len(run.logger.messages), 0, "Improper action logged")
        run.insert('execute[p(x)] :- q(x)')
        self.assertEqual(len(run.logger.messages), 1, "No action logged")
        self.assertEqual(run.logger.messages[0], 'Executing test:p(1)')
        run.delete('q(1)')
        self.assertEqual(len(run.logger.messages), 1, "Delete failure")
        self.assertEqual(run.logger.messages[0], 'Executing test:p(1)')

        expected_args = ('test', 'p')
        expected_kwargs = {'args': {'positional': [1]}}
        args, kwargs = run.request.call_args_list[0]

        self.assertEqual(expected_args, args)
        self.assertEqual(expected_kwargs, kwargs)

    def test_insert_data_insert_rule_delete_rule(self):
        args = {}
        args['d6cage'] = TestActionExecution.FakeCage('test')
        args['rootdir'] = None
        args['log_actions_only'] = True
        run = agnostic.DseRuntime(
            name='test', keys='', inbox=None, datapath=None, args=args)

        run.request = mock.Mock()
        run.request.return_value = 'mocked request'

        run.create_policy('test')
        run.debug_mode()
        run.insert('q(1)')
        self.assertEqual(len(run.logger.messages), 0, "Improper action logged")
        run.insert('execute[p(x)] :- q(x)')
        self.assertEqual(len(run.logger.messages), 1, "No action logged")
        self.assertEqual(run.logger.messages[0], 'Executing test:p(1)')
        run.delete('execute[p(x)] :- q(x)')
        self.assertEqual(len(run.logger.messages), 1, "Delete failure")
        self.assertEqual(run.logger.messages[0], 'Executing test:p(1)')

        expected_args = ('test', 'p')
        expected_kwargs = {'args': {'positional': [1]}}
        args, kwargs = run.request.call_args_list[0]

        self.assertEqual(expected_args, args)
        self.assertEqual(expected_kwargs, kwargs)

    def test_insert_data_insert_rule_noop_insert(self):
        args = {}
        args['d6cage'] = TestActionExecution.FakeCage('test')
        args['rootdir'] = None
        args['log_actions_only'] = True
        run = agnostic.DseRuntime(
            name='test', keys='', inbox=None, datapath=None, args=args)

        run.request = mock.Mock()
        run.request.return_value = 'mocked request'

        run.create_policy('test')
        run.debug_mode()
        run.insert('q(1)')
        self.assertEqual(len(run.logger.messages), 0, "Improper action logged")
        run.insert('execute[p(x)] :- q(x)')
        self.assertEqual(len(run.logger.messages), 1, "No action logged")
        self.assertEqual(run.logger.messages[0], 'Executing test:p(1)')
        run.insert('q(1)')
        self.assertEqual(len(run.logger.messages), 1, "Improper action logged")
        self.assertEqual(run.logger.messages[0], 'Executing test:p(1)')

        expected_args = ('test', 'p')
        expected_kwargs = {'args': {'positional': [1]}}
        args, kwargs = run.request.call_args_list[0]

        self.assertEqual(expected_args, args)
        self.assertEqual(expected_kwargs, kwargs)

    def test_disjunction(self):
        args = {}
        args['d6cage'] = TestActionExecution.FakeCage('test')
        args['rootdir'] = None
        args['log_actions_only'] = True
        run = agnostic.DseRuntime(
            name='test', keys='', inbox=None, datapath=None, args=args)

        run.request = mock.Mock()
        run.request.return_value = 'mocked request'

        run.create_policy('test')
        run.debug_mode()
        run.insert('execute[p(x)] :- q(x)')
        run.insert('execute[p(x)] :- r(x)')
        self.assertEqual(len(run.logger.messages), 0, "Improper action logged")
        run.insert('q(1)')
        self.assertEqual(len(run.logger.messages), 1, "No action logged")
        self.assertEqual(run.logger.messages[0], 'Executing test:p(1)')
        run.insert('r(1)')
        self.assertEqual(len(run.logger.messages), 1, "Improper action logged")
        self.assertEqual(run.logger.messages[0], 'Executing test:p(1)')

        expected_args = ('test', 'p')
        expected_kwargs = {'args': {'positional': [1]}}
        args, kwargs = run.request.call_args_list[0]

        self.assertEqual(expected_args, args)
        self.assertEqual(expected_kwargs, kwargs)

    def test_multiple_instances(self):
        args = {}
        args['d6cage'] = TestActionExecution.FakeCage('test')
        args['rootdir'] = None
        args['log_actions_only'] = True
        run = agnostic.DseRuntime(
            name='test', keys='', inbox=None, datapath=None, args=args)

        run.request = mock.Mock()
        run.request.return_value = 'mocked request'

        run.create_policy('test')
        run.debug_mode()
        run.insert('q(1)')
        run.insert('q(2)')
        self.assertEqual(len(run.logger.messages), 0, "Improper action logged")
        run.insert('execute[p(x)] :- q(x)')
        self.assertEqual(len(run.logger.messages), 2, "No action logged")
        actualset = set([u'Executing test:p(1)', u'Executing test:p(2)'])
        self.assertEqual(actualset, set(run.logger.messages))

        expected_args_list = [
            [('test', 'p'), {'args': {'positional': [1]}}],
            [('test', 'p'), {'args': {'positional': [2]}}],
        ]

        for args, kwargs in run.request.call_args_list:
            self.assertTrue([args, kwargs] in expected_args_list)
            expected_args_list.remove([args, kwargs])

    def test_disabled_execute_action(self):
        args = {}
        args['d6cage'] = None
        args['rootdir'] = None
        args['log_actions_only'] = False
        run = agnostic.DseRuntime(
            name='test', keys='', inbox=None, datapath=None, args=args)

        run.request = mock.Mock()
        run.request.return_value = 'mocked request'

        service_name = 'test-service'
        action = 'non_executable_action'
        action_args = {'positional': ['p_arg1'],
                       'named': {'key1': 'value1'}}

        run.execute_action(service_name, action, action_args)
        self.assertFalse(run.request.called)


class TestDisabledRules(base.TestCase):
    """Tests for Runtime's ability to enable/disable rules."""
    # insertions
    def test_insert_enabled(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        schema = compile.Schema({'q': ('id', 'name', 'status')})
        run.set_schema('test', schema)
        obj = run.policy_object('test')
        run.insert('p(x) :- q(id=x)')
        self.assertEqual(len(run.error_events), 0)
        self.assertEqual(len(run.disabled_events), 0)
        self.assertEqual(len(obj.content()), 1)

    def test_insert_disabled(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        obj = run.policy_object('test')
        run.insert('p(x) :- q(id=x)')
        self.assertEqual(len(run.disabled_events), 1)
        self.assertEqual(len(obj.content()), 0)

    def test_insert_errors(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        schema = compile.Schema({'q': ('name', 'status')})
        run.set_schema('test', schema)
        obj = run.policy_object('test')
        permitted, errors = run.insert('p(x) :- q(id=x)')
        self.assertFalse(permitted)
        errstring = " ".join(str(x) for x in errors)
        self.assertTrue("column name id does not exist" in errstring)
        self.assertEqual(len(run.error_events), 0)
        self.assertEqual(len(run.disabled_events), 0)
        self.assertEqual(len(obj.content()), 0)

    def test_insert_set_schema_disabled(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        obj = run.policy_object('test')
        run.insert('p(x) :- q(id=x)')   # rule is disabled
        self.assertEqual(len(run.disabled_events), 1)
        schema = compile.Schema({'q': ('id', 'name', 'status')})
        run.set_schema('test', schema)
        self.assertEqual(len(run.error_events), 0)
        self.assertEqual(len(run.disabled_events), 0)
        self.assertEqual(len(obj.content()), 1)

    def test_insert_set_schema_disabled_multiple(self):
        # insert rule that gets disabled
        run = agnostic.Runtime()
        run.create_policy('test')
        run.create_policy('nova')
        obj = run.policy_object('test')
        run.insert('p(x) :- q(id=x), nova:r(id=x)', 'test')
        self.assertEqual(len(run.disabled_events), 1)
        # set first schema
        schema = compile.Schema({'q': ('id', 'name', 'status')})
        run.set_schema('test', schema)
        self.assertEqual(len(run.error_events), 0)
        self.assertEqual(len(run.disabled_events), 1)
        self.assertEqual(len(obj.content()), 0)
        # set second schema
        schema = compile.Schema({'r': ('id', 'name', 'status')})
        run.set_schema('nova', schema)
        self.assertEqual(len(run.error_events), 0)
        self.assertEqual(len(run.disabled_events), 0)
        self.assertEqual(len(obj.content()), 1)

    def test_insert_set_schema_errors(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        obj = run.policy_object('test')
        run.insert('p(x) :- q(id=x)')   # rule is disabled
        self.assertEqual(len(run.disabled_events), 1)
        schema = compile.Schema({'q': ('name', 'status')},)
        run.set_schema('test', schema)
        self.assertEqual(len(run.error_events), 1)
        self.assertEqual(len(run.disabled_events), 0)
        self.assertEqual(len(obj.content()), 0)

    def test_insert_inferred_schema_errors(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        run.insert('p(x) :- q(x)')
        permitted, errs = run.insert('q(1,2)')
        self.assertFalse(permitted)

    # deletions
    def test_delete_enabled(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        schema = compile.Schema({'q': ('id', 'name', 'status')})
        run.set_schema('test', schema)
        obj = run.policy_object('test')
        run.insert('p(x) :- q(id=x)')
        self.assertEqual(len(obj.content()), 1)
        run.delete('p(x) :- q(id=x)')
        self.assertEqual(len(run.error_events), 0)
        self.assertEqual(len(run.disabled_events), 0)
        self.assertEqual(len(obj.content()), 0)

    def test_delete_set_schema_disabled(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        obj = run.policy_object('test')
        run.insert('p(x) :- q(id=x)')
        run.delete('p(x) :- q(id=x)')
        self.assertEqual(len(run.disabled_events), 2)
        self.assertEqual(len(obj.content()), 0)
        schema = compile.Schema({'q': ('id', 'name', 'status')})
        run.set_schema('test', schema)
        self.assertEqual(len(run.disabled_events), 0)
        self.assertEqual(len(obj.content()), 0)

    def test_delete_errors(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        schema = compile.Schema({'q': ('name', 'status')})
        run.set_schema('test', schema)
        obj = run.policy_object('test')
        permitted, errors = run.delete('p(x) :- q(id=x)')
        self.assertFalse(permitted)
        errstring = " ".join(str(x) for x in errors)
        self.assertTrue("column name id does not exist" in errstring)
        self.assertEqual(len(run.error_events), 0)
        self.assertEqual(len(run.disabled_events), 0)
        self.assertEqual(len(obj.content()), 0)

    def test_delete_set_schema_errors(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        obj = run.policy_object('test')
        run.delete('p(x) :- q(id=x)')   # rule is disabled
        self.assertEqual(len(run.disabled_events), 1)
        schema = compile.Schema({'q': ('name', 'status')})
        run.set_schema('test', schema)
        self.assertEqual(len(run.error_events), 1)
        self.assertEqual(len(run.disabled_events), 0)
        self.assertEqual(len(obj.content()), 0)

    # errors in set_schema
    def test_set_schema_unknown_policy(self):
        run = agnostic.Runtime()
        schema = compile.Schema({'q': ('name', 'status')})
        try:
            run.set_schema('test', schema)
            self.fail("Error not thrown on unknown policy")
        except exception.CongressException as e:
            self.assertTrue("not been created" in str(e))

    def test_disallow_schema_change(self):
        # Ensures that cannot change schema once it is set.
        # Can be removed once we support schema changes (e.g. for upgrade).
        run = agnostic.Runtime()
        run.create_policy('test')
        schema = compile.Schema({'q': ('name', 'status')})
        run.set_schema('test', schema)
        schema = compile.Schema({'q': ('id', 'name', 'status')})
        try:
            run.set_schema('test', schema)
            self.fail("Error not thrown on schema change")
        except exception.CongressException as e:
            self.assertTrue("Schema for test already set" in str(e))


class TestDelegation(base.TestCase):
    """Tests for Runtime's delegation functionality."""

    def test_subpolicy(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        policy = 'error(x) :- q(x), r(x)'
        run.insert(policy)
        subpolicy = run.find_subpolicy(
            set(['q']), set(), set(['error', 'warning']))
        e = helper.datalog_equal(subpolicy, policy)
        self.assertTrue(e)

    def test_subpolicy_multiple(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        policy = ('error(x) :- q(x), r(x) '
                  'error(x) :- q(x), s(x) '
                  'warning(x) :- t(x), q(x)')
        run.insert(policy)
        subpolicy = run.find_subpolicy(
            set(['q']), set(), set(['error', 'warning']))
        e = helper.datalog_equal(subpolicy, policy)
        self.assertTrue(e)

    def test_subpolicy_prohibited(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        policy1 = 'error(x) :- q(x), r(x) '
        policy2 = 'error(x) :- q(x), s(x) '
        policy3 = 'error(x) :- q(x), prohibit(x, y) '
        policy4 = 'warning(x) :- t(x), q(x)'
        run.insert(policy1 + policy2 + policy3 + policy4)
        subpolicy = run.find_subpolicy(
            set(['q']), set(['prohibit']), set(['error', 'warning']))
        e = helper.datalog_equal(subpolicy, policy1 + policy2 + policy4)
        self.assertTrue(e)

    def test_subpolicy_layers(self):
        run = agnostic.Runtime()
        run.create_policy('test')
        policy1 = 'error(x) :- t(x), u(x) '
        policy2 = '    t(x) :- q(x), s(x) '
        policy3 = 'error(x) :- p(x) '
        policy4 = '    p(x) :- prohibit(x, y)'
        policy5 = 'warning(x) :- t(x), q(x)'
        run.insert(policy1 + policy2 + policy3 + policy4 + policy5)
        subpolicy = run.find_subpolicy(
            set(['q']), set(['prohibit']), set(['error', 'warning']))
        e = helper.datalog_equal(subpolicy, policy1 + policy2 + policy5)
        self.assertTrue(e)
