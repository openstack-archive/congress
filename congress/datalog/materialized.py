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

from oslo_log import log as logging
from six.moves import range

from congress.datalog import base
from congress.datalog import compile
from congress.datalog import database
from congress.datalog import topdown
from congress.datalog import utility


LOG = logging.getLogger(__name__)


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
                    for i in range(0, len(self.body))))

    def __hash__(self):
        return hash((self.trigger, self.head, tuple(self.body)))

    def variables(self):
        """Return the set of variables occurring in this delta rule."""
        vs = self.trigger.variables()
        vs |= self.head.variables()
        for atom in self.body:
            vs |= atom.variables()
        return vs

    def tablenames(self, body_only=False, include_builtin=False,
                   include_modal=True):
        """Return the set of tablenames occurring in this delta rule."""
        tables = set()
        if not body_only:
            tables.add(self.head.tablename())
        tables.add(self.trigger.tablename())
        for atom in self.body:
            tables.add(atom.tablename())
        return tables


class DeltaRuleTheory (base.Theory):
    """A collection of DeltaRules.  Not useful by itself as a policy."""
    def __init__(self, name=None, abbr=None, theories=None):
        super(DeltaRuleTheory, self).__init__(
            name=name, abbr=abbr, theories=theories)
        # dictionary from table name to list of rules with that table as
        # trigger
        self.rules = {}
        # dictionary from delta_rule to the rule from which it was derived
        self.originals = set()
        # dictionary from table name to number of rules with that table in
        # head
        self.views = {}
        # all tables
        self.all_tables = {}
        self.kind = base.DELTA_POLICY_TYPE

    def modify(self, event):
        """Insert/delete the compile.Rule RULE into the theory.

        Return list of changes (either the empty list or
        a list including just RULE).
        """
        self.log(None, "DeltaRuleTheory.modify %s", event.formula)
        self.log(None, "originals: %s", utility.iterstr(self.originals))
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
            self.log(None, utility.iterstr(self.originals))
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
        if delta.head.table.table in self.views:
            self.views[delta.head.table.table] += 1
        else:
            self.views[delta.head.table.table] = 1

        # tables
        for table in delta.tablenames():
            if table in self.all_tables:
                self.all_tables[table] += 1
            else:
                self.all_tables[table] = 1

        # contents
        # TODO(thinrichs): eliminate dups, maybe including
        #     case where bodies are reorderings of each other
        if delta.trigger.table.table not in self.rules:
            self.rules[delta.trigger.table.table] = utility.OrderedSet()
        self.rules[delta.trigger.table.table].add(delta)

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
        if delta.head.table.table in self.views:
            self.views[delta.head.table.table] -= 1
            if self.views[delta.head.table.table] == 0:
                del self.views[delta.head.table.table]

        # tables
        for table in delta.tablenames():
            if table in self.all_tables:
                self.all_tables[table] -= 1
                if self.all_tables[table] == 0:
                    del self.all_tables[table]

        # contents
        self.rules[delta.trigger.table.table].discard(delta)
        if not len(self.rules[delta.trigger.table.table]):
            del self.rules[delta.trigger.table.table]

    def policy(self):
        return self.originals

    def get_arity_self(self, tablename):
        for p in self.originals:
            if p.head.table.table == tablename:
                return len(p.head.arguments)
        return None

    def __contains__(self, formula):
        return formula in self.originals

    def __str__(self):
        return str(self.rules)

    def rules_with_trigger(self, table):
        """Return the list of DeltaRules that trigger on the given TABLE."""
        if table in self.rules:
            return self.rules[table]
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
            for i in range(0, n):
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
                    atom.table.table = new_table_name(table, arity,
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
            for i in range(1, global_self_joins[tablearity] + 1):
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
                if literal.is_builtin():
                    continue
                newbody = [lit for lit in rule.body if lit is not literal]
                delta_rules.append(
                    DeltaRule(literal, rule.head, newbody, rule))
        return delta_rules


class MaterializedViewTheory(topdown.TopDownTheory):
    """A theory that stores the table contents of views explicitly.

    Relies on included theories to define the contents of those
    tables not defined by the rules of the theory.
    Recursive rules are allowed.
    """

    def __init__(self, name=None, abbr=None, theories=None, schema=None,
                 desc=None, owner=None):
        super(MaterializedViewTheory, self).__init__(
            name=name, abbr=abbr, theories=theories, schema=schema,
            desc=desc, owner=owner)
        # queue of events left to process
        self.queue = base.EventQueue()
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
        self.database = database.Database(name=db_name, abbr=db_abbr)
        # rules that dictate how database changes in response to events
        self.delta_rules = DeltaRuleTheory(name=delta_name, abbr=delta_abbr)
        self.kind = base.MATERIALIZED_POLICY_TYPE

    def set_tracer(self, tracer):
        if isinstance(tracer, base.Tracer):
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
        return self.update([compile.Event(formula=formula, insert=True)])

    def delete(self, formula):
        return self.update([compile.Event(formula=formula, insert=False)])

    def update(self, events):
        """Apply inserts/deletes described by EVENTS and return changes.

           Does not check if EVENTS would cause errors.
           """
        for event in events:
            assert compile.is_datalog(event.formula), (
                "Non-formula not allowed: {}".format(str(event.formula)))
            self.enqueue_any(event)
        changes = self.process_queue()
        return changes

    def update_would_cause_errors(self, events):
        """Return a list of PolicyException.

        Return a list of PolicyException if we were
        to apply the events EVENTS to the current policy.
        """
        self.log(None, "update_would_cause_errors %s", utility.iterstr(events))
        errors = []
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
        self.log(query.table.table, "Explaining %s", query, depth=depth)
        # Bail out on negated literals.  Need different
        #   algorithm b/c we need to introduce quantifiers.
        if query.is_negated():
            return base.Proof(query, [])
        # grab first local proof, since they're all equally good
        localproofs = self.database.explain(query)
        if localproofs is None:
            return None
        if len(localproofs) == 0:   # base fact
            return base.Proof(query, [])
        localproof = localproofs[0]
        rule_instance = localproof.rule.plug(localproof.binding)
        subproofs = []
        for lit in rule_instance.body:
            subproof = self.explain_aux(lit, depth + 1)
            if subproof is None:
                return None
            subproofs.append(subproof)
        return base.Proof(query, subproofs)

    def modify(self, event):
        """Modifies contents of theory to insert/delete FORMULA.

        Returns True iff the theory changed.
        """
        self.log(None, "Materialized.modify")
        self.enqueue_any(event)
        changes = self.process_queue()
        self.log(event.formula.tablename(),
                 "modify returns %s", utility.iterstr(changes))
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
            assert not self.is_view(formula.table.table), (
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
                new_event = compile.Event(formula=rule, insert=event.insert,
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
                             utility.iterstr(bindings))
                    self.process_new_bindings(bindings, event.formula.head,
                                              event.insert, event.formula)
            else:
                self.propagate(event)
                history.extend(self.database.modify(event))
            self.log(event.tablename(), "History: %s",
                     utility.iterstr(history))
        return history

    def propagate(self, event):
        """Propagate event.

        Computes and enqueue events generated by EVENT and the DELTA_RULES.
        """
        self.log(event.formula.table.table, "Processing event: %s", event)
        applicable_rules = self.delta_rules.rules_with_trigger(
            event.formula.table.table)
        if len(applicable_rules) == 0:
            self.log(event.formula.table.table, "No applicable delta rule")
        for delta_rule in applicable_rules:
            self.propagate_rule(event, delta_rule)

    def propagate_rule(self, event, delta_rule):
        """Propagate event and delta_rule.

        Compute and enqueue new events generated by EVENT and DELTA_RULE.
        """
        self.log(event.formula.table.table, "Processing event %s with rule %s",
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
                             event.formula, self.new_bi_unifier(), self.name)
        if undo is None:
            return
        self.log(event.formula.table.table,
                 "binding list for event and delta-rule trigger: %s", binding)
        bindings = self.top_down_evaluation(
            delta_rule.variables(), delta_rule.body, binding)
        self.log(event.formula.table.table, "new bindings after top-down: %s",
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
            new_atoms[new_atom].append(database.Database.Proof(
                binding, original_rule))
        self.log(atom.table.table, "new tuples generated: %s",
                 utility.iterstr(new_atoms))

        # enqueue each distinct generated tuple, recording appropriate bindings
        for new_atom in new_atoms:
            # self.log(event.table, "new_tuple %s: %s", new_tuple,
            #          new_tuples[new_tuple])
            # Only enqueue if new data.
            # Putting the check here is necessary to support recursion.
            self.enqueue(compile.Event(formula=new_atom,
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

    def _top_down_th(self, context, caller):
        return self.database._top_down_th(context, caller)

    def content(self, tablenames=None):
        return self.database.content(tablenames=tablenames)

    def __contains__(self, formula):
        # TODO(thinrichs): if formula is a rule, we need to check
        #   self.delta_rules; if formula is an atom, we need to check
        #   self.database, but only if the table for that atom is
        #   not defined by rules.  As it stands, for atoms, we are
        #   conflating membership with evaluation.
        return (formula in self.database or formula in self.delta_rules)
