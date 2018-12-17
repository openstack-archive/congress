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

# Conflict with flake8
# pylint: disable = bad-continuation

"""A theory that contains rules that must be treated by Z3."""

import time

import logging
import six

from congress.datalog import base
from congress.datalog import compile as ast
from congress.datalog import nonrecursive
from congress.datalog import ruleset
from congress.datalog import unify
from congress import exception
from congress.z3 import typechecker
from congress.z3 import z3builtins
from congress.z3 import z3types

# pylint: disable = ungrouped-imports
MYPY = False
if MYPY:
    # pylint: disable = unused-import
    from congress.datalog import topdown                        # noqa
    from mypy_extensions import TypedDict                       # noqa
    from typing import Dict, Callable, Optional, Union, List, Any, Tuple  # noqa
    import z3                                                   # noqa
    Z3_RESULT = Tuple[Union[bool, List[List[z3.ExprRef]]],
                      List[ast.Variable],
                      List[z3types.Z3Type]]

LOG = logging.getLogger(__name__)

Z3_ENGINE_OPTIONS = {'engine': 'datalog'}

Z3OPT = z3types.z3

INTER_COMPILE_DELAY = 60.0


def cycle_not_contained_in_z3(theories, cycles):
    # type: (Dict[str, base.Theory], List[List[str]]) -> bool
    """Check that there is a true cycle not through Z3 theory

    A cycle is irreducible if it contains at least one element which is not a
    Z3Theory for which recursion is allowed. Cycles are represented by lists of
    qualified table names.
    """
    acceptables = [
        th.name
        for th in six.itervalues(theories)
        if isinstance(th, Z3Theory)]
    return any(fullname[:fullname.index(':')] not in acceptables
               for cycle in cycles for fullname in cycle)


# TODO(pcregut): Object constants should evolve to use the type system
# rather than custom types.
def congress_constant(val):
    """Creates an object constant from a value using its type"""
    if isinstance(val, six.string_types):
        typ = ast.ObjectConstant.STRING
    elif isinstance(val, int):
        typ = ast.ObjectConstant.INTEGER
    elif isinstance(val, float):
        typ = ast.ObjectConstant.FLOAT
    else:
        val = str(val)
        typ = ast.ObjectConstant.STRING
    return ast.ObjectConstant(val, typ)


def retrieve(theory, tablename):
    # type: (topdown.TopDownTheory, str) -> List[ast.Literal]
    """Retrieves all the values of an external table.

    Performs a select on the theory with a query computed from the schema
    of the table.
    """
    arity = theory.schema.arity(tablename)
    table = ast.Tablename(tablename, theory.name)
    args = [ast.Variable('X' + str(i)) for i in range(arity)]
    query = ast.Literal(table, args)
    return theory.select(query)


class Z3Theory(nonrecursive.RuleHandlingMixin, base.Theory):
    """Theory for Z3 engine

    Z3Theory is a datalog theory interpreted by the Z3 engine instead of
    the usual congress internal engine.
    """

    def __init__(self, name=None, abbr=None,
                 schema=None, theories=None, desc=None, owner=None):
        super(Z3Theory, self).__init__(
            name=name, abbr=abbr, theories=theories,
            schema=ast.Schema() if schema is None else schema,
            desc=desc, owner=owner)
        LOG.info('z3theory: create %s', name)
        self.kind = base.Z3_POLICY_TYPE
        self.rules = ruleset.RuleSet()
        self.dirty = False
        self.z3context = None
        Z3Context.get_context().register(self)

    def select(self, query, find_all=True):
        """Performs a query"""
        return self.z3context.select(self, query, find_all)

    def arity(self, tablename, modal=None):
        """Arity of a table"""
        return self.schema.arity(tablename)

    def drop(self):
        """To call when the theory is forgotten"""
        self.z3context.drop(self)

    def _top_down_eval(self,
                       context,  # type: topdown.TopDownTheory.TopDownContext
                       caller    # type: topdown.TopDownTheory.TopDownCaller
                       ):
        # type: (...) -> bool
        """Evaluation entry point for the non recursive engine

        We must compute unifiers and clear off as soon as we can
        giving back control to the theory context.
        Returns true if we only need one binding and it has been found,
        false otherwise.
        """
        raw_lit = context.literals[context.literal_index]
        query_lit = raw_lit.plug(context.binding)
        answers, bvars, translators = self.z3context.eval(self, query_lit)
        if isinstance(answers, bool):
            if answers:
                return (context.theory._top_down_finish(context, caller)
                        and not caller.find_all)
            return False
        for answer in answers:
            changes = []
            for (val, var, trans) in six.moves.zip(answer, bvars, translators):
                chg = context.binding.add(var, trans.to_os(val), None)
                changes.append(chg)
            context.theory._top_down_finish(context, caller)
            unify.undo_all(changes)
            if not caller.find_all:
                return True
        return False


