# Copyright (c) 2015 VMware, Inc. All rights reserved.
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

import eventlet
from oslo_log import log as logging

from congress.datalog import arithmetic_solvers
from congress.dse import d6cage
from congress import harness
from congress.policy_engines import vm_placement
from congress.tests import base
from congress.tests import helper

LOG = logging.getLogger(__name__)

NREC_THEORY = 'non-recursive theory'


class TestEngine(base.TestCase):

    def test_parse(self):
        engine = vm_placement.ComputePlacementEngine()
        engine.debug_mode()
        f = engine.parse1('nova:q(1)')
        self.assertTrue(f.table.table, 'nova:q')
        self.assertIsNone(f.table.service)

        f = engine.parse1('p(x) :- q(x)')
        self.assertEqual(f.head.table.table, 'p')
        self.assertEqual(f.body[0].table.table, 'q')

    def test_select(self):
        engine = vm_placement.ComputePlacementEngine()
        engine.debug_mode()
        engine.insert('p(x) :- q(x)')
        engine.insert('q(1)')
        ans = engine.select('p(x)')
        self.assertTrue(helper.datalog_equal(ans, 'p(1)'))

    def test_theory_in_head(self):
        engine = vm_placement.ComputePlacementEngine()
        engine.debug_mode()
        engine.policy.insert(engine.parse1('p(x) :- nova:q(x)'))
        engine.policy.insert(engine.parse1('nova:q(1)'))
        ans = engine.policy.select(engine.parse1('p(x)'))
        ans = " ".join(str(x) for x in ans)
        self.assertTrue(helper.datalog_equal(ans, 'p(1)'))


class TestSetPolicy(base.TestCase):
    """Tests for setting policy."""

    def setUp(self):
        # create DSE and add vm-placement engine and fake datasource
        super(TestSetPolicy, self).setUp()
        self.cage = d6cage.d6Cage()
        config = {'vmplace':
                  {'module': "congress/policy_engines/vm_placement.py"},
                  'fake':
                  {'poll_time': 0,
                   'module': "congress/tests/fake_datasource.py"}}

        harness.load_data_service("vmplace", config['vmplace'],
                                  self.cage, helper.root_path(), 1)
        harness.load_data_service("fake", config['fake'],
                                  self.cage, helper.root_path(), 2)

        self.vmplace = self.cage.service_object('vmplace')
        self.vmplace.debug_mode()
        self.fake = self.cage.service_object('fake')

    def test_set_policy_subscriptions(self):
        self.vmplace.set_policy('p(x) :- fake:q(x)')
        helper.retry_check_subscriptions(
            self.vmplace, [(self.fake.name, 'q')])
        helper.retry_check_subscribers(
            self.fake, [(self.vmplace.name, 'q')])

    def test_set_policy(self):
        LOG.info("set_policy")
        self.vmplace.set_policy('p(x) :- fake:q(x)')
        self.fake.state = {'q': set([tuple([1]), tuple([2])])}
        self.fake.poll()
        ans = ('p(1) p(2)')
        helper.retry_check_db_equal(self.vmplace, 'p(x)', ans)

    # TODO(thinrichs): add tests for data update
    #   Annoying since poll() saves self.state, invokes
    #   update_from_datasource (which updates self.state),
    #   computes deltas, and publishes.  No easy way to inject
    #   a new value for self.state and get it to send non-empty
    #   deltas over the message bus.  Probably want to extend
    #   fake_datasource to include a client (default to None), make
    #   update_from_datasource use that client to set self.state,
    #   and then mock out the client.

    # TODO(thinrichs): add tests for setting policy to something that
    #   requires tables to be unsubscribed from

    # TODO(thinrichs): test production_mode()


