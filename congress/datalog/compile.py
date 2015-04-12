# Copyright (c) 2013 VMware, Inc. All rights reserved.
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

import copy
import optparse

import antlr3

import CongressLexer
import CongressParser
import utility

from congress.datalog.analysis import ModalIndex
from congress.datalog.builtin import congressbuiltin
from congress.datalog.utility import iterstr
from congress.exception import PolicyException
from congress.openstack.common import log as logging
from congress.utils import Location

LOG = logging.getLogger(__name__)


##############################################################################
# Internal representation of policy language
##############################################################################

# TODO(thinrichs): create a Tablename class
def parse_tablename(tablename):
    """Given tablename returns (service, name)."""
    pieces = tablename.split(':')
    if len(pieces) == 1:
        return (None, pieces[0])
    else:
        return (pieces[0], ':'.join(pieces[1:]))


def build_tablename(service, table):
    return service + ':' + table


class Schema(object):
    """Meta-data about a collection of tables."""
    def __init__(self, dictionary=None, complete=False):
        if dictionary is None:
            self.map = {}
        elif isinstance(dictionary, Schema):
            self.map = dict(dictionary.map)
        else:
            self.map = dictionary
        # whether to assume there is an entry in this schema for
        # every permitted table
        self.complete = complete

    def __contains__(self, tablename):
        return tablename in self.map

    def columns(self, tablename):
        """Returns the list of column names for the given TABLENAME.

        Return None if the tablename's columns are unknown.
        """
        if tablename in self.map:
            return self.map[tablename]

    def arity(self, tablename):
        """Returns the number of columns for the given TABLENAME.

        Return None if TABLENAME is unknown.
        """
        if tablename in self.map:
            return len(self.map[tablename])

    def __str__(self):
        return str(self.map)


class Term(object):
    """Represents the union of Variable and ObjectConstant.

    Should only be instantiated via factory method.
    """
    def __init__(self):
        assert False, "Cannot instantiate Term directly--use factory method"

    @staticmethod
    def create_from_python(value, force_var=False):
        """Create Variable or ObjectConstants.

        To create variable, FORCE_VAR needs to be true.  There is currently
        no way to avoid this since variables are strings.
        """
        if isinstance(value, Term):
            return value
        elif force_var:
            return Variable(str(value))
        elif isinstance(value, basestring):
            return ObjectConstant(value, ObjectConstant.STRING)
        elif isinstance(value, (int, long)):
            return ObjectConstant(value, ObjectConstant.INTEGER)
        elif isinstance(value, float):
            return ObjectConstant(value, ObjectConstant.FLOAT)
        else:
            assert False, "No Term corresponding to {}".format(repr(value))


class Variable (Term):
    """Represents a term without a fixed value."""

    __slots__ = ['name', 'location', '_hash']

    def __init__(self, name, location=None):
        assert isinstance(name, basestring)
        self.name = name
        self.location = location
        self._hash = None

    def __str__(self):
        return str(self.name)

    def __eq__(self, other):
        return isinstance(other, Variable) and self.name == other.name

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        # Use repr to hash rule--can't include location
        return "Variable(name={})".format(repr(self.name))

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(('Variable', hash(self.name)))
        return self._hash

    def is_variable(self):
        return True

    def is_object(self):
        return False


class ObjectConstant (Term):
    """Represents a term with a fixed value."""
    STRING = 'STRING'
    FLOAT = 'FLOAT'
    INTEGER = 'INTEGER'
    __slots__ = ['name', 'type', 'location', '_hash']

    def __init__(self, name, type, location=None):
        assert(type in [self.STRING, self.FLOAT, self.INTEGER])
        self.name = name
        self.type = type
        self.location = location
        self._hash = None

    def __str__(self):
        if self.type == ObjectConstant.STRING:
            return '"' + str(self.name) + '"'
        else:
            return str(self.name)

    def __repr__(self):
        # Use repr to hash rule--can't include location
        return "ObjectConstant(name={}, type={})".format(
            repr(self.name), repr(self.type))

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(('ObjectConstant', hash(self.name),
                               hash(self.type)))
        return self._hash

    def __eq__(self, other):
        return (isinstance(other, ObjectConstant) and
                self.name == other.name and
                self.type == other.type)

    def __ne__(self, other):
        return not self == other

    def is_variable(self):
        return False

    def is_object(self):
        return True


class Fact (tuple):
    """Represent a Fact (a ground literal)

    Use this class to represent a fact such as Foo(1,2,3).  While one could
    use a Rule to represent the same fact, this Fact datastructure is more
    memory efficient than a Rule object since this Fact stores the information
    as a native tuple, containing native values like ints and strings.  Notes
    that this subclasses from tuple.
    """
    def __new__(cls, table, values):
        return super(Fact, cls).__new__(cls, values)

    def __init__(self, table, values):
        super(Fact, self).__init__(table, values)
        self.table = table


