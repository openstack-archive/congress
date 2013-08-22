#! /usr/bin/python

import collections
import logging
import compile

class Tracer(object):
    def __init__(self):
        self.expressions = []
    def trace(self, table):
        self.expressions.append(table)
    def is_traced(self, table):
        return table in self.expressions or '*' in self.expressions
    def log(self, table, msg, depth=0):
        if self.is_traced(table):
            logging.debug("{}{}".format(("| " * depth), msg))


class CongressRuntime (Exception):
    pass

##############################################################################
## Delta Rules
##############################################################################

class DeltaRule(object):
    def __init__(self, trigger, head, body, original):
        self.trigger = trigger  # atom
        self.head = head  # atom
        self.body = body  # list of atoms with is_negated()
        self.original = original # Rule from which derived

    def __str__(self):
        return "<trigger: {}, head: {}, body: {}>".format(
            str(self.trigger), str(self.head), [str(lit) for lit in self.body])

    def __eq__(self, other):
        return (self.trigger == other.trigger and
                self.head == other.head and
                len(self.body) == len(other.body) and
                all(self.body[i] == other.body[i]
                        for i in xrange(0, len(self.body))))

class DeltaRuleTheory (object):
    """ A collection of DeltaRules. """
    def __init__(self, rules=None):
        # dictionary from table name to list of rules with that table as trigger
        self.contents = {}
        # dictionary from table name to number of rules with that table in head
        self.views = {}
        if rules is not None:
            for rule in rules:
                self.insert(rule)

    def modify(self, delta, is_insert):
        if is_insert is True:
            return self.insert(delta)
        else:
            return self.delete(delta)

    def insert(self, delta):
        if delta.head.table in self.views:
            self.views[delta.head.table] += 1
        else:
            self.views[delta.head.table] = 1

        if delta.trigger.table not in self.contents:
            self.contents[delta.trigger.table] = [delta]
        else:
            self.contents[delta.trigger.table].append(delta)

    def delete(self, delta):
        if delta.head.table in self.views:
            self.views[delta.head.table] -= 1
            if self.views[delta.head.table] == 0:
                del self.views[delta.head.table]
        if delta.trigger.table not in self.contents:
            return
        self.contents[delta.trigger.table].remove(delta)

    def __str__(self):
        return str(self.contents)

    def rules_with_trigger(self, table):
        if table not in self.contents:
            return []
        else:
            return self.contents[table]

    def is_view(self, x):
        return x in self.views

##############################################################################
## Events
##############################################################################

class EventQueue(object):
    def __init__(self):
        self.queue = collections.deque()

    def enqueue(self, event):
        # should eliminate duplicates (or refcount dups)
        self.queue.append(event)

    def dequeue(self):
        return self.queue.popleft()

    def __len__(self):
        return len(self.queue)

    def __str__(self):
        return "[" + ",".join([str(x) for x in self.queue]) + "]"

class Event(object):
    def __init__(self, table=None, tuple=None, insert=True, proofs=None):
        self.table = table
        self.tuple = Database.DBTuple(tuple, proofs=proofs)
        self.insert = insert
        logging.debug("EV: created event {}".format(str(self)))

    def is_insert(self):
        return self.insert

    def __str__(self):
        if self.is_insert():
            sign = '+'
        else:
            sign = '-'
        return "{}{}({})".format(self.table, sign, str(self.tuple))

##############################################################################
## Database
##############################################################################