class TestLpLang(base.TestCase):
    """Test the DatalogLp language."""
    def test_variables(self):
        var1 = arithmetic_solvers.LpLang.makeVariable('alice', 1, 3.1)
        var2 = arithmetic_solvers.LpLang.makeVariable('alice', 1, 3.1)
        var3 = arithmetic_solvers.LpLang.makeVariable('alice', 1, 4.0)
        self.assertEqual(var1, var2)
        self.assertNotEqual(var1, var3)

    def test_or(self):
        var1 = arithmetic_solvers.LpLang.makeVariable('alice', 1)
        var2 = arithmetic_solvers.LpLang.makeVariable('bob', 1)
        var3 = arithmetic_solvers.LpLang.makeVariable('charlie', 1)
        p1 = arithmetic_solvers.LpLang.makeOr(var1, var2)
        p2 = arithmetic_solvers.LpLang.makeOr(var1, var2)
        p3 = arithmetic_solvers.LpLang.makeOr(var1, var3)
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)
        p4 = arithmetic_solvers.LpLang.makeOr(var1)
        self.assertEqual(p4, var1)
        p5 = arithmetic_solvers.LpLang.makeOr(var2, var1)
        self.assertEqual(p1, p5)

    def test_and(self):
        var1 = arithmetic_solvers.LpLang.makeVariable('alice', 1)
        var2 = arithmetic_solvers.LpLang.makeVariable('bob', 1)
        var3 = arithmetic_solvers.LpLang.makeVariable('charlie', 1)
        p1 = arithmetic_solvers.LpLang.makeAnd(var1, var2)
        p2 = arithmetic_solvers.LpLang.makeAnd(var1, var2)
        p3 = arithmetic_solvers.LpLang.makeAnd(var1, var3)
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)
        p4 = arithmetic_solvers.LpLang.makeAnd(var1)
        self.assertEqual(p4, var1)
        p5 = arithmetic_solvers.LpLang.makeAnd(var2, var1)
        self.assertEqual(p1, p5)

    def test_equal(self):
        var1 = arithmetic_solvers.LpLang.makeVariable('alice', 1)
        var2 = arithmetic_solvers.LpLang.makeVariable('bob', 1)
        var3 = arithmetic_solvers.LpLang.makeVariable('charlie', 1)
        p1 = arithmetic_solvers.LpLang.makeEqual(var1, var2)
        p2 = arithmetic_solvers.LpLang.makeEqual(var1, var2)
        p3 = arithmetic_solvers.LpLang.makeEqual(var1, var3)
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)
        p4 = arithmetic_solvers.LpLang.makeEqual(var2, var1)
        self.assertEqual(p1, p4)

    def test_notequal(self):
        var1 = arithmetic_solvers.LpLang.makeVariable('alice', 1)
        var2 = arithmetic_solvers.LpLang.makeVariable('bob', 1)
        var3 = arithmetic_solvers.LpLang.makeVariable('charlie', 1)
        p1 = arithmetic_solvers.LpLang.makeNotEqual(var1, var2)
        p2 = arithmetic_solvers.LpLang.makeNotEqual(var1, var2)
        p3 = arithmetic_solvers.LpLang.makeNotEqual(var1, var3)
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)
        p4 = arithmetic_solvers.LpLang.makeNotEqual(var2, var1)
        self.assertEqual(p1, p4)

    def test_arith(self):
        var1 = arithmetic_solvers.LpLang.makeVariable('alice', 1)
        var2 = arithmetic_solvers.LpLang.makeVariable('bob', 1)
        p1 = arithmetic_solvers.LpLang.makeArith('lt', var1, var2)
        p2 = arithmetic_solvers.LpLang.makeArith('lt', var1, var2)
        p3 = arithmetic_solvers.LpLang.makeArith('gt', var1, var2)
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)

    def test_complex(self):
        var1 = arithmetic_solvers.LpLang.makeVariable('alice', 1)
        var2 = arithmetic_solvers.LpLang.makeVariable('bob', 1)
        arith1 = arithmetic_solvers.LpLang.makeArith('lt', var1, var2)
        arith2 = arithmetic_solvers.LpLang.makeArith('lt', var1, var2)
        arith3 = arithmetic_solvers.LpLang.makeArith('gt', var1, var2)
        p1 = arithmetic_solvers.LpLang.makeEqual(
            var1, arithmetic_solvers.LpLang.makeOr(arith1, arith2))
        p2 = arithmetic_solvers.LpLang.makeEqual(
            var1, arithmetic_solvers.LpLang.makeOr(arith2, arith1))
        p3 = arithmetic_solvers.LpLang.makeEqual(
            var1, arithmetic_solvers.LpLang.makeOr(arith1, arith3))

        # equality
        self.assertEqual(p1, p2)
        self.assertNotEqual(p1, p3)

        # sets
        s1 = set([arith1, p1])
        s2 = set([p1, arith1])
        s3 = set([arith1, arith2])
        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, s3)