class Literal (object):
    """Represents a possibly negated atomic statement, e.g. p(a, 17, b)."""
    __slots__ = ['theory', 'table', 'arguments', 'location', 'negated',
                 '_hash', 'modal']

    def __init__(self, table, arguments, location=None, negated=False,
                 theory=None, modal=None, use_modules=True):
        # if use_modules is True,
        # break full tablename up into 2 pieces.  Example: "nova:servers:cpu"
        # self.theory = "nova"
        # self.table = "servers:cpu"
        if theory is None and use_modules:
            (self.theory, self.table) = self.partition_tablename(table)
        else:
            self.theory = theory
            self.table = table
        self.modal = modal
        self.arguments = arguments
        self.location = location
        self.negated = negated
        self._hash = None

    def __copy__(self):
        newone = Literal(self.table, self.arguments, self.location,
                         self.negated, self.theory, self.modal)
        return newone

    @classmethod
    def partition_tablename(cls, tablename):
        """Cut string TABLENAME into the theory and the name of the table."""
        (theory, sep, table) = tablename.rpartition(':')
        if theory == '':
            return (None, table)
        return (theory, table)

    @classmethod
    def create_from_table_tuple(cls, table, tuple):
        """Create Literal from table and tuple.

        TABLE is the tablename.
        TUPLE is a python list representing a row, e.g.
        [17, "string", 3.14].  Returns the corresponding Literal.
        """
        return cls(table, [Term.create_from_python(x) for x in tuple])

    @classmethod
    def create_from_iter(cls, list):
        """Create Literal from list.

        LIST is a python list representing an atom, e.g.
        ['p', 17, "string", 3.14].  Returns the corresponding Literal.
        """
        arguments = []
        for i in xrange(1, len(list)):
            arguments.append(Term.create_from_python(list[i]))
        return cls(list[0], arguments)

    def __str__(self):
        s = "{}({})".format(self.tablename(),
                            ", ".join([str(x) for x in self.arguments]))
        if self.modal is not None:
            s = "{}[{}]".format(self.modal, s)
        if self.negated:
            s = "not " + s
        return s

    def pretty_str(self):
        return self.__str__()

    def __eq__(self, other):
        return (isinstance(other, Literal) and
                self.table == other.table and
                self.theory == other.theory and
                self.negated == other.negated and
                len(self.arguments) == len(other.arguments) and
                all(self.arguments[i] == other.arguments[i]
                    for i in xrange(0, len(self.arguments))))

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        # Use repr to hash Rule--don't include location
        return ("Literal(modal={}, theory={}, table={}, arguments={}, "
                "negated={})").format(
            repr(self.modal),
            repr(self.theory),
            repr(self.table),
            "[" + ",".join(repr(arg) for arg in self.arguments) + "]",
            repr(self.negated))

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(('Literal', hash(self.theory), hash(self.table),
                               tuple([hash(a) for a in self.arguments]),
                               hash(self.negated)))
        return self._hash

    def is_negated(self):
        return self.negated

    def is_atom(self):
        return not self.negated

    def is_rule(self):
        return False

    def variable_names(self):
        return set([x.name for x in self.arguments if x.is_variable()])

    def variables(self):
        return set([x for x in self.arguments if x.is_variable()])

    def is_ground(self):
        return all(not arg.is_variable() for arg in self.arguments)

    def plug(self, binding, caller=None):
        """Assumes domain of BINDING is Terms."""
        new = copy.copy(self)
        if isinstance(binding, dict):
            args = []
            for arg in self.arguments:
                if arg in binding:
                    args.append(Term.create_from_python(binding[arg]))
                else:
                    args.append(arg)
            new.arguments = args
            return new
        else:
            args = [Term.create_from_python(binding.apply(arg, caller))
                    for arg in self.arguments]
            new.arguments = args
            return new

    def argument_names(self):
        return tuple([arg.name for arg in self.arguments])

    def complement(self):
        """Copies SELF and inverts is_negated."""
        new = copy.copy(self)
        new.negated = not new.negated
        return new

    def make_positive(self):
        """Return handle to self or copy of self based on positive check.

        Either returns SELF if is_negated() is false or
        returns copy of SELF where is_negated() is set to false.
        """
        if self.negated:
            new = copy.copy(self)
            new.negated = False
            return new
        else:
            return self

    def invert_update(self):
        """Invert the update.

        If end of table name is + or -, return a copy after switching
        the copy's sign.
        Does not make a copy if table name does not end in + or -.
        """
        if self.table.endswith('+'):
            suffix = '-'
        elif self.table.endswith('-'):
            suffix = '+'
        else:
            suffix = None

        if suffix is None:
            return self
        else:
            new = copy.copy(self)
            new.table = new.table[:-1] + suffix
            return new

    def drop_update(self):
        """Drop the update.

        If end of table name is + or -, return a copy without the sign.
        If table name does not end in + or -, make no copy.
        """
        if self.table.endswith('+') or self.table.endswith('-'):
            new = copy.copy(self)
            new.table = new.table[:-1]
            return new
        else:
            return self

    def make_update(self, is_insert=True):
        new = copy.copy(self)
        if is_insert:
            new.table = new.table + "+"
        else:
            new.table = new.table + "-"
        return new

    def is_update(self):
        return self.table.endswith('+') or self.table.endswith('-')

    def tablename(self, theory=None):
        return full_tablename(self.table, self.theory, theory)

    def theory_name(self):
        return self.theory

    def drop_theory(self):
        """Destructively sets the theory to None."""
        self._hash = None
        self.theory = None
        return self


