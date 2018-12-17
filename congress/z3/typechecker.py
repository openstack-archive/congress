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

"""A static Datalog typechecker.

It is mandatory for Z3, but should be usable by the standard engine.
Everything should be typable as we can always assign CongressStr as
a catch-all type.

The typechecker works as follows:

* Types are stored in theories schema.

* First we reset all types to bottom in theories that we want to type-check.
  The type-checker must not change the types in other theories.
  The bottom type is None with nullability set to False.
  It must be set explicitly because otherwise the default type is scalar, True
  which corresponds to the top type in the type hierarchy.

* We prepare a type environment for each rule (identified by rule.id).that
  contains the type of the variables (again a cell initialized to the bottom
  type)

* First we type facts. Then we type rules iteratively.
  A work phase types all the rules in the theories. Typing a rule means
  propagating constraints in atoms. head and body atoms are treated with
  the same algorithm.

* We request types to be the same when we solve a constraint or to be in
  direct subtype relation. In that case we take the most precise type.
  The reason for this is that we do not precisely constrain constants in
  programs. Their type will be forced by the constraints from external tables.
  Verification will occur when we translate the value to Z3.

* Types from external tables cannot be constrained. If the type of an
  external table should be changed, typing fails.

* built-ins support will be added in the future. It is the only tricky point
  as we usually need polymorphism for equalities, tests, some numeric
  operations that can operate on various size of integers.

* convergence: there is a finite number of type cells (one per column for
  tables and one per variable for rules). We iterate only if the type of
  at least one type cell has been made more precise. There are only finite
  ascending chains of types if the type hierarchy is well founded (and it is
  ultimately based on python inheritance hierarchy which is well-founded).
"""

from oslo_log import log as logging
import six

from congress import data_types
from congress.datalog import compile as ast
from congress import exception
from congress.z3 import z3builtins

MYPY = False
# pylint: disable = ungrouped-imports
if MYPY:
    # pylint: disable = unused-import
    from mypy_extensions import TypedDict  # noqa
    from typing import Any, Union, List, Dict, Optional  # noqa

    from congress.datalog import base   # noqa

    CELLTYPE = TypedDict(
        'CELLTYPE', {'nullable': bool, 'type': Optional[str]})
    GEN_TYPE_ENV = Dict[str, Dict[int, List[CELLTYPE]]]

LOG = logging.getLogger(__name__)


def min_type(name1, name2, strict):
    # type: (str, str, bool) -> Optional[str]
    """Given two type names, gives back the most precise one or None.

    If one of the type is more precise than the other, give it back otherwise
    gives back None. strict implies that the second type cannot be
    constrained. Usually because it is defined in an external table.
    """
    typ1 = data_types.TypesRegistry.type_class(name1)
    typ2 = data_types.TypesRegistry.type_class(name2)
    if typ2.least_ancestor([typ1]) is not None:
        return name2
    if not strict and typ1.least_ancestor([typ2]) is not None:
        return name1
    return None