class TestDatalogToLp(base.TestCase):
    def check(self, code, data, query, ans, possibility=None):
        if possibility is None:
            possibility = []
        engine = vm_placement.ComputePlacementEngine(
            arithmetic_solvers.LpLang())
        engine.debug_mode()
        engine.insert(code)
        for d in data:
            engine.insert(d)
        query = engine.parse1(query)
        (rules, variables) = engine.datalog_to_lp(query, possibility)
        LOG.info("Checking equality")
        if not same_sets(rules, ans):
            LOG.info("-- actual --")
            for rule in rules:
                LOG.info("%s", rule)
            LOG.info("-- correct --")
            for rule in ans:
                LOG.info("%s", rule)
            self.fail("actual and correct mismatch")

    def test_basic(self):
        code = ('warning(id) :- '
                ' nova:host(id, zone, memory_capacity), '
                ' legacy:special_zone(zone), '
                ' ceilometer:mem_consumption(id, avg), '
                ' mul(0.75, memory_capacity, three_quarters_mem),'
                ' lt(avg, three_quarters_mem)')
        data = ('nova:host(123, "dmz", 10) ',
                'legacy:special_zone("dmz") ',
                'ceilometer:mem_consumption(123, 15)')  # ignored
        query = 'warning(x)'
        ans = arithmetic_solvers.LpLang.makeExpr(['eq',
                                                  ['var', 'warning', 123],
                                                  ['lt',
                                                   ['var', 'hMemUse', 123],
                                                   7.5]])
        self.check(code, data, query, [ans])

    def test_multiple_rows(self):
        code = ('warning(id) :- '
                ' nova:host(id, zone, memory_capacity), '
                ' legacy:special_zone(zone), '
                ' ceilometer:mem_consumption(id, avg), '
                ' mul(0.75, memory_capacity, three_quarters_mem),'
                ' lt(avg, three_quarters_mem)')
        data = ('nova:host(123, "dmz", 10) ',
                'nova:host(456, "dmz", 20) ',
                'legacy:special_zone("dmz") ',
                'ceilometer:mem_consumption(123, 15)')   # ignored
        query = 'warning(x)'
        ans1 = arithmetic_solvers.LpLang.makeExpr(['eq',
                                                   ['var', 'warning', 123],
                                                   ['lt',
                                                    ['var', 'hMemUse', 123],
                                                    7.5]])
        ans2 = arithmetic_solvers.LpLang.makeExpr(['eq',
                                                   ['var', 'warning', 456],
                                                   ['lt',
                                                    ['var', 'hMemUse', 456],
                                                    15.0]])
        self.check(code, data, query, [ans1, ans2])

    # def test_disjunction(self):
    #     code = ('warning(id) :- '
    #             ' nova:host(id, zone, memory_capacity), '
    #             ' legacy:special_zone(zone), '
    #             ' ceilometer:mem_consumption(id, avg), '
    #             ' mul(0.75, memory_capacity, three_quarters_mem),'
    #             ' lt(avg, three_quarters_mem)')
    #     data = ('nova:host(123, "dmz", 10) ',
    #             'nova:host(456, "dmz", 20) ',
    #             'nova:host(456, "dmz", 30) ',  # doesn't really make sense
    #             'legacy:special_zone("dmz") ',
    #             'ceilometer:mem_consumption(123, 15)')   # ignored
    #     query = 'warning(x)'
    #     ans1 = LpLang.makeExpr(['eq',
    #                             ['var', 'warning', 123],
    #                             ['lt', ['var', 'hMemUse', 123], 7.5]])
    #     ans2 = LpLang.makeExpr(['eq',
    #                             ['var', 'warning', 456],
    #                             ['or',
    #                              ['lt', ['var', 'hMemUse', 123], 7.5],
    #                              ['lt', ['var', 'hMemUse', 456], 15.0]]])
    #     self.check(code, data, query, [ans1, ans2])

    def test_multiple_constraints(self):
        code = ('warning(id) :- '
                ' nova:host(id, zone, memory_capacity), '
                ' legacy:special_zone(zone), '
                ' ceilometer:mem_consumption(id, avg), '
                ' mul(0.75, memory_capacity, three_quarters_mem),'
                ' lt(avg, three_quarters_mem),'
                ' lt(avg, 100)')
        data = ('nova:host(123, "dmz", 10) ',
                'legacy:special_zone("dmz") ',
                'ceilometer:mem_consumption(123, 15)')   # ignored
        query = 'warning(x)'
        ans1 = arithmetic_solvers.LpLang.makeExpr(
            ['eq',
             ['var', 'warning', 123],
             ['and', ['lt', ['var', 'hMemUse', 123], 7.5],
                     ['lt', ['var', 'hMemUse', 123], 100]]])
        self.check(code, data, query, [ans1])


