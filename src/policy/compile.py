#! /usr/bin/python

import sys
sys.path.insert(0, '/home/thinrichs/congress/thirdparty')
#sys.path.insert(0, '/opt/python-antlr3')
import optparse
import CongressLexer
import CongressParser
import antlr3
import logging
import copy

import runtime

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
    """ A location in the program source code. """
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
    """ Represents the union of Variable and ObjectConstant. Should
        only be instantiated via factory method. """
    def __init__(self):
        assert False, "Cannot instantiate Term directly--use factory method"

    @classmethod
    def create_from_python(cls, value, force_var=False):
        """ To create variable, FORCE_VAR needs to be true.  There is currently
            no way to avoid this since variables are strings. """
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
    """ Represents a term without a fixed value. """
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
        return "Variable(name={}, location={})".format(
            repr(self.name), repr(self.location))

    def __hash__(self):
        return hash("Variable(name={})".format(repr(self.name)))

    def is_variable(self):
        return True

    def is_object(self):
        return False

class ObjectConstant (Term):
    """ Represents a term with a fixed value. """
    STRING = 'STRING'
    FLOAT = 'FLOAT'
    INTEGER = 'INTEGER'

    def __init__(self, name, type, location=None):
        assert(type in [self.STRING, self.FLOAT, self.INTEGER])
        self.name = name
        self.type = type
        self.location = location

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return "ObjectConstant(name={}, type={}, location={})".format(
            repr(self.name), repr(self.type), repr(self.location))

    def __hash__(self):
        return hash("ObjectConstant(name={}, type={})".format(
            repr(self.name), repr(self.type)))

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

class Atom (object):
    """ Represents an atomic statement, e.g. p(a, 17, b) """
    def __init__(self, table, arguments, location=None):
        self.table = table
        self.arguments = arguments
        self.location = location

    @classmethod
    def create_from_table_tuple(cls, table, tuple):
        """ LIST is a python list representing an atom, e.g.
            ['p', 17, "string", 3.14].  Returns the corresponding Atom. """
        return cls(table, [Term.create_from_python(x) for x in tuple])

    @classmethod
    def create_from_iter(cls, list):
        """ LIST is a python list representing an atom, e.g.
            ['p', 17, "string", 3.14].  Returns the corresponding Atom. """
        arguments = []
        for i in xrange(1, len(list)):
            arguments.append(Term.create_from_python(list[i]))
        return cls(list[0], arguments)

    def __str__(self):
        return "{}({})".format(self.table,
            ", ".join([str(x) for x in self.arguments]))

    def __eq__(self, other):
        return (isinstance(other, Atom) and
                self.table == other.table and
                len(self.arguments) == len(other.arguments) and
                all(self.arguments[i] == other.arguments[i]
                        for i in xrange(0, len(self.arguments))))

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "Atom(table={}, arguments={}, location={})".format(
            repr(self.table),
            "[" + ",".join(repr(arg) for arg in self.arguments) + "]",
            repr(self.location))

    def __hash__(self):
        return hash("Atom(table={}, arguments={})".format(
                repr(self.table),
                "[" + ",".join(repr(arg) for arg in self.arguments) + "]"))

    def is_atom(self):
        return True

    def is_negated(self):
        return False

    def is_rule(self):
        return False

    def variable_names(self):
        return set([x.name for x in self.arguments if x.is_variable()])

    def variables(self):
        return set([x for x in self.arguments if x.is_variable()])

    def is_ground(self):
        return all(not arg.is_variable() for arg in self.arguments)

    def plug(self, binding, caller=None):
        "Assumes domain of BINDING is Terms"
        logging.debug("Atom.plug({}, {})".format(str(binding), str(caller)))
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


class Literal(Atom):
    """ Represents either a negated atom or an atom. """
    def __init__(self, table, arguments, negated=False, location=None):
        Atom.__init__(self, table, arguments, location=location)
        self.negated = negated

    def __str__(self):
        if self.negated:
            return "not {}".format(Atom.__str__(self))
        else:
            return Atom.__str__(self)

    def __eq__(self, other):
        return (self.negated == other.negated and Atom.__eq__(self, other))

    def __repr__(self):
        return "Literal(table={}, arguments={}, location={}, negated={})".format(
            repr(self.table),
            "[" + ",".join(repr(arg) for arg in self.arguments) + "]",
            repr(self.location),
            repr(self.negated))

    def __hash__(self):
        return hash("Literal(table={}, arguments={}, negated={})".format(
            repr(self.table),
            "[" + ",".join(repr(arg) for arg in self.arguments) + "]",
            repr(self.negated)))

    def is_negated(self):
        return self.negated

    def is_atom(self):
        return not self.negated

    def is_rule(self):
        return False

    def complement(self):
        """ Copies SELF and inverts is_negated. """
        new = copy.copy(self)
        new.negated = not new.negated
        return new

