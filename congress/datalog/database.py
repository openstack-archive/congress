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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from six.moves import range

from congress.datalog import base
from congress.datalog import compile
from congress.datalog import topdown
from congress.datalog import unify
from congress.datalog import utility
from congress import exception


##############################################################################
# Concrete Theory: Database
##############################################################################
class Database(topdown.TopDownTheory):
    class Proof(object):
        def __init__(self, binding, rule):
            self.binding = binding
            self.rule = rule

        def __str__(self):
            return "apply({}, {})".format(str(self.binding), str(self.rule))

        def __eq__(self, other):
            result = (self.binding == other.binding and
                      self.rule == other.rule)
            # LOG.debug("Pf: Comparing %s and %s: %s", self, other, result)
            # LOG.debug("Pf: %s == %s is %s",
            #     self.binding, other.binding, self.binding == other.binding)
            # LOG.debug("Pf: %s == %s is %s",
            #     self.rule, other.rule, self.rule == other.rule)
            return result

    class ProofCollection(object):
        def __init__(self, proofs):
            self.contents = list(proofs)

        def __str__(self):
            return '{' + ",".join(str(x) for x in self.contents) + '}'

        def __isub__(self, other):
            if other is None:
                return
            # LOG.debug("PC: Subtracting %s and %s", self, other)
            remaining = []
            for proof in self.contents:
                if proof not in other.contents:
                    remaining.append(proof)
            self.contents = remaining
            return self

        def __ior__(self, other):
            if other is None:
                return
            # LOG.debug("PC: Unioning %s and %s", self, other)
            for proof in other.contents:
                # LOG.debug("PC: Considering %s", proof)
                if proof not in self.contents:
                    self.contents.append(proof)
            return self

        def __getitem__(self, key):
            return self.contents[key]

        def __len__(self):
            return len(self.contents)

        def __ge__(self, iterable):
            for proof in iterable:
                if proof not in self.contents:
                    # LOG.debug("Proof %s makes %s not >= %s",
                    #     proof, self, iterstr(iterable))
                    return False
            return True

        def __le__(self, iterable):
            for proof in self.contents:
                if proof not in iterable:
                    # LOG.debug("Proof %s makes %s not <= %s",
                    #     proof, self, iterstr(iterable))
                    return False
            return True

        def __eq__(self, other):
            return self <= other and other <= self

    class DBTuple(object):
        def __init__(self, iterable, proofs=None):
            self.tuple = tuple(iterable)
            if proofs is None:
                proofs = []
            self.proofs = Database.ProofCollection(proofs)

        def __eq__(self, other):
            return self.tuple == other.tuple

        def __str__(self):
            return str(self.tuple) + str(self.proofs)

        def __len__(self):
            return len(self.tuple)

        def __getitem__(self, index):
            return self.tuple[index]

        def __setitem__(self, index, value):
            self.tuple[index] = value

        def match(self, atom, unifier):
            # LOG.debug("DBTuple matching %s against atom %s in %s",
            #     self, iterstr(atom.arguments), unifier)
            if len(self.tuple) != len(atom.arguments):
                return None
            changes = []
            for i in range(0, len(atom.arguments)):
                val, binding = unifier.apply_full(atom.arguments[i])
                # LOG.debug("val(%s)=%s at %s; comparing to object %s",
                #     atom.arguments[i], val, binding, self.tuple[i])
                if val.is_variable():
                    changes.append(binding.add(
                        val, compile.Term.create_from_python(self.tuple[i]),
                        None))
                else:
                    if val.name != self.tuple[i]:
                        unify.undo_all(changes)
                        return None
            return changes

    def __init__(self, name=None, abbr=None, theories=None, schema=None,
                 desc=None, owner=None):
        super(Database, self).__init__(
            name=name, abbr=abbr, theories=theories, schema=schema,
            desc=desc, owner=owner)
        self.data = {}
        self.kind = base.DATABASE_POLICY_TYPE

    def str2(self):
        def hash2str(h):
            s = "{"
            s += ", ".join(["{} : {}".format(str(key), str(h[key]))
                           for key in h])
            return s

        def hashlist2str(h):
            strings = []
            for key in h:
                s = "{} : ".format(key)
                s += '['
                s += ', '.join([str(val) for val in h[key]])
                s += ']'
                strings.append(s)
            return '{' + ", ".join(strings) + '}'

        return hashlist2str(self.data)

    def __eq__(self, other):
        return self.data == other.data

    def __sub__(self, other):
        def add_tuple(table, dbtuple):
            new = [table]
            new.extend(dbtuple.tuple)
            results.append(new)

        results = []
        for table in self.data:
            if table not in other.data:
                for dbtuple in self.data[table]:
                    add_tuple(table, dbtuple)
            else:
                for dbtuple in self.data[table]:
                    if dbtuple not in other.data[table]:
                        add_tuple(table, dbtuple)
        return results

    def __or__(self, other):
        def add_db(db):
            for table in db.data:
                for dbtuple in db.data[table]:
                    result.insert(compile.Literal.create_from_table_tuple(
                        table, dbtuple.tuple), proofs=dbtuple.proofs)
        result = Database()
        add_db(self)
        add_db(other)
        return result

    def __getitem__(self, key):
        # KEY must be a tablename
        return self.data[key]

    def content(self, tablenames=None):
        """Return a sequence of Literals representing all the table data."""
        results = []
        if tablenames is None:
            tablenames = self.data.keys()
        for table in tablenames:
            if table not in self.data:
                continue
            for dbtuple in self.data[table]:
                results.append(compile.Literal.create_from_table_tuple(
                    table, dbtuple.tuple))
        return results

    def is_noop(self, event):
        """Returns T if EVENT is a noop on the database."""
        # insert/delete same code but with flipped return values
        # Code below is written as insert, except noop initialization.
        if event.is_insert():
            noop = True
        else:
            noop = False
        if event.formula.table.table not in self.data:
            return not noop
        event_data = self.data[event.formula.table.table]
        raw_tuple = tuple(event.formula.argument_names())
        for dbtuple in event_data:
            if dbtuple.tuple == raw_tuple:
                if event.proofs <= dbtuple.proofs:
                    return noop
        return not noop

    def __contains__(self, formula):
        if not compile.is_atom(formula):
            return False
        if formula.table.table not in self.data:
            return False
        event_data = self.data[formula.table.table]
        raw_tuple = tuple(formula.argument_names())
        return any((dbtuple.tuple == raw_tuple for dbtuple in event_data))

    def explain(self, atom):
        if atom.table.table not in self.data or not atom.is_ground():
            return self.ProofCollection([])
        args = tuple([x.name for x in atom.arguments])
        for dbtuple in self.data[atom.table.table]:
            if dbtuple.tuple == args:
                return dbtuple.proofs

    def tablenames(self, body_only=False, include_builtin=False,
                   include_modal=True):
        """Return all table names occurring in this theory."""
        if body_only:
            return []
        return self.data.keys()

    # overloads for TopDownTheory so we can properly use the
    #    top_down_evaluation routines
    def defined_tablenames(self):
        return self.data.keys()

    def head_index(self, table, match_literal=None):
        if table not in self.data:
            return []
        return self.data[table]

    def head(self, thing):
        return thing

    def body(self, thing):
        return []

    def bi_unify(self, dbtuple, unifier1, atom, unifier2, theoryname):
        """THING1 is always a ground DBTuple and THING2 is always an ATOM."""
        return dbtuple.match(atom, unifier2)

    def atom_to_internal(self, atom, proofs=None):
        return atom.table.table, self.DBTuple(atom.argument_names(), proofs)

    def insert(self, atom, proofs=None):
        """Inserts ATOM into the DB.  Returns changes."""
        return self.modify(compile.Event(formula=atom, insert=True,
                                         proofs=proofs))

    def delete(self, atom, proofs=None):
        """Deletes ATOM from the DB.  Returns changes."""
        return self.modify(compile.Event(formula=atom, insert=False,
                                         proofs=proofs))

    def update(self, events):
        """Applies all of EVENTS to the DB.

        Each event is either an insert or a delete.
        """
        changes = []
        for event in events:
            changes.extend(self.modify(event))
        return changes

    def update_would_cause_errors(self, events):
        """Return a list of Policyxception.

        Return a list of PolicyException if we were
        to apply the events EVENTS to the current policy.
        """
        self.log(None, "update_would_cause_errors %s", utility.iterstr(events))
        errors = []
        for event in events:
            if not compile.is_atom(event.formula):
                errors.append(exception.PolicyException(
                    "Non-atomic formula is not permitted: {}".format(
                        str(event.formula))))
            else:
                errors.extend(compile.fact_errors(
                    event.formula, self.theories, self.name))
        return errors

    def modify(self, event):
        """Insert/Delete atom.

        Inserts/deletes ATOM and returns a list of changes that
        were caused. That list contains either 0 or 1 Event.
        """
        assert compile.is_atom(event.formula), "Modify requires Atom"
        atom = event.formula
        self.log(atom.table.table, "Modify: %s", atom)
        if self.is_noop(event):
            self.log(atom.table.table, "Event %s is a noop", event)
            return []
        if event.insert:
            self.insert_actual(atom, proofs=event.proofs)
        else:
            self.delete_actual(atom, proofs=event.proofs)
        return [event]

    def insert_actual(self, atom, proofs=None):
        """Workhorse for inserting ATOM into the DB.

        Along with proofs explaining how ATOM was computed from other tables.
        """
        assert compile.is_atom(atom), "Insert requires Atom"
        table, dbtuple = self.atom_to_internal(atom, proofs)
        self.log(table, "Insert: %s", atom)
        if table not in self.data:
            self.data[table] = [dbtuple]
            self.log(atom.table.table, "First tuple in table %s", table)
            return
        else:
            for existingtuple in self.data[table]:
                assert existingtuple.proofs is not None
                if existingtuple.tuple == dbtuple.tuple:
                    assert existingtuple.proofs is not None
                    existingtuple.proofs |= dbtuple.proofs
                    assert existingtuple.proofs is not None
                    return
            self.data[table].append(dbtuple)

    def delete_actual(self, atom, proofs=None):
        """Workhorse for deleting ATOM from the DB.

        Along with the proofs that are no longer true.
        """
        assert compile.is_atom(atom), "Delete requires Atom"
        self.log(atom.table.table, "Delete: %s", atom)
        table, dbtuple = self.atom_to_internal(atom, proofs)
        if table not in self.data:
            return
        for i in range(0, len(self.data[table])):
            existingtuple = self.data[table][i]
            if existingtuple.tuple == dbtuple.tuple:
                existingtuple.proofs -= dbtuple.proofs
                if len(existingtuple.proofs) == 0:
                    del self.data[table][i]
                return

    def policy(self):
        """Return the policy for this theory.

        No policy in this theory; only data.
        """
        return []

    def get_arity_self(self, tablename):
        if tablename not in self.data:
            return None
        if len(self.data[tablename]) == 0:
            return None
        return len(self.data[tablename][0].tuple)

    def content_string(self):
        s = ""
        for lit in self.content():
            s += str(lit) + '\n'
        return s + '\n'