class TestDatalogPolicyToLp(base.TestCase):
    def check(self, actual, correct):
        extra = diff(actual, correct)
        missing = diff(correct, actual)
        if len(extra) or len(missing):
            LOG.info("-- missing --")
            for rule in missing:
                LOG.info("%s", rule)
            LOG.info("-- extra --")
            for rule in extra:
                LOG.info("%s", rule)
            self.fail("actual and correct mismatch")

    def test_domain_axioms(self):
        engine = vm_placement.ComputePlacementEngine()
        engine.debug_mode()
        engine.insert('nova:host(123, 1, 10)')
        engine.insert('nova:host(456, 1, 10)')
        engine.insert('nova:server(789, "alice", 123)')
        engine.insert('nova:server(101, "bob", 123)')
        engine.insert('ceilometer:mem_consumption(789, 10)')
        engine.insert('ceilometer:mem_consumption(101, 20)')
        self.assertEqual(set(engine.get_hosts()), set([123, 456]))
        self.assertEqual(set(engine.get_guests()), set([789, 101]))
        ans1 = arithmetic_solvers.LpLang.makeExpr(
            ['eq',
             ['var', 'hMemUse', 456],
             ['plus',
              ['times', ['var', 'assign', 101, 456], 20],
              ['times', ['var', 'assign', 789, 456], 10]]])
        ans2 = arithmetic_solvers.LpLang.makeExpr(
            ['eq',
             ['var', 'hMemUse', 123],
             ['plus',
              ['times', ['var', 'assign', 101, 123], 20],
              ['times', ['var', 'assign', 789, 123], 10]]])
        ans3 = arithmetic_solvers.LpLang.makeExpr(
            ['eq',
             1,
             ['plus',
              ['var', 'assign', 101, 123],
              ['var', 'assign', 101, 456]]])
        ans4 = arithmetic_solvers.LpLang.makeExpr(
            ['eq',
             1,
             ['plus',
              ['var', 'assign', 789, 123],
              ['var', 'assign', 789, 456]]])
        self.check(engine.domain_axioms(), [ans1, ans2, ans3, ans4])

    def test_policy_to_lp(self):
        engine = vm_placement.ComputePlacementEngine()
        engine.debug_mode()
        engine.insert('nova:host(123, 1, 10)')
        engine.insert('nova:host(456, 1, 10)')
        engine.insert('nova:server(789, "alice", 123)')
        engine.insert('nova:server(101, "bob", 123)')
        code = ('warning(id) :- '
                ' nova:host(id, zone, memory_capacity), '
                ' legacy:special_zone(zone), '
                ' ceilometer:mem_consumption(id, avg), '
                ' mul(0.75, memory_capacity, three_quarters_mem),'
                ' lt(avg, three_quarters_mem)')
        engine.insert(code)
        engine.insert('legacy:special_zone(1)')
        engine.insert('ceilometer:mem_consumption(123, 15)')
        engine.insert('ceilometer:mem_consumption(456, 20)')
        engine.insert('ceilometer:mem_consumption(789, 5)')
        engine.insert('ceilometer:mem_consumption(101, 10)')
        opt, constraints = engine.policy_to_lp()

        optans = arithmetic_solvers.LpLang.makeExpr(['or',
                                                     ['var', 'warning', 456],
                                                     ['var', 'warning', 123]])
        ans1 = arithmetic_solvers.LpLang.makeExpr(['eq',
                                                   ['var', 'warning', 123],
                                                   ['lt',
                                                    ['var', 'hMemUse', 123],
                                                    7.5]])
        ans2 = arithmetic_solvers.LpLang.makeExpr(['eq',
                                                   ['var', 'warning', 456],
                                                   ['lt',
                                                    ['var', 'hMemUse', 456],
                                                    7.5]])
        ans3 = arithmetic_solvers.LpLang.makeExpr(
            ['eq',
             ['var', 'hMemUse', 456],
             ['plus',
              ['times', ['var', 'assign', 101, 456], 10],
              ['times', ['var', 'assign', 789, 456], 5]]])
        ans4 = arithmetic_solvers.LpLang.makeExpr(
            ['eq',
             ['var', 'hMemUse', 123],
             ['plus',
              ['times', ['var', 'assign', 101, 123], 10],
              ['times', ['var', 'assign', 789, 123], 5]]])
        ans5 = arithmetic_solvers.LpLang.makeExpr(
            ['eq',
             1,
             ['plus',
              ['var', 'assign', 101, 123],
              ['var', 'assign', 101, 456]]])
        ans6 = arithmetic_solvers.LpLang.makeExpr(
            ['eq',
             1,
             ['plus',
              ['var', 'assign', 789, 123],
              ['var', 'assign', 789, 456]]])

        self.check([opt], [optans])
        self.check(constraints, [ans1, ans2, ans3, ans4, ans5, ans6])


