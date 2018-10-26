# Copyright (c) 2018 Orange. All rights reserved.
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

import collections

# BuiltinPred describes a builtin predicate
#
# @param ty_vars: the number of generic type variables
# @param args: an array describing the type of each argument of the predicate.
#     It is a string for standard type and an integer for type variables in
#     the range 0, ty_vars - 1.
# @param z3: a function generating the z3 code from an array coding the
#     z3 arguments
BuiltinPred = collections.namedtuple(
    'BuiltinPred',
    ['args', 'ty_vars', 'z3'])

# Warning: the z3 code operates on syntax and builds syntax. It does not
# perform an operation on the fly. This is a clever trick of z3 library
# but may puzzle the casual reader.
BUILTINS = {
    # Bit arithmetic
    "and": BuiltinPred(
        ty_vars=1, args=[0, 0, 0], z3=(lambda x, y, z: z == x & y)),
    "or": BuiltinPred(
        ty_vars=1, args=[0, 0, 0], z3=(lambda x, y, z: z == x | y)),
    "bnot": BuiltinPred(ty_vars=1, args=[0, 0], z3=(lambda x, y: y == ~x)),
    # Arithmetic (limited as it may render z3 slow in some modes)
    "plus": BuiltinPred(
        ty_vars=1, args=[0, 0, 0], z3=(lambda x, y, z: z == x + y)),
    "minus": BuiltinPred(
        ty_vars=1, args=[0, 0, 0], z3=(lambda x, y, z: z == x - y)),
    "mul": BuiltinPred(
        ty_vars=1, args=[0, 0, 0], z3=(lambda x, y, z: z == x * y)),
    # Comparisons
    "lt": BuiltinPred(ty_vars=1, args=[0, 0], z3=(lambda x, y: x < y)),
    "lteq": BuiltinPred(ty_vars=1, args=[0, 0], z3=(lambda x, y: x <= y)),
    "equal": BuiltinPred(ty_vars=1, args=[0, 0], z3=(lambda x, y: x == y)),
    "gteq": BuiltinPred(ty_vars=1, args=[0, 0], z3=(lambda x, y: x >= y)),
    "gt": BuiltinPred(ty_vars=1, args=[0, 0], z3=(lambda x, y: x > y)),
}