class Database(object):
    class Proof(object):
        def __init__(self, binding, rule):
            self.binding = binding
            self.rule = rule

        def __str__(self):
            return "apply({}, {})".format(str(self.binding), str(self.rule))

        def __eq__(self, other):
            result = (self.binding == other.binding and
                      self.rule == other.rule)
            # logging.debug("Pf: Comparing {} and {}: {}".format(
            #     str(self), str(other), result))
            # logging.debug("Pf: {} == {} is {}".format(
            #     str(self.binding), str(other.binding), self.binding == other.binding))
            # logging.debug("Pf: {} == {} is {}".format(
            #     str(self.rule), str(other.rule), self.rule == other.rule))
            return result

    class ProofCollection(object):
        def __init__(self, proofs):
            self.contents = list(proofs)

        def __str__(self):
            return '{' + ",".join(str(x) for x in self.contents) + '}'

        def __isub__(self, other):
            if other is None:
                return
            # logging.debug("PC: Subtracting {} and {}".format(str(self), str(other)))
            remaining = []
            for proof in self.contents:
                if proof not in other.contents:
                    remaining.append(proof)
            self.contents = remaining
            return self

        def __ior__(self, other):
            if other is None:
                return
            # logging.debug("PC: Unioning {} and {}".format(str(self), str(other)))
            for proof in other.contents:
                # logging.debug("PC: Considering {}".format(str(proof)))
                if proof not in self.contents:
                    self.contents.append(proof)
            return self

        def __getitem__(self, key):
            return self.contents[key]

        def __len__(self):
            return len(self.contents)

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

        def match(self, atom, binding):
            logging.debug("Checking if tuple {} matches atom {} with binding {}".format(
                str(self), str(atom), str(binding)))
            if len(self.tuple) != len(atom.arguments):
                return None
            new_binding = {}
            for i in xrange(0, len(atom.arguments)):
                if atom.arguments[i].name in binding:
                    # check existing binding
                    if binding[atom.arguments[i].name] != self.tuple[i]:
                        return None
                else:
                    new_binding[atom.arguments[i].name] = self.tuple[i]
            logging.debug("Check succeeded with binding {}".format(str(new_binding)))
            return new_binding

    def __init__(self):
        self.data = {}
        self.tracer = Tracer()

    def __str__(self):
        def hash2str (h):
            s = "{"
            s += ", ".join(["{} : {}".format(str(key), str(h[key]))
                  for key in h])
            return s

        def hashlist2str (h):
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

    def __getitem__(self, key):
        # KEY must be a tablename
        return self.data[key]

    def table_names(self):
        return self.data.keys()

    def log(self, table, msg, depth=0):
        self.tracer.log(table, "DB: " + msg, depth)

    def select(self, atom):
        bindings = self.top_down_eval([atom], 0, {})
        result = []
        for binding in bindings:
            new_atom = [atom.table]
            new_atom.extend(plug(atom, binding))
            if new_atom not in result:
                result.append(new_atom)
        return result

    def explain(self, atom):
        if atom.table not in self.data or not atom.is_ground():
            return self.ProofCollection()
        args = tuple([x.name for x in atom.arguments])
        for dbtuple in self.data[atom.table]:
            if dbtuple.tuple == args:
                return dbtuple.proofs

    def top_down_eval(self, literals, literal_index, binding):
        """ Compute all instances of LITERALS (from LITERAL_INDEX and above) that
            are true in the Database (after applying the dictionary binding
            BINDING to LITERALS).  Returns a list of dictionary bindings. """
        if literal_index > len(literals) - 1:
            return [binding]
        lit = literals[literal_index]
        self.log(lit.table, ("Top_down_eval(literals={}, literal_index={}, "
                   "bindings={})").format(
                    "[" + ",".join(str(x) for x in literals) + "]",
                    literal_index,
                    str(binding)),
                   depth=literal_index)
        # assume that for negative literals, all vars are bound at this point
        # if there is a match, data_bindings will contain at least one binding
        #     (possibly including the empty binding)
        data_bindings = self.matches(lit, binding)
        self.log(lit.table, "data_bindings: " + str(data_bindings), depth=literal_index)
        # if not negated, empty data_bindings means failure
        if len(data_bindings) == 0 :
            return []

        results = []
        for data_binding in data_bindings:
            # add new binding to current binding
            binding.update(data_binding)
            if literal_index == len(literals) - 1:  # last element
                results.append(dict(binding))  # need to copy
            else:
                results.extend(self.top_down_eval(literals, literal_index + 1,
                    binding))
            # remove new binding from current bindings
            for var in data_binding:
                del binding[var]
        self.log(lit.table, "Top_down_eval return value: {}".format(
            '[' + ", ".join([str(x) for x in results]) + ']'), depth=literal_index)

        return results

    def matches(self, literal, binding):
        """ Returns a list of binding lists for the variables in LITERAL
            not bound in BINDING.  If LITERAL is negative, returns
            either [] meaning the lookup failed or [{}] meaning the lookup
            succeeded; otherwise, returns one binding list for each tuple in
            the database matching LITERAL under BINDING. """
        # slow--should stop at first match, not find all of them
        matches = self.matches_atom(literal, binding)
        if literal.is_negated():
            if len(matches) > 0:
                return []
            else:
                return [{}]
        else:
            return matches

    def matches_atom(self, atom, binding):
        """ Returns a list of binding lists for the variables in ATOM
            not bound in BINDING: one binding list for each tuple in
            the database matching ATOM under BINDING. """
        if atom.table not in self.data:
            return []
        result = []
        for tuple in self.data[atom.table]:
            logging.debug("Matching database tuple {}".format(str(tuple)))
            new_binding = tuple.match(atom, binding)
            if new_binding is not None:
                result.append(new_binding)
        return result

    def insert(self, table, dbtuple):
        if not isinstance(dbtuple, Database.DBTuple):
            dbtuple = Database.DBTuple(dbtuple)
        self.log(table, "Inserting table {} tuple {}".format(
            table, str(dbtuple)))
        if table not in self.data:
            self.data[table] = [dbtuple]
            # self.log(table, "First tuple in table {}".format(table))
        else:
            # self.log(table, "Not first tuple in table {}".format(table))
            for existingtuple in self.data[table]:
                assert(existingtuple.proofs is not None)
                if existingtuple.tuple == dbtuple.tuple:
                    # self.log(table, "Found existing tuple: {}".format(
                    #     str(existingtuple)))
                    assert(existingtuple.proofs is not None)
                    existingtuple.proofs |= dbtuple.proofs
                    # self.log(table, "Updated tuple: {}".format(str(existingtuple)))
                    assert(existingtuple.proofs is not None)
                    return
            self.data[table].append(dbtuple)


    def delete(self, table, dbtuple):
        if not isinstance(dbtuple, Database.DBTuple):
            dbtuple = Database.DBTuple(dbtuple)
        self.log(table, "Deleting table {} tuple {} from DB".format(
            table, str(dbtuple)))
        if table not in self.data:
            return
        for i in xrange(0, len(self.data[table])):
            existingtuple = self.data[table][i]
            self.log(table, "Checking tuple {}".format(str(existingtuple)))
            if existingtuple.tuple == dbtuple.tuple:
                existingtuple.proofs -= dbtuple.proofs
                if len(existingtuple.proofs) == 0:
                    del self.data[table][i]
                return

