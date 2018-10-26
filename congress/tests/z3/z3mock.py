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

"""A Mock of Z3"""

Z3_OP_OR = 262
Z3_OP_AND = 261
Z3_OP_EQ = 258
Z3_OP_FALSE = 257
Z3_OP_TRUE = 256
Z3_OP_NOT = 265
Z3_OP_IMPLIES = 266

Z3_OP_BNUM = 1024
Z3_OP_UNINTERPRETED = 2354


class BoolSort(object):

    def __repr__(self):
        return 'bool'


class BitVecSort(object):
    def __init__(self, size):
        self._size = size

    def size(self):
        return self._size

    def __repr__(self):
        return 'BV({})'.format(self._size)


class FuncDeclRef(object):
    def __init__(self, name, kind, typs=None):
        self._name = name
        self._kind = kind
        self._typs = [] if typs is None else typs

    def name(self):
        return self._name

    def kind(self):
        return self._kind

    def __eq__(self, x):
        return (isinstance(x, self.__class__) and x._name == self._name and
                x._kind == self._kind)

    def __call__(self, *args):
        return ExprRef(self, args)

    def __repr__(self):
        return (self._name if self._typs == []
                else self._name + repr(self._typs))


class ExprRef(object):
    def __init__(self, decl, args):
        self._decl = decl
        self.args = args

    def decl(self):
        return self._decl

    def children(self):
        return self.args

    def __eq__(self, v):
        return ExprRef(FuncDeclRef('=', Z3_OP_EQ), [self, v])

    def __repr__(self):
        return repr(self._decl) + repr(self.args)


class BoolRef(ExprRef):
    def __init__(self, decl, args):
        super(BoolRef, self).__init__(decl, args)
    pass


class BitVecRef(ExprRef):
    def __init__(self, decl, args, sort, val=None):
        super(BitVecRef, self).__init__(decl, args)
        self.val = val
        self.sort = sort

    def as_long(self):
        return self.val

    def size(self):
        return self.sort.size()

    def __add__(self, b):
        return BitVecRef(FuncDeclRef('bvadd', 1028), [self, b], self.sort)

    def __sub__(self, b):
        return BitVecRef(FuncDeclRef('bvsub', 1029), [self, b], self.sort)

    def __mul__(self, b):
        return BitVecRef(FuncDeclRef('bvmul', 1030), [self, b], self.sort)

    def __or__(self, b):
        return BitVecRef(FuncDeclRef('bvor', 1050), [self, b], self.sort)

    def __and__(self, b):
        return BitVecRef(FuncDeclRef('bvand', 1049), [self, b], self.sort)

    def __not__(self, b):
        return BitVecRef(FuncDeclRef('bvnot', 1051), [self, b], self.sort)

    def __lt__(self, b):
        return BoolRef(FuncDeclRef('bvslt', 1046), [self, b])

    def __le__(self, b):
        return BoolRef(FuncDeclRef('bvsle', 1042), [self, b])

    def __gt__(self, b):
        return BoolRef(FuncDeclRef('bvsgt', 1048), [self, b])

    def __ge__(self, b):
        return BoolRef(FuncDeclRef('bvsge', 1044), [self, b])

    def __eq__(self, b):
        return BoolRef(FuncDeclRef('=', 258), [self, b])

    def __ne__(self, b):
        return BoolRef(FuncDeclRef('distinct', 259), [self, b])

    def __repr__(self):
        return (
            "bv({})".format(self.val) if self.val is not None
            else super(BitVecRef, self).__repr__())


def BitVecVal(v, s):
    return BitVecRef(FuncDeclRef('bv', Z3_OP_BNUM), [], s, v)


def BoolVal(val):
    return BoolRef(FuncDeclRef('true' if val else 'false',
                               Z3_OP_TRUE if val else Z3_OP_FALSE),
                   [])


def And(*args):
    return BoolRef(FuncDeclRef('and', Z3_OP_AND), args)


def Or(*args):
    return BoolRef(FuncDeclRef('or', Z3_OP_OR), args)


def Not(arg):
    return BoolRef(FuncDeclRef('not', Z3_OP_NOT), [arg])


def Eq(arg1, arg2):
    return BoolRef(FuncDeclRef('=', Z3_OP_EQ), [arg1, arg2])


def Implies(a, b):
    return BoolRef(FuncDeclRef("=>", Z3_OP_IMPLIES), [a, b])


def ForAll(l, t):
    return BoolRef(FuncDeclRef("forall", 0), l + [t])


def Exists(l, t):
    return BoolRef(FuncDeclRef("exists", 0), l + [t])


def Const(x, sort):
    return ExprRef(FuncDeclRef(x, Z3_OP_UNINTERPRETED, typs=[sort]), [])


def Function(f, *args):
    return FuncDeclRef(f, Z3_OP_UNINTERPRETED, typs=args)


class Fixedpoint(object):

    def __init__(self):
        self._relations = []
        self._rules = []
        self._options = {}

    def set(self, **kwargs):
        self._options = kwargs

    def register_relation(self, r):
        self._relations.append(r)

    def fact(self, f):
        self._rules.append(f)

    def rule(self, r):
        self._rules.append(r)

    def query(self, q):
        pass

    @staticmethod
    def get_answer():
        return BoolVal(True)

    def get_rules(self):
        return self._rules
