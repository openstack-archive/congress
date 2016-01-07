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
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import collections
import copy
import functools
import optparse
import uuid


import six
from six.moves import range

from oslo_log import log as logging

from congress.datalog import analysis
from congress.datalog.builtin import congressbuiltin

# set up appropriate antlr paths per python version and import runtime
# import appropriate Lexer & Parser per python version
import os
import sys
_congressDir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if six.PY2:
    sys.path.append(_congressDir +
                    "/thirdparty/antlr3-antlr-3.5/runtime/Python/")
    from congress.datalog.Python2 import CongressLexer
    from congress.datalog.Python2 import CongressParser
else:
    sys.path.append(_congressDir +
                    "/thirdparty/antlr3-antlr-3.5/runtime/Python3/")
    from congress.datalog.Python3 import CongressLexer
    from congress.datalog.Python3 import CongressParser
import antlr3

from congress.datalog import utility
from congress import exception
from congress import utils

LOG = logging.getLogger(__name__)

PERMITTED_MODALS = ['execute']


##############################################################################
# Internal representation of policy language
##############################################################################


class Schema(object):
    """Meta-data about a collection of tables."""
    def __init__(self, dictionary=None, complete=False):
        if dictionary is None:
            self.map = {}
            self.count = {}
        elif isinstance(dictionary, Schema):
            self.map = dict(dictionary.map)
            self.count = dictionary.count
        else:
            self.map = dictionary
            self.count = None
        # whether to assume there is an entry in this schema for
        # every permitted table
        self.complete = complete

    def __contains__(self, tablename):
        return tablename in self.map

    @classmethod
    def col(self, cols):
        # For Datasource tables, columns would be in the format -
        # {'name': 'colname', 'desc': 'description'}
        if len(cols) and isinstance(cols[0], dict):
            return [x['name'] for x in cols]
        else:
            return [x for x in cols]

    def columns(self, tablename):
        """Returns the list of column names for the given TABLENAME.

        Return None if the tablename's columns are unknown.
        """
        if tablename not in self.map.keys():
            return
        cols = self.map[tablename]
        return Schema.col(cols)

    def arity(self, tablename):
        """Returns the number of columns for the given TABLENAME.

        Return None if TABLENAME is unknown.
        """
        if tablename in self.map:
            return len(self.map[tablename])

    def update(self, item, is_insert):
        """Returns the schema change of this update.

        Return schema change.
        """
        if self.count is None:
            return None
        if isinstance(item, Fact):
            tablename, tablelen = item.table, len(item)
            th = None
        elif isinstance(item, Literal):
            tablename, tablelen = item.table.table, len(item.arguments)
            th = item.table.service
        else:
            raise exception.PolicyException(
                "Schema cannot update item: %r" % item)

        schema_change = None
        if is_insert:
            if tablename in self:
                self.count[tablename] += 1
                schema_change = (tablename, None, True, th)
            else:
                self.count[tablename] = 1
                val = ["Col"+str(i) for i in range(0, tablelen)]
                self.map[tablename] = val
                schema_change = (tablename, val, True, th)
        else:
            if tablename not in self:
                LOG.warn("Attempt to delete a non-existant rule: %s" % item)
            elif self.count[tablename] > 1:
                self.count[tablename] -= 1
                schema_change = (tablename, None, False, th)
            else:
                schema_change = (tablename, self.map[tablename], False, th)
                del self.count[tablename]
                del self.map[tablename]
        return schema_change

    def revert(self, change):
        """Revert change made by update.

        Return None
        """
        if change is None:
            return

        inserted = change[2]
        tablename = change[0]
        val = change[1]

        if inserted:
            if self.count[tablename] > 1:
                self.count[tablename] -= 1
            else:
                del self.map[tablename]
                del self.count[tablename]
        else:
            if tablename in self.count:
                self.count[tablename] += 1
            else:
                assert val is not None
                self.map[tablename] = val
                self.count[tablename] = 1

    def column_number(self, tablename, column):
        """Returns the 0-indexed position of the given COLUMN for TABLENAME.

        Returns None if TABLENAME or COLUMNNAME are unknown.
        Returns COLUMN if it is a number.
        """
        table_columns = self.columns(tablename)
        if table_columns is None:
            return

        if isinstance(column, six.integer_types):
            if column > len(table_columns):
                return
            return column
        try:
            return table_columns.index(column)
        except ValueError:
            return

    def column_name(self, tablename, column):
        """Returns name for given COLUMN or None if it is unknown."""
        table_columns = self.columns(tablename)
        if table_columns is None:
            return
        if isinstance(column, six.string_types):
            if column in table_columns:
                return column
            return
        try:
            return self.map[tablename][column]
        except IndexError:
            return

    def __str__(self):
        schemas = []
        for table, columns in self.map.items():
            cols = ",".join(str(x) for x in columns)
            schemas.append("schema[%s(%s)]" % (table, cols))
        return " ".join(schemas)

    def __len__(self):
        return len(self.map)


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
        elif isinstance(value, six.string_types):
            return ObjectConstant(value, ObjectConstant.STRING)
        elif isinstance(value, six.integer_types):
            return ObjectConstant(value, ObjectConstant.INTEGER)
        elif isinstance(value, float):
            return ObjectConstant(value, ObjectConstant.FLOAT)
        else:
            assert False, "No Term corresponding to {}".format(repr(value))


