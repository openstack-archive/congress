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

"""Type translators between Congress and Z3."""
import abc
import six

from congress import data_types
from congress import exception

try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    z3 = None

MYPY = False
if MYPY:
    # pylint: disable = unused-import
    from typing import Any, Union, List, Optional  # noqa


Z3OPT = z3


@six.add_metaclass(abc.ABCMeta)
class Z3Type(object):
    """Translate Openstack values to Z3"""

    def __init__(self, name, type_instance):
        self.name = name
        self.type_instance = type_instance

    @abc.abstractmethod
    def to_z3(self, val, strict=False):
        # type: (Any, bool) -> z3.ExprRef
        """Transforms a value from OpenStack in a Z3 value"""
        raise NotImplementedError

    @abc.abstractmethod
    def to_os(self, val):
        # type: (z3.ExprRef) -> Any
        """Transforms a value from Z3 back to python"""
        raise NotImplementedError

    def type(self):
        # type: () -> z3.SortRef
        """Gives back the Z3 type"""
        return self.type_instance

    def reset(self):
        """Reset internal state of type transformer"""
        pass


class BoolType(Z3Type):
    """Transcode boolean in Z3"""

    def __init__(self):
        super(BoolType, self).__init__(u'Bool', z3.BoolSort())

    def to_z3(self, val, strict=False):
        return z3.BoolVal(val)

    def to_os(self, val):
        return val.decl().kind() == z3.Z3_OP_TRUE


class StringType(Z3Type):
    """Transcode strings in Z3"""

    def __init__(self, name, size=16):
        super(StringType, self).__init__(name, z3.BitVecSort(size))
        self.map = {}
        self.back = {}

    def to_z3(self, val, strict=False):
        if val in self.map:
            return self.map[val]
        code = len(self.map)
        bvect = z3.BitVecVal(code, self.type_instance)
        self.map[val] = bvect
        self.back[code] = val
        return bvect

    def to_os(self, val):
        return self.back[val.as_long()]

    def reset(self):
        self.map = {}
        self.back = {}


class FiniteType(StringType):
    """Z3 Coding for data_types with a finite number of elements

    This is the counterpart to data_types.CongressTypeFiniteDomain.
    """

    def __init__(self, name, domain):
        size = (len(domain) + 1).bit_length()
        super(FiniteType, self).__init__(name, size)
        self.domain = domain

    def to_z3(self, val, strict=False):
        if val in self.map:
            return self.map[val]
        if val not in self.domain and val is not None:
            if strict:
                raise exception.PolicyRuntimeException(
                    "Z3 Finite type: {} is not a value of {}".format(
                        val, self.name))
            else:
                val = '__OTHER__'
        code = len(self.map)
        bvect = z3.BitVecVal(code, self.type_instance)
        self.map[val] = bvect
        self.back[code] = val
        return bvect


class IntType(Z3Type):
    """Transcode numbers in Z3"""

    def __init__(self, name, size=32):
        super(IntType, self).__init__(name, z3.BitVecSort(size))
        self.map = {}
        self.back = {}

    def to_z3(self, val, strict=False):
        return z3.BitVecVal(val, self.type_instance)

    def to_os(self, val):
        return val.as_long()


class DummyType(Z3Type):
    """Dummy type when Z3 not available"""
    def to_z3(self, val, strict=False):
        pass

    def to_os(self, val):
        pass


class TypeRegistry(object):
    """A registry of Z3 types and their translators"""

    def __init__(self):
        self.type_dict = {}     # type: Dict[Str, Z3Type]
        self.top_type = DummyType('dummy', None)
        self.init()

    def register(self, typ):
        # type: (Z3Type) -> None
        """Registers a new Z3 type"""
        self.type_dict[typ.name] = typ

    def init(self):
        """Initialize the registry"""
        if Z3_AVAILABLE:
            self.top_type = StringType(u'Scalar', 34)
            for typ in [self.top_type, StringType(u'Str', 32),
                        IntType(u'Int', 32), BoolType(),
                        StringType('IPAddress', 32),
                        StringType('IPNetwork', 32),
                        StringType('UUID', 32)]:
                self.register(typ)

    def get_type(self, name):
        # type: (str) -> z3.SortRef
        """Return a Z3 type given a type name"""
        return self.get_translator(name).type()

    def get_translator(self, name):
        # type: (str) -> Z3Type
        """Return the translator for a given type name"""
        trans = self.type_dict.get(name, None)
        if trans is None:
            try:
                congress_type = data_types.TypesRegistry.type_class(name)
            except KeyError:
                raise exception.PolicyRuntimeException(
                    "Z3 typechecker: Unknown congress type {}".format(name))
            if issubclass(congress_type, data_types.CongressTypeFiniteDomain):
                trans = FiniteType(name, congress_type.DOMAIN)
                self.register(trans)
            else:
                raise exception.PolicyRuntimeException(
                    "Z3 typechecker: cannot handle type {}".format(name))
        return trans

    def reset(self):
        # type: () -> None
        """Reset the internal tables of all types"""
        for typ in six.itervalues(self.type_dict):
            typ.reset()


def z3_to_array(expr):
    # type: (z3.BoolRef) -> Union[bool, List[List[Any]]]
    """Compiles back a Z3 result to a matrix of values"""
    def extract(item):
        """Extract a row"""
        kind = item.decl().kind()
        if kind == z3.Z3_OP_AND:
            return [x.children()[1] for x in item.children()]
        elif kind == z3.Z3_OP_EQ:
            return [item.children()[1]]
        else:
            raise exception.PolicyRuntimeException(
                "Bad Z3 result not translatable {}: {}".format(expr, kind))
    kind = expr.decl().kind()

    if kind == z3.Z3_OP_OR:
        return [extract(item) for item in expr.children()]
    elif kind == z3.Z3_OP_AND:
        return [[item.children()[1] for item in expr.children()]]
    elif kind == z3.Z3_OP_EQ:
        return [[expr.children()[1]]]
    elif kind == z3.Z3_OP_FALSE:
        return False
    elif kind == z3.Z3_OP_TRUE:
        return True
    else:
        raise exception.PolicyRuntimeException(
            "Bad Z3 result not translatable {}: {}".format(expr, kind))