class Rule (object):
    """ Represents a rule, e.g. p(x) :- q(x). """
    def __init__(self, head, body, location=None):
        self.head = head
        self.body = body
        self.location = location

    def __str__(self):
        return "{} :- {}".format(
            str(self.head),
            ", ".join([str(atom) for atom in self.body]))

    def __eq__(self, other):
        return (self.head == other.head and
                len(self.body) == len(other.body) and
                all(self.body[i] == other.body[i]
                        for i in xrange(0, len(self.body))))

    def __repr__(self):
        return "Rule(head={}, body={}, location={})".format(
            repr(self.head),
            "[" + ",".join(repr(arg) for arg in self.body) + "]",
            repr(self.location))

    def __hash__(self):
        return hash("Rule(head={}, body={})".format(
            repr(self.head),
            "[" + ",".join(repr(arg) for arg in self.body) + "]"))

    def is_atom(self):
        return False

    def is_rule(self):
        return True

    def plug(self, binding, caller=None):
        newhead = self.head.plug(binding, caller=caller)
        newbody = [lit.plug(binding, caller=caller) for lit in self.body]
        return Rule(newhead, newbody)

    def variables(self):
        vs = self.head.variables()
        for lit in self.body:
            vs |= lit.variables()
        return vs

    def variable_names(self):
        vs = self.head.variable_names()
        for lit in self.body:
            vs |= lit.variable_names()
        return vs


def formulas_to_string(formulas):
    """ Takes an iterable of compiler sentence objects and returns a
    string representing that iterable, which the compiler will parse
    into the original iterable. """
    return " ".join([str(formula) for formula in formulas])

##############################################################################
## Compiler
##############################################################################

class Compiler (object):
    """ Process Congress policy file. """
    def __init__(self):
        self.raw_syntax_tree = None
        self.theory = []
        self.errors = []
        self.warnings = []

    def __str__ (self):
        s = ""
        s += '**Theory**\n'
        if self.theory is not None:
            s += '\n'.join([str(x) for x in self.theory])
        else:
            s += 'None'
        return s

    def read_source(self, input, input_string=False):
        # parse input file and convert to internal representation
        self.raw_syntax_tree = CongressSyntax.parse_file(input,
            input_string=input_string)
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
            raise CongressException('Compiler found errors:' + '\n'.join(errors))

    def compute_delta_rules(self):
        # logging.debug("self.theory: {}".format([str(x) for x in self.theory]))
        self.delta_rules = compute_delta_rules(self.theory)


def eliminate_self_joins(theory):
    """ Modify THEORY so that all self-joins have been eliminated. """
    def new_table_name(name, arity, index):
        return "___{}_{}_{}".format(name, arity, index)
    def n_variables(n):
        vars = []
        for i in xrange(0, n):
            vars.append("x" + str(i))
        return vars
    # dict from (table name, arity) tuple to
    #      max num of occurrences of self-joins in any rule
    global_self_joins = {}
    # dict from (table name, arity) to # of args for
    arities = {}
    # remove self-joins from rules
    for rule in theory:
        if rule.is_atom():
            continue
        logging.debug("eliminating self joins from {}".format(rule))
        occurrences = {}  # for just this rule
        for atom in rule.body:
            table = atom.table
            arity = len(atom.arguments)
            tablearity = (table, arity)
            if tablearity not in occurrences:
                occurrences[tablearity] = 1
            else:
                # change name of atom
                atom.table = new_table_name(table, arity,
                    occurrences[tablearity])
                # update our counters
                occurrences[tablearity] += 1
                if tablearity not in global_self_joins:
                    global_self_joins[tablearity] = 1
                else:
                    global_self_joins[tablearity] = \
                        max(occurrences[tablearity] - 1,
                            global_self_joins[tablearity])
        logging.debug("final rule: {}".format(str(rule)))
    # add definitions for new tables
    for tablearity in global_self_joins:
        table = tablearity[0]
        arity = tablearity[1]
        for i in xrange(1, global_self_joins[tablearity] + 1):
            newtable = new_table_name(table, arity, i)
            args = [Variable(var) for var in n_variables(arity)]
            head = Atom(newtable, args)
            body = [Atom(table, args)]
            theory.append(Rule(head, body))
            logging.debug("Adding rule {}".format(str(theory[-1])))
    return theory