class Rule (object):
    """Represents a rule, e.g. p(x) :- q(x)."""

    __slots__ = ['heads', 'head', 'body', 'location', '_hash']

    def __init__(self, head, body, location=None):
        # self.head is self.heads[0]
        # Keep self.head around since a rule with multiple
        #   heads is not used by reasoning algorithms.
        # Most code ignores self.heads entirely.
        if is_literal(head):
            self.heads = [head]
            self.head = head
        else:
            self.heads = head
            self.head = self.heads[0]
        self.body = body
        self.location = location
        self._hash = None

    def __copy__(self):
        newone = Rule(self.head, self.body, self.location)
        return newone

    def __str__(self):
        if len(self.body) == 0:
            return " ".join([str(atom) for atom in self.heads])
        return "{} :- {}".format(
            ", ".join([str(atom) for atom in self.heads]),
            ", ".join([str(lit) for lit in self.body]))

    def pretty_str(self):
        if len(self.body) == 0:
            return self.__str__()
        else:
            return "{} :- \n    {}".format(
                ", ".join([str(atom) for atom in self.heads]),
                ",\n    ".join([str(lit) for lit in self.body]))

    def __eq__(self, other):
        return (isinstance(other, Rule) and
                len(self.heads) == len(other.heads) and
                len(self.body) == len(other.body) and
                all(self.heads[i] == other.heads[i]
                    for i in xrange(0, len(self.heads))) and
                all(self.body[i] == other.body[i]
                    for i in xrange(0, len(self.body))))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return "Rule(head={}, body={}, location={})".format(
            "[" + ",".join(repr(arg) for arg in self.heads) + "]",
            "[" + ",".join(repr(arg) for arg in self.body) + "]",
            repr(self.location))

    def __hash__(self):
        # won't properly treat a positive literal and an atom as the same
        if self._hash is None:
            self._hash = hash(('Rule', tuple([hash(h) for h in self.heads]),
                               tuple([hash(b) for b in self.body])))
        return self._hash

    def is_atom(self):
        return False

    def is_rule(self):
        return True

    def tablename(self, theory=None):
        return self.head.tablename(theory)

    def theory_name(self):
        return self.head.theory

    def drop_theory(self):
        """Destructively sets the theory to None in all heads."""
        for head in self.heads:
            head.drop_theory()
        self._hash = None
        return self

    def tablenames(self, theory=None):
        """Return all the tablenames occurring in this rule."""
        result = set()
        for lit in self.heads:
            result.add(lit.tablename(theory))
        for lit in self.body:
            result.add(lit.tablename(theory))
        return result

    def variables(self):
        vs = set()
        for lit in self.heads:
            vs |= lit.variables()
        for lit in self.body:
            vs |= lit.variables()
        return vs

    def variable_names(self):
        vs = set()
        for lit in self.heads:
            vs |= lit.variable_names()
        for lit in self.body:
            vs |= lit.variable_names()
        return vs

    def plug(self, binding, caller=None):
        newheads = self.plug_heads(binding, caller)
        newbody = self.plug_body(binding, caller)
        return Rule(newheads, newbody)

    def plug_body(self, binding, caller=None):
        return [lit.plug(binding, caller=caller) for lit in self.body]

    def plug_heads(self, binding, caller=None):
        return [atom.plug(binding, caller=caller) for atom in self.heads]

    def invert_update(self):
        new = copy.copy(self)
        new.heads = [atom.invert_update() for atom in self.heads]
        new.head = new.heads[0]
        return new

    def drop_update(self):
        new = copy.copy(self)
        new.heads = [atom.drop_update() for atom in self.heads]
        new.head = new.heads[0]
        return new

    def make_update(self, is_insert=True):
        new = copy.copy(self)
        new.heads = [atom.make_update(is_insert) for atom in self.heads]
        new.head = new.heads[0]
        return new

    def is_update(self):
        return (self.head.table.endswith('+') or
                self.head.table.endswith('-'))


class Event(object):
    """Represents a change to a formula."""

    __slots__ = ['formula', 'proofs', 'insert', 'target']

    def __init__(self, formula=None, insert=True, proofs=None, target=None):
        if proofs is None:
            proofs = []
        self.formula = formula
        self.proofs = proofs
        self.insert = insert
        self.target = target

    def is_insert(self):
        return self.insert

    def tablename(self):
        return self.formula.tablename()

    def __str__(self):
        if self.insert:
            text = "insert"
        else:
            text = "delete"
        if self.target is None:
            target = ""
        else:
            target = " for {}".format(str(self.target))
        return "{}[{}]{}".format(
            text, str(self.formula), target)

    def lstr(self):
        return self.__str__() + " with proofs " + iterstr(self.proofs)

    def __hash__(self):
        return hash("Event(formula={}, proofs={}, insert={}".format(
            str(self.formula), str(self.proofs), str(self.insert)))

    def __eq__(self, other):
        return (self.formula == other.formula and
                self.proofs == other.proofs and
                self.insert == other.insert)

    def __ne__(self, other):
        return not self.__eq__(other)


def full_tablename(table, theory, default_theory=None):
    theory = theory or default_theory
    if theory is None:
        return table
    return theory + ":" + table


def formulas_to_string(formulas):
    """Convert formulas to string.

    Takes an iterable of compiler sentence objects and returns a
    string representing that iterable, which the compiler will parse
    into the original iterable.

    """
    if formulas is None:
        return "None"
    return " ".join([str(formula) for formula in formulas])


def is_update(x):
    """Returns T iff x is a formula or tablename representing an update."""
    if isinstance(x, basestring):
        return x.endswith('+') or x.endswith('-')
    elif is_atom(x):
        return is_update(x.table)
    elif is_regular_rule(x):
        return is_update(x.head.table)
    else:
        return False


def is_result(x):
    """Check if x is result representation.

    Returns T iff x is a formula or tablename representing the result of
    an action invocation.
    """
    if isinstance(x, basestring):
        return x == 'result'
    elif is_atom(x):
        return is_update(x.table)
    elif is_rule(x):
        return is_update(x.head.table)
    else:
        return False


def is_recursive(x):
    """Check for recursive.

    X can be either a Graph or a list of rules.
    Returns T iff the list of rules RULES has a table defined in Terms
    of itself.
    """
    if isinstance(x, utility.Graph):
        return x.has_cycle()
    return RuleDependencyGraph(x).has_cycle()


def stratification(rules):
    """Stratify the rules.

    Returns a dictionary from table names to an integer representing
    the strata to which the table is assigned or None if the rules
    are not stratified.
    """
    return RuleDependencyGraph(rules).stratification([True])


