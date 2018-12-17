#    Copyright 2018 Orange
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

"""Unit tests for typechecker"""

import six

from congress import data_types
from congress.datalog import base as datalog
from congress.datalog import compile as ast
from congress.datalog import nonrecursive
from congress.datalog import ruleset
from congress.tests import base
from congress.z3 import typechecker


def mkc(typ, nullable):
    return {'type': typ, 'nullable': nullable}


class TestMinTypes(base.TestCase):

    def setUp(self):
        try:
            data_types.TypesRegistry.type_class('Enum')
        except KeyError:
            typ = data_types.create_congress_enum_type(
                'Enum', ['a', 'b', 'c'], data_types.Str)
            data_types.TypesRegistry.register(typ)
        super(TestMinTypes, self).setUp()

    def test_not_convertible(self):
        self.assertIsNone(typechecker.min_type('Str', 'Int', False))

    def test_convertible(self):
        self.assertEqual('Enum', typechecker.min_type('Str', 'Enum', False))
        self.assertEqual('Enum', typechecker.min_type('Enum', 'Str', False))

    def test_constrained(self):
        self.assertEqual('Enum', typechecker.min_type('Str', 'Enum', True))
        self.assertIsNone(typechecker.min_type('Enum', 'Str', True))


class TestCellPrimitives(base.TestCase):

    def test_constrain1(self):
        tc = typechecker.Typechecker([], [])
        cell = mkc(None, False)
        tc.work = False
        tc.constrain_type(cell, 'Str')
        self.assertEqual('Str', cell['type'])
        self.assertIs(True, tc.work)

    def test_constrain2(self):
        tc = typechecker.Typechecker([], [])
        cell = mkc('Int', False)
        tc.work = False
        tc.constrain_type(cell, 'Str')
        self.assertEqual('Scalar', cell['type'])
        self.assertIs(True, tc.work)

    def test_constrain3(self):
        tc = typechecker.Typechecker([], [])
        cell = mkc('Str', False)
        tc.work = False
        tc.constrain_type(cell, 'Str')
        self.assertEqual('Str', cell['type'])
        self.assertIs(False, tc.work)

    def test_nullable1(self):
        tc = typechecker.Typechecker([], [])
        cell = mkc('Str', False)
        tc.work = False
        tc.set_nullable(cell)
        self.assertIs(True, cell['nullable'])
        self.assertIs(True, tc.work)

    def test_nullable2(self):
        tc = typechecker.Typechecker([], [])
        cell = mkc('Str', True)
        tc.work = False
        tc.set_nullable(cell)
        self.assertIs(True, cell['nullable'])
        self.assertIs(False, tc.work)

    def test_type_cells1(self):
        tc = typechecker.Typechecker([], [])
        cell1, cell2 = mkc('Str', True), mkc(None, False)
        self.assertIsNone(tc.type_cells(cell1, cell2, False))
        self.assertEqual(mkc('Str', True), cell1)
        self.assertEqual(mkc('Str', True), cell2)
        self.assertIs(True, tc.work)

    def test_type_cells2(self):
        tc = typechecker.Typechecker([], [])
        cell1, cell2 = mkc(None, False), mkc('Str', True)
        self.assertIsNone(tc.type_cells(cell1, cell2, False))
        self.assertEqual(mkc('Str', True), cell1)
        self.assertEqual(mkc('Str', True), cell2)
        self.assertIs(True, tc.work)

    def test_type_cells3(self):
        tc = typechecker.Typechecker([], [])
        cell1, cell2 = mkc(None, False), mkc('Str', True)
        self.assertIsNone(tc.type_cells(cell1, cell2, False))
        self.assertEqual(mkc('Str', True), cell1)
        self.assertEqual(mkc('Str', True), cell2)
        self.assertIs(True, tc.work)

    def test_type_cells4(self):
        tc = typechecker.Typechecker([], [])
        cell1, cell2 = mkc('Str', False), mkc('Str', False)
        self.assertIsNone(tc.type_cells(cell1, cell2, False))
        self.assertEqual(mkc('Str', False), cell1)
        self.assertEqual(mkc('Str', False), cell2)
        self.assertIs(False, tc.work)
        cell1, cell2 = mkc('Str', True), mkc('Str', True)
        self.assertIsNone(tc.type_cells(cell1, cell2, False))
        cell1, cell2 = mkc(None, False), mkc(None, False)
        self.assertIsNone(tc.type_cells(cell1, cell2, False))
        self.assertIs(False, tc.work)

    def test_type_cells5(self):
        tc = typechecker.Typechecker([], [])
        cell1, cell2 = mkc('Int', False), mkc('Str', True)
        self.assertIsNotNone(tc.type_cells(cell1, cell2, False))

    def test_type_constant(self):
        tc = typechecker.Typechecker([], [])

        def check(val, typ, nullable):
            cell = mkc(None, False)
            tc.type_constant(val, cell)
            self.assertEqual(mkc(typ, nullable), cell)

        check(1, 'Int', False)
        check('aaa', 'Str', False)
        check(True, 'Bool', False)
        check(1.3, 'Float', False)
        check(None, None, True)
        check((1, 3), 'Scalar', False)


