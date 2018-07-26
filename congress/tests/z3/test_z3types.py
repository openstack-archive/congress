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

"""Unit tests for z3types"""
import mock

from congress import data_types
from congress import exception
from congress.tests import base
from congress.tests.z3 import z3mock as z3
from congress.z3 import z3types


def mockz3(f):
    z3types.Z3_AVAILABLE = True
    return mock.patch("congress.z3.z3types.z3", new=z3)(f)


class TestBoolType(base.TestCase):
    """Z3 Boolean values"""

    @mockz3
    def setUp(self):
        self.type = z3types.BoolType()
        super(TestBoolType, self).setUp()

    @mockz3
    def test_to_z3(self):
        self.assertEqual(z3.Z3_OP_TRUE, self.type.to_z3(True).decl().kind())
        self.assertEqual(z3.Z3_OP_FALSE, self.type.to_z3(False).decl().kind())

    @mockz3
    def test_from_z3(self):
        self.assertEqual(True, self.type.to_os(z3.BoolVal(True)))
        self.assertEqual(False, self.type.to_os(z3.BoolVal(False)))


class TestStringType(base.TestCase):
    """Z3 String values"""

    @mockz3
    def setUp(self):
        self.type = z3types.StringType('string', size=8)
        super(TestStringType, self).setUp()

    @mockz3
    def test_to_z3(self):
        x = self.type.to_z3('aaaa')
        self.assertEqual(8, x.size())
        # Do not try to use equality on Z3 values.
        self.assertEqual(self.type.to_z3('aaaa').as_long(), x.as_long())
        self.assertIs(False,
                      self.type.to_z3('bbbb').as_long() == x.as_long())

    @mockz3
    def test_from_z3(self):
        self.assertEqual('aaaa', self.type.to_os(self.type.to_z3('aaaa')))


class TestIntType(base.TestCase):
    """Z3 Int values"""

    @mockz3
    def setUp(self):
        self.type = z3types.IntType('int', size=16)
        super(TestIntType, self).setUp()

    @mockz3
    def test_to_z3(self):
        x = self.type.to_z3(342)
        self.assertEqual(16, x.size())
        self.assertEqual(342, x.as_long())

    @mockz3
    def test_from_z3(self):
        self.assertEqual(421, self.type.to_os(self.type.to_z3(421)))


class TestZ3TypeRegistry(base.TestCase):
    """Other Z3Types Unit tests"""
    def setUp(self):
        try:
            data_types.TypesRegistry.type_class('Foo')
        except KeyError:
            typ = data_types.create_congress_enum_type(
                'Foo', ['a', 'b'], data_types.Str)
            data_types.TypesRegistry.register(typ)
        super(TestZ3TypeRegistry, self).setUp()

    @mockz3
    def test_get_type(self):
        registry = z3types.TypeRegistry()
        t = registry.get_type('Bool')
        self.assertIs(True, isinstance(t, z3.BoolSort))
        t = registry.get_type('Foo')
        self.assertIs(True, isinstance(t, z3.BitVecSort))

    @mockz3
    def test_get_translator(self):
        registry = z3types.TypeRegistry()
        t = registry.get_translator('Bool')
        self.assertIs(True, isinstance(t, z3types.BoolType))
        t = registry.get_translator('Foo')
        self.assertIs(True, isinstance(t, z3types.FiniteType))

    @mockz3
    def test_register(self):
        registry = z3types.TypeRegistry()
        test_type = mock.MagicMock()
        test_type.name = 'Bar'
        registry.register(test_type)
        self.assertEqual(test_type, registry.get_translator('Bar'))

    @mockz3
    def test_reset(self):
        registry = z3types.TypeRegistry()
        test_type = mock.MagicMock()
        test_type.name = 'Bar'
        registry.register(test_type)
        registry.reset()
        test_type.reset.assert_called_once_with()


class TestZ3ToArray(base.TestCase):

    @staticmethod
    def project(z3res):
        return [[x.as_long() for x in vec] for vec in z3res]

    @mockz3
    def test_sat(self):
        self.assertIs(True, z3types.z3_to_array(z3.BoolVal(True)))
        self.assertIs(False, z3types.z3_to_array(z3.BoolVal(False)))

    @mockz3
    def test_simple(self):
        s = z3.BitVecSort(10)

        def vec(x):
            return z3.BitVecVal(x, s)

        x, y = z3.Const('x', s), z3.Const('y', s)
        expr = z3.Eq(x, vec(1))
        self.assertEqual([[1]], self.project(z3types.z3_to_array(expr)))
        expr = z3.And(z3.Eq(x, vec(1)), z3.Eq(y, vec(2)))
        self.assertEqual([[1, 2]], self.project(z3types.z3_to_array(expr)))

    @mockz3
    def test_two_dims(self):
        s = z3.BitVecSort(10)

        def vec(x):
            return z3.BitVecVal(x, s)

        x, y = z3.Const('x', s), z3.Const('y', s)
        expr = z3.Or(z3.Eq(x, vec(1)), z3.Eq(x, vec(2)))
        self.assertEqual([[1], [2]], self.project(z3types.z3_to_array(expr)))

        expr = z3.Or(z3.And(z3.Eq(x, vec(1)), z3.Eq(y, vec(2))),
                     z3.And(z3.Eq(x, vec(3)), z3.Eq(y, vec(4))))
        self.assertEqual([[1, 2], [3, 4]],
                         self.project(z3types.z3_to_array(expr)))

    @mockz3
    def test_fails(self):
        s = z3.BitVecSort(10)
        x = z3.Const('x', s)
        expr = x
        self.assertRaises(exception.PolicyRuntimeException,
                          z3types.z3_to_array, expr)
        expr = z3.Or(x, x)
        self.assertRaises(exception.PolicyRuntimeException,
                          z3types.z3_to_array, expr)