def is_stratified(rules):
    """Check if rules are stratified.

    Returns T iff the list of rules RULES has no table defined in terms
    of its negated self.
    """
    return stratification(rules) is not None


class RuleDependencyGraph(utility.BagGraph):
    """A Graph representing the table dependencies of rules.

    Returns a Graph that includes one node for each table and an edge
    <u,v> if there is some rule with u in the head and v in the body.
    THEORY is the name of the theory to be used for any literal whose
    theory is None.
    INCLUDE_ATOMS is a boolean controlling whether atoms should contribute
    to nodes.
    SELECT_HEAD is a function that returns True for those head literals
    that should be included in the graph.
    SELECT_BODY is a function that returns True for those body literals
    that should be included in the graph.
    HEAD_TO_BODY controls whether edges are oriented from the tables in
    the head toward the tables in the body, or vice versa.
    """
    def __init__(self, formulas=None, theory=None, include_atoms=True,
                 select_head=None, select_body=None, head_to_body=True):
        super(RuleDependencyGraph, self).__init__()
        # direction of edges
        self.head_to_body = head_to_body
        # dict from modal name to set of tablenames appearing in rule head
        #   with that modal (with refcounts)
        self.modal_index = ModalIndex()
        # insert formulas
        if formulas:
            for formula in formulas:
                self.formula_insert(
                    formula,
                    theory=theory,
                    include_atoms=include_atoms,
                    select_head=select_head,
                    select_body=select_body)

    def formula_update(self, events,
                       include_atoms=True, select_head=None, select_body=None):
        """Modify graph with inserts/deletes in EVENTS.

        Returns list of changes.
        """
        changes = []
        for event in events:
            theory = event.target
            nodes, edges, modals = self.formula_nodes_edges(
                event.formula,
                theory=theory,
                include_atoms=include_atoms,
                select_head=select_head,
                select_body=select_body)
            if event.insert:
                for node in nodes:
                    self.add_node(node)
                    changes.append(('node', node, True))
                for (src, dst, label) in edges:
                    self.add_edge(src, dst, label)
                    changes.append(('edge', src, dst, label, True))
                self.modal_index += modals
                changes.append(('modal', modals, True))
            else:
                for node in nodes:
                    self.delete_node(node)
                    changes.append(('node', node, False))
                for (src, dst, label) in edges:
                    self.delete_edge(src, dst, label)
                    changes.append(('edge', src, dst, label, False))
                self.modal_index -= modals
                changes.append(('modal', modals, False))
        return changes

    def undo_changes(self, changes):
        """Reverse the given changes.

        Each change is either ('node', <node>, <is-insert>) or
        ('edge', <src_node>, <dst_node>, <label>, <is_insert>) or
        ('modal', <modal-index>, <is-insert>).
        """
        for change in changes:
            if change[0] == 'node':
                if change[2]:
                    self.delete_node(change[1])
                else:
                    self.add_node(change[1])
            elif change[0] == 'edge':
                if change[4]:
                    self.delete_edge(change[1], change[2], change[3])
                else:
                    self.add_edge(change[1], change[2], change[3])
            else:
                assert change[0] == 'modal', 'unknown change type'
                if change[2]:
                    self.modal_index -= change[1]
                else:
                    self.modal_index += change[1]

    def formula_insert(self, formula, theory=None, include_atoms=True,
                       select_head=None, select_body=None):
        """Insert rows/edges for the given FORMULA."""
        return self.formula_update(
            [Event(formula, target=theory, insert=True)],
            include_atoms=include_atoms,
            select_head=select_head,
            select_body=select_body)

    def formula_delete(self, formula, theory=None, include_atoms=True,
                       select_head=None, select_body=None):
        """Delete rows/edges for the given FORMULA."""
        return self.formula_update(
            [Event(formula, target=theory, insert=False)],
            include_atoms=include_atoms,
            select_head=select_head,
            select_body=select_body)

    def tables_with_modal(self, modal):
        return self.modal_index.tables(modal)

    def formula_nodes_edges(self, formula, theory=None, include_atoms=True,
                            select_head=None, select_body=None):
        """Compute dependency graph nodes and edges for FORMULA.

        Returns (NODES, EDGES, MODALS), where NODES/EDGES are sets and
        MODALS is a ModalIndex.  Each EDGE is a tuple of the form
        (source, destination, label).
        """
        nodes = set()
        edges = set()
        modals = ModalIndex()
        if is_atom(formula):
            if include_atoms:
                table = formula.tablename(theory)
                nodes.add(table)
                if formula.modal:
                    modals.add(formula.modal, table)
        else:
            for head in formula.heads:
                if select_head is not None and not select_head(head):
                    continue
                head_table = head.tablename(theory)
                if head.modal:
                    modals.add(head.modal, head_table)
                nodes.add(head_table)
                for lit in formula.body:
                    if select_body is not None and not select_body(lit):
                        continue
                    lit_table = lit.tablename(theory)
                    nodes.add(lit_table)
                    # label on edge is True for negation, else False
                    if self.head_to_body:
                        edges.add((head_table, lit_table, lit.is_negated()))
                    else:
                        edges.add((lit_table, head_table, lit.is_negated()))
        return (nodes, edges, modals)


