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
import sys
import uuid

import antlr3

import CongressLexer
import CongressParser
import runtime
import utility

from builtin.congressbuiltin import CongressBuiltinCategoryMap as cbcmap
from builtin.congressbuiltin import start_builtin_map as initbuiltin


class CongressException (Exception):
    def __init__(self, msg, obj=None, line=None, col=None):
        Exception.__init__(self, msg)
        self.obj = obj
        self.location = Location(line=line, col=col, obj=obj)

    def __str__(self):
        s = str(self.location)
        if len(s) > 0:
            s = " at" + s
        return Exception.__str__(self) + s


##############################################################################
## Internal representation of policy language
##############################################################################

class Location (object):
    """A location in the program source code.
    """
    def __init__(self, line=None, col=None, obj=None):
        self.line = None
        self.col = None
        try:
            self.line = obj.location.line
            self.col = obj.location.col
        except AttributeError:
            pass
        self.col = col
        self.line = line

    def __str__(self):
        s = ""
        if self.line is not None:
            s += " line: {}".format(self.line)
        if self.col is not None:
            s += " col: {}".format(self.col)
        return s

    def __repr__(self):
        return "Location(line={}, col={})".format(
            repr(self.line), repr(self.col))

    def __hash__(self):
        return hash(self.__repr__())


class Term(object):
    """Represents the union of Variable and ObjectConstant. Should
    only be instantiated via factory method.
    """
    def __init__(self):
        assert False, "Cannot instantiate Term directly--use factory method"

    @classmethod
    def create_from_python(cls, value, force_var=False):
        """To create variable, FORCE_VAR needs to be true.  There is currently
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
    """Represents a term without a fixed value.
    """
    def __init__(self, name, location=None):
        self.name = name
        self.location = location

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
        return hash(repr(self))

    def is_variable(self):
        return True

    def is_object(self):
        return False


class ObjectConstant (Term):
    """Represents a term with a fixed value.
    """
    STRING = 'STRING'
    FLOAT = 'FLOAT'
    INTEGER = 'INTEGER'

    def __init__(self, name, type, location=None):
        assert(type in [self.STRING, self.FLOAT, self.INTEGER])
        self.name = name
        self.type = type
        self.location = location

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
        return hash(repr(self))

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


class Literal (object):
    """Represents a possibly negated atomic statement, e.g. p(a, 17, b)."""
    def __init__(self, table, arguments, location=None, negated=False):
        self.table = table
        self.arguments = arguments
        self.location = location
        self.negated = negated
        self.id = str(uuid.uuid4())

    @classmethod
    def create_from_table_tuple(cls, table, tuple):
        """TABLE is the tablename.
        TUPLE is a python list representing a row, e.g.
        [17, "string", 3.14].  Returns the corresponding Literal.
        """
        return cls(table, [Term.create_from_python(x) for x in tuple])

    @classmethod
    def create_from_iter(cls, list):
        """LIST is a python list representing an atom, e.g.
        ['p', 17, "string", 3.14].  Returns the corresponding Literal.
        """
        arguments = []
        for i in xrange(1, len(list)):
            arguments.append(Term.create_from_python(list[i]))
        return cls(list[0], arguments)

    def __str__(self):
        s = "{}({})".format(self.table,
                            ", ".join([str(x) for x in self.arguments]))
        if self.negated:
            s = "not " + s
        return s

    def pretty_str(self):
        return self.__str__()

    def __eq__(self, other):
        return (isinstance(other, Literal) and
                self.table == other.table and
                self.negated == other.negated and
                len(self.arguments) == len(other.arguments) and
                all(self.arguments[i] == other.arguments[i]
                    for i in xrange(0, len(self.arguments))))

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        # Use repr to hash Rule--don't include location
        return "Literal(table={}, arguments={}, negated={})".format(
            repr(self.table),
            "[" + ",".join(repr(arg) for arg in self.arguments) + "]",
            repr(self.negated))

    def __hash__(self):
        return hash(repr(self))

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
        """Either returns SELF if is_negated() is false or
        returns copy of SELF where is_negated() is set to false.
        """
        if self.negated:
            new = copy.copy(self)
            new.negated = False
            return new
        else:
            return self

    def invert_update(self):
        """If end of table name is + or -, return a copy after switching
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
        """If end of table name is + or -, return a copy without the sign.
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

    def tablename(self):
        return self.table


# A more general version of negation, which is more awkward than
#    Literal for literals.  Keep around in case we end up supporting
#    a generalized syntax.
# class Negation(object):
#     """Represents the negation of a formula.  UNUSED as of now.
#     All negations are represented via LITERAL with is_negated.
#     """
#     def __init__(self, formula, location=None):
#         self.formula = formula