class TestPureLp(base.TestCase):
    """Test conversion of Datalog LP to pure LP."""
    def check(self, expr, bounds, correct):
        lang = arithmetic_solvers.LpLang()
        actual = lang.pure_lp(lang.makeExpr(expr), bounds)
        correct = [lang.makeExpr(x) for x in correct]
        if not same_sets(actual, correct):
            LOG.info("-- actual --")
            for rule in actual:
                LOG.info("%s", rule)
            LOG.info("-- correct --")
            for rule in correct:
                LOG.info("%s", rule)
            self.fail("actual and correct mismatch")

    def test_real_1(self):
        """Test a real use case."""
        exp = ['eq', ['var', 'warning', 123],
                     ['lteq', ['var', 'hMemUse', 123], 7.5]]
        bounds = {('VAR', 'hMemUse', 123): 100}
        y = ['var', 'warning', 123]
        x = ['minus',
             ['minus', ['var', 'hMemUse', 123], 7.5],
             arithmetic_solvers.LpLang.MIN_THRESHOLD]
        upperx = 101
        c1 = ['lteq', ['times', -1, x], ['times', y, upperx]]
        c2 = ['lt', x, ['times', ['minus', 1, y], upperx]]
        self.check(exp, bounds, [c1, c2])

    def test_real_2(self):
        e = ['eq',
             ['var', 'hMemUse', 456],
             ['plus',
              ['times', ['var', 'assign', 101, 456], ['var', 'gMemUse', 101]],
              ['times',
               ['var', 'assign', 789, 456],
               ['var', 'gMemUse', 789]]]]
        ans1 = ['eq',
                ['var', 'internal', 0],
                ['times',
                 ['var', 'assign', 101, 456],
                 ['var', 'gMemUse', 101]]]
        ans2 = ['eq',
                ['var', 'internal', 1],
                ['times',
                 ['var', 'assign', 789, 456],
                 ['var', 'gMemUse', 789]]]
        ans3 = ['eq',
                ['var', 'hMemUse', 456],
                ['plus', ['var', 'internal', 0], ['var', 'internal', 1]]]
        self.check(e, {}, [ans1, ans2, ans3])