def reorder_for_safety(rule):
    """Reorder the rule.

    Moves builtins/negative literals so that when left-to-right evaluation
    is performed all of a builtin's inputs are bound by the time that builtin
    is evaluated.  Reordering is stable, meaning that if the rule is
    properly ordered, no changes are made.
    """
    if not is_rule(rule):
        return rule
    safe_vars = set()
    unsafe_literals = []
    unsafe_variables = {}  # dictionary from literal to its unsafe vars
    new_body = []

    def make_safe(lit):
        safe_vars.update(lit.variable_names())
        new_body.append(lit)

    def make_safe_plus(lit):
        make_safe(lit)
        found_safe = True
        while found_safe:
            found_safe = False
            for unsafe_lit in unsafe_literals:
                if unsafe_variables[unsafe_lit] <= safe_vars:
                    unsafe_literals.remove(unsafe_lit)
                    make_safe(unsafe_lit)
                    found_safe = True
                    break  # so that we reorder as little as possible

    for lit in rule.body:
        target_vars = None
        if lit.is_negated():
            target_vars = lit.variable_names()
        elif congressbuiltin.builtin_registry.is_builtin(lit.table,
                                                         len(lit.arguments)):
            builtin = congressbuiltin.builtin_registry.builtin(lit.table)
            target_vars = lit.arguments[0:builtin.num_inputs]
            target_vars = set([x.name for x in target_vars if x.is_variable()])
        else:
            # neither a builtin nor negated
            make_safe_plus(lit)
            continue

        new_unsafe_vars = target_vars - safe_vars
        if new_unsafe_vars:
            unsafe_literals.append(lit)
            unsafe_variables[lit] = new_unsafe_vars
        else:
            make_safe_plus(lit)

    if len(unsafe_literals) > 0:
        lit_msgs = [str(lit) + " (vars " + str(unsafe_variables[lit]) + ")"
                    for lit in unsafe_literals]
        raise PolicyException(
            "Could not reorder rule {}.  Unsafe lits: {}".format(
                str(rule), "; ".join(lit_msgs)))
    rule.body = new_body
    return rule


def fact_errors(atom, theories=None, theory=None):
    """Checks if ATOM has any errors.

    THEORIES is a dictionary mapping a theory name to a theory object.
    """
    assert atom.is_atom(), "fact_errors expects an atom"
    errors = []
    if not atom.is_ground():
        errors.append(PolicyException("Fact not ground: " + str(atom)))
    errors.extend(literal_schema_consistency(atom, theories, theory))
    errors.extend(fact_has_no_theory(atom))
    return errors


def fact_has_no_theory(atom):
    """Checks that ATOM has an empty theory.  Returns exceptions."""
    if atom.theory is None:
        return []
    return [PolicyException(
        "Fact {} should not reference any policy: {}".format(
            str(atom), str(atom.theory)))]


def rule_head_safety(rule):
    """Checks if every variable in the head of RULE is also in the body.

    Returns list of exceptions.
    """
    assert not rule.is_atom(), "rule_head_safety expects a rule"
    errors = []
    # Variables in head must appear in body
    head_vars = set()
    body_vars = set()
    for head in rule.heads:
        head_vars |= head.variables()
    for lit in rule.body:
        body_vars |= lit.variables()
    unsafe = head_vars - body_vars
    for var in unsafe:
        errors.append(PolicyException(
            "Variable {} found in head but not in body, rule {}".format(
                str(var), str(rule)),
            obj=var))
    return errors


def rule_head_has_no_theory(rule, permit_head=None):
    """Checks if head of rule has None for theory.  Returns exceptions.

    PERMIT_HEAD is a function that takes a literal as argument and returns
    True if the literal is allowed to have a theory in the head.
    """
    errors = []
    for head in rule.heads:
        if (head.theory is not None and
           (not permit_head or not permit_head(head))):
            errors.append(PolicyException(
                "Rule head {} should not reference any policy: {}".format(
                    str(head), str(rule))))
    return errors


def rule_body_safety(rule):
    """Check rule body for safety.

    Checks if every variable in a negative literal also appears in
    a positive literal in the body.  Checks if every variable
    in a builtin input appears in the body. Returns list of exceptions.
    """
    assert not rule.is_atom(), "rule_body_safety expects a rule"
    try:
        reorder_for_safety(rule)
        return []
    except PolicyException as e:
        return [e]


def rule_schema_consistency(rule, theories, theory=None):
    """Returns list of problems with rule's schema."""
    assert not rule.is_atom(), "rule_schema_consistency expects a rule"
    errors = []
    for lit in rule.body:
        errors.extend(literal_schema_consistency(lit, theories, theory))
    return errors


def literal_schema_consistency(literal, theories, theory=None):
    """Returns list of errors."""
    if theories is None:
        return []

    # figure out theory that pertains to this literal
    active_theory = literal.theory or theory

    # if current theory is unknown, no violation of schema
    if active_theory is None:
        return []

    # check if known module
    if active_theory not in theories:
        # May not have been created yet
        return []

    # if schema is unknown, no errors with schema
    schema = theories[active_theory].schema
    if schema is None:
        return []

    # check if known table
    if literal.table not in schema:
        if schema.complete:
            return [PolicyException(
                "Literal {} uses unknown table {} "
                "from policy {}".format(
                    str(literal), str(literal.table), str(active_theory)))]
        else:
            # may not have a declaration for this table's columns
            return []

    # check width
    arity = schema.arity(literal.table)
    if arity and len(literal.arguments) != arity:
        return [PolicyException(
            "Literal {} contained {} arguments but only "
            "{} arguments are permitted".format(
                str(literal), len(literal.arguments), arity))]

    return []


def rule_errors(rule, theories=None, theory=None):
    """Returns list of errors for RULE."""
    errors = []
    errors.extend(rule_head_safety(rule))
    errors.extend(rule_body_safety(rule))
    errors.extend(rule_schema_consistency(rule, theories, theory))
    errors.extend(rule_head_has_no_theory(rule))
    return errors