def compute_delta_rules(theory):
    eliminate_self_joins(theory)
    delta_rules = []
    for rule in theory:
        if rule.is_atom():
            continue
        for literal in rule.body:
            newbody = [lit for lit in rule.body if lit is not literal]
            delta_rules.append(
                runtime.DeltaRule(literal, rule.head, newbody, rule))
    return delta_rules

##############################################################################
## External syntax: datalog
##############################################################################

class CongressSyntax (object):
    """ External syntax and converting it into internal representation. """

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
            raise CongressException("Parse failure.\n" + \
                "\n".join(parser.error_list))
        return result.tree

    @classmethod
    def create(cls, antlr):
        obj = antlr.getText()
        if obj == 'RULE':
            return cls.create_rule(antlr)
        elif obj == 'NOT':
            return cls.create_literal(antlr)
        elif obj == 'ATOM':  # Note we're creating an ATOM, not a LITERAL
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
        # (RULE (ATOM LITERAL1 ... LITERALN))
        # Makes body a list of literals
        head = cls.create_atom(antlr.children[0])
        body = []
        for i in xrange(1, len(antlr.children)):
            body.append(cls.create_literal(antlr.children[i]))
        loc = Location(line=antlr.children[0].token.line,
                        col=antlr.children[0].token.charPositionInLine)
        return Rule(head, body, location=loc)

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
        (table, args, loc) = cls.create_atom_aux(antlr)
        return Atom(table, args, location=loc)

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

    @classmethod
    def create_structured_name(cls, antlr):
        # (STRUCTURED_NAME (ARG1 ... ARGN))
        return ":".join([x.getText() for x in antlr.children])

    @classmethod
    def create_term(cls, antlr):
        # (TYPE (VALUE))
        op = antlr.getText()
        loc = Location(line=antlr.children[0].token.line,
                 col=antlr.children[0].token.charPositionInLine)
        if op == 'STRING_OBJ':
            value = antlr.children[0].getText()
            return ObjectConstant(value[1:len(value) - 1], # prune quotes
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
            return Variable(antlr.children[0].getText(), location=loc)
        else:
            raise CongressException("Unknown term operator: {}".format(op))


def print_tree(tree, text, kids, ind=0):
    """ Print out TREE using function TEXT to extract node description and
        function KIDS to compute the children of a given node.
        IND is a number representing the indentation level. """
    print "|" * ind,
    print "{}".format(str(text(tree)))
    children = kids(tree)
    if children:
        for child in children:
            print_tree(child, text, kids, ind + 1)

##############################################################################
## Mains
##############################################################################

def get_compiled(args):
    """ Run compiler as per ARGS and return the resulting Compiler instance. """
    compiler = get_compiler(args)
    compiler.compute_delta_rules()
    return compiler

def get_parsed(args):
    """ Run compiler as per ARGS and return the parsed rules. """
    compiler = get_compiler(args)
    return compiler.theory

def get_compiler(args):
    """ Run compiler as per ARGS and return the compiler object. """
    # assumes script name is not passed
    parser = optparse.OptionParser()
    parser.add_option("--input_string", dest="input_string", default=False,
        action="store_true",
        help="Indicates that inputs should be treated not as file names but "
             "as the contents to compile")
    (options, inputs) = parser.parse_args(args)
    compiler = Compiler()
    for i in inputs:
        compiler.read_source(i, input_string=options.input_string)
    return compiler


def get_runtime(args):
    """ Create runtime by running compiler as per ARGS and initializing runtime
        with result of compilation. """
    comp = get_compiled(args)
    run = runtime.Runtime(comp.delta_rules)
    tracer = runtime.Tracer()
    tracer.trace('*')
    run.tracer = tracer
    run.database.tracer = tracer
    return run

def main(args):
    c = get_compiled(args)
    for formula in c.theory:
        print str(c)

if __name__ == '__main__':
     main(sys.argv[1:])


