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

"""Unit tests for z3theory"""
import mock
import six

from congress import data_types
from congress.datalog import compile as ast
from congress.datalog import topdown
from congress import exception
from congress.tests import base
from congress.tests.z3 import z3mock as z3
from congress.z3 import z3theory
from congress.z3 import z3types


def mockz3(f):
    z3types.Z3_AVAILABLE = True
    return (
        mock.patch("congress.z3.z3types.z3", new=z3)
        (mock.patch("congress.z3.z3theory.Z3OPT", new=z3)(f)))


class TestZ3Utilities(base.TestCase):

    def test_cycle_not_contained_in_z3(self):
        t1 = mock.MagicMock(spec=z3theory.Z3Theory)
        t2 = mock.MagicMock(spec=z3theory.Z3Theory)
        t3 = mock.MagicMock(spec=topdown.TopDownTheory)
        theories = {'t1': t1, 't2': t2, 't3': t3}
        for name, th in six.iteritems(theories):
            th.name = name
        cycles = [['t1:p', 't2:q', 't1:r'], ['t1:p1', 't2:q2']]
        r = z3theory.cycle_not_contained_in_z3(theories, cycles)
        self.assertIs(False, r)
        cycles = [['t1:p', 't2:q', 't1:r'], ['t3:p1', 't2:q2']]
        r = z3theory.cycle_not_contained_in_z3(theories, cycles)
        self.assertIs(True, r)

    def test_congress_constant(self):
        test_cases = [
            (3, "INTEGER", 3), ("aa", "STRING", "aa"),
            (4.3, "FLOAT", 4.3), ([], "STRING", "[]")]
        for (val, typ, name) in test_cases:
            obj = z3theory.congress_constant(val)
            self.assertIsInstance(
                obj, ast.ObjectConstant,
                msg=('not a constant for %s' % (str(val))))
            self.assertEqual(typ, obj.type)
            self.assertEqual(name, obj.name)

    def test_retrieve(self):
        theory = mock.MagicMock(spec=topdown.TopDownTheory)
        theory.name = 'test'
        theory.schema = mock.MagicMock(spec=ast.Schema)
        theory.schema.arity.return_value = 3
        z3theory.retrieve(theory, 'table')
        args = theory.select.call_args
        query = args[0][0]
        self.assertIsInstance(query, ast.Literal)
        self.assertEqual('table', query.table.table)
        self.assertEqual('test', query.table.service)
        self.assertEqual(3, len(query.arguments))
        self.assertIs(
            True,
            all(isinstance(arg, ast.Variable) for arg in query.arguments))


class TestZ3Theory(base.TestCase):

    @mockz3
    def setUp(self):
        world = {}
        self.theory = z3theory.Z3Theory('test', theories=world)
        world['test'] = self.theory    # invariant to maintain in agnostic
        super(TestZ3Theory, self).setUp()

    def test_init(self):
        self.assertIsInstance(self.theory.schema, ast.Schema)
        self.assertIsInstance(self.theory.z3context, z3theory.Z3Context)
        context = z3theory.Z3Context.get_context()
        self.assertIn('test', context.z3theories)
        self.assertEqual(self.theory, context.z3theories['test'])

    def test_select(self):
        context = z3theory.Z3Context.get_context()
        context.select = mock.MagicMock()
        lit = ast.Literal(ast.Tablename('t'), [])
        self.theory.select(lit)
        context.select.assert_called_once_with(self.theory, lit, True)

    def test_drop(self):
        self.theory.drop()
        context = z3theory.Z3Context.get_context()
        self.assertNotIn('test', context.z3theories)

    def test_arity(self):
        lit = ast.Literal(ast.Tablename('t'),
                          [ast.Variable('x'), ast.Variable('x')])
        self.theory.insert(lit)
        self.assertEqual(2, self.theory.arity('t'))


def mkc(name, nullable=False):
    return {'type': name, 'nullable': nullable}