#     def __str__(self):
#         return "not {}".format(str(self.formula))

#     def __eq__(self, other):
#         return isinstance(other, Negation), (self.formula == other.formula)

#     def __repr__(self):
#         # Use repr to hash rule--can't include location
#         return "Negation(formula={})".format(repr(self.formula))

#     def __hash__(self):
#         return hash("Negation(formula={})".format(repr(self.formula)))

#     def is_negated(self):
#         return True

#     def is_atom(self):
#         return False

#     def is_rule(self):
#         return False

#     def complement(self):
#         """Returns the negation of SELF.  No copy is made."""
#         return self.formula

#     def make_positive(self):
#         """Returns a formula representing negation of SELF.
#         No copy is made.
#         """
#         return self.formula

#     def variable_names(self):
#         """Returns list of all variable names"""
#         return self.formula.variable_names()

#     def variables(self):
#         """Returns list of all variables."""
#         return self.formula.variables()

#     def is_ground(self):
#         """Returns IS_GROUND() result on inner formula."""
#         return self.formula.is_ground()

#     def plug(self, binding, caller=None):
#         """Applies variable substitution BINDING.
#         Returns a new formula only if resulting formula is different."""
#         new = self.formula.plug(binding,caller)
#         if new is not self.formula:
#             return Negation(self.formula.plug(binding,caller))
#         else:
#             return self

#     def argument_names(self):
#         return self.formula.argument_names()

#     def invert_update(self):
#         """Applies INVERT_UPDATE to inner formula.
#         Only makes a copy if resulting formula is different.
#         """
#         new = self.formula.invert_update()
#         if new is not self.formula:
#             return Negation(new)
#         else:
#             return self

#     def drop_update(self):
#         """Applies DROP_UPDATE to inner formula and returns the result.
#         Only makes a copy if resulting formula is different.
#         """
#         new = self.formula.drop_update()
#         if new is not self.formula:
#             return Negation(new)
#         else:
#             return self

#     def make_update(self, is_insert=True):
#         """Applies MAKE_UPDATE to inner formula and returns the result.
#         Only makes a copy if resulting formula is different.
#         """
#         new = self.formula.make_update(is_insert)
#         if new is not self.formula:
#             return Negation(new)
#         else:
#             return self

#     def tablename(self):
#         """Applies TABLENAME to inner formula and returns result."""
#         return self.formula.tablename()

class Rule (object):
    """Represents a rule, e.g. p(x) :- q(x)."""

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
        self.id = str(uuid.uuid4())

    def __copy__(self):
        newone = Rule(self.head, self.body, self.location)
        newone.id = str(uuid.uuid4())
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

    def __repr__(self):
        return "Rule(head={}, body={}, location={})".format(
            "[" + ",".join(repr(arg) for arg in self.heads) + "]",
            "[" + ",".join(repr(arg) for arg in self.body) + "]",
            repr(self.location))

    def __hash__(self):
        # won't properly treat a positive literal and an atom as the same
        return hash("Rule(head={}, body={})".format(
            "[" + ",".join(repr(arg) for arg in self.heads) + "]",
            "[" + ",".join(repr(arg) for arg in self.body) + "]"))

    def is_atom(self):
        return False

    def is_rule(self):
        return True

    def tablename(self):
        return self.head.table

    def tablenames(self):
        """Return all the tablenames occurring in this rule."""
        result = set()
        for lit in self.heads:
            result.add(lit.tablename())
        for lit in self.body:
            result.add(lit.tablename())
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


def formulas_to_string(formulas):
    """Takes an iterable of compiler sentence objects and returns a
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
    """Returns T iff x is a formula or tablename representing the result of
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


def is_recursive(rules):
    """Returns T iff the list of rules RULES has a table defined in Terms
    of itself.
    """
    return head_to_body_dependency_graph(rules).has_cycle()


def stratification(rules):
    """Returns a dictionary from table names to an integer representing
    the strata to which the table is assigned or None if the rules
    are not stratified.
    """
    return head_to_body_dependency_graph(rules).stratification([True])


def is_stratified(rules):
    """Returns T iff the list of rules RULES has no table defined in terms
    of its negated self.
    """
    return stratification(rules) is not None


def head_to_body_dependency_graph(formulas):
    """Returns a Graph() that includes one node for each table and an edge
    <u,v> if there is some rule with u in the head and v in the body.
    """
    g = utility.Graph()
    for formula in formulas:
        if formula.is_atom():
            g.add_node(formula.table)
        else:
            for head in formula.heads:
                for lit in formula.body:
                    # label on edge is True for negation, else False
                    g.add_edge(head.table, lit.table, lit.is_negated())
    return g


