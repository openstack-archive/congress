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
import os

from congress.openstack.common import log as logging
from congress.policy.base import ACTION_POLICY_TYPE
from congress.policy.base import DATABASE_POLICY_TYPE
from congress.policy.base import DELTA_POLICY_TYPE
from congress.policy.base import Event
from congress.policy.base import EventQueue
from congress.policy.base import MATERIALIZED_POLICY_TYPE
from congress.policy.base import NONRECURSIVE_POLICY_TYPE
from congress.policy.base import StringTracer
from congress.policy.base import Theory
from congress.policy.base import Tracer
from congress.policy.builtin.congressbuiltin import builtin_registry
from congress.policy import compile
from congress.policy.nonrecursive import ActionTheory
from congress.policy.nonrecursive import NonrecursiveRuleTheory
from congress.policy.ruleset import RuleSet
from congress.policy.topdown import TopDownTheory
from congress.policy import unify
from congress.policy.utility import iterstr

LOG = logging.getLogger(__name__)


class CongressRuntime (Exception):
    pass


class ExecutionLogger(object):
    def __init__(self):
        self.messages = []

    def debug(self, msg, *args):
        self.messages.append(msg % args)

    def info(self, msg, *args):
        self.messages.append(msg % args)

    def warn(self, msg, *args):
        self.messages.append(msg % args)

    def error(self, msg, *args):
        self.messages.append(msg % args)

    def critical(self, msg, *args):
        self.messages.append(msg % args)

    def content(self):
        return '\n'.join(self.messages)

    def empty(self):
        self.messages = []


def list_to_database(atoms):
    database = Database()
    for atom in atoms:
        if atom.is_atom():
            database.insert(atom)
    return database


def string_to_database(string, theories=None):
    return list_to_database(compile.parse(
        string, theories=theories))


##############################################################################
# Logical Building Blocks
##############################################################################

