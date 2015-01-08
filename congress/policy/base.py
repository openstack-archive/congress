# Copyright (c) 2015 VMware, Inc. All rights reserved.
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
import cStringIO

from congress.openstack.common import log as logging
from congress.policy import compile
from congress.policy.utility import iterstr

LOG = logging.getLogger(__name__)

DATABASE_POLICY_TYPE = 'database'
NONRECURSIVE_POLICY_TYPE = 'nonrecursive'
ACTION_POLICY_TYPE = 'action'
MATERIALIZED_POLICY_TYPE = 'materialized'
DELTA_POLICY_TYPE = 'delta'


class Tracer(object):
    def __init__(self):
        self.expressions = []
        self.funcs = [LOG.debug]   # functions to call to trace

    def trace(self, table):
        self.expressions.append(table)

    def is_traced(self, table):
        return table in self.expressions or '*' in self.expressions

    def log(self, table, msg, *args, **kwargs):
        depth = kwargs.pop("depth", 0)
        if kwargs:
            raise TypeError("Unexpected keyword arguments: %s" % kwargs)
        if self.is_traced(table):
            for func in self.funcs:
                func(("| " * depth) + msg, *args)


class StringTracer(Tracer):
    def __init__(self):
        super(StringTracer, self).__init__()
        self.stream = cStringIO.StringIO()
        self.funcs.append(self.string_output)

    def string_output(self, msg, *args):
        self.stream.write((msg % args) + "\n")

    def get_value(self):
        return self.stream.getvalue()


##############################################################################
# Events
##############################################################################

class EventQueue(object):
    def __init__(self):
        self.queue = collections.deque()

    def enqueue(self, event):
        self.queue.append(event)

    def dequeue(self):
        return self.queue.popleft()

    def __len__(self):
        return len(self.queue)

    def __str__(self):
        return "[" + ",".join([str(x) for x in self.queue]) + "]"


class Event(object):
    def __init__(self, formula=None, insert=True, proofs=None, target=None):
        if proofs is None:
            proofs = []
        self.formula = formula
        self.proofs = proofs
        self.insert = insert
        self.target = target
        # LOG.debug("EV: created event %s", self)

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
        elif isinstance(self.target, Theory):
            target = " for {}".format(self.target.name)
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


##############################################################################
# Abstract Theories
##############################################################################

class Theory(object):
    def __init__(self, name=None, abbr=None, schema=None, theories=None):
        # reference to Runtime class, for cross-theory info
        #  Especially for testing, we don't always need
        self.schema = schema
        self.theories = theories
        self.kind = None

        self.tracer = Tracer()
        if name is None:
            self.name = repr(self)
        else:
            self.name = name
        if abbr is None:
            self.abbr = "th"
        else:
            self.abbr = abbr
        maxlength = 6
        if len(self.abbr) > maxlength:
            self.trace_prefix = self.abbr[0:maxlength]
        else:
            self.trace_prefix = self.abbr + " " * (maxlength - len(self.abbr))
        self.dependency_graph = compile.cross_theory_dependency_graph([], name)

    def set_tracer(self, tracer):
        self.tracer = tracer

    def get_tracer(self):
        return self.tracer

    def log(self, table, msg, *args, **kwargs):
        msg = self.trace_prefix + ": " + msg
        self.tracer.log(table, msg, *args, **kwargs)

    def policy(self):
        """Return a list of the policy statements in this theory."""
        raise NotImplementedError()

    def content(self):
        """Return a list of the contents of this theory.

        Maybe rules and/or data. Note: do not change name to CONTENTS, as this
        is reserved for a dictionary of stuff used by TopDownTheory.
        """
        raise NotImplementedError()

    def tablenames(self):
        tablenames = set()
        for rule in self.policy():
            tablenames |= rule.tablenames()
        return tablenames

    def __str__(self):
        return '\n'.join([str(p) for p in self.content()]) + '\n'

    def get_rule(self, ident):
        for p in self.policy():
            if hasattr(p, 'id') and p.id == ident:
                return p
        return

    def get_arity_self(self, tablename):
        """Returns the number of arguments for the given TABLENAME.

        If the table is not defined by SELF, returns None.
        A table is defined-by SELF if this theory believes it is
        the source of truth for that table, i.e. this is a Database
        theory and we store the contents of that table or this is
        a rule theory, and that tablename is in the head of a rule.
        """
        raise NotImplementedError

    def get_arity_includes(self, tablename):
        """Returns the number of arguments for the given TABLENAME or None.

        Ignores the global_schema.
        """
        result = self.get_arity_self(tablename)
        if result is not None:
            return result
        if not hasattr(self, "includes"):
            return None
        for th in self.includes:
            result = th.get_arity_includes(tablename)
            if result is not None:
                return result
        return None

    def get_arity(self, tablename):
        """Returns the number of arguments for the given TABLENAME or None."""
        if self.theories is None:
            return self.get_arity_includes(tablename)
        (theory, name) = compile.Literal.partition_tablename(tablename)
        if theory is None:
            return self.get_arity_includes(tablename)
        if theory in self.theories:
            return self.theories[theory].arity(name)

    def update_dependency_graph(self):
        self.dependency_graph = compile.cross_theory_dependency_graph(
            self.content(), self.name)

    def _causes_recursion_across_theories(self, current):
        """Check for recursion.

        Returns True if changing policy to CURRENT rules would result
        in recursion across theories.
        """
        if not self.theories:
            return False
        global_graph = compile.cross_theory_dependency_graph([], self.name)
        me = compile.cross_theory_dependency_graph(current, self.name)
        global_graph |= me
        for theory, theory_obj in self.theories.iteritems():
            if theory != self.name:
                global_graph |= theory_obj.dependency_graph
        # TODO(thinrichs): improve the accuracy of this implementation.
        #   Right now it disallows recursion even within a theory.
        return compile.is_recursive(global_graph)
