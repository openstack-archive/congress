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

from oslo_log import log as logging
import six

from congress import exception

LOG = logging.getLogger(__name__)

DATABASE_POLICY_TYPE = 'database'
NONRECURSIVE_POLICY_TYPE = 'nonrecursive'
ACTION_POLICY_TYPE = 'action'
MATERIALIZED_POLICY_TYPE = 'materialized'
DELTA_POLICY_TYPE = 'delta'
DATASOURCE_POLICY_TYPE = 'datasource'


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
        self.stream = six.moves.StringIO()
        self.funcs.append(self.string_output)

    def string_output(self, msg, *args):
        self.stream.write((msg % args) + "\n")

    def get_value(self):
        return self.stream.getvalue()


##############################################################################
# Logical Building Blocks
##############################################################################

class Proof(object):
    """A single proof.

    Differs semantically from Database's
    Proof in that this version represents a proof that spans rules,
    instead of just a proof for a single rule.
    """
    def __init__(self, root, children):
        self.root = root
        self.children = children

    def __str__(self):
        return self.str_tree(0)

    def str_tree(self, depth):
        s = " " * depth
        s += str(self.root)
        s += "\n"
        for child in self.children:
            s += child.str_tree(depth + 1)
        return s

    def leaves(self):
        if len(self.children) == 0:
            return [self.root]
        result = []
        for child in self.children:
            result.extend(child.leaves())
        return result


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


##############################################################################
# Abstract Theories
##############################################################################

class Theory(object):
    def __init__(self, name=None, abbr=None, schema=None, theories=None,
                 id=None, desc=None, owner=None, kind=None):
        self.schema = schema
        self.theories = theories
        self.kind = kind
        self.id = id
        self.desc = desc
        self.owner = owner

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

    def set_id(self, id):
        self.id = id

    def initialize_tables(self, tablenames, facts):
        """initialize_tables

        Event handler for (re)initializing a collection of tables.  Clears
        tables befores assigning the new table content.

        @facts must be an iterable containing compile.Fact objects.
        """
        raise NotImplementedError

    def actual_events(self, events):
        """Returns subset of EVENTS that are not noops."""
        actual = []
        for event in events:
            if event.insert:
                if event.formula not in self:
                    actual.append(event)
            else:
                if event.formula in self:
                    actual.append(event)
        return actual

    def debug_mode(self):
        tr = Tracer()
        tr.trace('*')
        self.set_tracer(tr)

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

    def tablenames(self, body_only=False, include_builtin=False,
                   include_modal=True):
        tablenames = set()
        for rule in self.policy():
            tablenames |= rule.tablenames(
                body_only=body_only, include_builtin=include_builtin,
                include_modal=include_modal)
        return tablenames

    def __str__(self):
        return "Theory %s" % self.name

    def content_string(self):
        return '\n'.join([str(p) for p in self.content()]) + '\n'

    def get_rule(self, ident):
        for p in self.policy():
            if hasattr(p, 'id') and str(p.id) == str(ident):
                return p
        raise exception.NotFound('rule_id %s  is not found.' % ident)

    def arity(self, tablename, modal=None):
        """Return the number of columns for the given tablename.

        TABLENAME is of the form <policy>:<table> or <table>.
        MODAL is the value of the modal operator.
        """
        return NotImplementedError