class Z3Context(object):
    """An instance of Z3 defined first by its execution context"""

    _singleton = None

    def __init__(self):
        self.context = Z3OPT.Fixedpoint()
        self.context.set(**Z3_ENGINE_OPTIONS)
        self.z3theories = {}        # type: Dict[str, Z3Theory]
        self.relations = {}         # type: Dict[str, z3.Function]
        # back pointer on all theories extracted from registered theory.
        self.theories = None        # type: Dict[str, topdown.TopDownTheory]
        self.externals = set()      # type: Set[Tuple[str, str]]
        self.type_registry = z3types.TypeRegistry()
        self.last_compiled = 0

    def register(self, theory):
        # type: (Z3Theory) -> None
        """Registers a Z3 theory in the context"""
        if self.theories is None:
            self.theories = theory.theories
        theory.z3context = self
        self.z3theories[theory.name] = theory

    def drop(self, theory):
        # type: (Z3Theory) -> None
        """Unregister a Z3 theory from the context"""
        del self.z3theories[theory.name]

    @staticmethod
    def get_context():
        # type: () -> Z3Context
        """Gives back the unique instance of this class.

        Users should not use the class constructor but this method.
        """
        if Z3Context._singleton is None:
            Z3Context._singleton = Z3Context()
        return Z3Context._singleton

    def eval(self,
             theory,   # type: Z3Theory
             query     # type: ast.Literal
             ):
        # type: (...) -> Z3_RESULT
        """Solves a query and gives back a raw result

        Result is in Z3 ast format with a translator
        """
        theories_changed = any(t.dirty for t in self.z3theories.values())
        # TODO(pcregut): replace either with an option or find something
        # better for the refresh of datasources.
        needs_refresh = time.time() - self.last_compiled > INTER_COMPILE_DELAY
        if theories_changed or needs_refresh:
            # There is no reset on Z3 context. Replace with a new one.
            self.context = Z3OPT.Fixedpoint()
            self.context.set(**Z3_ENGINE_OPTIONS)
            type_env = self.typecheck()
            self.compile_all(type_env)
            self.synchronize_external()
        z3query = self.compile_query(theory, query)
        self.context.query(z3query)
        z3answer = self.context.get_answer()
        answer = z3types.z3_to_array(z3answer)
        typ_args = theory.schema.types(query.table.table)
        variables = []    # type: List[ast.Variable]
        translators = []  # type: List[z3types.Z3Type]
        for arg, typ_arg in six.moves.zip(query.arguments, typ_args):
            if isinstance(arg, ast.Variable) and arg not in variables:
                translators.append(
                    self.type_registry.get_translator(str(typ_arg.type)))
                variables.append(arg)
        return (answer, variables, translators)

    def select(self, theory, query, find_all):
        # type: (Z3Theory, ast.Literal, bool) -> List[ast.Literal]
        """Query a theory"""
        (answer, variables, trans) = self.eval(theory, query)
        pattern = [
            variables.index(arg) if isinstance(arg, ast.Variable) else arg
            for arg in query.arguments]

        def plug(row):
            """Plugs in found values in query litteral"""
            args = [
                (congress_constant(trans[arg].to_os(row[arg]))
                 if isinstance(arg, int) else arg)
                for arg in pattern]
            return ast.Literal(query.table, args)

        if isinstance(answer, bool):
            return [query] if answer else []
        if find_all:
            result = [plug(row) for row in answer]
        else:
            result = [plug(answer[0])]
        return result

    def declare_table(self, theory, tablename):
        """Declares a new table in Z3 context"""
        fullname = theory.name + ':' + tablename
        if fullname in self.relations:
            return
        typ_args = theory.schema.types(tablename)
        param_types = [
            self.type_registry.get_type(str(tArg.type))
            for tArg in typ_args]
        param_types.append(Z3OPT.BoolSort())
        relation = Z3OPT.Function(fullname, *param_types)
        self.context.register_relation(relation)
        self.relations[fullname] = relation

    def declare_tables(self):
        """Declares all tables defined in Z3 context"""
        for theory in six.itervalues(self.z3theories):
            for tablename in theory.schema.map.keys():
                self.declare_table(theory, tablename)

    def declare_external_tables(self):
        """Declares tables from other theories used in Z3 context"""
        def declare_for_lit(lit):
            """Declares the table of a litteral if necessary"""
            service = lit.table.service
            table = lit.table.table
            if (service is not None and service != 'builtin' and
                    service not in self.z3theories):
                self.externals.add((service, table))
        for theory in six.itervalues(self.z3theories):
            for rules in six.itervalues(theory.rules.rules):
                for rule in rules:
                    for lit in rule.body:
                        declare_for_lit(lit)
        for (service, table) in self.externals:
            self.declare_table(self.theories[service], table)

    def compile_facts(self, theory):
        # type: (Z3Theory) -> None
        """Compiles the facts of a theory in Z3 context"""
        for tname, facts in six.iteritems(theory.rules.facts):
            translators = [
                self.type_registry.get_translator(str(arg_type.type))
                for arg_type in theory.schema.types(tname)]
            fullname = theory.name + ':' + tname
            z3func = self.relations[fullname]
            for fact in facts:
                z3args = (tr.to_z3(v, strict=True)
                          for (v, tr) in six.moves.zip(fact, translators))
                z3fact = z3func(*z3args)
                self.context.fact(z3fact)

    def compile_atoms(self,
                      type_env,
                      theory,    # type: Z3Theory
                      head,      # type: ast.Literal
                      body       # type: List[ast.Literal]
                      ):
        # type: (...) -> Tuple[z3.Const, z3.ExprRef, List[z3.ExprRef]]
        """Compile a list of atoms belonging to a single variable scope

        As it is used mainly for rules, the head is distinguished.
        """
        variables = {}  # type: Dict[str, z3.Const]
        z3vars = []

        def compile_expr(expr, translator):
            """Compiles an expression to Z3"""
            if isinstance(expr, ast.Variable):
                name = expr.name
                if name in variables:
                    return variables[name]
                var = Z3OPT.Const(name, translator.type())
                variables[name] = var
                z3vars.append(var)
                return var
            elif isinstance(expr, ast.ObjectConstant):
                return translator.to_z3(expr.name)
            else:
                raise exception.PolicyException(
                    "Expr {} not handled by Z3".format(expr))

        def compile_atom(literal, pos=-1):
            """Compiles an atom in Z3"""
            name = literal.table.table
            svc = literal.table.service
            if svc == 'builtin':
                translators = [
                    self.type_registry.get_translator(str(arg_type['type']))
                    for arg_type in type_env[pos]
                ]
                fullname = 'builtin:'+name
            else:
                lit_theory = theory if svc is None else self.theories[svc]
                translators = [
                    self.type_registry.get_translator(str(arg_type.type))
                    for arg_type in lit_theory.schema.types(name)]
                fullname = lit_theory.name + ":" + name
            try:
                z3func = (
                    z3builtins.BUILTINS[name].z3 if svc == 'builtin'
                    else self.relations[fullname])
                z3args = (compile_expr(arg, tr)
                          for (arg, tr) in six.moves.zip(literal.arguments,
                                                         translators))
                z3lit = z3func(*z3args)
                return (Z3OPT.Not(z3lit) if literal.negated
                        else z3lit)
            except KeyError:
                raise exception.PolicyException(
                    "Z3: Relation %s not registered" % fullname)

        z3head = compile_atom(head)
        z3body = [compile_atom(atom, pos) for (pos, atom) in enumerate(body)]
        # We give back variables explicitely and do not rely on declare_var and
        # abstract. Otherwise rules are cluttered with useless variables.
        return (z3vars, z3head, z3body)

    def compile_rule(self, type_env, theory, rule):
        # type: (typechecker.GEN_TYPE_ENV, Z3Theory, ast.Rule) -> None
        """compiles a single rule

        :param theory: the theory containing the rule
        :param rule: the rule to compile.
        """
        z3vars, z3head, z3body = self.compile_atoms(
            type_env.get(rule.id, {}), theory, rule.head, rule.body)
        term1 = (z3head if z3body == []
                 else Z3OPT.Implies(Z3OPT.And(*z3body), z3head))
        term2 = term1 if z3vars == [] else Z3OPT.ForAll(z3vars, term1)
        self.context.rule(term2)

    def compile_query(self, theory, literal):
        # type: (Z3Theory, ast.Literal) -> z3.ExprRef
        """compiles a query litteral

        :param theory: theory used as the context of the query
        :param litteral: the query
        :returns: an existentially quantified litteral in Z3 format.
        """
        z3vars, z3head, _ = self.compile_atoms({}, theory, literal, [])
        return z3head if z3vars == [] else Z3OPT.Exists(z3vars, z3head)

    def compile_theory(self, type_env, theory):
        # type: (typechecker.GEN_TYPE_ENV, Z3Theory) -> None
        """Compiles all the rules of a theory

        :param theory: theory to compile. Will be marked clean after.
        """
        self.compile_facts(theory)
        for rules in six.itervalues(theory.rules.rules):
            for rule in rules:
                self.compile_rule(type_env, theory, rule)
        theory.dirty = False

    def compile_all(self, type_env):
        """Compile all Z3 theories"""
        self.relations = {}
        self.externals.clear()
        self.declare_tables()
        self.declare_external_tables()
        for theory in six.itervalues(self.z3theories):
            self.compile_theory(type_env, theory)
        self.last_compiled = time.time()

    def typecheck(self):
        """Typechecker for rules defined"""
        typer = typechecker.Typechecker(
            self.z3theories.values(), self.theories)
        return typer.type_all()

    def inject(self, theoryname, tablename):
        # type: (str, str) -> None
        """Inject the values of an external table in the Z3 Context.

        Loops over the literal retrieved from a standard query.
        """
        theory = self.theories[theoryname]
        translators = [
            self.type_registry.get_translator(str(arg_type.type))
            for arg_type in theory.schema.types(tablename)]
        fullname = theory.name + ':' + tablename
        z3func = self.relations[fullname]
        for lit in retrieve(theory, tablename):
            z3args = (tr.to_z3(v.name, strict=True)
                      for (v, tr) in six.moves.zip(lit.arguments, translators))
            z3fact = z3func(*z3args)
            self.context.fact(z3fact)

    def synchronize_external(self):
        """Synchronize all external tables"""
        for (theoryname, tablename) in self.externals:
            self.inject(theoryname, tablename)