# Type-checkers
def is_atom(x):
    """Returns True if object X is an atomic Datalog formula."""
    return isinstance(x, Literal) and not x.is_negated()


def is_literal(x):
    """Check if x is Literal.

    Returns True if X is a possibly negated atomic Datalog formula
    and one that if replaced by an ATOM syntactically be replaced by an ATOM.
    """
    return isinstance(x, Literal)


def is_rule(x):
    """Returns True if x is a rule."""
    return (isinstance(x, Rule) and
            all(is_atom(y) for y in x.heads) and
            all(is_literal(y) for y in x.body))


def is_regular_rule(x):
    """Returns True if X is a rule with a single head."""
    return (is_rule(x) and len(x.heads) == 1)


def is_multi_rule(x):
    """Returns True if X is a rule with multiple heads."""
    return (is_rule(x) and len(x.heads) != 1)


def is_datalog(x):
    """Returns True if X is an atom or a rule with one head."""
    return is_atom(x) or is_regular_rule(x)


def is_extended_datalog(x):
    """Returns True if X is a valid datalog sentence.

    Allows X to be a multi_rule in addition to IS_DATALOG().
    """
    return is_rule(x) or is_atom(x)


##############################################################################
# Compiler
##############################################################################


class Compiler (object):
    """Process Congress policy file."""
    def __init__(self):
        self.raw_syntax_tree = None
        self.theory = []
        self.errors = []
        self.warnings = []

    def __str__(self):
        s = ""
        s += '**Theory**\n'
        if self.theory is not None:
            s += '\n'.join([str(x) for x in self.theory])
        else:
            s += 'None'
        return s

    def read_source(self, input, input_string=False, theories=None,
                    use_modules=True):
        syntax = DatalogSyntax(theories, use_modules)
        # parse input file and convert to internal representation
        self.raw_syntax_tree = syntax.parse_file(
            input, input_string=input_string)
        self.theory = syntax.convert_to_congress(self.raw_syntax_tree)
        if syntax.errors:
            self.errors = syntax.errors
        self.raise_errors()

    def print_parse_result(self):
        print_tree(
            self.raw_syntax_tree,
            lambda x: x.getText(),
            lambda x: x.children,
            ind=1)

    def sigerr(self, error):
        self.errors.append(error)

    def sigwarn(self, error):
        self.warnings.append(error)

    def raise_errors(self):
        if len(self.errors) > 0:
            errors = [str(err) for err in self.errors]
            raise PolicyException(
                'Compiler found errors:' + '\n'.join(errors))


##############################################################################
# External syntax: datalog
##############################################################################