class MinTheory(nonrecursive.RuleHandlingMixin, datalog.Theory):

    def __init__(self, name, theories):
        super(MinTheory, self).__init__(name=name, theories=theories)
        self.rules = ruleset.RuleSet()
        self.schema = ast.Schema()


class TestTypeChecker(base.TestCase):

    def setUp(self):
        self.world = {}
        t1 = MinTheory('t1', self.world)
        t2 = MinTheory('t2', self.world)
        self.world['t1'] = t1
        self.world['t2'] = t2
        self.rules = ast.parse(
            'l(2). l(3). p(x) :- l(x). q(x,x) :- m(x). '
            'm("a"). k(x) :- t2:f(x). r(y) :- q(x,y). '
            's(x) :- l(y),builtin:plus(y, 2, x).')
        for rule in self.rules:
            t1.insert(rule)
        for rule in ast.parse("f(3)."):
            t2.insert(rule)
        self.t1 = t1
        self.t2 = t2
        super(TestTypeChecker, self).setUp()

    def test_reset(self):
        tc = typechecker.Typechecker([self.t1], self.world)
        tc.reset_types()
        sch1 = self.t1.schema
        for (_, cols) in six.iteritems(sch1.map):
            for col in cols:
                self.assertIs(False, col['nullable'])
                self.assertIsNone(col['type'])

    def test_reset_variables(self):
        tc = typechecker.Typechecker([self.t1], self.world)
        tc.reset_type_environment()
        env = tc.type_env
        self.assertEqual(5, len(env.keys()))
        for variables in six.itervalues(env):
            for (v, cell) in six.iteritems(variables):
                self.assertIn(v, [u'x', u'y'])
                self.assertEqual(mkc(None, False), cell)

    def test_reset_polymorphic_calls(self):
        tc = typechecker.Typechecker([self.t1], self.world)
        tc.reset_type_environment()
        env = tc.type_env_builtins
        rule = self.rules[7]
        typ = mkc(None, False)
        self.assertEqual(5, len(env.keys()))
        self.assertEqual({1: [typ, typ, typ]}, env[rule.id])

    def test_type_facts(self):
        tc = typechecker.Typechecker([self.t1], self.world)
        tc.reset_types()
        tc.reset_type_environment()
        tc.type_facts(self.t1)
        cols1 = self.t1.schema.map['l']
        self.assertEqual(1, len(cols1))
        self.assertEqual('Int', cols1[0]['type'])
        self.assertIs(False, cols1[0]['nullable'])
        cols2 = self.t1.schema.map['m']
        self.assertEqual(1, len(cols2))
        self.assertEqual('Str', cols2[0]['type'])
        self.assertIs(False, cols2[0]['nullable'])

    def test_type_rule(self):
        rule = self.rules[2]
        tc = typechecker.Typechecker([self.t1], self.world)
        tc.reset_types()
        tc.reset_type_environment()
        tc.type_facts(self.t1)
        tc.type_rule(self.t1, rule)
        self.assertEqual(mkc('Int', False), tc.type_env[rule.id]['x'])
        self.assertEqual('Int', self.t1.schema.map['p'][0]['type'])
        self.assertIs(True, tc.work)

    def test_type_all(self):
        tc = typechecker.Typechecker([self.t1], self.world)
        type_env = tc.type_all()
        smap = self.t1.schema.map
        self.assertEqual('Int', smap['p'][0]['type'])      # propagation of l
        self.assertEqual('Str', smap['q'][0]['type'])      # propagation of m
        self.assertEqual('Str', smap['q'][1]['type'])
        self.assertEqual('Str', smap['r'][0]['type'])
        self.assertEqual('Scalar', smap['k'][0]['type'])   # prop of ext table
        self.assertEqual('Int', smap['s'][0]['type'])      # through builtins
        rule = self.rules[7]
        typ = mkc('Int', False)
        self.assertEqual([typ, typ, typ], type_env[rule.id][1])