class TestZ3Context(base.TestCase):

    @mockz3
    def test_registration(self):
        context = z3theory.Z3Context()
        theory = mock.MagicMock(z3theory.Z3Theory)
        name = 'test'
        world = {}
        theory.name = name
        theory.theories = world
        world['foo'] = theory
        context.register(theory)
        self.assertIn(name, context.z3theories)
        self.assertEqual(theory, context.z3theories[name])
        self.assertEqual(world, context.theories)
        context.drop(theory)
        self.assertNotIn(name, context.z3theories)

    @mockz3
    def test_get_context(self):
        self.assertIsInstance(
            z3theory.Z3Context.get_context(), z3theory.Z3Context)

    @mockz3
    def test_declare_table(self):
        """Test single table declaration

        Declare table declares the relation of a single table from its type
        """
        context = z3theory.Z3Context()
        name = 'test'
        tbname = 'table'
        world = {}
        theory = z3theory.Z3Theory(name, theories=world)
        theory.schema.map[tbname] = [mkc('Int'), mkc('Int')]
        world[name] = theory
        context.declare_table(theory, tbname)
        # Only the mock as a _relations element and pylint is confused
        rels = context.context._relations  # pylint: disable=E1101
        self.assertEqual(1, len(rels))
        self.assertEqual(name + ':' + tbname, rels[0].name())
        self.assertEqual(3, len(rels[0]._typs))

    @mockz3
    def test_declare_tables(self):
        """Test declaration of internal z3theories tables

        Declare tables must iterate over all schemas and create relations
        with the right arity and types
        """
        context = z3theory.Z3Context()
        world = {}
        t1 = z3theory.Z3Theory('t1', theories=world)
        t2 = z3theory.Z3Theory('t2', theories=world)
        world['t1'] = t1
        world['t2'] = t2
        t1.schema.map['p'] = [mkc('Int')]
        t1.schema.map['q'] = [mkc('Str'), mkc('Str')]
        t2.schema.map['k'] = [mkc('Bool')]
        context.register(t1)
        context.register(t2)
        context.declare_tables()
        # Only the mock as a _relations element and pylint is confused
        rels = context.context._relations  # pylint: disable=E1101
        self.assertEqual(3, len(rels))
        self.assertIn('t1:q', context.relations)
        self.assertEqual(2, len(context.relations['t1:p']._typs))

    def init_three_theories(self):
        context = z3theory.Z3Context()
        world = {}
        for name in ['t1', 't2', 't3']:
            world[name] = z3theory.Z3Theory(name, theories=world)
        t1, t2, t3 = world['t1'], world['t2'], world['t3']
        context.register(t1)
        context.register(t2)
        # t3 is kept external
        # Declare rules
        for rule in ast.parse('p(x) :- t2:r(x), t3:s(x). q(x) :- p(x). p(4).'):
            t1.insert(rule)
        for rule in ast.parse('r(x) :- t1:p(x).'):
            t2.insert(rule)
        # typechecker
        t1.schema.map['p'] = [mkc('Int')]
        t1.schema.map['q'] = [mkc('Int')]
        t2.schema.map['r'] = [mkc('Int')]
        t3.schema.map['s'] = [mkc('Int')]
        t3.schema.map['t'] = [mkc('Int')]
        return context

    @mockz3
    def test_declare_external_tables(self):
        """Test declaration of internal z3theories tables

        Declare tables must iterate over all schemas and create relations
        with the right arity and types
        """
        context = self.init_three_theories()
        context.declare_external_tables()
        # Only the mock as a _relations element and pylint is confused
        rels = context.context._relations  # pylint: disable=E1101
        self.assertEqual(1, len(rels))
        self.assertIn('t3:s', context.relations)

    @mockz3
    def test_compile_facts(self):
        context = z3theory.Z3Context()
        world = {}
        t1 = z3theory.Z3Theory('t1', theories=world)
        world['t1'] = t1
        context.register(t1)
        for rule in ast.parse('l(1,2). l(3,4). l(5,6).'):
            t1.insert(rule)
        t1.schema.map['l'] = [mkc('Int'), mkc('Int')]
        context.declare_tables()
        context.compile_facts(t1)
        rules = context.context.get_rules()
        self.assertEqual(3, len(rules))
        self.assertIs(True, all(r.decl().name() == 't1:l' for r in rules))
        self.assertEqual(
            [[1, 2], [3, 4], [5, 6]],
            [[c.as_long() for c in r.children()] for r in rules])

    def init_one_rule(self):
        context = z3theory.Z3Context()
        world = {}
        t1 = z3theory.Z3Theory('t1', theories=world)
        world['t1'] = t1
        context.register(t1)
        rule = ast.parse('p(x) :- l(x,y), l(3,x).')[0]
        t1.schema.map['l'] = [mkc('Int'), mkc('Int')]
        t1.schema.map['p'] = [mkc('Int')]
        context.declare_tables()
        return (context, t1, rule)

    def init_one_builtin(self, body, typ, arity):
        context = z3theory.Z3Context()
        world = {}
        t1 = z3theory.Z3Theory('t1', theories=world)
        world['t1'] = t1
        context.register(t1)
        rule = ast.parse('p(x) :- ' + body + '.')[0]
        t1.schema.map['p'] = [mkc(typ)]
        context.declare_tables()
        return (context, t1, rule, {0: [mkc(typ)] * arity})

    def init_one_theory(self, prog):
        context = z3theory.Z3Context()
        world = {}
        t1 = z3theory.Z3Theory('t1', theories=world)
        world['t1'] = t1
        context.register(t1)
        for rule in ast.parse(prog):
            t1.insert(rule)
        return (context, t1)

    @mockz3
    def test_compile_atoms(self):
        (context, t1, rule) = self.init_one_rule()
        result = context.compile_atoms({}, t1, rule.head, rule.body)
        self.assertEqual(3, len(result))
        (vars, head, body) = result
        self.assertEqual(2, len(vars))
        # two variables
        self.assertIs(
            True, all(x.decl().kind() == z3.Z3_OP_UNINTERPRETED for x in vars))
        # two literals in the body
        self.assertEqual(2, len(body))
        # Head literal is p
        self.assertEqual('t1:p', head.decl().name())
        # First body literal is l
        self.assertEqual('t1:l', body[0].decl().name())
        # First arg of second body literal is a compiled int constant
        self.assertEqual(3, body[1].children()[0].as_long())
        # Second arg of second body literal is a variable
        self.assertEqual(z3.Z3_OP_UNINTERPRETED,
                         body[1].children()[1].decl().kind())

    @mockz3
    def test_compile_binop_builtin(self):
        tests = [('plus', 'bvadd'), ('minus', 'bvsub'), ('mul', 'bvmul'),
                 ('and', 'bvand'), ('or', 'bvor')]
        for (datalogName, z3Name) in tests:
            (context, t1, rule, env) = self.init_one_builtin(
                'builtin:' + datalogName + '(2, 3, x)', 'Int', 3)
            result = context.compile_atoms(env, t1, rule.head, rule.body)
            (_, _, body) = result
            # two literals in the body
            self.assertEqual(1, len(body))
            # First body literal is l
            eqExpr = body[0]
            self.assertEqual('=', eqExpr.decl().name())
            right = eqExpr.children()[0]
            self.assertEqual(z3Name, right.decl().name())
            self.assertEqual(2, right.children()[0].as_long())
            self.assertEqual(3, right.children()[1].as_long())

    @mockz3
    def test_compile_builtin_tests(self):
        tests = [('gt', 'bvsgt'), ('lt', 'bvslt'), ('gteq', 'bvsge'),
                 ('lteq', 'bvsle'), ('equal', '=')]
        for (datalogName, z3Name) in tests:
            (context, t1, rule, env) = self.init_one_builtin(
                'builtin:' + datalogName + '(2, x)', 'Int', 2)
            result = context.compile_atoms(env, t1, rule.head, rule.body)
            (_, _, body) = result
            # two literals in the body
            self.assertEqual(1, len(body))
            # First body literal is l
            testExpr = body[0]
            self.assertEqual(z3Name, testExpr.decl().name())
            self.assertEqual(2, testExpr.children()[0].as_long())

    @mockz3
    def test_compile_rule(self):
        (context, t1, rule) = self.init_one_rule()
        context.compile_rule({}, t1, rule)
        result = context.context._rules[0]   # pylint: disable=E1101
        self.assertEqual('forall', result.decl().name())
        self.assertEqual('=>', result.children()[2].decl().name())
        self.assertEqual(
            'and', result.children()[2].children()[0].decl().name())

    @mockz3
    def test_compile_query(self):
        (context, t1, rule) = self.init_one_rule()
        result = context.compile_query(t1, rule.head)
        self.assertEqual('exists', result.decl().name())
        self.assertEqual('t1:p', result.children()[1].decl().name())

    @mockz3
    def test_compile_theory(self):
        context = self.init_three_theories()
        context.declare_tables()
        context.declare_external_tables()
        context.compile_theory({}, context.z3theories['t1'])
        rules = context.context._rules     # pylint: disable=E1101
        self.assertEqual(3, len(rules))

    @mockz3
    def test_compile_all(self):
        context = self.init_three_theories()
        context.compile_all({})
        rules = context.context._rules     # pylint: disable=E1101
        rels = context.context._relations  # pylint: disable=E1101
        self.assertEqual(4, len(rules))
        self.assertEqual(['t1:p', 't1:q', 't2:r', 't3:s'],
                         sorted([k.name() for k in rels]))

    @staticmethod
    def mk_z3_result(context):
        sort = context.type_registry.get_type('Int')

        def vec(x):
            return z3.BitVecVal(x, sort)

        x, y = z3.Const('x', sort), z3.Const('y', sort)
        return z3.Or(z3.And(z3.Eq(x, vec(1)), z3.Eq(y, vec(2))),
                     z3.And(z3.Eq(x, vec(3)), z3.Eq(y, vec(4))))

    @mock.patch('congress.z3.z3types.z3.Fixedpoint.get_answer')
    @mockz3
    def test_eval(self, mock_get_answer):
        (context, t1) = self.init_one_theory('l(1,2). l(3,4).')
        expr = self.mk_z3_result(context)
        mock_get_answer.return_value = expr
        query = ast.parse('l(x,y)')[0]
        result = context.eval(t1, query)
        self.assertEqual(2, len(result[1]))
        self.assertEqual(2, len(result[2]))
        self.assertIs(True, all(len(row) == 2 for row in result[0]))

    @mock.patch('congress.z3.z3types.z3.Fixedpoint.get_answer')
    @mockz3
    def test_select(self, mock_get_answer):
        (context, t1) = self.init_one_theory('l(1,2). l(3,4).')
        expr = self.mk_z3_result(context)
        mock_get_answer.return_value = expr
        query = ast.parse('l(x,y)')[0]
        result = context.select(t1, query, True)
        self.assertEqual(ast.parse('l(1,2). l(3,4).'), result)

    @mockz3
    def test_inject(self):
        theory = mock.MagicMock(spec=topdown.TopDownTheory)
        world = {'t': theory}
        theory.name = 't'
        theory.schema = ast.Schema()
        theory.schema.map['l'] = [mkc('Int'), mkc('Int')]
        theory.select.return_value = ast.parse('l(1,2). l(3,4). l(5,6)')
        context = z3theory.Z3Context()
        # An external theory world
        context.theories = world
        # inject the declaration of external relation without rules
        param_types = [
            context.type_registry.get_type(typ)
            for typ in ['Int', 'Int', 'Bool']]
        relation = z3.Function('t:l', *param_types)
        context.context.register_relation(relation)
        context.relations['t:l'] = relation
        # the test
        context.inject('t', 'l')
        rules = context.context._rules  # pylint: disable=E1101
        self.assertIs(True, all(r.decl().name() == 't:l' for r in rules))
        self.assertEqual(
            [[1, 2], [3, 4], [5, 6]],
            sorted([[c.as_long() for c in r.children()] for r in rules]))