class TestFlatten(base.TestCase):
    """Test reformulation of embedded operators into flattened formulas."""
    def check(self, input_expression, correct, correct_support):
        lang = arithmetic_solvers.LpLang()
        input_expr = lang.makeExpr(input_expression)
        LOG.info("input_expression: %s", input_expr)
        actual, actual_support = lang.flatten(input_expr, indicator=False)
        correct = lang.makeExpr(correct)
        correct_support = [lang.makeExpr(x) for x in correct_support]
        if (actual != correct or not same_sets(
                actual_support, correct_support)):
            LOG.info("-- actual: %s", actual)
            LOG.info("-- actual support --")
            for rule in actual_support:
                LOG.info("%s", rule)
            LOG.info("-- correct: %s", correct)
            LOG.info("-- correct support --")
            for rule in correct_support:
                LOG.info("%s", rule)
            self.fail("actual and correct mismatch")

    def test_flat(self):
        self.check(['or', 1, 2], ['or', 1, 2], [])
        self.check(['and', 1, 2], ['and', 1, 2], [])

    def test_nested(self):
        self.check(['or', 1, ['or', 2, 3]],  # orig
                   ['or', 1, ['var', 'internal', 0]],  # flat
                   [['eq', ['var', 'internal', 0],  # support
                           ['or', 2, 3]]])
        self.check(['or', 1, ['and', 2, 3]],  # orig
                   ['or', 1, ['var', 'internal', 0]],  # flat
                   [['eq', ['var', 'internal', 0],  # support
                           ['and', 2, 3]]])
        self.check(['eq',      # orig
                    ['var', 1, 2],
                    ['or',
                     ['and', 3, 4],
                     ['and', 5, 6]]],
                   ['eq',      # flat
                    ['var', 1, 2],
                    ['or', ['var', 'internal', 0], ['var', 'internal', 1]]],
                   [['eq', ['var', 'internal', 0], ['and', 3, 4]],  # support
                    ['eq', ['var', 'internal', 1], ['and', 5, 6]]])

    def test_real(self):
        self.check(['eq', ['var', 'warning', 123],
                          ['lt', ['var', 'hMemUse', 123], 7.5]],
                   ['eq', ['var', 'warning', 123],
                          ['lt', ['var', 'hMemUse', 123], 7.5]],
                   [])
        self.check(
            ['eq',  # orig
             ['var', 'hMemUse', 456],
             ['or',
              ['and', ['var', 'assign', 101, 456], ['var', 'gMemUse', 101]],
              ['and', ['var', 'assign', 789, 456], ['var', 'gMemUse', 789]]]],
            ['eq',  # flat
             ['var', 'hMemUse', 456],
             ['or', ['var', 'internal', 0], ['var', 'internal', 1]]],
            [['eq',  # support
              ['var', 'internal', 0],
              ['and', ['var', 'assign', 101, 456], ['var', 'gMemUse', 101]]],
             ['eq',
              ['var', 'internal', 1],
              ['and', ['var', 'assign', 789, 456], ['var', 'gMemUse', 789]]]])


class TestIndicatorElim(base.TestCase):
    """Test binary indicator variable elimination."""
    def check(self, input_expression, bounds, correct_expressions):
        lang = arithmetic_solvers.LpLang()
        input_expr = lang.makeExpr(input_expression)
        LOG.info("input_expression: %s", input_expr)
        actual = lang.indicator_to_pure_lp(input_expr, bounds)
        correct = [lang.makeExpr(x) for x in correct_expressions]
        extra = diff(actual, correct)
        missing = diff(correct, actual)
        if len(extra) or len(missing):
            LOG.info("-- missing --")
            for rule in missing:
                LOG.info("%s", rule)
            LOG.info("-- extra --")
            for rule in extra:
                LOG.info("%s", rule)
            self.fail("actual and correct mismatch")

    def test_simple(self):
        exp = ['eq', ['var', 'warning', 123],
                     ['lteq', ['var', 'hMemUse', 123], 7.5]]
        bounds = {('VAR', 'hMemUse', 123): 100}
        y = ['var', 'warning', 123]
        x = ['minus', ['minus', ['var', 'hMemUse', 123], 7.5],
             arithmetic_solvers.LpLang.MIN_THRESHOLD]
        upperx = 101
        c1 = ['lteq', ['times', -1, x], ['times', y, upperx]]
        c2 = ['lt', x, ['times', ['minus', 1, y], upperx]]
        self.check(exp, bounds, [c1, c2])