@functools.total_ordering
class Variable (Term):
    """Represents a term without a fixed value."""

    SORT_RANK = 1
    __slots__ = ['name', 'location', '_hash']

    def __init__(self, name, location=None):
        assert isinstance(name, six.string_types)
        self.name = name
        self.location = location
        self._hash = None

    def __str__(self):
        return str(self.name)

    def __lt__(self, other):
        if self.SORT_RANK < other.SORT_RANK:
            return self.SORT_RANK < other.SORT_RANK
        return self.name < other.name

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


@functools.total_ordering
class ObjectConstant (Term):
    """Represents a term with a fixed value."""
    STRING = 'STRING'
    FLOAT = 'FLOAT'
    INTEGER = 'INTEGER'
    SORT_RANK = 2
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

    def __lt__(self, other):
        if self.SORT_RANK != other.SORT_RANK:
            return self.SORT_RANK < other.SORT_RANK
        if self.name != other.name:
            return self.name < other.name
        return self.type < other.type

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


@functools.total_ordering
class Fact (tuple):
    """Represent a Fact (a ground literal)

    Use this class to represent a fact such as Foo(1,2,3).  While one could
    use a Rule to represent the same fact, this Fact datastructure is more
    memory efficient than a Rule object since this Fact stores the information
    as a native tuple, containing native values like ints and strings.  Notes
    that this subclasses from tuple.
    """
    SORT_RANK = 3

    def __new__(cls, table, values):
        return super(Fact, cls).__new__(cls, values)

    def __init__(self, table, values):
        self.table = table

    def __lt__(self, other):
        if self.SORT_RANK != other.SORT_RANK:
            return self.SORT_RANK < other.SORT_RANK
        if self.table != other.table:
            return self.table < other.table
        return super(Fact, self).__lt__(other)

    def __eq__(self, other):
        if self.SORT_RANK != other.SORT_RANK:
            return False
        if self.table != other.table:
            return False
        return super(Fact, self).__eq__(other)

    def __hash__(self):
        return hash((self.SORT_RANK, self.table, super(Fact, self).__hash__()))


@functools.total_ordering
class Tablename(object):
    SORT_RANK = 4
    __slots__ = ['service', 'table', 'modal', '_hash']

    def __init__(self, table=None, service=None, modal=None):
        self.table = table
        self.service = service
        self.modal = modal
        self._hash = None

    @classmethod
    def create_from_tablename(cls, tablename, service=None, use_modules=True):
        # if use_modules is True,
        # break full tablename up into 2 pieces.  Example: "nova:servers:cpu"
        # self.theory = "nova"
        # self.table = "servers:cpu"
        if service is None and use_modules:
            (service, tablename) = cls.parse_service_table(tablename)
        return cls(service=service, table=tablename)

    @classmethod
    def parse_service_table(cls, tablename):
        """Given tablename returns (service, name)."""
        pieces = tablename.split(':')
        if len(pieces) == 1:
            table = pieces[0]
            service = None
        else:
            service = pieces[0]
            table = ':'.join(pieces[1:])
        return service, table

    @classmethod
    def build_service_table(cls, service, table):
        """Return string service:table."""
        return str(service) + ":" + str(table)

    def global_tablename(self, prefix=None):
        pieces = [x for x in [prefix, self.service, self.table]
                  if x is not None]
        return ":".join(pieces)

    def matches(self, service, table, modal):
        if (service == self.service and table == self.table and
                modal == self.modal):
            return True
        self_service, self_table = self.parse_service_table(self.table)
        return (service == self_service and
                table == self_table and
                modal == self.modal)

    def __copy__(self):
        return Tablename(
            table=self.table, modal=self.modal, service=self.service)

    def __lt__(self, other):
        if self.SORT_RANK != other.SORT_RANK:
            return self.SORT_RANK < other.SORT_RANK
        if self.modal != other.modal:
            return self.modal < other.modal
        if self.service != other.service:
            # manually handle None cases for py3 compat
            if (self.service is None):
                return True
            if (other.service is None):
                return False
            return self.service < other.service
        if self.table != other.table:
            return self.table < other.table
        return False

    def __eq__(self, other):
        return (isinstance(other, Tablename) and
                self.table == other.table and
                self.service == other.service and
                self.modal == other.modal)

    def same(self, other, default_service):
        """Equality but where default_service is used for None service."""
        if self.table != other.table:
            return False
        if self.modal != other.modal:
            return False
        selfservice = self.service or default_service
        otherservice = other.service or default_service
        return selfservice == otherservice

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(('Tablename',
                               hash(self.service),
                               hash(self.table),
                               hash(self.modal)))
        return self._hash

    def __str__(self):
        return ":".join([x for x in [self.modal, self.service, self.table]
                         if x is not None])

    def __repr__(self):
        return "Tablename(table=%s, service=%s, modal=%s)" % (
            self.table, self.service, self.modal)

    def name(self, default_service=None):
        """Compute string name with default service."""
        service = self.service or default_service
        if service is None:
            return self.table
        return service + ":" + self.table

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
            return self, False

        new = copy.copy(self)
        new.table = self.table[:-1] + suffix
        return new, True

    def drop_update(self):
        """Drop the update.

        If end of table name is + or -, return a copy without the sign.
        If table name does not end in + or -, make no copy.
        """
        if self.table.endswith('+') or self.table.endswith('-'):
            new = copy.copy(self)
            new.table = new.table[:-1]
            return new, True
        else:
            return self, False

    def make_update(self, is_insert=True):
        """Turn the tablename into a +/- update."""
        new = copy.copy(self)
        if is_insert:
            new.table = new.table + "+"
        else:
            new.table = new.table + "-"
        return new, True

    def is_update(self):
        return self.table.endswith('+') or self.table.endswith('-')

    def drop_service(self):
        self.service = None