class TestTypeConstraints(base.TestCase):

    @mockz3
    def setUp(self):
        try:
            data_types.TypesRegistry.type_class('Small')
        except KeyError:
            typ = data_types.create_congress_enum_type(
                'Small', ['a', 'b'], data_types.Str)
            data_types.TypesRegistry.register(typ)
        super(TestTypeConstraints, self).setUp()

    @staticmethod
    def init_two_theories(prog):
        context = z3theory.Z3Context()
        world = {}
        for name in ['t1', 't2']:
            world[name] = z3theory.Z3Theory(name, theories=world)
        t1, t2 = world['t1'], world['t2']
        context.register(t1)
        # t2 is kept external
        # Declare rules
        for rule in ast.parse(prog):
            t1.insert(rule)
        # typechecker
        t2.schema.map['p'] = [mkc('Small')]
        t2.schema.map['q'] = [mkc('Str')]
        return context

    @mockz3
    def test_compile_all_ok(self):
        context = self.init_two_theories('p("a"). p(x) :- t2:p(x).')
        env = context.typecheck()
        context.compile_all(env)
        rules = context.context._rules     # pylint: disable=E1101
        self.assertEqual(2, len(rules))

    @mockz3
    def test_compile_fails_constraints(self):
        # Two external tables with different types: caught by typechecker.
        context = self.init_two_theories('p(x) :- t2:p(x), t2:q(x).')
        self.assertRaises(exception.PolicyRuntimeException, context.typecheck)

    @mockz3
    def test_compile_fails_values(self):
        context = self.init_two_theories('p("c"). p(x) :- t2:p(x).')
        # Type-check succeeds
        env = context.typecheck()
        # But we are caught when trying to convert 'c' as a 'Small' value
        self.assertRaises(exception.PolicyRuntimeException,
                          context.compile_all, env)