class TestToLtZero(base.TestCase):
    """Test conversion of inequality to form A < 0."""
    small = arithmetic_solvers.LpLang.MIN_THRESHOLD

    def check(self, expr, correct):
        lang = arithmetic_solvers.LpLang()
        actual = lang.arith_to_lt_zero(lang.makeExpr(expr))
        self.assertEqual(actual, lang.makeExpr(correct))

    def test_lt(self):
        expr = ['lt', 7, 8]
        self.check(expr, ['lt', ['minus', 7, 8], 0])

    def test_lteq(self):
        expr = ['lteq', 10, 11]
        self.check(expr, ['lt', ['minus', ['minus', 10, 11], self.small], 0])

    def test_gt(self):
        expr = ['gt', 12, 13]
        self.check(expr, ['lt', ['minus', 13, 12], 0])

    def test_gteq(self):
        expr = ['gteq', 14, 15]
        self.check(expr, ['lt', ['minus', ['minus', 15, 14], self.small], 0])


class TestUpperBound(base.TestCase):
    """Test upper bound computation."""
    def check(self, expr, bounds, correct):
        lang = arithmetic_solvers.LpLang()
        actual = lang.upper_bound(lang.makeExpr(expr), bounds)
        self.assertEqual(actual, correct)

    def test_times(self):
        exp = ['times', ['VAR', 'a', 1], ['VAR', 'a', 2]]
        bounds = {('VAR', 'a', 1): 2, ('VAR', 'a', 2): 3}
        self.check(exp, bounds, 6)

    def test_plus(self):
        exp = ['plus', ['VAR', 'a', 1], ['VAR', 'a', 2]]
        bounds = {('VAR', 'a', 1): 2, ('VAR', 'a', 2): 3}
        self.check(exp, bounds, 5)

    def test_minus(self):
        exp = ['minus', ['VAR', 'a', 1], ['VAR', 'a', 2]]
        bounds = {('VAR', 'a', 1): 2, ('VAR', 'a', 2): 3}
        self.check(exp, bounds, 2)

    def test_nested(self):
        exp = ['plus',
               ['times', ['VAR', 'a', 1], ['VAR', 'a', 2]],
               ['minus', ['VAR', 'a', 3], ['VAR', 'a', 4]]]
        bounds = {('VAR', 'a', 1): 5,
                  ('VAR', 'a', 2): 7,
                  ('VAR', 'a', 3): 2,
                  ('VAR', 'a', 4): 1}
        self.check(exp, bounds, 37)

    def test_nested2(self):
        exp = ['times',
               ['times', ['VAR', 'a', 1], ['VAR', 'a', 2]],
               ['minus', ['VAR', 'a', 3], ['VAR', 'a', 4]]]
        bounds = {('VAR', 'a', 1): 5,
                  ('VAR', 'a', 2): 7,
                  ('VAR', 'a', 3): 2,
                  ('VAR', 'a', 4): 1}
        self.check(exp, bounds, 70)