class Proof(object):
    """A single proof.

    Differs semantically from Database's
    Proof in that this verison represents a proof that spans rules,
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


class DeltaRule(object):
    """Rule describing how updates to data sources change table."""
    def __init__(self, trigger, head, body, original):
        self.trigger = trigger  # atom
        self.head = head  # atom
        self.body = body  # list of literals
        self.original = original  # Rule from which SELF was derived

    def __str__(self):
        return "<trigger: {}, head: {}, body: {}>".format(
            str(self.trigger), str(self.head), [str(lit) for lit in self.body])

    def __eq__(self, other):
        return (self.trigger == other.trigger and
                self.head == other.head and
                len(self.body) == len(other.body) and
                all(self.body[i] == other.body[i]
                    for i in xrange(0, len(self.body))))

    def variables(self):
        """Return the set of variables occurring in this delta rule."""
        vs = self.trigger.variables()
        vs |= self.head.variables()
        for atom in self.body:
            vs |= atom.variables()
        return vs

    def tablenames(self):
        """Return the set of tablenames occurring in this delta rule."""
        tables = set()
        tables.add(self.head.tablename())
        tables.add(self.trigger.tablename())
        for atom in self.body:
            tables.add(atom.tablename())
        return tables


##############################################################################
# Concrete Theory: Database
##############################################################################
class Database(TopDownTheory):
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
            for i in xrange(0, len(atom.arguments)):
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

    def __init__(self, name=None, abbr=None, theories=None, schema=None):
        super(Database, self).__init__(
            name=name, abbr=abbr, theories=theories, schema=schema)
        self.data = {}
        self.kind = DATABASE_POLICY_TYPE

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
        if event.formula.table not in self.data:
            return not noop
        event_data = self.data[event.formula.table]
        raw_tuple = tuple(event.formula.argument_names())
        for dbtuple in event_data:
            if dbtuple.tuple == raw_tuple:
                if event.proofs <= dbtuple.proofs:
                    return noop
        return not noop

    def explain(self, atom):
        if atom.table not in self.data or not atom.is_ground():
            return self.ProofCollection([])
        args = tuple([x.name for x in atom.arguments])
        for dbtuple in self.data[atom.table]:
            if dbtuple.tuple == args:
                return dbtuple.proofs

    def tablenames(self):
        """Return all table names occurring in this theory."""
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

    def bi_unify(self, dbtuple, unifier1, atom, unifier2):
        """THING1 is always a ground DBTuple and THING2 is always an ATOM."""
        return dbtuple.match(atom, unifier2)

    def atom_to_internal(self, atom, proofs=None):
        return atom.table, self.DBTuple(atom.argument_names(), proofs)

    def insert(self, atom, proofs=None):
        """Inserts ATOM into the DB.  Returns changes."""
        return self.modify(Event(formula=atom, insert=True, proofs=proofs))

    def delete(self, atom, proofs=None):
        """Deletes ATOM from the DB.  Returns changes."""
        return self.modify(Event(formula=atom, insert=False, proofs=proofs))

    def update(self, events):
        """Applies all of EVENTS to the DB.

        Each event is either an insert or a delete.
        """
        changes = []
        for event in events:
            changes.extend(self.modify(event))
        return changes

    def update_would_cause_errors(self, events):
        """Return a list of compile.CongressException.

        Return a list of compile.CongressException if we were
        to apply the events EVENTS to the current policy.
        """
        self.log(None, "update_would_cause_errors %s", iterstr(events))
        errors = []
        for event in events:
            if not compile.is_atom(event.formula):
                errors.append(compile.CongressException(
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
        self.log(atom.table, "Modify: %s", atom)
        if self.is_noop(event):
            self.log(atom.table, "Event %s is a noop", event)
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
            self.log(atom.table, "First tuple in table %s", table)
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
        self.log(atom.table, "Delete: %s", atom)
        table, dbtuple = self.atom_to_internal(atom, proofs)
        if table not in self.data:
            return
        for i in xrange(0, len(self.data[table])):
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

    def update_dependency_graph(self):
        self.dependency_graph = compile.cross_theory_dependency_graph([])

    def get_arity_self(self, tablename):
        if tablename not in self.data:
            return None
        if len(self.data[tablename]) == 0:
            return None
        return len(self.data[tablename][0].tuple)

    def __str__(self):
        s = ""
        for lit in self.content():
            s += str(lit) + '\n'
        return s + '\n'


##############################################################################
# Concrete Theories: other
##############################################################################

class DeltaRuleTheory (Theory):
    """A collection of DeltaRules.  Not useful by itself as a policy."""
    def __init__(self, name=None, abbr=None, theories=None):
        super(DeltaRuleTheory, self).__init__(
            name=name, abbr=abbr, theories=theories)
        # dictionary from table name to list of rules with that table as
        # trigger
        self.rules = RuleSet()
        # dictionary from delta_rule to the rule from which it was derived
        self.originals = set()
        # dictionary from table name to number of rules with that table in
        # head
        self.views = {}
        # all tables
        self.all_tables = {}
        self.kind = DELTA_POLICY_TYPE

    def modify(self, event):
        """Insert/delete the compile.Rule RULE into the theory.

        Return list of changes (either the empty list or
        a list including just RULE).
        """
        self.log(None, "DeltaRuleTheory.modify %s", event.formula)
        self.log(None, "originals: %s", iterstr(self.originals))
        if event.insert:
            if self.insert(event.formula):
                return [event]
        else:
            if self.delete(event.formula):
                return [event]
        return []

    def insert(self, rule):
        """Insert a compile.Rule into the theory.

        Return True iff the theory changed.
        """
        assert compile.is_regular_rule(rule), (
            "DeltaRuleTheory only takes rules")
        self.log(rule.tablename(), "Insert: %s", rule)
        if rule in self.originals:
            self.log(None, iterstr(self.originals))
            return False
        self.log(rule.tablename(), "Insert 2: %s", rule)
        for delta in self.compute_delta_rules([rule]):
            self.insert_delta(delta)
        self.originals.add(rule)
        return True

    def insert_delta(self, delta):
        """Insert a delta rule."""
        self.log(None, "Inserting delta rule %s", delta)
        # views (tables occurring in head)
        if delta.head.table in self.views:
            self.views[delta.head.table] += 1
        else:
            self.views[delta.head.table] = 1

        # tables
        for table in delta.tablenames():
            if table in self.all_tables:
                self.all_tables[table] += 1
            else:
                self.all_tables[table] = 1

        # contents
        # TODO(thinrichs): eliminate dups, maybe including
        #     case where bodies are reorderings of each other
        self.rules.add_rule(delta.trigger.table, delta)

    def delete(self, rule):
        """Delete a compile.Rule from theory.

        Assumes that COMPUTE_DELTA_RULES is deterministic.
        Returns True iff the theory changed.
        """
        self.log(rule.tablename(), "Delete: %s", rule)
        if rule not in self.originals:
            return False
        for delta in self.compute_delta_rules([rule]):
            self.delete_delta(delta)
        self.originals.remove(rule)
        return True

    def delete_delta(self, delta):
        """Delete the DeltaRule DELTA from the theory."""
        # views
        if delta.head.table in self.views:
            self.views[delta.head.table] -= 1
            if self.views[delta.head.table] == 0:
                del self.views[delta.head.table]

        # tables
        for table in delta.tablenames():
            if table in self.all_tables:
                self.all_tables[table] -= 1
                if self.all_tables[table] == 0:
                    del self.all_tables[table]

        # contents
        self.rules.discard_rule(delta.trigger.table, delta)

    def policy(self):
        return self.originals

    def get_arity_self(self, tablename):
        for p in self.originals:
            if p.head.table == tablename:
                return len(p.head.arguments)
        return None

    def __str__(self):
        return str(self.rules)

    def rules_with_trigger(self, table):
        """Return the list of DeltaRules that trigger on the given TABLE."""
        if table in self.rules:
            return self.rules.get_rules(table)
        else:
            return []

    def is_view(self, x):
        return x in self.views

    def is_known(self, x):
        return x in self.all_tables

    def base_tables(self):
        base = []
        for table in self.all_tables:
            if table not in self.views:
                base.append(table)
        return base

    @classmethod
    def eliminate_self_joins(cls, formulas):
        """Remove self joins.

        Return new list of formulas that is equivalent to
        the list of formulas FORMULAS except that there
        are no self-joins.
        """
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
        # remove self-joins from rules
        results = []
        for rule in formulas:
            if rule.is_atom():
                results.append(rule)
                continue
            LOG.debug("eliminating self joins from %s", rule)
            occurrences = {}  # for just this rule
            for atom in rule.body:
                table = atom.tablename()
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
                        global_self_joins[tablearity] = (
                            max(occurrences[tablearity] - 1,
                                global_self_joins[tablearity]))
            results.append(rule)
            LOG.debug("final rule: %s", rule)
        # add definitions for new tables
        for tablearity in global_self_joins:
            table = tablearity[0]
            arity = tablearity[1]
            for i in xrange(1, global_self_joins[tablearity] + 1):
                newtable = new_table_name(table, arity, i)
                args = [compile.Variable(var) for var in n_variables(arity)]
                head = compile.Literal(newtable, args)
                body = [compile.Literal(table, args)]
                results.append(compile.Rule(head, body))
                LOG.debug("Adding rule %s", results[-1])
        return results

    @classmethod
    def compute_delta_rules(cls, formulas):
        """Return list of DeltaRules computed from formulas.

        Assuming FORMULAS has no self-joins, return a list of DeltaRules
        derived from those FORMULAS.
        """
        # Should do the following for correctness, but it needs to be
        #    done elsewhere so that we can properly maintain the tables
        #    that are generated.
        # formulas = cls.eliminate_self_joins(formulas)
        delta_rules = []
        for rule in formulas:
            if rule.is_atom():
                continue
            rule = compile.reorder_for_safety(rule)
            for literal in rule.body:
                if builtin_registry.is_builtin(literal.table,
                                               len(literal.arguments)):
                    continue
                newbody = [lit for lit in rule.body if lit is not literal]
                delta_rules.append(
                    DeltaRule(literal, rule.head, newbody, rule))
        return delta_rules


class MaterializedViewTheory(TopDownTheory):
    """A theory that stores the table contents of views explicitly.

    Relies on included theories to define the contents of those
    tables not defined by the rules of the theory.
    Recursive rules are allowed.
    """

    def __init__(self, name=None, abbr=None, theories=None, schema=None):
        super(MaterializedViewTheory, self).__init__(
            name=name, abbr=abbr, theories=theories, schema=schema)
        # queue of events left to process
        self.queue = EventQueue()
        # data storage
        db_name = None
        db_abbr = None
        delta_name = None
        delta_abbr = None
        if name is not None:
            db_name = name + "Database"
            delta_name = name + "Delta"
        if abbr is not None:
            db_abbr = abbr + "DB"
            delta_abbr = abbr + "Dlta"
        self.database = Database(name=db_name, abbr=db_abbr)
        # rules that dictate how database changes in response to events
        self.delta_rules = DeltaRuleTheory(name=delta_name, abbr=delta_abbr)
        self.update_dependency_graph()
        self.kind = MATERIALIZED_POLICY_TYPE

    def set_tracer(self, tracer):
        if isinstance(tracer, Tracer):
            self.tracer = tracer
            self.database.tracer = tracer
            self.delta_rules.tracer = tracer
        else:
            self.tracer = tracer['self']
            self.database.tracer = tracer['database']
            self.delta_rules.tracer = tracer['delta_rules']

    def get_tracer(self):
        return {'self': self.tracer,
                'database': self.database.tracer,
                'delta_rules': self.delta_rules.tracer}

    # External Interface

    # SELECT is handled by TopDownTheory

    def insert(self, formula):
        return self.update([Event(formula=formula, insert=True)])

    def delete(self, formula):
        return self.update([Event(formula=formula, insert=False)])

    def update(self, events):
        """Apply inserts/deletes described by EVENTS and return changes.

           Does not check if EVENTS would cause errors.
           """
        for event in events:
            assert compile.is_datalog(event.formula), (
                "Non-formula not allowed: {}".format(str(event.formula)))
            self.enqueue_any(event)
        changes = self.process_queue()
        if changes:
            self.update_dependency_graph()
        return changes

    def update_would_cause_errors(self, events):
        """Return a list of compile.CongressException.

        Return a list of compile.CongressException if we were
        to apply the events EVENTS to the current policy.
        """
        self.log(None, "update_would_cause_errors %s", iterstr(events))
        errors = []
        current = set(self.policy())  # copy so can modify and discard
        # compute new rule set
        for event in events:
            assert compile.is_datalog(event.formula), (
                "update_would_cause_errors operates only on objects")
            self.log(None, "Updating %s", event.formula)
            if event.formula.is_atom():
                errors.extend(compile.fact_errors(
                    event.formula, self.theories, self.name))
            else:
                errors.extend(compile.rule_errors(
                    event.formula, self.theories, self.name))
            if event.insert:
                current.add(event.formula)
            elif event.formula in current:
                current.remove(event.formula)
        # check for stratified
        # TODO(thinrichs): include path in error message
        if not compile.is_stratified(current):
            errors.append(compile.CongressException(
                "Rules are not stratified"))
        if self._causes_recursion_across_theories(current):
            errors.append(compile.CongressException(
                "Rules are recursive across theories"))
        return errors

    def explain(self, query, tablenames, find_all):
        """Returns a list of proofs if QUERY is true or None if else."""
        assert compile.is_atom(query), "Explain requires an atom"
        # ignoring TABLENAMES and FIND_ALL
        #    except that we return the proper type.
        proof = self.explain_aux(query, 0)
        if proof is None:
            return None
        else:
            return [proof]

    def policy(self):
        return self.delta_rules.policy()

    def get_arity_self(self, tablename):
        result = self.database.get_arity_self(tablename)
        if result:
            return result
        return self.delta_rules.get_arity_self(tablename)

    # Interface implementation

    def explain_aux(self, query, depth):
        self.log(query.table, "Explaining %s", query, depth=depth)
        # Bail out on negated literals.  Need different
        #   algorithm b/c we need to introduce quantifiers.
        if query.is_negated():
            return Proof(query, [])
        # grab first local proof, since they're all equally good
        localproofs = self.database.explain(query)
        if localproofs is None:
            return None
        if len(localproofs) == 0:   # base fact
            return Proof(query, [])
        localproof = localproofs[0]
        rule_instance = localproof.rule.plug(localproof.binding)
        subproofs = []
        for lit in rule_instance.body:
            subproof = self.explain_aux(lit, depth + 1)
            if subproof is None:
                return None
            subproofs.append(subproof)
        return Proof(query, subproofs)

    def modify(self, event):
        """Modifies contents of theory to insert/delete FORMULA.

        Returns True iff the theory changed.
        """
        self.log(None, "Materialized.modify")
        self.enqueue_any(event)
        changes = self.process_queue()
        self.log(event.formula.tablename(),
                 "modify returns %s", iterstr(changes))
        return changes

    def enqueue_any(self, event):
        """Enqueue event.

        Processing rules is a bit different than processing atoms
        in that they generate additional events that we want
        to process either before the rule is deleted or after
        it is inserted.  PROCESS_QUEUE is similar but assumes
        that only the data will cause propagations (and ignores
        included theories).
        """
        # Note: all included theories must define MODIFY
        formula = event.formula
        if formula.is_atom():
            self.log(formula.tablename(), "compute/enq: atom %s", formula)
            assert not self.is_view(formula.table), (
                "Cannot directly modify tables" +
                " computed from other tables")
            # self.log(formula.table, "%s: %s", text, formula)
            self.enqueue(event)
            return []
        else:
            # rules do not need to talk to included theories because they
            #   only generate events for views
            # need to eliminate self-joins here so that we fill all
            #   the tables introduced by self-join elimination.
            for rule in DeltaRuleTheory.eliminate_self_joins([formula]):
                new_event = Event(formula=rule, insert=event.insert,
                                  target=event.target)
                self.enqueue(new_event)
            return []

    def enqueue(self, event):
        self.log(event.tablename(), "Enqueueing: %s", event)
        self.queue.enqueue(event)

    def process_queue(self):
        """Data and rule propagation routine.

        Returns list of events that were not noops
        """
        self.log(None, "Processing queue")
        history = []
        while len(self.queue) > 0:
            event = self.queue.dequeue()
            self.log(event.tablename(), "Dequeued %s", event)
            if compile.is_regular_rule(event.formula):
                changes = self.delta_rules.modify(event)
                if len(changes) > 0:
                    history.extend(changes)
                    bindings = self.top_down_evaluation(
                        event.formula.variables(), event.formula.body)
                    self.log(event.formula.tablename(),
                             "new bindings after top-down: %s",
                             iterstr(bindings))
                    self.process_new_bindings(bindings, event.formula.head,
                                              event.insert, event.formula)
            else:
                self.propagate(event)
                history.extend(self.database.modify(event))
            self.log(event.tablename(), "History: %s", iterstr(history))
        return history

    def propagate(self, event):
        """Propagate event.

        Computes and enqueue events generated by EVENT and the DELTA_RULES.
        """
        self.log(event.formula.table, "Processing event: %s", event)
        applicable_rules = self.delta_rules.rules_with_trigger(
            event.formula.table)
        if len(applicable_rules) == 0:
            self.log(event.formula.table, "No applicable delta rule")
        for delta_rule in applicable_rules:
            self.propagate_rule(event, delta_rule)

    def propagate_rule(self, event, delta_rule):
        """Propagate event and delta_rule.

        Compute and enqueue new events generated by EVENT and DELTA_RULE.
        """
        self.log(event.formula.table, "Processing event %s with rule %s",
                 event, delta_rule)

        # compute tuples generated by event (either for insert or delete)
        # print "event: {}, event.tuple: {},
        #     event.tuple.rawtuple(): {}".format(
        #     str(event), str(event.tuple), str(event.tuple.raw_tuple()))
        # binding_list is dictionary

        # Save binding for delta_rule.trigger; throw away binding for event
        #   since event is ground.
        binding = self.new_bi_unifier()
        assert compile.is_literal(delta_rule.trigger)
        assert compile.is_literal(event.formula)
        undo = self.bi_unify(delta_rule.trigger, binding,
                             event.formula, self.new_bi_unifier())
        if undo is None:
            return
        self.log(event.formula.table,
                 "binding list for event and delta-rule trigger: %s", binding)
        bindings = self.top_down_evaluation(
            delta_rule.variables(), delta_rule.body, binding)
        self.log(event.formula.table, "new bindings after top-down: %s",
                 ",".join([str(x) for x in bindings]))

        if delta_rule.trigger.is_negated():
            insert_delete = not event.insert
        else:
            insert_delete = event.insert
        self.process_new_bindings(bindings, delta_rule.head,
                                  insert_delete, delta_rule.original)

    def process_new_bindings(self, bindings, atom, insert, original_rule):
        """Process new bindings.

        For each of BINDINGS, apply to ATOM, and enqueue it as an insert if
        INSERT is True and as a delete otherwise.
        """
        # for each binding, compute generated tuple and group bindings
        #    by the tuple they generated
        new_atoms = {}
        for binding in bindings:
            new_atom = atom.plug(binding)
            if new_atom not in new_atoms:
                new_atoms[new_atom] = []
            new_atoms[new_atom].append(Database.Proof(
                binding, original_rule))
        self.log(atom.table, "new tuples generated: %s", iterstr(new_atoms))

        # enqueue each distinct generated tuple, recording appropriate bindings
        for new_atom in new_atoms:
            # self.log(event.table, "new_tuple %s: %s", new_tuple,
            #          new_tuples[new_tuple])
            # Only enqueue if new data.
            # Putting the check here is necessary to support recursion.
            self.enqueue(Event(formula=new_atom,
                         proofs=new_atoms[new_atom],
                         insert=insert))

    def is_view(self, x):
        """Return True if the table X is defined by the theory."""
        return self.delta_rules.is_view(x)

    def is_known(self, x):
        """Return True if this theory has any rule mentioning table X."""
        return self.delta_rules.is_known(x)

    def base_tables(self):
        """Get base tables.

        Return the list of tables that are mentioned in the rules but
        for which there are no rules with those tables in the head.
        """
        return self.delta_rules.base_tables()

    def top_down_th(self, context, caller):
        return self.database.top_down_th(context, caller)

    def content(self, tablenames=None):
        return self.database.content(tablenames=tablenames)

    def update_dependency_graph(self):
        self.dependency_graph = compile.cross_theory_dependency_graph(
            self.policy(), theory=self.name)


##############################################################################
# Runtime
##############################################################################

class Runtime (object):
    """Runtime for the Congress policy language.

    Only have one instantiation in practice, but using a
    class is natural and useful for testing.
    """

    def __init__(self):
        # tracer object
        self.tracer = Tracer()
        # record execution
        self.logger = ExecutionLogger()
        # collection of theories
        self.theory = {}
        # collection of builtin theories
        self.builtin_policy_names = set()

    def create_policy(self, name, abbr=None, kind=None):
        """Create a new policy and add it to the runtime.

        ABBR is a shortened version of NAME that appears in
        traces.  KIND is the name of the datastructure used to
        represent a policy.
        """
        if not isinstance(name, basestring):
            raise KeyError("Policy name %s must be a string" % name)
        if name in self.theory:
            raise KeyError("Policy with name %s already exists" % name)
        if not isinstance(abbr, basestring):
            abbr = name[0:5]
        LOG.debug("Creating policy <%s> with abbr <%s> and kind <%s>",
                  name, abbr, kind)
        if kind is None:
            kind = NONRECURSIVE_POLICY_TYPE
        else:
            kind = kind.lower()
        if kind is None or kind == NONRECURSIVE_POLICY_TYPE:
            PolicyClass = NonrecursiveRuleTheory
        elif kind == ACTION_POLICY_TYPE:
            PolicyClass = ActionTheory
        elif kind == DATABASE_POLICY_TYPE:
            PolicyClass = Database
        elif kind == MATERIALIZED_POLICY_TYPE:
            PolicyClass = MaterializedViewTheory
        else:
            raise compile.CongressException(
                "Unknown kind of policy: %s" % kind)
        policy_obj = PolicyClass(name=name, abbr=abbr, theories=self.theory)
        policy_obj.set_tracer(self.tracer)
        self.theory[name] = policy_obj
        return policy_obj

    def delete_policy(self, name):
        """Deletes policy with name NAME or throws KeyError."""
        LOG.debug("Deleting policy named %s", name)
        try:
            del self.theory[name]
        except KeyError:
            raise KeyError("Policy with name %s does not exist" % name)

    def rename_policy(self, oldname, newname):
        """Renames policy OLDNAME to NEWNAME or raises KeyError."""
        if newname in self.theory:
            raise KeyError('Cannot rename %s to %s: %s already exists',
                           oldname, newname, newname)
        try:
            self.theory[newname] = self.theory[oldname]
            del self.theory[oldname]
        except KeyError:
            raise KeyError('Cannot rename %s to %s: %s does not exist',
                           oldname, newname, oldname)

    # TODO(thinrichs): make Runtime act like a dictionary so that we
    #   can iterate over policy names (keys), check if a policy exists, etc.
    def policy_exists(self, name):
        """Returns True iff policy called NAME exists."""
        return name in self.theory

    def policy_names(self):
        """Returns list of policy names."""
        return self.theory.keys()

    def policy_object(self, name):
        """Return policy by given name.  Raises KeyError if does not exist."""
        try:
            return self.theory[name]
        except KeyError:
            raise KeyError("Policy with name %s does not exist" % name)

    def policy_type(self, name):
        """Return type of policy NAME.  Throws KeyError if does not exist."""
        policy = self.policy_object(name)
        if isinstance(policy, NonrecursiveRuleTheory):
            return NONRECURSIVE_POLICY_TYPE
        if isinstance(policy, MaterializedViewTheory):
            return MATERIALIZED_POLICY_TYPE
        if isinstance(policy, ActionTheory):
            return ACTION_POLICY_TYPE
        if isinstance(policy, Database):
            return DATABASE_POLICY_TYPE
        raise compile.CongressException("Policy %s has unknown type" % name)

    def get_target(self, name):
        if name is None:
            if len(self.theory) == 1:
                name = self.theory.keys()[0]
            elif len(self.theory) == 0:
                raise compile.CongressException("No policies exist.")
            else:
                raise compile.CongressException(
                    "Must choose a policy to operate on")
        if name not in self.theory:
            raise compile.CongressException("Unknown policy " + str(name))
        return self.theory[name]

    def get_action_names(self, target):
        """Return a list of the names of action tables."""
        if target not in self.theory:
            return []
        actionth = self.theory[target]
        actions = actionth.select(self.parse1('action(x)'))
        return [action.arguments[0].name for action in actions]

    def table_log(self, table, msg, *args):
        self.tracer.log(table, "RT    : %s" % msg, *args)

    def set_tracer(self, tracer):
        if isinstance(tracer, Tracer):
            self.tracer = tracer
            for th in self.theory:
                self.theory[th].set_tracer(tracer)
        else:
            self.tracer = tracer[0]
            for th, tracr in tracer[1].items():
                if th in self.theory:
                    self.theory[th].set_tracer(tracr)

    def get_tracer(self):
        """Return (Runtime's tracer, dict of tracers for each theory).

        Useful so we can temporarily change tracing.
        """
        d = {}
        for th in self.theory:
            d[th] = self.theory[th].get_tracer()
        return (self.tracer, d)

    def debug_mode(self):
        tracer = Tracer()
        tracer.trace('*')
        self.set_tracer(tracer)

    def production_mode(self):
        tracer = Tracer()
        self.set_tracer(tracer)

    # External interface
    def dump_dir(self, path):
        """Dump each theory into its own file within the directory PATH.

        The name of the file is the name of the theory.
        """
        for name in self.theory:
            self.dump_file(os.path.join(path, name), name)

    def dump_file(self, filename, target):
        """Dump the contents of the theory called TARGET into file."""
        d = os.path.dirname(filename)
        if not os.path.exists(d):
            os.makedirs(d)
        with open(filename, "w") as f:
            f.write(str(self.theory[target]))

    def load_dir(self, path):
        """Load files in the directory PATH into its own theory.

        The theory is named the same as the filename.
        """
        permitted = True
        errors = []
        for file in os.listdir(path):
            perm, errs = self.load_file(os.path.join(path, file), target=file)
            if not perm:
                permitted = False
                errors.extend(errs)
        return (permitted, errors)

    def load_file(self, filename, target=None):
        """Load content from file.

        Compile the given FILENAME and insert each of the statements
        into the runtime.  Assumes that FILENAME includes no modals.
        """
        formulas = compile.parse_file(
            filename, theories=self.theory)
        try:
            self.policy_object(target)
        except KeyError:
            self.create_policy(target)
        return self.update(
            [Event(formula=x, insert=True) for x in formulas], target)

    def set_schema(self, name, schema, complete=False):
        """Set the schema for module NAME to be SCHEMA."""
        self.theory[name].schema = compile.Schema(schema, complete=complete)

    def select(self, query, target=None, trace=False):
        """Event handler for arbitrary queries.

        Returns the set of all instantiated QUERY that are true.
        """
        if isinstance(query, basestring):
            return self.select_string(query, self.get_target(target), trace)
        elif isinstance(query, tuple):
            return self.select_tuple(query, self.get_target(target), trace)
        else:
            return self.select_obj(query, self.get_target(target), trace)

    def initialize(self, tablenames, formulas, target=None):
        """Event handler for (re)initializing a collection of tables."""
        # translate FORMULAS into list of formula objects
        actual_formulas = []
        formula_tables = set()

        if isinstance(formulas, basestring):
            formulas = self.parse(formulas)

        for formula in formulas:
            if isinstance(formula, basestring):
                formula = self.parse1(formula)
            elif isinstance(formula, tuple):
                formula = compile.Literal.create_from_iter(formula)
            assert formula.is_atom()
            actual_formulas.append(formula)
            formula_tables.add(formula.table)

        tablenames = set(tablenames) | formula_tables
        self.table_log(None, "Initializing tables %s with %s",
                       iterstr(tablenames), iterstr(actual_formulas))
        # implement initialization by computing the requisite
        #   update.
        theory = self.get_target(target)
        old = set(theory.content(tablenames=tablenames))
        new = set(actual_formulas)
        to_add = new - old
        to_rem = old - new
        to_add = [Event(formula_) for formula_ in to_add]
        to_rem = [Event(formula_, insert=False) for formula_ in to_rem]
        self.table_log(None, "Initialize converted to update with %s and %s",
                       iterstr(to_add), iterstr(to_rem))
        return self.update(to_add + to_rem, target=target)

    def insert(self, formula, target=None):
        """Event handler for arbitrary insertion (rules and facts)."""
        if isinstance(formula, basestring):
            return self.insert_string(formula, self.get_target(target))
        elif isinstance(formula, tuple):
            return self.insert_tuple(formula, self.get_target(target))
        else:
            return self.insert_obj(formula, self.get_target(target))

    def delete(self, formula, target=None):
        """Event handler for arbitrary deletion (rules and facts)."""
        if isinstance(formula, basestring):
            return self.delete_string(formula, self.get_target(target))
        elif isinstance(formula, tuple):
            return self.delete_tuple(formula, self.get_target(target))
        else:
            return self.delete_obj(formula, self.get_target(target))

    def update(self, sequence, target=None):
        """Event handler for applying an arbitrary sequence of insert/deletes.

        If TARGET is supplied, it overrides the targets in SEQUENCE.
        """
        if target is not None:
            target = self.get_target(target)
            for event in sequence:
                event.target = target
        else:
            for event in sequence:
                event.target = self.get_target(event.target)
        if isinstance(sequence, basestring):
            return self.update_string(sequence)
        else:
            return self.update_obj(sequence)

    def policy(self, target=None):
        """Event handler for querying policy."""
        target = self.get_target(target)
        if target is None:
            return ""
        return " ".join(str(p) for p in target.policy())

    def content(self, target=None):
        """Event handler for querying content()."""
        target = self.get_target(target)
        if target is None:
            return ""
        return " ".join(str(p) for p in target.content())

    def simulate(self, query, theory, sequence, action_theory, delta=False,
                 trace=False):
        """Event handler for simulation.

        The computation of a query given an action sequence. That sequence
        can include updates to atoms, updates to rules, and action
        invocations.  Returns a collection of Literals (as a string if the
        query and sequence are strings or as a Python collection otherwise).
        If delta is True, the return is a collection of Literals where
        each tablename ends with either + or - to indicate whether
        that fact was added or deleted.
        Example atom update: q+(1) or q-(1)
        Example rule update: p+(x) :- q(x) or p-(x) :- q(x)
        Example action invocation:
           create_network(17), options:value(17, "name", "net1") :- true
        """
        assert self.get_target(theory) is not None, "Theory must be known"
        assert self.get_target(action_theory) is not None, (
            "Action theory must be known")
        if isinstance(query, basestring) and isinstance(sequence, basestring):
            return self.simulate_string(query, theory, sequence, action_theory,
                                        delta, trace)
        else:
            return self.simulate_obj(query, theory, sequence, action_theory,
                                     delta, trace)

    def tablenames(self):
        """Return tablenames occurring in some theory."""
        tables = set()
        for th in self.theory.values():
            tables |= set(th.tablenames())
        return tables

    def reserved_tablename(self, name):
        return name.startswith('___')

    # Internal interface
    # Translate different representations of formulas into
    #   the compiler's internal representation and then invoke
    #   appropriate theory's version of the API.

    # Arguments that are strings are suffixed with _string.
    # All other arguments are instances of Theory, Literal, etc.

    ###################################
    # Update policies and data.

    # insert: convenience wrapper around Update
    def insert_string(self, policy_string, theory):
        policy = self.parse(policy_string)
        return self.update_obj(
            [Event(formula=x, insert=True, target=theory) for x in policy])

    def insert_tuple(self, iter, theory):
        return self.insert_obj(compile.Literal.create_from_iter(iter), theory)

    def insert_obj(self, formula, theory):
        return self.update_obj([Event(formula=formula, insert=True,
                                      target=theory)])

    # delete: convenience wrapper around Update
    def delete_string(self, policy_string, theory):
        policy = self.parse(policy_string)
        return self.update_obj(
            [Event(formula=x, insert=False, target=theory) for x in policy])

    def delete_tuple(self, iter, theory):
        return self.delete_obj(compile.Literal.create_from_iter(iter), theory)

    def delete_obj(self, formula, theory):
        return self.update_obj([Event(formula=formula, insert=False,
                                      target=theory)])

    # update
    def update_string(self, events_string, theory):
        assert False, "Not yet implemented--need parser to read events"
        return self.update_obj(self.parse(events_string))

    def update_obj(self, events):
        """Do the updating.

        Checks if applying EVENTS is permitted and if not
        returns a list of errors.  If it is permitted, it
        applies it and then returns a list of changes.
        In both cases, the return is a 2-tuple (if-permitted, list).
        """
        self.table_log(None, "Updating with %s", iterstr(events))
        by_theory = self.group_events_by_target(events)
        # check that the updates would not cause an error
        errors = []
        for th, th_events in by_theory.items():
            errors.extend(th.update_would_cause_errors(th_events))
        if len(errors) > 0:
            return (False, errors)
        # actually apply the updates
        changes = []
        for th, th_events in by_theory.items():
            changes.extend(th.update(events))
        return (True, changes)

    def group_events_by_target(self, events):
        """Return mapping of targets and events.

        Return a dictionary mapping event.target to the list of events
        with that target.  Assumes each event.target is a Theory instance.
        Returns a dictionary from event.target.name to (event.target, <list )
        """
        by_target = {}
        for event in events:
            if event.target not in by_target:
                by_target[event.target] = [event]
            else:
                by_target[event.target].append(event)
        return by_target

    def reroute_events(self, events):
        """Events re-routing.

        Given list of events with different event.target values,
        change each event.target so that the events are routed to the
        proper place.
        """
        by_target = self.group_events_by_target(events)
        for target, target_events in by_target.items():
            newth = self.compute_route(target_events, target)
            for event in target_events:
                event.target = newth

    ##########################
    # Analyze (internal) state

    # select
    def select_string(self, policy_string, theory, trace):
        policy = self.parse(policy_string)
        assert (len(policy) == 1), (
            "Queries can have only 1 statement: {}".format(
                [str(x) for x in policy]))
        results = self.select_obj(policy[0], theory, trace)
        if trace:
            return (compile.formulas_to_string(results[0]), results[1])
        else:
            return compile.formulas_to_string(results)

    def select_tuple(self, tuple, theory, trace):
        return self.select_obj(compile.Literal.create_from_iter(tuple),
                               theory, trace)

    def select_obj(self, query, theory, trace):
        if trace:
            old_tracer = self.get_tracer()
            tracer = StringTracer()  # still LOG.debugs trace
            tracer.trace('*')     # trace everything
            self.set_tracer(tracer)
            value = theory.select(query)
            self.set_tracer(old_tracer)
            return (value, tracer.get_value())
        return theory.select(query)

    # simulate
    def simulate_string(self, query, theory, sequence, action_theory, delta,
                        trace):
        query = self.parse1(query)
        sequence = self.parse(sequence)
        result = self.simulate_obj(query, theory, sequence, action_theory,
                                   delta, trace)
        return compile.formulas_to_string(result)

    def simulate_obj(self, query, theory, sequence, action_theory, delta,
                     trace):
        """Simulate objects.

        Both THEORY and ACTION_THEORY are names of theories.
        Both QUERY and SEQUENCE are parsed.
        """
        assert compile.is_datalog(query), "Query must be formula"
        # Each action is represented as a rule with the actual action
        #    in the head and its supporting data (e.g. options) in the body
        assert all(compile.is_extended_datalog(x) for x in sequence), (
            "Sequence must be an iterable of Rules")
        th_object = self.get_target(theory)

        if trace:
            old_tracer = self.get_tracer()
            tracer = StringTracer()  # still LOG.debugs trace
            tracer.trace('*')     # trace everything
            self.set_tracer(tracer)

        # if computing delta, query the current state
        if delta:
            self.table_log(query.tablename(),
                           "** Simulate: Querying %s", query)
            oldresult = th_object.select(query)
            self.table_log(query.tablename(),
                           "Original result of %s is %s",
                           query, iterstr(oldresult))

        # apply SEQUENCE
        self.table_log(query.tablename(), "** Simulate: Applying sequence %s",
                       iterstr(sequence))
        undo = self.project(sequence, theory, action_theory)

        # query the resulting state
        self.table_log(query.tablename(), "** Simulate: Querying %s", query)
        result = th_object.select(query)
        self.table_log(query.tablename(), "Result of %s is %s", query,
                       iterstr(result))
        # rollback the changes
        self.table_log(query.tablename(), "** Simulate: Rolling back")
        self.project(undo, theory, action_theory)

        # if computing the delta, do it
        if delta:
            result = set(result)
            oldresult = set(oldresult)
            pos = result - oldresult
            neg = oldresult - result
            pos = [formula.make_update(is_insert=True) for formula in pos]
            neg = [formula.make_update(is_insert=False) for formula in neg]
            result = pos + neg
        if trace:
            self.set_tracer(old_tracer)
            return (result, tracer.get_value())
        return result

    # Helpers

    def react_to_changes(self, changes):
        """Filters changes and executes actions contained therein."""
        # LOG.debug("react to: %s", iterstr(changes))
        actions = self.get_action_names()
        formulas = [change.formula for change in changes
                    if (isinstance(change, Event)
                        and change.is_insert()
                        and change.formula.is_atom()
                        and change.tablename() in actions)]
        # LOG.debug("going to execute: %s", iterstr(formulas))
        self.execute(formulas)

    def data_listeners(self):
        return [self.theory[self.ENFORCEMENT_THEORY]]

    def compute_route(self, events, theory):
        """Compute rerouting.

        When a formula is inserted/deleted (in OPERATION) into a THEORY,
        it may need to be rerouted to another theory.  This function
        computes that rerouting.  Returns a Theory object.
        """
        self.table_log(None, "Computing route for theory %s and events %s",
                       theory.name, iterstr(events))
        # Since Enforcement includes Classify and Classify includes Database,
        #   any operation on data needs to be funneled into Enforcement.
        #   Enforcement pushes it down to the others and then
        #   reacts to the results.  That is, we really have one big theory
        #   Enforcement + Classify + Database as far as the data is concerned
        #   but formulas can be inserted/deleted into each policy individually.
        if all([compile.is_atom(event.formula) for event in events]):
            if (theory is self.theory[self.CLASSIFY_THEORY] or
                    theory is self.theory[self.DATABASE]):
                return self.theory[self.ENFORCEMENT_THEORY]
        return theory

    def project(self, sequence, policy_theory, action_theory):
        """Apply the list of updates SEQUENCE.

        Apply the list of updates SEQUENCE, where actions are described
        in ACTION_THEORY. Return an update sequence that will undo the
        projection.

        SEQUENCE can include atom insert/deletes, rule insert/deletes,
        and action invocations.  Projecting an action only
        simulates that action's invocation using the action's description;
        the results are therefore only an approximation of executing
        actions directly.  Elements of SEQUENCE are just formulas
        applied to the given THEORY.  They are NOT Event()s.

        SEQUENCE is really a program in a mini-programming
        language--enabling results of one action to be passed to another.
        Hence, even ignoring actions, this functionality cannot be achieved
        by simply inserting/deleting.
        """
        actth = self.theory[action_theory]
        policyth = self.theory[policy_theory]
        # apply changes to the state
        newth = NonrecursiveRuleTheory(abbr="Temp")
        newth.tracer.trace('*')
        actth.includes.append(newth)
        # TODO(thinrichs): turn 'includes' into an object that guarantees
        #   there are no cycles through inclusion.  Otherwise we get
        #   infinite loops
        if actth is not policyth:
            actth.includes.append(policyth)
        actions = self.get_action_names(action_theory)
        self.table_log(None, "Actions: %s", iterstr(actions))
        undos = []         # a list of updates that will undo SEQUENCE
        self.table_log(None, "Project: %s", sequence)
        last_results = []
        for formula in sequence:
            self.table_log(None, "** Updating with %s", formula)
            self.table_log(None, "Actions: %s", iterstr(actions))
            self.table_log(None, "Last_results: %s", iterstr(last_results))
            tablename = formula.tablename()
            if tablename not in actions:
                if not formula.is_update():
                    raise compile.CongressException(
                        "Sequence contained non-action, non-update: " +
                        str(formula))
                updates = [formula]
            else:
                self.table_log(tablename, "Projecting %s", formula)
                # define extension of current Actions theory
                if formula.is_atom():
                    assert formula.is_ground(), (
                        "Projection atomic updates must be ground")
                    assert not formula.is_negated(), (
                        "Projection atomic updates must be positive")
                    newth.define([formula])
                else:
                    # instantiate action using prior results
                    newth.define(last_results)
                    self.table_log(tablename, "newth (with prior results) %s",
                                   iterstr(newth.content()))
                    bindings = actth.top_down_evaluation(
                        formula.variables(), formula.body, find_all=False)
                    if len(bindings) == 0:
                        continue
                    grounds = formula.plug_heads(bindings[0])
                    grounds = [act for act in grounds if act.is_ground()]
                    assert all(not lit.is_negated() for lit in grounds)
                    newth.define(grounds)
                self.table_log(tablename,
                               "newth contents (after action insertion): %s",
                               iterstr(newth.content()))
                # self.table_log(tablename, "action contents: %s",
                #     iterstr(actth.content()))
                # self.table_log(tablename, "action.includes[1] contents: %s",
                #     iterstr(actth.includes[1].content()))
                # self.table_log(tablename, "newth contents: %s",
                #     iterstr(newth.content()))
                # compute updates caused by action
                updates = actth.consequences(compile.is_update)
                updates = self.resolve_conflicts(updates)
                updates = unify.skolemize(updates)
                self.table_log(tablename, "Computed updates: %s",
                               iterstr(updates))
                # compute results for next time
                for update in updates:
                    newth.insert(update)
                last_results = actth.consequences(compile.is_result)
                last_results = set([atom for atom in last_results
                                    if atom.is_ground()])
            # apply updates
            for update in updates:
                undo = self.project_updates(update, policy_theory)
                if undo is not None:
                    undos.append(undo)
        undos.reverse()
        if actth is not policyth:
            actth.includes.remove(policyth)
        actth.includes.remove(newth)
        return undos

    def project_updates(self, delta, theory):
        """Project atom/delta rule insertion/deletion.

        Takes an atom/rule DELTA with update head table
        (i.e. ending in + or -) and inserts/deletes, respectively,
        that atom/rule into THEORY after stripping
        the +/-. Returns None if DELTA had no effect on the
        current state.
        """
        theory = delta.theory_name() or theory

        self.table_log(None, "Applying update %s to %s", delta, theory)
        th_obj = self.theory[theory]
        insert = delta.tablename().endswith('+')
        newdelta = delta.drop_update().drop_theory()
        changed = th_obj.update([Event(formula=newdelta, insert=insert)])
        if changed:
            return delta.invert_update()
        else:
            return None

    def resolve_conflicts(self, atoms):
        """If p+(args) and p-(args) are present, removes the p-(args)."""
        neg = set()
        result = set()
        # split atoms into NEG and RESULT
        for atom in atoms:
            if atom.table.endswith('+'):
                result.add(atom)
            elif atom.table.endswith('-'):
                neg.add(atom)
            else:
                result.add(atom)
        # add elems from NEG only if their inverted version not in RESULT
        for atom in neg:
            if atom.invert_update() not in result:  # slow: copying ATOM here
                result.add(atom)
        return result

    def parse(self, string):
        return compile.parse(string, theories=self.theory)

    def parse1(self, string):
        return compile.parse1(string, theories=self.theory)


##############################################################################
# ExperimentalRuntime
##############################################################################

class ExperimentalRuntime (Runtime):
    def explain(self, query, tablenames=None, find_all=False, target=None):
        """Event handler for explanations.

        Given a ground query and a collection of tablenames
        that we want the explanation in terms of,
        return proof(s) that the query is true. If
        FIND_ALL is True, returns list; otherwise, returns single proof.
        """
        if isinstance(query, basestring):
            return self.explain_string(
                query, tablenames, find_all, self.get_target(target))
        elif isinstance(query, tuple):
            return self.explain_tuple(
                query, tablenames, find_all, self.get_target(target))
        else:
            return self.explain_obj(
                query, tablenames, find_all, self.get_target(target))

    def remediate(self, formula):
        """Event handler for remediation."""
        if isinstance(formula, basestring):
            return self.remediate_string(formula)
        elif isinstance(formula, tuple):
            return self.remediate_tuple(formula)
        else:
            return self.remediate_obj(formula)

    def execute(self, action_sequence):
        """Event handler for execute:

        Execute a sequence of ground actions in the real world.
        """
        if isinstance(action_sequence, basestring):
            return self.execute_string(action_sequence)
        else:
            return self.execute_obj(action_sequence)

    def access_control(self, action, support=''):
        """Event handler for making access_control request.

        ACTION is an atom describing a proposed action instance.
        SUPPORT is any data that should be assumed true when posing
        the query.  Returns True iff access is granted.
        """
        # parse
        if isinstance(action, basestring):
            action = self.parse1(action)
            assert compile.is_atom(action), "ACTION must be an atom"
        if isinstance(support, basestring):
            support = self.parse(support)
        # add support to theory
        newth = NonrecursiveRuleTheory(abbr="Temp")
        newth.tracer.trace('*')
        for form in support:
            newth.insert(form)
        acth = self.theory[self.ACCESSCONTROL_THEORY]
        acth.includes.append(newth)
        # check if action is true in theory
        result = len(acth.select(action, find_all=False)) > 0
        # allow new theory to be freed
        acth.includes.remove(newth)
        return result

    # explain
    def explain_string(self, query_string, tablenames, find_all, theory):
        policy = self.parse(query_string)
        assert len(policy) == 1, "Queries can have only 1 statement"
        results = self.explain_obj(policy[0], tablenames, find_all, theory)
        return compile.formulas_to_string(results)

    def explain_tuple(self, tuple, tablenames, find_all, theory):
        self.explain_obj(compile.Literal.create_from_iter(tuple),
                         tablenames, find_all, theory)

    def explain_obj(self, query, tablenames, find_all, theory):
        return theory.explain(query, tablenames, find_all)

    # remediate
    def remediate_string(self, policy_string):
        policy = self.parse(policy_string)
        assert len(policy) == 1, "Queries can have only 1 statement"
        return compile.formulas_to_string(self.remediate_obj(policy[0]))

    def remediate_tuple(self, tuple, theory):
        self.remediate_obj(compile.Literal.create_from_iter(tuple))

    def remediate_obj(self, formula):
        """Find a collection of action invocations

        That if executed result in FORMULA becoming false.
        """
        actionth = self.theory[self.ACTION_THEORY]
        classifyth = self.theory[self.CLASSIFY_THEORY]
        # look at FORMULA
        if compile.is_atom(formula):
            pass  # TODO(tim): clean up unused variable
            # output = formula
        elif compile.is_regular_rule(formula):
            pass  # TODO(tim): clean up unused variable
            # output = formula.head
        else:
            assert False, "Must be a formula"
        # grab a single proof of FORMULA in terms of the base tables
        base_tables = classifyth.base_tables()
        proofs = classifyth.explain(formula, base_tables, False)
        if proofs is None:  # FORMULA already false; nothing to be done
            return []
        # Extract base table literals that make that proof true.
        #   For remediation, we assume it suffices to make any of those false.
        #   (Leaves of proof may not be literals or may not be written in
        #    terms of base tables, despite us asking for base tables--
        #    because of negation.)
        leaves = [leaf for leaf in proofs[0].leaves()
                  if (compile.is_atom(leaf) and
                      leaf.table in base_tables)]
        self.table_log(None, "Leaves: %s", iterstr(leaves))
        # Query action theory for abductions of negated base tables
        actions = self.get_action_names()
        results = []
        for lit in leaves:
            goal = lit.make_positive()
            if lit.is_negated():
                goal.table = goal.table + "+"
            else:
                goal.table = goal.table + "-"
            # return is a list of goal :- act1, act2, ...
            # This is more informative than query :- act1, act2, ...
            for abduction in actionth.abduce(goal, actions, False):
                results.append(abduction)
        return results

    ##########################
    # Execute actions

    def execute_string(self, actions_string):
        self.execute_obj(self.parse(actions_string))

    def execute_obj(self, actions):
        """Executes the list of ACTION instances one at a time.

        For now, our execution is just logging.
        """
        LOG.debug("Executing: %s", iterstr(actions))
        assert all(compile.is_atom(action) and action.is_ground()
                   for action in actions)
        action_names = self.get_action_names()
        assert all(action.table in action_names for action in actions)
        for action in actions:
            if not action.is_ground():
                if self.logger is not None:
                    self.logger.warn("Unground action to execute: %s", action)
                continue
            if self.logger is not None:
                self.logger.info("%s", action)