def fact_errors(atom):
    """Checks if ATOM is ground."""
    assert atom.is_atom(), "fact_errors expects an atom"
    if not atom.is_ground():
        return [CongressException("Fact not ground: " + str(atom))]
    return []


def check_builtin_vars(litvars, rule):
    body_vars = set()
    errors = []
    for lit in rule.body:
        body_vars |= lit.variables()
    for var in litvars:
        if var not in body_vars:
            errors.append(var)
    return errors


def rule_builtin_safety(rule):
    """Checks for builtin safety Returns list of exceptions."""
    cbcmapinst = cbcmap(initbuiltin)
    assert not rule.is_atom(), "rule_builtin_safety expects a rule"
    errors = []
    lit_vars = set()
    unsafe = []

    for lit in rule.body:
        if cbcmapinst.check_if_builtin_by_name(lit.table, len(lit.arguments)):
            lit_vars |= lit.variables()
            copyrule = copy.deepcopy(rule)
            if lit in copyrule.body:
                copyrule.body.remove(lit)
            unsafe = check_builtin_vars(lit_vars, copyrule)

    for var in unsafe:
        errors.append(CongressException(
            "Variable {} found in builtin but not in body, rule {}".format(
                str(var), str(rule)),
            obj=var))
    return errors


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
        errors.append(CongressException(
            "Variable {} found in head but not in body, rule {}".format(
                str(var), str(rule)),
            obj=var))
    return errors


def rule_negation_safety(rule):
    """Checks if every variable in a negative literal also appears in
    a positive literal in the body.  Returns list of exceptions.
    """
    assert not rule.is_atom(), "rule_negation_safety expects a rule"
    errors = []

    # Variables in negative literals must appear in positive literals
    neg_vars = set()
    pos_vars = set()
    for lit in rule.body:
        if lit.is_negated():
            neg_vars |= lit.variables()
        else:
            pos_vars |= lit.variables()
    unsafe = neg_vars - pos_vars
    for var in unsafe:
        errors.append(CongressException(
            "Variable {} found in negative literal but not in "
            "positive literal, rule {}".format(str(var), str(rule)),
            obj=var))
    return errors


def rule_errors(rule):
    """Returns list of errors for RULE."""
    errors = []
    errors.extend(rule_head_safety(rule))
    errors.extend(rule_negation_safety(rule))
    errors.extend(rule_builtin_safety(rule))
    return errors


# Type-checkers
def is_atom(x):
    """Returns True if object X is an atomic Datalog formula."""
    return isinstance(x, Literal) and not x.is_negated()