##############################################################################
## Runtime classes
##############################################################################

class Runtime (object):
    """ Runtime for the Congress policy language.  Only have one instantiation
        in practice, but using a class is natural and useful for testing. """

    class Proof(object):
        """ A single proof. Differs semantically from Database's
        Proof in that this verison represents a proof that spans rules,
        instead of just a proof for a single rule. """
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


    def __init__(self, rules=None):
        # rules dictating how an insert/delete to one table
        #   affects other tables
        self.delta_rules = DeltaRuleTheory(rules)
        # queue of events left to process
        self.queue = EventQueue()
        # collection of all tables
        self.database = Database()
        # tracer object
        self.tracer = Tracer()

    def log(self, table, msg, depth=0):
        self.tracer.log(table, "RT: " + msg, depth)

    ############### External interface ###############
    def load_file(self, filename):
        """ Compile the given FILENAME and insert each of the statements
            into the runtime. """
        compiler = compile.get_compiled([filename])
        for formula in compiler.theory:
            self.insert_obj(formula)

    def select(self, query):
        """ Event handler for arbitrary queries. Returns the set of
            all instantiated QUERY that are true. """
        if isinstance(query, basestring):
            return self.select_string(query)
        else:
            return self.select_obj(query)

    def select_if(self, query, temporary_data):
        """ Event handler for hypothetical queries.  Returns the set of
        all instantiated QUERYs that would be true IF
        TEMPORARY_DATA were true. """
        if isinstance(query, basestring):
            return self.select_if_string(query, temporary_data)
        else:
            return self.select_if_obj(query, temporary_data)

    def explain(self, query):
        """ Event handler for explanations.  Given a ground query, return
            a single proof that it belongs in the database. """
        if isinstance(query, basestring):
            return self.explain_string(query)
        else:
            return self.explain_obj(query)

    def insert(self, formula):
        """ Event handler for arbitrary insertion (rules and facts). """
        if isinstance(formula, basestring):
            return self.insert_string(formula)
        else:
            return self.insert_obj(formula)

    def delete(self, formula):
        """ Event handler for arbitrary deletion (rules and facts). """
        if isinstance(formula, basestring):
            return self.delete_string(formula)
        else:
            return self.delete_obj(formula)

    ############### External typed interface ###############

    def select_obj(self, query):
        # should generalize to at least a (conjunction of atoms)
        #   Need to change compiler a bit, but runtime should be fine.
        assert isinstance(query, compile.Atom), "Only have support for atomic queries"
        return self.database.select(query)

    def select_string(self, policy_string):
        def str_tuple_atom (atom):
            s = atom[0]
            s += '('
            s += ', '.join([str(x) for x in atom[1:]])
            s += ')'
            return s
        c = compile.get_compiled(['--input_string', policy_string])
        assert len(c.theory) == 1, "Queries can have only 1 statement: {}".format(
            [str(x) for x in c.theory])
        assert c.theory[0].is_atom(), "Queries must be atomic"
        results = self.select_obj(c.theory[0])
        return " ".join([str_tuple_atom(x) for x in results])

    def select_if_obj(self, query, temporary_data):
        assert False, "Not yet implemented"

    def select_if_string(self, query_string, temporary_data):
        assert False, "Not yet implemented"

    def explain_obj(self, query):
        assert isinstance(query, compile.Atom), "Only have support for literals"
        return self.explain_aux(query, 0)

    def explain_string(self, query_string):
        c = compile.get_compiled([query_string, '--input_string'])
        assert len(c.theory) == 1, "Queries can have only 1 statement"
        assert c.theory[0].is_atom(), "Queries must be atomic"
        results = self.explain_obj(c.theory[0])
        return str(results)

    def insert_obj(self, formula):
        return self.modify(formula, is_insert=True)

    def insert_string(self, policy_string):
        c = compile.get_compiled([policy_string, '--input_string'])
        for formula in c.theory:
            logging.debug("Parsed {}".format(str(formula)))
            self.insert_obj(formula)

    def delete_obj(self, formula):
        return self.modify(formula, is_insert=False)

    def delete_string(self, policy_string):
        c = compile.get_compiled([policy_string, '--input_string'])
        for formula in c.theory:
            self.delete_obj(formula)

    ############### Interface implementation ###############

    def explain_aux(self, query, depth):
        self.log(query.table, "Explaining {}".format(str(query)), depth)
        if query.is_negated():
            return self.Proof(query, [])
        # grab first local proof, since they're all equally good
        localproofs = self.database.explain(query)
        if len(localproofs) == 0:   # base fact
            return self.Proof(query, [])
        localproof = localproofs[0]
        rule_instance = localproof.rule.plug(localproof.binding)
        subproofs = []
        for lit in rule_instance.body:
            subproof = self.explain_aux(lit, depth + 1)
            if subproof is None:
                return None
            subproofs.append(subproof)
        return self.Proof(query, subproofs)

    def modify(self, formula, is_insert=True):
        """ Event handler for arbitrary insertion/deletion (rules and facts). """
        if formula.is_atom():
            if self.delta_rules.is_view(formula.table):
                return self.view_update_options(formula)
            else:
                args = tuple([arg.name for arg in formula.arguments])
                self.modify_tuple(formula.table, args, is_insert=is_insert)
                return None
        else:
            self.modify_rule(formula, is_insert=is_insert)
            for delta_rule in compile.compute_delta_rules([formula]):
                self.delta_rules.modify(delta_rule, is_insert=is_insert)
            return None

    def modify_rule(self, rule, is_insert):
        """ Add rule (not a DeltaRule) to collection and update
            tables as appropriate. """
        # don't have separate queue since inserting/deleting a rule doesn't generate any
        #   new rule insertion/deletion events
        bindings = self.database.top_down_eval(rule.body, 0, {})
        self.log(None, "new bindings after top-down: {}".format(
            ",".join([str(x) for x in bindings])))
        self.process_new_bindings(bindings, rule.head, is_insert, rule)
        self.process_queue()

    def modify_tuple(self, table, row, is_insert):
        """ Event handler for a tuple insertion/deletion.
        TABLE is the name of a table (a string).
        TUPLE is a Python tuple.
        IS_INSERT is True or False."""
        if is_insert:
            text = "Inserting into queue"
        else:
            text = "Deleting from queue"
        self.log(table, "{}: table {} with tuple {}".format(
            text, table, str(row)))
        if not isinstance(row, Database.DBTuple):
            row = Database.DBTuple(row)
        self.log(table, "{}: table {} with tuple {}".format(
            text, table, str(row)))
        self.queue.enqueue(Event(table, row, insert=is_insert))
        self.process_queue()

    ############### Data manipulation ###############

    def process_queue(self):
        """ Toplevel data evaluation routine. """
        while len(self.queue) > 0:
            event = self.queue.dequeue()
            if event.is_insert():
                self.propagate(event)
                self.database.insert(event.table, event.tuple)
            else:
                self.propagate(event)
                self.database.delete(event.table, event.tuple)

    def propagate(self, event):
        """ Computes events generated by EVENT and the DELTA_RULES,
            and enqueues them. """
        self.log(event.table, "Processing event: {}".format(str(event)))
        applicable_rules = self.delta_rules.rules_with_trigger(event.table)
        if len(applicable_rules) == 0:
            self.log(event.table, "No applicable delta rule")
        for delta_rule in applicable_rules:
            self.propagate_rule(event, delta_rule)

    def propagate_rule(self, event, delta_rule):
        """ Compute and enqueue new events generated by EVENT and DELTA_RULE. """
        self.log(event.table, "Processing event {} with rule {}".format(
            str(event), str(delta_rule)))

        # compute tuples generated by event (either for insert or delete)
        # print "event: {}, event.tuple: {}, event.tuple.rawtuple(): {}".format(
        #     str(event), str(event.tuple), str(event.tuple.raw_tuple()))
        binding_list = match(event.tuple, delta_rule.trigger)
        if binding_list is None:
            return
        self.log(event.table,
            "binding_list for event-tuple and delta_rule trigger: {}".format(
                str(binding_list)))
        new_bindings = self.database.top_down_eval(delta_rule.body, 0, binding_list)
        self.log(event.table, "new bindings after top-down: {}".format(
            ",".join([str(x) for x in new_bindings])))

        if delta_rule.trigger.is_negated():
            insert_delete = not event.insert
        else:
            insert_delete = event.insert
        self.process_new_bindings(new_bindings, delta_rule.head, insert_delete,
            delta_rule.original)

    def process_new_bindings(self, bindings, atom, insert, original_rule):
        """ For each of BINDINGS, apply to ATOM, and enqueue it as an insert if
            INSERT is True and as a delete otherwise. """
        # for each binding, compute generated tuple and group bindings
        #    by the tuple they generated
        new_tuples = {}
        for binding in bindings:
            new_tuple = tuple(plug(atom, binding))
            if new_tuple not in new_tuples:
                new_tuples[new_tuple] = []
            new_tuples[new_tuple].append(Database.Proof(
                binding, original_rule))
        self.log(atom.table, "new tuples generated: {}".format(
            ", ".join([str(x) for x in new_tuples])))

        # enqueue each distinct generated tuple, recording appropriate bindings
        for new_tuple in new_tuples:
            # self.log(event.table,
            #     "new_tuple {}: {}".format(str(new_tuple), str(new_tuples[new_tuple])))
            self.queue.enqueue(Event(table=atom.table,
                                     tuple=new_tuple,
                                     proofs=new_tuples[new_tuple],
                                     insert=insert))

    ############### View updates ###############
    def view_update_options(self):
        return [None]


def plug(atom, binding, withtable=False):
    """ Returns a tuple representing the arguments to ATOM after having
        applied BINDING to the variables in ATOM. """
    if withtable is True:
        result = [atom.table]
    else:
        result = []
    for i in xrange(0, len(atom.arguments)):
        if atom.arguments[i].is_variable() and atom.arguments[i].name in binding:
            result.append(binding[atom.arguments[i].name])
        else:
            result.append(atom.arguments[i].name)
    return tuple(result)

def match(tuple, atom):
    """ Returns a binding dictionary that when applied to ATOM's arguments
        gives exactly TUPLE, or returns None if no such binding exists. """
    if len(tuple) != len(atom.arguments):
        return None
    binding = {}
    for i in xrange(0, len(tuple)):
        arg = atom.arguments[i]
        if arg.is_variable():
            if arg.name in binding:
                oldval = binding[arg.name]
                if oldval != tuple[i]:
                    return None
            else:
                binding[arg.name] = tuple[i]
    return binding