class Typechecker(object):
    """Typechecks a set of theories"""

    def __init__(self, theories, world):
        # type: (List[base.Theory], Dict[str, base.Theory]) -> None
        self.world = world
        self.theories = theories
        self.theorynames = set(th.name for th in theories)
        self.work = False
        self.once = False
        self.type_env = {}   # type: Dict[str, Dict[str, CELLTYPE]]
        self.type_env_builtins = {}  # type: GEN_TYPE_ENV

    def constrain_type(self, cell, typ):
        # type: (CELLTYPE, str) -> None
        """Constrains the type set in a type cell"""
        if cell['type'] is None:
            cell['type'] = typ
            self.work = True
        else:
            old_typ = cell['type']
            if typ != old_typ:
                cell['type'] = 'Scalar'
                self.work = True

    def set_nullable(self, cell):
        # type: (CELLTYPE) -> None
        """Force type to be nullable"""
        if not cell['nullable']:
            cell['nullable'] = True
            self.work = True

    def type_cells(self, cell1, cell2, strict):
        # type: (CELLTYPE, Union[str, CELLTYPE], bool) -> Optional[str]
        """Propagates type constraints between two type cells

        Updates work if a change has been made.

        :param cell1: type cell to constrain
        :param cell2: type cell to constrain
        :param strict: boolean, true if cell2 is from an external table and
             cannot be changed.
        :return: None if ok, the text of an error otherwise.
        """
        if isinstance(cell2, six.string_types):
            # Just fake the cells. Occurs for a table from a nonrecursive
            # theory.
            cell2 = {'type': 'Scalar', 'nullable': True}
        if (cell1['nullable'] and not cell2.get('nullable', True)
                and not strict):
            cell2['nullable'] = True
            self.work = True
        if cell2.get('nullable', True) and not cell1['nullable']:
            cell1['nullable'] = True
            self.work = True
        typ1 = cell1['type']
        typ2 = cell2['type']
        if typ1 is None and typ2 is not None:
            cell1['type'] = typ2
            self.work = True
        elif typ1 is not None:
            if typ2 is None:
                cell2['type'] = typ1
                self.work = True
            else:  # then typ2 is not None too
                if typ1 != typ2:
                    typ3 = min_type(typ1, typ2, strict)
                    if typ3 is not None:
                        cell1['type'] = typ3
                        cell2['type'] = typ3
                        self.work = True
                    else:
                        return "{} != {}".format(typ1, typ2)
        # else: two unresolved constraints, we do nothing
        return None

    def type_constant(self, value, column):
        # type: (Any, CELLTYPE) -> None
        """Types a constant and set the constraint"""
        if value is None:
            self.set_nullable(column)
        elif isinstance(value, six.string_types):
            self.constrain_type(column, 'Str')
        elif isinstance(value, bool):
            self.constrain_type(column, 'Bool')
        elif isinstance(value, int):
            self.constrain_type(column, 'Int')
        elif isinstance(value, float):
            self.constrain_type(column, 'Float')
        else:
            self.constrain_type(column, 'Scalar')

    def reset_type_environment(self):
        """Reset the type environment for all variables in rules"""
        def builtin_type_env(atom):
            """Generates the type of a builtin.

            The builtin can be polymorphic
            For a fixed type, we must tell if the type is nullable.
            Nullable types must begin with character @.
            """
            tablename = atom.table.table
            builtin = z3builtins.BUILTINS.get(tablename)
            if builtin is None:
                raise exception.PolicyRuntimeException(
                    'Unknown builtin {}'.format(tablename))
            typ_vars = [
                {'type': None, 'nullable': False}
                for _ in range(builtin.ty_vars)]

            def cell(t):
                return (
                    {'type': arg[1:], 'nullable': True}
                    if arg[0] == '@'
                    else {'type': arg, 'nullable': False})
            return [
                typ_vars[arg] if isinstance(arg, int) else cell(arg)
                for arg in builtin.args
            ]

        self.type_env = {
            rule.id: {
                variable.name: {'type': None, 'nullable': False}
                for variable in rule.variables()
            }
            for theory in self.theories
            for ruleset in theory.rules.rules.values()
            for rule in ruleset
        }
        self.type_env_builtins = {
            rule.id: {
                pos: builtin_type_env(atom)
                for (pos, atom) in enumerate(rule.body)
                if atom.table.service == 'builtin'
            }
            for theory in self.theories
            for ruleset in theory.rules.rules.values()
            for rule in ruleset
        }

    def reset_types(self):
        """Set all types in theory to typechecks to bottom"""

        def refresh_item(elt):
            """Refresh the type of a table's column"""
            elt = {'name': elt} if isinstance(elt, six.string_types) else elt
            elt['type'] = None
            elt['nullable'] = False
            return elt
        for theory in self.theories:
            theory.schema.map = {
                k: [refresh_item(e) for e in row]
                for (k, row) in six.iteritems(theory.schema.map)}

    def type_facts(self, theory):
        # type: (base.Theory) -> None
        """Types the facts taking the best plausible type from arguments"""
        for (tablename, facts) in six.iteritems(theory.rules.facts):
            type_row = theory.schema.map[tablename]
            for fact in facts:
                for (value, typ) in six.moves.zip(fact, type_row):
                    self.type_constant(value, typ)

    def type_rule(self, theory, rule):
        # type: (base.Theory, ast.Rule) -> None
        """One type iteration over a single rule"""
        LOG.debug("Type rule %s", rule.id)
        var_types = self.type_env[rule.id]
        builtin_types = self.type_env_builtins[rule.id]

        def type_atom(atom, pos):
            # type: (ast.Literal, int) -> None
            """Type iteration for a single atom"""
            table = atom.table
            svc = theory.name if table.service is None else table.service
            tablename = table.table
            if svc == 'builtin':
                if pos == -1:
                    raise exception.PolicyRuntimeException(
                        'builtin not authorized in rule head')
                strict = False
                tbl_schema = builtin_types.get(pos, [])  # type: List[CELLTYPE]
            else:
                strict = svc not in self.theorynames
                tbl_schema = self.world[svc].schema.map[tablename]
            for (arg, typ_col) in six.moves.zip(atom.arguments, tbl_schema):
                if isinstance(arg, ast.Variable):
                    typ_var = var_types[arg.name]
                    err = self.type_cells(typ_var, typ_col, strict)
                    if err is not None:
                        raise exception.PolicyRuntimeException(
                            ("Type error while typing variable '{}' "
                             "in {} in rule {}: {}").format(
                                 arg.name, atom, rule.id, err)
                        )
                elif isinstance(arg, ast.ObjectConstant) and self.once:
                    self.type_constant(arg.name, typ_col)

        for (pos, atom) in enumerate(rule.body):
            type_atom(atom, pos)
        type_atom(rule.head, -1)

    def type_all(self):
        # type: () -> GEN_TYPE_ENV
        """Iterative typechecker"""
        self.reset_types()
        self.reset_type_environment()
        for theory in self.theories:
            self.type_facts(theory)

        self.work = True
        self.once = True
        while self.work:
            LOG.debug("*** Z3 Type iteration")
            self.work = False
            for theory in self.theories:
                for ruleset in theory.rules.rules.values():
                    for rule in ruleset:
                        self.type_rule(theory, rule)
            self.once = False
        return self.type_env_builtins