def is_literal(x):
    """Returns True if X is a possibly negated atomic Datalog formula
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
## Compiler
##############################################################################


class Compiler (object):
    """Process Congress policy file.
    """
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

    def read_source(self, input, input_string=False):
        # parse input file and convert to internal representation
        self.raw_syntax_tree = CongressSyntax.parse_file(
            input, input_string=input_string)
        # self.print_parse_result()
        self.theory = CongressSyntax.create(self.raw_syntax_tree)
        # print str(self)

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
            raise CongressException(
                'Compiler found errors:' + '\n'.join(errors))


##############################################################################
## External syntax: datalog
##############################################################################

class CongressSyntax(object):
    """External syntax and converting it into internal representation."""

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
        lexer = cls.Lexer(char_stream)
        tokens = antlr3.CommonTokenStream(lexer)
        parser = cls.Parser(tokens)
        result = parser.prog()
        if len(lexer.error_list) > 0:
            raise CongressException("Lex failure.\n" +
                                    "\n".join(lexer.error_list))
        if len(parser.error_list) > 0:
            raise CongressException("Parse failure.\n" +
                                    "\n".join(parser.error_list))
        return result.tree

    @classmethod
    def create(cls, antlr):
        obj = antlr.getText()
        if obj == 'RULE':
            return cls.create_rule(antlr)
        elif obj == 'NOT':
            return cls.create_literal(antlr)
        elif obj == 'ATOM':
            return cls.create_atom(antlr)
        elif obj == 'THEORY':
            return [cls.create(x) for x in antlr.children]
        elif obj == '<EOF>':
            return []
        else:
            raise CongressException(
                "Antlr tree with unknown root: {}".format(obj))

    @classmethod
    def create_rule(cls, antlr):
        # (RULE AND1 AND2)
        heads = cls.create_and(antlr.children[0])
        body = cls.create_and(antlr.children[1])
        loc = Location(line=antlr.children[0].token.line,
                       col=antlr.children[0].token.charPositionInLine)
        return Rule(heads, body, location=loc)

    @classmethod
    def create_and(cls, antlr):
        # (AND (ARG1 ... ARGN))
        # For now we represent ANDs as simple lists.  Convenient
        #    since we only have rules.
        return [cls.create(child) for child in antlr.children]

    @classmethod
    def create_literal(cls, antlr):
        # (NOT (ATOM (TABLE ARG1 ... ARGN)))
        # (ATOM (TABLE ARG1 ... ARGN))
        if antlr.getText() == 'NOT':
            negated = True
            antlr = antlr.children[0]
        else:
            negated = False
        (table, args, loc) = cls.create_atom_aux(antlr)
        return Literal(table, args, negated=negated, location=loc)

    @classmethod
    def create_atom(cls, antlr):
        # (ATOM (TABLENAME ARG1 ... ARGN))
        (table, args, loc) = cls.create_atom_aux(antlr)
        return Literal(table, args, location=loc)

    @classmethod
    def create_atom_aux(cls, antlr):
        # (ATOM (TABLENAME ARG1 ... ARGN))
        table = cls.create_structured_name(antlr.children[0])
        args = []
        for i in xrange(1, len(antlr.children)):
            args.append(cls.create_term(antlr.children[i]))
        loc = Location(line=antlr.children[0].token.line,
                       col=antlr.children[0].token.charPositionInLine)
        return (table, args, loc)

    # Use the following if we were to start using NEGATION instead of
    #    LITERAL.
    # @classmethod
    # def create_literal(cls, antlr):
    #     # (NOT (ATOM (TABLE ARG1 ... ARGN)))
    #     # (ATOM (TABLE ARG1 ... ARGN))
    #     if antlr.getText() == 'NOT':
    #         return Negation(cls.create_atom(antlr.children[0]))
    #     else:
    #         return cls.create_atom(antlr)

    # @classmethod
    # def create_atom(cls, antlr):
    #     # (ATOM (TABLENAME ARG1 ... ARGN))
    #     table = cls.create_structured_name(antlr.children[0])
    #     args = []
    #     for i in xrange(1, len(antlr.children)):
    #         args.append(cls.create_term(antlr.children[i]))
    #     loc = Location(line=antlr.children[0].token.line,
    #                    col=antlr.children[0].token.charPositionInLine)
    #     return (table, args, loc)

    @classmethod
    def create_structured_name(cls, antlr):
        # (STRUCTURED_NAME (ARG1 ... ARGN))
        if antlr.children[-1].getText() in ['+', '-']:
            return (":".join([x.getText() for x in antlr.children[:-1]]) +
                    antlr.children[-1].getText())
        else:
            return ":".join([x.getText() for x in antlr.children])

    @classmethod
    def create_term(cls, antlr):
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
            name = "".join([child.getText() for child in antlr.children])
            return Variable(name, location=loc)
        else:
            raise CongressException("Unknown term operator: {}".format(op))


def print_tree(tree, text, kids, ind=0):
    """Print out TREE using function TEXT to extract node description and
    function KIDS to compute the children of a given node.
    IND is a number representing the indentation level.
    """
    print "|" * ind,
    print "{}".format(str(text(tree)))
    children = kids(tree)
    if children:
        for child in children:
            print_tree(child, text, kids, ind + 1)


##############################################################################
## Mains
##############################################################################

def parse(policy_string):
    """Run compiler on policy string and return the parsed formulas."""
    compiler = get_compiler([policy_string, '--input_string'])
    return compiler.theory


def parse1(policy_string):
    """Run compiler on policy string and return 1st parsed formula."""
    return parse(policy_string)[0]


def parse_file(filename):
    """Run compiler on policy stored in FILENAME and return the parsed
    formulas.
    """
    compiler = get_compiler([filename])
    return compiler.theory


def get_compiler(args):
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
        compiler.read_source(i, input_string=options.input_string)
    return compiler


def get_runtime(args):
    """Create runtime by running compiler as per ARGS and initializing runtime
    with result of compilation.
    """
    comp = get_compiler(args)
    run = runtime.Runtime(comp.delta_rules)
    tracer = runtime.Tracer()
    tracer.trace('*')
    run.tracer = tracer
    run.database.tracer = tracer
    return run


def main(args):
    c = get_compiler(args)
    for formula in c.theory:
        print str(c)


if __name__ == '__main__':
    main(sys.argv[1:])