class DatalogSyntax(object):
    """Read Datalog syntax and convert it to internal representation."""

    def __init__(self, theories=None, use_modules=True):
        self.theories = theories or {}
        self.errors = []
        self.use_modules = use_modules

    class Lexer(CongressLexer.CongressLexer):
        def __init__(self, char_stream, state=None):
            self.error_list = []
            CongressLexer.CongressLexer.__init__(self, char_stream, state)

        def displayRecognitionError(self, token_names, e):
            hdr = self.getErrorHeader(e)
            msg = self.getErrorMessage(e, token_names)
            self.error_list.append(str(hdr) + "  " + str(msg))

        def getErrorHeader(self, e):
            return "line:{},col:{}".format(
                e.line, e.charPositionInLine)

    class Parser(CongressParser.CongressParser):
        def __init__(self, tokens, state=None):
            self.error_list = []
            CongressParser.CongressParser.__init__(self, tokens, state)

        def displayRecognitionError(self, token_names, e):
            hdr = self.getErrorHeader(e)
            msg = self.getErrorMessage(e, token_names)
            self.error_list.append(str(hdr) + "  " + str(msg))

        def getErrorHeader(self, e):
            return "line:{},col:{}".format(
                e.line, e.charPositionInLine)

    @classmethod
    def parse_file(cls, input, input_string=False):
        if not input_string:
            char_stream = antlr3.ANTLRFileStream(input)
        else:
            char_stream = antlr3.ANTLRStringStream(input)

        # Obtain LEXER
        lexer = cls.Lexer(char_stream)

        # Obtain ANTLR Token stream
        tokens = antlr3.CommonTokenStream(lexer)

        # Obtain PARSER derive parse tree
        parser = cls.Parser(tokens)
        result = parser.prog()
        if len(lexer.error_list) > 0:
            raise PolicyException("Lex failure.\n" +
                                  "\n".join(lexer.error_list))
        if len(parser.error_list) > 0:
            raise PolicyException("Parse failure.\n" +
                                  "\n".join(parser.error_list))
        return result.tree

    def convert_to_congress(self, antlr):
        return self.create(antlr)

    def create(self, antlr):
        obj = antlr.getText()
        if obj == 'RULE':
            rule = self.create_rule(antlr)
            return rule
        elif obj == 'NOT':
            return self.create_literal(antlr)
        elif obj == 'MODAL':
            return self.create_modal_atom(antlr)
        elif obj == 'ATOM':
            return self.create_modal_atom(antlr)
        elif obj == 'THEORY':
            children = []
            for x in antlr.children:
                xchild = self.create(x)
                children.append(xchild)
            return [self.create(x) for x in antlr.children]
        elif obj == '<EOF>':
            return []
        else:
            raise PolicyException(
                "Antlr tree with unknown root: {}".format(obj))

    def create_rule(self, antlr):
        # (RULE (AND1 AND2))
        prefix = self.unused_variable_prefix(antlr)
        heads = self.create_and_literals(antlr.children[0], prefix)
        body = self.create_and_literals(antlr.children[1], prefix)
        loc = Location(line=antlr.children[0].token.line,
                       col=antlr.children[0].token.charPositionInLine)
        return Rule(heads, body, location=loc)

    def create_and_literals(self, antlr, prefix):
        # (AND (LIT1 ... LITN))
        return [self.create_literal(child, index, prefix)
                for (index, child) in enumerate(antlr.children)]

    def create_literal(self, antlr, index=-1, prefix=''):
        # (NOT <atom>)
        # <atom>
        # (NOT (MODAL ID <atom>))
        # (MODAL ID <atom>)
        if antlr.getText() == 'NOT':
            negated = True
            antlr = antlr.children[0]
        else:
            negated = False

        lit = self.create_modal_atom(antlr, index, prefix)
        lit.negated = negated
        return lit

    def create_modal_atom(self, antlr, index=-1, prefix=''):
        # (MODAL ID <atom>)
        # <atom>
        if antlr.getText() == 'MODAL':
            modal = antlr.children[0].getText()
            atom = antlr.children[1]
        else:
            modal = None
            atom = antlr
        (table, args, loc) = self.create_atom_aux(atom, index, prefix)
        return Literal(table, args, location=loc, modal=modal,
                       use_modules=self.use_modules)

    def create_atom_aux(self, antlr, index, prefix):
        # (ATOM (TABLENAME ARG1 ... ARGN))
        table = self.create_structured_name(antlr.children[0])
        if self.use_modules:
            theory, tablename = Literal.partition_tablename(table)
        else:
            theory = None
            tablename = table
        loc = Location(line=antlr.children[0].token.line,
                       col=antlr.children[0].token.charPositionInLine)

        # Construct args (without column references)
        has_named_param = any(x for x in antlr.children
                              if x.getText() == 'NAMED_PARAM')

        # Find the schema for this table if we know it.
        columns = None
        if theory in self.theories:
            schema = self.theories[theory].schema
            if schema is not None and tablename in schema:
                columns = schema.columns(tablename)
        # Compute the args, after having converted them to Terms
        args = []
        if columns is None:
            if has_named_param:
                self.errors.append(PolicyException(
                    "Atom {} uses named parameters but the columns for "
                    "table {} have not been declared.".format(
                        self.antlr_atom_str(antlr), table)))
            else:
                args = [self.create_term(antlr.children[i])
                        for i in xrange(1, len(antlr.children))]
        else:
            args = self.create_atom_arg_list(antlr, index, prefix, columns)
        return (table, args, loc)

    def create_atom_arg_list(self, antlr, index, prefix, columns):
        """Get parameter list representation in atom.

        Return a list of compile.Term representing the parameter list
        specified in atom ANTLR.  If there are errors, the empty list
        is returned and self.errors is modified; otherwise,
        the length of the return list is len(COLUMNS).
        """
        # (ATOM (TABLENAME ARG1 ... ARGN))
        # construct string representation of atom for error messages
        atomstr = self.antlr_atom_str(antlr)

        # partition into regular args and column-ref args
        errors = []
        position_args = []
        reference_args = []
        for i in xrange(1, len(antlr.children)):
            if antlr.children[i].getText() != 'NAMED_PARAM':
                position_args.append(self.create_term(antlr.children[i]))
            else:
                reference_args = antlr.children[i:]
                break

        # index the column refs and translate into Terms
        names = {}
        numbers = {}
        column_int = dict([reversed(x) for x in enumerate(columns)])
        for param in reference_args:
            # (NAMED_PARAM (COLUMN_REF TERM))
            if param.getText() != 'NAMED_PARAM':
                errors.append(PolicyException(
                    "Atom {} has a positional parameter after "
                    "a reference parameter".format(
                        atomstr)))
            elif param.children[0].getText() == 'COLUMN_NAME':
                # (COLUMN_NAME (ID))
                name = param.children[0].children[0].getText()
                if name in names:
                    errors.append(PolicyException(
                        "In atom {} two values for column name {} "
                        "were provided".format(atomstr, name)))
                names[name] = self.create_term(param.children[1])
                if name not in column_int:
                    errors.append(PolicyException(
                        "In atom {} column name {} does not exist".format(
                            atomstr, name)))
                else:
                    number = column_int[name]
                    if number < len(position_args):
                        errors.append(PolicyException(
                            "In atom {} column name {} references position {},"
                            " which is already provided by position "
                            "arguments.".format(
                                atomstr, name, str(number))))
            else:
                # (COLUMN_NUMBER (INT))
                # Know int() will succeed because of lexer
                number = int(param.children[0].children[0].getText())
                if number in numbers:
                    errors.append(PolicyException(
                        "In atom {} two values for column number {} "
                        "were provided.".format(atomstr, str(number))))
                numbers[number] = self.create_term(param.children[1])
                if number < len(position_args):
                    errors.append(PolicyException(
                        "In atom {} column number {} is already provided by "
                        "position arguments.".format(
                            atomstr, number)))
                if number >= len(columns):
                    errors.append(PolicyException(
                        "In atom {} column number {} is too large. The "
                        "permitted column numbers are 0..{} ".format(
                            atomstr, number, len(columns) - 1)))
        if errors:
            self.errors.extend(errors)
            return []

        # turn reference args into position args
        for i in xrange(len(position_args), len(columns)):
            name = names.get(columns[i], None)  # a Term or None
            number = numbers.get(i, None)       # a Term or None
            if name is not None and number is not None:
                errors.append(PolicyException(
                    "In atom {} a column was given two values by reference "
                    "parameters: one by name {} and one by number {}. ".format(
                        atomstr, name, str(number))))
            elif name is not None:
                position_args.append(name)
            elif number is not None:
                position_args.append(number)
            else:
                newvar = prefix + "x_{}_{}".format(index, i)
                position_args.append(Variable(newvar))
        if errors:
            self.errors.extend(errors)
            return []
        return position_args

    def antlr_atom_str(self, antlr):
        # (ATOM (TABLENAME ARG1 ... ARGN))
        table = self.create_structured_name(antlr.children[0])
        argstrs = []
        for i in xrange(1, len(antlr.children)):
            arg = antlr.children[i]
            if arg.getText() == 'NAMED_PARAM':
                arg = (arg.children[0].children[0].getText() +
                       '=' +
                       arg.children[1].children[0].getText())
                argstrs.append(arg)
            else:
                arg = arg.children[0].getText()
        return table + "(" + ",".join(argstrs) + ")"

    def create_structured_name(self, antlr):
        # (STRUCTURED_NAME (ARG1 ... ARGN))
        if antlr.children[-1].getText() in ['+', '-']:
            return (":".join([x.getText() for x in antlr.children[:-1]]) +
                    antlr.children[-1].getText())
        else:
            return ":".join([x.getText() for x in antlr.children])

    def create_term(self, antlr):
        # (TYPE (VALUE))
        op = antlr.getText()
        loc = Location(line=antlr.children[0].token.line,
                       col=antlr.children[0].token.charPositionInLine)
        if op == 'STRING_OBJ':
            value = antlr.children[0].getText()
            return ObjectConstant(value[1:len(value) - 1],  # prune quotes
                                  ObjectConstant.STRING,
                                  location=loc)
        elif op == 'INTEGER_OBJ':
            return ObjectConstant(int(antlr.children[0].getText()),
                                  ObjectConstant.INTEGER,
                                  location=loc)
        elif op == 'FLOAT_OBJ':
            return ObjectConstant(float(antlr.children[0].getText()),
                                  ObjectConstant.FLOAT,
                                  location=loc)
        elif op == 'VARIABLE':
            return Variable(self.variable_name(antlr), location=loc)
        else:
            raise PolicyException("Unknown term operator: {}".format(op))

    def unused_variable_prefix(self, antlr_rule):
        """Get unused variable prefix.

        Returns variable prefix (string) that is used by no other variable
        in the rule ANTLR_RULE.
        """
        variables = self.rule_variables(antlr_rule)
        found = False
        prefix = "_"
        while not found:
            if next((var for var in variables if var.startswith(prefix)),
                    False):
                prefix += "_"
            else:
                found = True
        return prefix

    def rule_variables(self, antlr_rule):
        """Get variables in the rule.

        Returns a set of all variable names (as strings) that
        occur in the given rule ANTLR_RULE.
        """
        # (RULE (AND1 AND2))
        # grab all variable names for given atom
        variables = set()
        variables |= self.literal_and_vars(antlr_rule.children[0])
        variables |= self.literal_and_vars(antlr_rule.children[1])
        return variables

    def literal_and_vars(self, antlr_and):
        # (AND (ARG1 ... ARGN))
        variables = set()
        for literal in antlr_and.children:
            # (NOT (ATOM (TABLE ARG1 ... ARGN)))
            # (ATOM (TABLE ARG1 ... ARGN))
            if literal.getText() == 'NOT':
                literal = literal.children[0]
            variables |= self.atom_vars(literal)
        return variables

    def atom_vars(self, antlr_atom):
        # (ATOM (TABLENAME ARG1 ... ARGN))
        variables = set()
        for i in xrange(1, len(antlr_atom.children)):
            antlr = antlr_atom.children[i]
            op = antlr.getText()
            if op == 'VARIABLE':
                variables.add(self.variable_name(antlr))
            elif op == 'NAMED_PARAM':
                # (NAMED_PARAM (COLUMN-REF TERM))
                term = antlr.children[1]
                if term.getText() == 'VARIABLE':
                    variables.add(self.variable_name(term))
        return variables

    def variable_name(self, antlr):
        # (VARIABLE (ID))
        return "".join([child.getText() for child in antlr.children])


