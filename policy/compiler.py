#! /usr/bin/python

import sys
sys.path.insert(0, '/home/thinrichs/congress/outside')
import optparse
import CongressLexer
import CongressParser
import antlr3

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
        if self.file is not None:
            s += " file: {}".format(self.file)
        if self.line is not None:
            s += " line: {}".format(self.line)
        if self.col is not None:
            s += " col: {}".format(self.col)
        return s


class Variable (object):
    """ Represents a term without a fixed value. """
    def __init__(self, name, location=None):
        self.name = name
        self.location = location

    def __str__(self):
        return str(self.name)

    def is_variable(self):
        return True

    def is_object(self):
        return False

class ObjectConstant (object):
    """ Represents a term with a fixed value. """
    STRING = 'STRING'
    FLOAT = 'FLOAT'
    INTEGER = 'INTEGER'
    SYMBOL = 'SYMBOL'

    def __init__(self, name, type, location=None):
        self.name = name
        self.type = type
        self.location = location
        assert(self.type in [self.STRING, self.FLOAT, self.INTEGER, self.SYMBOL])

    def __str__(self):
        return str(self.name)

    def is_variable(self):
        return False

    def is_object(self):
        return True

class Literal(object):
    """ Represents either a negated atom or an atom. """
    def __init__(self, atom, negated=False, location=None):
        self.atom = atom
        self.negated = negated
        self.location = location

    def __str__(self):
        if self.negated:
            return "not {}".format(str(self.atom))
        else:
            return str(self.atom)

    def is_negated(self):
        return self.negated

    def is_atom(self):
        return not self.negated

    def is_rule(self):
        return False

class Atom (object):
    """ Represents an atomic statement, e.g. p(a, 17, b) """
    def __init__(self, operator, operands, location=None):
        self.operator = operator
        self.operands = operands
        self.location = location

    def __str__(self):
        return "{}({})".format(self.operator,
            ", ".join([str(x) for x in self.operands]))

    def is_atom(self):
        return True

    def is_negated(self):
        return False

    def is_rule(self):
        return False

class Rule (object):
    """ Represents a rule, e.g. p(x) :- q(x). """
    def __init__(self, head, body, location=None):
        self.operator = head
        self.operands = body
        self.location = location

    def __str__(self):
        return "{} :- {}".format(
            str(self.operator),
            ", ".join([str(opand) for opand in self.operands]))

    def is_atom(self):
        return False

    def is_rule(self):
        return True


class Compiler (object):
    """ Process Congress policy file. """
    def __init__(self):
        self.raw_syntax_tree = None
        self.theory = None
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

    def read_source(self, file):
        # parse input file and convert to internal representation
        self.raw_syntax_tree = CongressSyntax.parse_file(file)
        self.print_parse_result()
        self.theory = CongressSyntax.create(self.raw_syntax_tree)
        print str(self)

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
    def parse_file(cls, filename):
        char_stream = antlr3.ANTLRFileStream(filename)
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
            loc = Location(line=antlr.children[0].children[0].token.line,
                    col=antlr.children[0].children[0].token.charPositionInLine)
            return Literal(cls.create_atom(antlr.children[0]), negated=True,
                    location=loc)
        elif antlr.getText() == 'ATOM':
            loc = Location(line=antlr.children[0].token.line,
                    col=antlr.children[0].token.charPositionInLine)
            return Literal(cls.create_atom(antlr), negated=False,
                        location=loc)
        else:
            raise CongressException("Unknown literal operator: {}".format(
                antlr.getText()))

    @classmethod
    def create_atom(cls, antlr):
        # (ATOM (TABLE ARG1 ... ARGN))
        args = []
        for i in xrange(1, len(antlr.children)):
            args.append(cls.create_term(antlr.children[i]))
        loc = Location(line=antlr.children[0].token.line,
                 col=antlr.children[0].token.charPositionInLine)
        return Atom(antlr.children[0], args)

    @classmethod
    def create_term(cls, antlr):
        # (TYPE (VALUE))
        op = antlr.getText()
        loc = Location(line=antlr.children[0].token.line,
                 col=antlr.children[0].token.charPositionInLine)
        if op == 'STRING_OBJ':
            return ObjectConstant(antlr.children[0].getText(),
                                  ObjectConstant.STRING,
                                  location=loc)
        elif op == 'INTEGER_OBJ':
            return ObjectConstant(antlr.children[0].getText(),
                                  ObjectConstant.INTEGER,
                                  location=loc)
        elif op == 'FLOAT_OBJ':
            return ObjectConstant(antlr.children[0].getText(),
                                  ObjectConstant.FLOAT,
                                  location=loc)
        elif op == 'SYMBOL_OBJ':
            return ObjectConstant(antlr.children[0].getText(),
                                  ObjectConstant.SYMBOL,
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

def main():
    parser = optparse.OptionParser()
    (options, inputs) = parser.parse_args(sys.argv[1:])
    if len(inputs) != 1:
        parser.error("Usage: %prog [options] policy-file")
    compiler = Compiler()
    compiler.read_source(inputs[0])

if __name__ == '__main__':
    sys.exit(main())