@functools.total_ordering
class Literal (object):
    """Represents a possibly negated atomic statement, e.g. p(a, 17, b)."""
    SORT_RANK = 5
    __slots__ = ['table', 'arguments', 'location', 'negated', '_hash',
                 'id', 'name', 'comment', 'original_str', 'named_arguments']

    def __init__(self, table, arguments, location=None, negated=False,
                 use_modules=True, id_=None, name=None, comment=None,
                 original_str=None, named_arguments=None):
        if isinstance(table, Tablename):
            self.table = table
        else:
            self.table = Tablename.create_from_tablename(
                table, use_modules=use_modules)
        self.arguments = arguments
        self.location = location
        self.negated = negated
        self._hash = None
        self.id = id_
        self.name = name
        self.comment = comment
        self.original_str = original_str
        if named_arguments is None:
            self.named_arguments = collections.OrderedDict()
        else:
            # Python3: explicitly split out the integer names from others
            self.named_arguments = collections.OrderedDict(
                sorted([(n, o)
                        for n, o in named_arguments.items() if
                        isinstance(n, six.integer_types)])
                +
                sorted([(n, o)
                        for n, o in named_arguments.items() if
                        not isinstance(n, six.integer_types)])
            )

    def __copy__(self):
        # use_modules=False so that we get exactly what we started
        #   with
        newone = Literal(self.table, self.arguments, self.location,
                         self.negated, False, self.id,
                         self.name, self.comment, self.original_str,
                         self.named_arguments)
        return newone

    def set_id(self, id):
        self.id = id

    def set_name(self, name):
        self.name = name

    def set_comment(self, comment):
        self.comment = comment

    def set_original_str(self, original_str):
        self.original_str = original_str

    @classmethod
    def create_from_table_tuple(cls, table, tuple):
        """Create Literal from table and tuple.

        TABLE is a string tablename.
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
        for i in range(1, len(list)):
            arguments.append(Term.create_from_python(list[i]))
        return cls(list[0], arguments)

    def __str__(self):
        args = ", ".join([str(x) for x in self.arguments])
        named = ", ".join("{}={}".format(key, val)
                          for key, val in self.named_arguments.items())
        if len(args) > 0:
            if len(named):
                args += "," + named
        else:
            args = named
        s = "{}({})".format(self.tablename(), args)
        if self.table.modal is not None:
            s = "{}[{}]".format(self.table.modal, s)
        if self.negated:
            s = "not " + s
        return s

    def pretty_str(self):
        return self.__str__()

    def __lt__(self, other):
        if self.SORT_RANK != other.SORT_RANK:
            return self.SORT_RANK < other.SORT_RANK
        if self.table != other.table:
            return self.table < other.table
        if self.negated != other.negated:
            return self.negated < other.negated
        if len(self.arguments) != len(other.arguments):
            return len(self.arguments) < len(other.arguments)
        if len(self.named_arguments) != len(other.named_arguments):
            return len(self.named_arguments) < len(other.named_arguments)
        # final case
        # explicitly convert OrderedDict to list for comparison

        def od_list(input):
            return (
                list(input.items()) if isinstance(
                    input, collections.OrderedDict)
                else input)

        return (self.arguments < other.arguments or
                od_list(self.named_arguments) < od_list(other.named_arguments))

    def __eq__(self, other):
        return (isinstance(other, Literal) and
                self.table == other.table and
                self.negated == other.negated and
                len(self.arguments) == len(other.arguments) and
                self.arguments == other.arguments and
                self.named_arguments == other.named_arguments)

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        named = ",".join("%r: %r" % (key, value)
                         for key, value in self.named_arguments.items())
        named = "{" + named + "}"
        args = ",".join(repr(arg) for arg in self.arguments)
        args = "[" + args + "]"
        return ("Literal(table={}, arguments={}, negated={}, "
                "named_arguments={})").format(
            repr(self.table), args, repr(self.negated), named)

    def __hash__(self):
        if self._hash is None:
            args = tuple([hash(a) for a in self.arguments])
            named = tuple([(hash(key), hash(value))
                           for key, value in self.named_arguments.items()])
            self._hash = hash(('Literal',
                               hash(self.table),
                               args,
                               hash(self.negated),
                               named))
        return self._hash

    def is_negated(self):
        return self.negated

    def is_atom(self):
        return not self.negated

    def is_rule(self):
        return False

    def variable_names(self):
        """Return variable names in arguments.  Ignores named_arguments."""
        return set([x.name for x in self.arguments if x.is_variable()])

    def variables(self):
        """Return variables in arguments.  Ignores named_arguments."""
        return set([x for x in self.arguments if x.is_variable()])

    def is_ground(self):
        """Return True if all args are non-vars.  Ignores named_arguments."""
        return all(not arg.is_variable() for arg in self.arguments)

    def plug(self, binding, caller=None):
        """Assumes domain of BINDING is Terms.  Ignores named_arguments."""
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
        """Return names of all arguments.  Ignores named_arguments."""
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
        return self._modify_table(lambda x: x.invert_update())

    def drop_update(self):
        return self._modify_table(lambda x: x.drop_update())

    def make_update(self, is_insert=True):
        return self._modify_table(lambda x: x.make_update(is_insert=is_insert))

    def _modify_table(self, func):
        """Apply func to self.table and return a copy that uses the result."""
        newtable, is_different = func(self.table)
        if is_different:
            new = copy.copy(self)
            new.table = newtable
            return new
        return self

    def is_update(self):
        return self.table.is_update()

    def is_builtin(self, check_arguments=True):
        if check_arguments:
            return congressbuiltin.builtin_registry.is_builtin(
                self.table, len(self.arguments))
        else:
            return congressbuiltin.builtin_registry.is_builtin(
                self.table)

    def tablename(self, default_service=None):
        return self.table.name(default_service)

    def theory_name(self):
        return self.table.service

    def drop_theory(self):
        """Destructively sets the theory to None."""
        self._hash = None
        self.table.drop_service()
        return self

    def eliminate_column_references(self, schema, index, prefix=''):
        """Expand column references to traditional datalog positional args.

        Returns a new literal, unless no column references.
        """
        # corner cases
        if len(self.named_arguments) == 0:
            return self
        if schema is None:
            raise exception.IncompleteSchemaException(
                "Literal %s uses named arguments, but the "
                "schema is unknown." % self)
        if self.table.table not in schema:
            raise exception.IncompleteSchemaException(
                "Literal {} uses unknown table {} "
                "from schema {}".format(
                    str(self), str(self.table.table), str(schema)))

        # check if named arguments conflict with positional or named arguments
        errors = []
        term_index = {}
        for col, arg in six.iteritems(self.named_arguments):
            if isinstance(col, six.string_types):  # column name
                index = schema.column_number(self.table.table, col)
                if index is None:
                    errors.append(exception.PolicyException(
                        "In literal {} column name {} does not exist".format(
                            str(self), col)))
                    continue
                if index < len(self.arguments):
                    errors.append(exception.PolicyException(
                        "In literal {} column name {} references position {},"
                        " which is already provided by position.".format(
                            str(self), col, index)))
                if index in self.named_arguments:
                    errors.append(exception.PolicyException(
                        "In literal {} column name {} references position {}, "
                        "which is also referenced by number.))".format(
                            str(self), col, index)))
                if index in term_index:
                    # should have already caught this case above
                    errors.append(exception.PolicyException(
                        "In literal {}, column name {} references position {},"
                        " which already has reference {}".format(
                            str(self), col, index, str(term_index[index]))))
                term_index[index] = arg
            else:  # column number
                if col >= schema.arity(self.table.table):
                    errors.append(exception.PolicyException(
                        "In literal {} column index {} is too large".format(
                            str(self), col)))
                if col < len(self.arguments):
                    errors.append(exception.PolicyException(
                        "In literal {} column index {} "
                        " is already provided by position.".format(
                            str(self), col)))
                name = schema.column_name(self.table.table, col)
                if name in self.named_arguments:
                    errors.append(exception.PolicyException(
                        "In literal {} column index {} references column {}, "
                        "which is also referenced by name.))".format(
                            str(self), col, name)))
                if col in term_index:
                    # should have already caught this case above
                    errors.append(exception.PolicyException(
                        "In literal {} column index {} already has a reference"
                        " {}".format(str(self), col, str(term_index[col]))))
                term_index[col] = arg
        if errors:
            raise exception.PolicyException(
                " ".join(str(err) for err in errors))

        # turn reference args into position args
        position_args = list(self.arguments)  # copy the original list
        for i in range(len(position_args), schema.arity(self.table.table)):
            term = term_index.get(i, None)
            if term is None:
                term = Variable("%s%s" % (prefix, i))
            position_args.append(term)
        newlit = self.__copy__()
        newlit.named_arguments = collections.OrderedDict()
        newlit.arguments = position_args
        return newlit


@functools.total_ordering
class Rule(object):
    """Represents a rule, e.g. p(x) :- q(x)."""

    SORT_RANK = 6
    __slots__ = ['heads', 'head', 'body', 'location', '_hash', 'id', 'name',
                 'comment', 'original_str']

    def __init__(self, head, body, location=None, id=None, name=None,
                 comment=None, original_str=None):
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
        self.id = id or uuid.uuid4()
        self.name = name
        self.comment = comment
        self.original_str = original_str

    def __copy__(self):
        newone = Rule(self.head, self.body, self.location, self.id,
                      self.name, self.comment, self.original_str)
        return newone

    def set_id(self, id):
        self.id = id

    def set_name(self, name):
        self.name = name

    def set_comment(self, comment):
        self.comment = comment

    def set_original_str(self, original_str):
        self.original_str = original_str

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

    def __lt__(self, other):
        if self.SORT_RANK != other.SORT_RANK:
            return self.SORT_RANK < other.SORT_RANK
        if len(self.heads) != len(other.heads):
            return len(self.heads) < len(other.heads)
        if len(self.body) != len(other.body):
            return len(self.body) < len(other.body)
        x = sorted(self.heads)
        y = sorted(other.heads)
        if x != y:
            return x < y
        x = sorted(self.body)
        y = sorted(other.body)
        return x < y

    def __eq__(self, other):
        return (isinstance(other, Rule) and
                len(self.heads) == len(other.heads) and
                len(self.body) == len(other.body) and
                sorted(self.heads) == sorted(other.heads) and
                sorted(self.body) == sorted(other.body))

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
            self._hash = hash(('Rule',
                               tuple([hash(h) for h in sorted(self.heads)]),
                               tuple([hash(b) for b in sorted(self.body)])))
        return self._hash

    def is_atom(self):
        return False

    def is_rule(self):
        return True

    def tablename(self, theory=None):
        return self.head.tablename(theory)

    def theory_name(self):
        return self.head.theory_name()

    def drop_theory(self):
        """Destructively sets the theory to None in all heads."""
        for head in self.heads:
            head.drop_theory()
        self._hash = None
        return self

    def tablenames(self, theory=None, body_only=False, include_builtin=False,
                   include_modal=True):
        """Return all the tablenames occurring in this rule."""
        result = set()
        if not body_only:
            for lit in self.heads:
                if include_modal or not lit.table.modal:
                    result.add(lit.tablename(theory))
        for lit in self.body:
            if include_builtin or not lit.is_builtin():
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
        return self.head.is_update()

    def eliminate_column_references(self, theories, default_theory=None):
        """Return version of SELF where all column references have been removed.

        Throws exception if RULE is inconsistent with schemas.
        """

        pre = self._unused_variable_prefix()
        heads = []
        for i in range(0, len(self.heads)):
            heads.append(self.heads[i].eliminate_column_references(
                literal_schema(self.heads[i], theories, default_theory),
                i, prefix='%s%s' % (pre, i)))

        body = []
        for i in range(0, len(self.body)):
            body.append(self.body[i].eliminate_column_references(
                literal_schema(self.body[i], theories, default_theory),
                i, prefix='%s%s' % (pre, i)))

        return Rule(heads, body, self.location, name=self.name,
                    comment=self.comment, original_str=self.original_str)

    def _unused_variable_prefix(self):
        """Get unused variable prefix.

        Returns variable prefix (string) that is used by no other variable
        in the rule.
        """
        variables = self.variable_names()
        found = False
        prefix = "x_"
        while not found:
            if next((var for var in variables if var.startswith(prefix)),
                    False):
                prefix += "_"
            else:
                found = True
        return prefix


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

    def tablename(self, default_theory=None):
        return self.formula.tablename(default_theory)

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
        return self.__str__() + " with proofs " + utility.iterstr(self.proofs)

    def __hash__(self):
        return hash("Event(formula={}, proofs={}, insert={}".format(
            str(self.formula), str(self.proofs), str(self.insert)))

    def __eq__(self, other):
        return (self.formula == other.formula and
                self.proofs == other.proofs and
                self.insert == other.insert)

    def __ne__(self, other):
        return not self.__eq__(other)


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
    if isinstance(x, six.string_types):
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
    if isinstance(x, six.string_types):
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

    Creates a Graph that includes one node for each table and an edge
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
        self.modal_index = analysis.ModalIndex()
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
        modals = analysis.ModalIndex()
        # TODO(thinrichs): should be able to have global_tablename
        #   return a Tablename object and therefore build a graph
        #   of Tablename objects instead of strings.
        if is_atom(formula):
            if include_atoms:
                table = formula.table.global_tablename(theory)
                nodes.add(table)
                if formula.table.modal:
                    modals.add(formula.table.modal, table)
        else:
            for head in formula.heads:
                if select_head is not None and not select_head(head):
                    continue
                # head computed differently so that if head.theory is non-None
                #   we end up with theory:head.theory:head.table
                head_table = head.table.global_tablename(theory)
                if head.table.modal:
                    modals.add(head.table.modal, head_table)
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

    def table_delete(self, table):
        self.delete_node(table)

    def find_dependencies(self, tables):
        return self.find_dependent_nodes(tables)

    def find_definitions(self, tables):
        return self.find_reachable_nodes(tables)

    def tables(self):
        return set(self.nodes.keys())


def find_subpolicy(rules, required_tables, prohibited_tables,
                   output_tables):
    """Return a subset of rules pertinent to the parameters.

    :param rules is the collection of Datalog rules to analyze
    :param required_tables is the set of tablenames that a rule must depend on.
    :param prohibited_tables is the set of tablenames that a rule must
           NOT depend on.
    :param output_tables is the set of tablenames that all rules must support.

    Table R depends on table T if T occurs in the
    body of a rule with R in the head, or T occurs in the body of a rule
    where R depends on the table in the head of that rule.

    The subset of RULES chosen has several properties:
    i) if a chosen rule has table R in the head, then one of @output_tables
       depends on R
    ii) if a chosen rule has R in the head, then R does not depend on
        any of @prohibited_tables
    iii) if a chosen rule has R in the head, then R depends on at least
         one of @required_tables.
    """
    def filter_output_definitions(rule_permitted):
        for output_table in output_tables:
            if output_table in definitions:
                newset = set()
                for rule in definitions[output_table]:
                    if rule_permitted(rule):
                        newset.add(rule)
                    else:
                        graph.formula_delete(rule)
                definitions[output_table] = newset

    # Create data structures for analysis
    graph = RuleDependencyGraph(rules)
    LOG.info("graph: %s", graph)
    definitions = {}  # maps table name to set of rules that define it
    for rule in rules:
        for head in rule.heads:
            if head.table.table not in definitions:
                definitions[head.table.table] = set()
            definitions[head.table.table].add(rule)
    LOG.info("definitions: %s", definitions)

    # Remove rules dependent on prohibited tables (except output tables)
    prohibited = graph.find_dependencies(prohibited_tables) - output_tables
    rule_permitted = lambda rule: all(lit.table.table not in prohibited
                                      for lit in rule.body)
    filter_output_definitions(rule_permitted)
    LOG.info("definitions: %s", definitions)

    # Remove rules for tables not dependent on a required table
    required = graph.find_dependencies(required_tables)
    rule_permitted = lambda rule: any(
        lit.table.table in required for lit in rule.body)
    filter_output_definitions(rule_permitted)
    LOG.info("definitions: %s", definitions)

    # Return remaining rules for tables that help define output tables
    outputs = graph.find_definitions(output_tables)
    subpolicy = set()
    for table in outputs:
        if table in definitions:
            subpolicy |= definitions[table]
    return subpolicy


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
        elif lit.is_builtin():
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
        raise exception.PolicyException(
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
        errors.append(exception.PolicyException(
            "Fact not ground: " + str(atom)))
    errors.extend(check_schema_consistency(atom, theories, theory))
    errors.extend(fact_has_no_theory(atom))
    errors.extend(keywords_safety(atom))
    return errors


def keywords_safety(lit):
    errors = []
    if lit.is_builtin(check_arguments=False):
        errors.append(exception.PolicyException(
            "Conflict with built-in tablename: " + str(lit.table)))
    return errors


def fact_has_no_theory(atom):
    """Checks that ATOM has an empty theory.  Returns exceptions."""
    if atom.table.service is None:
        return []
    return [exception.PolicyException(
        "Fact {} should not reference any policy: {}".format(
            str(atom), str(atom.table.service)))]


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
        errors.append(exception.PolicyException(
            "Variable {} found in head but not in body, rule {}".format(
                str(var), str(rule)),
            obj=var))
    return errors


def rule_modal_safety(rule):
    """Check if the rule obeys the restrictions on modals."""
    errors = []
    modal_in_head = False
    for lit in rule.heads:
        if lit.table.modal is not None:
            modal_in_head = True
            if lit.table.modal.lower() not in PERMITTED_MODALS:
                errors.append(exception.PolicyException(
                    "Only 'execute' modal is allowed; found %s in head %s" % (
                        lit.table.modal, lit)))

    if modal_in_head and len(rule.heads) > 1:
        errors.append(exception.PolicyException(
            "May not have multiple rule heads with a modal: %s" % (
                ", ".join(str(x) for x in rule.heads))))

    for lit in rule.body:
        if lit.table.modal:
            errors.append(exception.PolicyException(
                "Modals not allowed in the rule body; "
                "found %s in body literal %s" % (lit.table.modal, lit)))

    return errors


def rule_head_has_no_theory(rule, permit_head=None):
    """Checks if head of rule has None for theory.  Returns exceptions.

    PERMIT_HEAD is a function that takes a literal as argument and returns
    True if the literal is allowed to have a theory in the head.
    """
    errors = []
    for head in rule.heads:
        if (head.table.service is not None and
            head.table.modal is None and
           (not permit_head or not permit_head(head))):
            errors.append(exception.PolicyException(
                "Non-modal rule head %s should not reference "
                "any policy: %s" % (head, rule)))
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
    except exception.PolicyException as e:
        return [e]


def literal_schema(literal, theories, default_theory=None):
    """Return the schema that applies to LITERAL or None."""
    if theories is None:
        return
    # figure out theory that pertains to this literal
    active_theory = literal.table.service or default_theory
    # if current theory is unknown, no schema
    if active_theory is None:
        return
    # if theory is known, still need to check if schema is known
    if active_theory not in theories:
        # May not have been created yet
        return
    # return schema
    return theories[active_theory].schema


def schema_consistency(thing, theories, theory=None):
    if thing.is_atom():
        return literal_schema_consistency(thing, theories, theory)
    else:
        return rule_schema_consistency(thing, theories, theory)


def rule_schema_consistency(rule, theories, theory=None):
    """Returns list of problems with rule's schema."""
    assert not rule.is_atom(), "rule_schema_consistency expects a rule"
    errors = []
    for lit in rule.body:
        errors.extend(literal_schema_consistency(lit, theories, theory))
    return errors