def print_tree(tree, text, kids, ind=0):
    """Helper function for printing.

    Print out TREE using function TEXT to extract node description and
    function KIDS to compute the children of a given node.
    IND is a number representing the indentation level.
    """
    print("|" * ind)
    print("{}".format(str(text(tree))))
    children = kids(tree)
    if children:
        for child in children:
            print_tree(child, text, kids, ind + 1)


##############################################################################
# Mains
##############################################################################

def parse(policy_string, theories=None, use_modules=True):
    """Run compiler on policy string and return the parsed formulas."""
    compiler = get_compiler(
        [policy_string, '--input_string'], theories=theories,
        use_modules=use_modules)
    return compiler.theory


def parse1(policy_string, theories=None, use_modules=True):
    """Run compiler on policy string and return 1st parsed formula."""
    return parse(policy_string, theories=theories, use_modules=use_modules)[0]


def parse_file(filename, theories=None):
    """Compile the file.

    Run compiler on policy stored in FILENAME and return the parsed
    formulas.
    """
    compiler = get_compiler([filename], theories=theories)
    return compiler.theory


def get_compiler(args, theories=None, use_modules=True):
    """Run compiler as per ARGS and return the compiler object."""
    # assumes script name is not passed
    parser = optparse.OptionParser()
    parser.add_option(
        "--input_string", dest="input_string", default=False,
        action="store_true",
        help="Indicates that inputs should be treated not as file names but "
             "as the contents to compile")
    (options, inputs) = parser.parse_args(args)
    compiler = Compiler()
    for i in inputs:
        compiler.read_source(i,
                             input_string=options.input_string,
                             theories=theories,
                             use_modules=use_modules)
    return compiler