class TestComputeVmAssignment(base.TestCase):
    """Test full computation of VM assignment."""
    def test_two_servers(self):
        engine = vm_placement.ComputePlacementEngine()
        engine.debug_mode()
        engine.insert('nova:host(123, 1, 10)')
        engine.insert('nova:host(456, 1, 5)')
        engine.insert('nova:server(789, "alice", 123)')
        engine.insert('nova:server(101, "bob", 123)')
        code = ('warning(id) :- '
                ' nova:host(id, zone, memory_capacity), '
                ' legacy:special_zone(zone), '
                ' ceilometer:mem_consumption(id, avg), '
                ' mul(0.75, memory_capacity, three_quarters_mem),'
                ' lteq(avg, three_quarters_mem)')
        engine.insert(code)
        engine.insert('legacy:special_zone(1)')
        engine.insert('ceilometer:mem_consumption(789, 2)')
        engine.insert('ceilometer:mem_consumption(101, 2)')
        ans = engine.calculate_vm_assignment()
        LOG.info("assignment: %s", ans)
        self.assertEqual(ans, {101: 456, 789: 456})

    def test_three_servers(self):
        engine = vm_placement.ComputePlacementEngine()
        engine.debug_mode()
        engine.insert('nova:host(100, 1, 6)')
        engine.insert('nova:host(101, 1, 10)')
        engine.insert('nova:server(200, "alice", 100)')
        engine.insert('nova:server(201, "bob", 100)')
        engine.insert('nova:server(202, "bob", 101)')
        code = ('warning(id) :- '
                ' nova:host(id, zone, memory_capacity), '
                ' legacy:special_zone(zone), '
                ' ceilometer:mem_consumption(id, avg), '
                ' mul(0.75, memory_capacity, three_quarters_mem),'
                ' lteq(avg, three_quarters_mem)')
        engine.insert(code)
        engine.insert('legacy:special_zone(1)')
        engine.insert('ceilometer:mem_consumption(200, 2)')
        engine.insert('ceilometer:mem_consumption(201, 2)')
        engine.insert('ceilometer:mem_consumption(202, 2)')
        ans = engine.calculate_vm_assignment()
        LOG.info("assignment: %s", ans)
        self.assertEqual({200: 100, 201: 100, 202: 100}, ans)

    def test_set_policy(self):
        engine = vm_placement.ComputePlacementEngine(inbox=eventlet.Queue(),
                                                     datapath=eventlet.Queue())
        engine.debug_mode()
        p = (
            'nova:host(100, 1, 6)'
            'nova:host(101, 1, 10)'
            'nova:server(200, "alice", 100)'
            'nova:server(201, "bob", 100)'
            'nova:server(202, "bob", 101)'
            'warning(id) :- '
            ' nova:host(id, zone, memory_capacity), '
            ' legacy:special_zone(zone), '
            ' ceilometer:mem_consumption(id, avg), '
            ' mul(0.75, memory_capacity, three_quarters_mem),'
            ' lteq(avg, three_quarters_mem)'
            'legacy:special_zone(1)'
            'ceilometer:mem_consumption(100, 4)'
            'ceilometer:mem_consumption(101, 2)'
            'ceilometer:mem_consumption(200, 2)'
            'ceilometer:mem_consumption(201, 2)'
            'ceilometer:mem_consumption(202, 2)')
        engine.set_policy(p)
        LOG.info("assignment: %s", engine.guest_host_assignment)
        self.assertEqual({200: 100, 201: 100, 202: 100},
                         engine.guest_host_assignment)

    def test_set_policy_with_dashes(self):
        engine = vm_placement.ComputePlacementEngine(inbox=eventlet.Queue(),
                                                     datapath=eventlet.Queue())
        engine.debug_mode()
        p = (
            'nova:host("Server-100", 1, 6)'
            'nova:host("Server-101", 1, 10)'
            'nova:server(200, "alice", "Server-100")'
            'nova:server(201, "bob", "Server-100")'
            'nova:server(202, "bob", "Server-101")'
            'warning(id) :- '
            ' nova:host(id, zone, memory_capacity), '
            ' legacy:special_zone(zone), '
            ' ceilometer:mem_consumption(id, avg), '
            ' mul(0.75, memory_capacity, three_quarters_mem),'
            ' lteq(avg, three_quarters_mem)'
            'legacy:special_zone(1)'
            'ceilometer:mem_consumption("Server-100", 4)'
            'ceilometer:mem_consumption("Server-101", 2)'
            'ceilometer:mem_consumption(200, 2)'
            'ceilometer:mem_consumption(201, 2)'
            'ceilometer:mem_consumption(202, 2)')
        engine.set_policy(p)
        LOG.info("assignment: %s", engine.guest_host_assignment)
        self.assertEqual({200: 'Server-100', 201: 'Server-100',
                          202: 'Server-100'},
                         engine.guest_host_assignment)


def diff(iter1, iter2):
    iter1 = list(iter1)
    iter2 = list(iter2)
    ans = []
    for x in iter1:
        if x not in iter2:
            ans.append(x)
    return ans


def same_sets(iter1, iter2):
    """Can't use set(iter1) == set(iter2) b/c hash doesn't respect OR."""
    iter1 = list(iter1)  # make sure iter1 and iter2 are not Python sets
    iter2 = list(iter2)
    for x in iter1:
        if x not in iter2:
            return False
    for x in iter2:
        if x not in iter1:
            return False
    return True