def literal_schema_consistency(literal, theories, theory=None):
    """Returns list of errors, but does no checking if column references."""
    if theories is None:
        return []

    # These checks are handled by eliminate_column_references
    if len(literal.named_arguments) > 0:
        return []

    # figure out theory that pertains to this literal
    active_theory = literal.table.service or theory

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
    if schema.complete and literal.table.table not in schema:
        if schema.complete:
            return [exception.PolicyException(
                "Literal {} uses unknown table {} "
                "from policy {}".format(
                    str(literal), str(literal.table.table),
                    str(active_theory)))]

    # check width
    arity = schema.arity(literal.table.table)
    if arity is not None and len(literal.arguments) != arity:
        return [exception.PolicyException(
            "Literal {} contained {} arguments but only "
            "{} arguments are permitted".format(
                str(literal), len(literal.arguments), arity))]

    return []


def check_schema_consistency(item, theories, theory=None):
    errors = []
    if item.is_rule():
        errors.extend(literal_schema_consistency(
            item.head, theories, theory))
        for lit in item.body:
            errors.extend(literal_schema_consistency(
                lit, theories, theory))
    else:
        errors.extend(literal_schema_consistency(
            item, theories, theory))
    return errors


def rule_errors(rule, theories=None, theory=None):
    """Returns list of errors for RULE."""
    errors = []
    errors.extend(rule_head_safety(rule))
    errors.extend(rule_body_safety(rule))
    errors.extend(check_schema_consistency(rule, theories, theory))
    errors.extend(rule_head_has_no_theory(rule))
    errors.extend(rule_modal_safety(rule))
    errors.extend(keywords_safety(rule.head))
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
        print_antlr(self.raw_syntax_tree)

    def sigerr(self, error):
        self.errors.append(error)

    def sigwarn(self, error):
        self.warnings.append(error)

    def raise_errors(self):
        if len(self.errors) > 0:
            errors = [str(err) for err in self.errors]
            raise exception.PolicyException(
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
            raise exception.PolicyException("Lex failure.\n" +
                                            "\n".join(lexer.error_list))
        if len(parser.error_list) > 0:
            raise exception.PolicyException("Parse failure.\n" +
                                            "\n".join(parser.error_list))
        return result.tree

    def convert_to_congress(self, antlr):
        return self.create(antlr)

    def create(self, antlr):
        obj = antlr.getText()
        if obj == 'EVENT':
            return self.create_event(antlr)
        elif obj == 'RULE':
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
            raise exception.PolicyException(
                "Antlr tree with unknown root: {}".format(obj))

    def create_event(self, antlr):
        # (EVENT (MODAL RULE [POLICY]))
        print_antlr(antlr)
        modal = antlr.children[0].getText().lower()
        if modal not in ['insert', 'delete']:
            raise exception.PolicyException(
                "Unknown modal operator applied to rule: %s" % modal)
        rule = self.create(antlr.children[1])
        isinsert = (modal == 'insert')
        policy = None
        if len(antlr.children) > 2:
            policy = antlr.children[2].getText()
            policy = policy[1:len(policy) - 1]
        return Event(formula=rule, insert=isinsert, target=policy)

    def create_rule(self, antlr):
        # (RULE (AND1 AND2))
        heads = self.create_and_literals(antlr.children[0])
        body = self.create_and_literals(antlr.children[1])
        loc = utils.Location(line=antlr.children[0].token.line,
                             col=antlr.children[0].token.charPositionInLine)
        return Rule(heads, body, location=loc)

    def create_and_literals(self, antlr):
        # (AND (LIT1 ... LITN))
        return [self.create_literal(child) for child in antlr.children]

    def create_literal(self, antlr):
        # (NOT <atom>)
        # <atom>
        # (NOT (MODAL ID <atom>))
        # (MODAL ID <atom>)
        if antlr.getText() == 'NOT':
            negated = True
            antlr = antlr.children[0]
        else:
            negated = False

        lit = self.create_modal_atom(antlr)
        lit.negated = negated
        return lit

    def create_modal_atom(self, antlr):
        # (MODAL ID <atom>)
        # <atom>
        if antlr.getText() == 'MODAL':
            modal = antlr.children[0].getText()
            atom = antlr.children[1]
        else:
            modal = None
            atom = antlr
        (table, args, named, loc) = self.create_atom_aux(atom)
        table.modal = modal
        return Literal(table, args, location=loc,
                       use_modules=self.use_modules,
                       named_arguments=named)

    def create_atom_aux(self, antlr):
        # (ATOM (TABLENAME ARG1 ... ARGN))
        table = self.create_tablename(antlr.children[0])
        loc = utils.Location(line=antlr.children[0].token.line,
                             col=antlr.children[0].token.charPositionInLine)
        # Compute the args, after having converted them to Terms
#         args = []
#         if columns is None:
#             if has_named_param:
#                 self.errors.append(exception.PolicyException(
#                     "Atom {} uses named parameters but the columns for "
#                     "table {} have not been declared.".format(
#                         self.antlr_atom_str(antlr), str(table))))
#             else:
#                 args = [self.create_term(antlr.children[i])
#                         for i in range(1, len(antlr.children))]
#         else:
#             args = self.create_atom_arg_list(antlr, index, prefix, columns)
#         return (table, args, loc)
# =======
        pos_args, named_args = self.create_atom_dual_arg_list(antlr)
        return (table, pos_args, named_args, loc)

    def create_atom_dual_arg_list(self, antlr):
        """Get parameter list and named list

        Return (i) a list of compile.Term representing the positionally
        specified parameters in the ANTLR atom and (ii) a dictionary mapping
        string/number to compile.Term representing the name/index-specified
        parameters. If there are errors self.errors is modified.
        """
        # (ATOM (TABLENAME ARG1 ... ARGN))
        # construct string representation of atom for error messages
        atomstr = self.antlr_atom_str(antlr)

        # partition into regular args and column-ref args
        errors = []
        position_args = []
        first_col_ref_index = len(antlr.children)  # default save
        for i in range(1, len(antlr.children)):
            if antlr.children[i].getText() != 'NAMED_PARAM':
                position_args.append(self.create_term(antlr.children[i]))
            else:
                first_col_ref_index = i
                break

        # index the column refs and translate into Terms
        reference_args = {}
        for i in range(first_col_ref_index, len(antlr.children)):
            param = antlr.children[i]
            # (NAMED_PARAM (COLUMN_REF TERM))
            if param.getText() != 'NAMED_PARAM':
                errors.append(exception.PolicyException(
                    "Atom {} has a positional parameter after "
                    "a reference parameter".format(
                        atomstr)))
            elif param.children[0].getText() == 'COLUMN_NAME':
                # (COLUMN_NAME (ID))
                name = param.children[0].children[0].getText()
                if name in reference_args:
                    errors.append(exception.PolicyException(
                        "In atom {} two values for column name {} "
                        "were provided".format(atomstr, name)))
                reference_args[name] = self.create_term(param.children[1])
            else:
                # (COLUMN_NUMBER (INT))
                # Know int() will succeed because of lexer
                number = int(param.children[0].children[0].getText())
                if number in reference_args:
                    errors.append(exception.PolicyException(
                        "In atom {} two values for column number {} "
                        "were provided.".format(atomstr, str(number))))
                reference_args[number] = self.create_term(param.children[1])
                if number < len(position_args):
                    errors.append(exception.PolicyException(
                        "In atom {} column number {} is already provided by "
                        "position arguments.".format(
                            atomstr, number)))
        if errors:
            self.errors.extend(errors)
        return position_args, reference_args

    def antlr_atom_str(self, antlr):
        # (ATOM (TABLENAME ARG1 ... ARGN))
        table = self.create_tablename(antlr.children[0])
        argstrs = []
        for i in range(1, len(antlr.children)):
            arg = antlr.children[i]
            if arg.getText() == 'NAMED_PARAM':
                arg = (arg.children[0].children[0].getText() +
                       '=' +
                       arg.children[1].children[0].getText())
                argstrs.append(arg)
            else:
                arg = arg.children[0].getText()
        return str(table) + "(" + ",".join(argstrs) + ")"

    def create_tablename(self, antlr):
        # (STRUCTURED_NAME (ARG1 ... ARGN))
        if antlr.children[-1].getText() in ['+', '-']:
            table = (":".join([x.getText() for x in antlr.children[:-1]]) +
                     antlr.children[-1].getText())
        else:
            table = ":".join([x.getText() for x in antlr.children])
        return Tablename.create_from_tablename(
            table, use_modules=self.use_modules)

    def create_term(self, antlr):
        # (TYPE (VALUE))
        op = antlr.getText()
        loc = utils.Location(line=antlr.children[0].token.line,
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
            raise exception.PolicyException(
                "Unknown term operator: {}".format(op))

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
        for i in range(1, len(antlr_atom.children)):
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


def print_antlr(tree):
    """Print an antlr Tree."""
    print_tree(
        tree,
        lambda x: x.getText(),
        lambda x: x.children,
        ind=1)


def print_tree(tree, text, kids, ind=0):
    """Helper function for printing.

    Print out TREE using function TEXT to extract node description and
    function KIDS to compute the children of a given node.
    IND is a number representing the indentation level.
    """
    print(("|" * ind), end=' ')
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
