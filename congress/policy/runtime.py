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
from congress.policy.base import MATERIALIZED_POLICY_TYPE
from congress.policy.base import NONRECURSIVE_POLICY_TYPE
from congress.policy.base import StringTracer
from congress.policy.base import Tracer
from congress.policy import compile
from congress.policy.compile import Event
from congress.policy.database import Database
from congress.policy.materialized import MaterializedViewTheory
from congress.policy.nonrecursive import ActionTheory
from congress.policy.nonrecursive import NonrecursiveRuleTheory
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
        # dependency graph for all theories
        self.global_dependency_graph = (
            compile.RuleDependencyGraph())

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
            f.write(self.theory[target].content_string())

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
        actual_events = []
        for th, th_events in by_theory.items():
            errors.extend(th.update_would_cause_errors(th_events))
            actual_events.extend(th.actual_events(th_events))
        # update dependency graph (and undo it if errors)
        changes = self.global_dependency_graph.formula_update(events)
        if changes:
            if self.global_dependency_graph.has_cycle():
                # TODO(thinrichs): include path
                errors.append(compile.CongressException(
                    "Rules are recursive"))
                self.global_dependency_graph.undo_changes(changes)
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
