#! /usr/bin/python

import collections
import logging

class Tracer(object):
    def __init__(self):
        self.expressions = []
    def trace(self, table):
        self.expressions.append(table)
    def is_traced(self, table):
        return table in self.expressions or '*' in self.expressions

class CongressRuntime (Exception):
    pass

class DeltaRule(object):
    def __init__(self, trigger, head, body):
        self.trigger = trigger  # atom
        self.head = head  # atom
        self.body = body  # list of atoms with is_negated()

    def __str__(self):
        return "<trigger: {}, head: {}, body: {}>".format(
            str(self.trigger), str(self.head), [str(lit) for lit in self.body])

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

    def is_insert(self):
        return self.insert

    def __str__(self):
        if self.is_insert():
            sign = '+'
        else:
            sign = '-'
        return "{}{}({})".format(self.table, sign, str(self.tuple))

# class Database(object):
#     class DictTuple(object):
#         def __init__(self, binding, refcount=1):
#             self.binding = binding
#             self.refcount = refcount

#         def __eq__(self, other):
#             return self.binding == other.binding

#         def __str__(self):
#             return "<binding: {}, refcount: {}>".format(
#                 str(self.binding), self.refcount)

#         def matches(self, binding):
#             print "Checking if tuple {} matches binding {}".format(str(self), str(binding))
#             for column_name in self.binding.keys():
#                 if column_name not in binding:
#                     return False
#                 if self.binding[column_name] != binding[column_name]:
#                     return False
#             print "Check succeeded with binding {}".format(str(binding))
#             return True

#     class Schema (object):
#         def __init__(self, column_names):
#             self.arguments = column_names
#         def __str__(self):
#             return str(self.arguments)

#     def __init__(self):
#         self.data = {'p': [], 'q': [], 'r': [self.DictTuple({1: 1})]}
#         # self.data = {'p': [self.DictTuple({1: 'a'}),
#         #                    self.DictTuple({1: 'b'}),
#         #                    self.DictTuple({1, 'c'})],
#         #              'q': [self.DictTuple({1: 'b'}),
#         #                    self.DictTuple({1: 'c'}),
#         #                    self.DictTuple({1, 'd'})],
#         #              'r': [self.DictTuple({1: 'c'}),
#         #                    self.DictTuple({1: 'd'}),
#         #                    self.DictTuple({1, 'e'})]
#         #              }
#         self.schemas = {'p': Database.Schema([1]),
#                         'q': Database.Schema([1]),
#                         'r': Database.Schema([1])}

#     def __str__(self):
#         def hash2str (h):
#             s = "{"
#             s += ", ".join(["{} : {}".format(str(key), str(h[key]))
#                   for key in h])
#             return s

#         def hashlist2str (h):
#             strings = []
#             for key in h:
#                 s = "{} : ".format(key)
#                 s += '['
#                 s += ', '.join([str(val) for val in h[key]])
#                 s += ']'
#                 strings.append(s)
#             return '{' + ", ".join(strings) + '}'

#         return "<data: {}, \nschemas: {}>".format(
#             hashlist2str(self.data), hash2str(self.schemas))

#     def get_matches(self, table, binding, columns=None):
#         print "Getting matches for table {} with binding {}".format(
#             str(table), str(binding))
#         if table not in self.data:
#             raise CongressRuntime("Table not found ".format(table))
#         result = []
#         for dicttuple in self.data[table]:
#             print "Matching database tuple {}".format(str(dicttuple))
#             if dicttuple.matches(binding):
#                 result.append(dicttuple)
#         return result

#     def insert(self, table, binding, refcount=1):
#         if table not in self.data:
#             raise CongressRuntime("Table not found ".format(table))
#         for dicttuple in self.data[table]:
#             if dicttuple.binding == binding:
#                 dicttuple.refcount += refcount
#                 return
#         self.data[table].append(self.DictTuple(binding, refcount))

#     def delete(self, table, binding, refcount=1):
#         if table not in self.data:
#             raise CongressRuntime("Table not found ".format(table))
#         for dicttuple in self.data[table]:
#             if dicttuple.binding == binding:
#                 dicttuple.refcount -= refcount
#                 if dicttuple.refcount < 0:
#                     raise CongressRuntime("Deleted more tuples than existed")
#                 return
#         raise CongressRuntime("Deleted tuple that didn't exist")


class Database(object):
    class ProofCollection(object):
        def __init__(self, proofs):
            self.contents = list(proofs)

        def __str__(self):
            return '{' + ",".join(str(x) for x in self.contents) + '}'

        def __isub__(self, other):
            if other is None:
                return
            remaining = []
            for proof in self.contents:
                if proof not in other.contents:
                    remaining.append(proof)
            self.contents = remaining
            return self

        def __ior__(self, other):
            if other is None:
                return
            for proof in other.contents:
                if proof not in self.contents:
                    self.contents.append(proof)
            return self

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

    class Schema (object):
        def __init__(self, column_names):
            self.arguments = column_names
        def __str__(self):
            return str(self.arguments)

    def __init__(self):
        self.data = {}
        self.schemas = {}  # not currently used
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
        # return "<data: {}, \nschemas: {}>".format(
        #     hashlist2str(self.data), hash2str(self.schemas))

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

    def log(self, table, msg):
        if self.tracer.is_traced(table):
            logging.debug(msg)

    def get_matches(self, atom, binding):
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
        self.log(table, "Inserting table {} tuple {} into DB".format(
            table, str(dbtuple)))
        if table not in self.data:
            self.data[table] = [dbtuple]
        else:
            for existingtuple in self.data[table]:
                assert(existingtuple.proofs is not None)
                if existingtuple.tuple == dbtuple.tuple:
                    assert(existingtuple.proofs is not None)
                    existingtuple.proofs |= dbtuple.proofs
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

class Runtime (object):
    """ Runtime for the Congress policy language.  Only have one instantiation
        in practice, but using a class is natural and useful for testing. """

    def __init__(self, rules):
        # rules dictating how an insert/delete to one table
        #   effects other tables
        self.delta_rules = index_delta_rules(rules)
        # queue of events left to process
        self.queue = EventQueue()
        # collection of all tables
        self.database = Database()
        # tracer object
        self.tracer = Tracer()

    def log(self, table, msg):
        if self.tracer.is_traced(table):
            logging.debug(msg)

    def insert(self, table, tuple):
        """ Event handler for an insertion.
        TABLE is the name of a table (a string).
        TUPLE is a Python tuple. """
        if not isinstance(tuple, Database.DBTuple):
            tuple = Database.DBTuple(tuple)
        self.log(table, "Inserting into queue: {} with {}".format(
            table, str(tuple)))
        self.queue.enqueue(Event(table, tuple, insert=True))
        self.process_queue()  # should be running in separate daemon

    def delete(self, table, tuple):
        """ Event handler for a deletion. TUPLE is a Python tuple.
        TABLE is the name of a table (a string).
        TUPLE is a Python tuple. """
        if not isinstance(tuple, Database.DBTuple):
            tuple = Database.DBTuple(tuple)
        self.log(table, "Deleting from queue: {} with {}".format(
            table, str(tuple)))
        self.queue.enqueue(Event(table, tuple, insert=False))
        self.process_queue()   # should be running in separate daemon

    def process_queue(self):
        """ Toplevel evaluation routine. """
        while len(self.queue) > 0:
            event = self.queue.dequeue()
            # Note differing order of insert/delete into database.
            # Insert happens before propagation; Delete happens after propagation.
            # Necessary for correctness on self-joins.
            if event.is_insert():
                self.database.insert(event.table, event.tuple)
                self.propagate(event)
            else:
                self.propagate(event)
                self.database.delete(event.table, event.tuple)

    def propagate(self, event):
        """ Computes events generated by EVENT and the DELTA_RULES,
            and enqueues them. """
        self.log(event.table, "Processing event: {}".format(str(event)))
        if event.table not in self.delta_rules.keys():
            self.log(event.table, "No applicable delta rule")
            return
        for delta_rule in self.delta_rules[event.table]:
            self.propagate_rule(event, delta_rule)

    def propagate_rule(self, event, delta_rule):
        """ Compute and enqueue new events generated by EVENT and DELTA_RULE. """
        assert(not delta_rule.trigger.is_negated())
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
        new_bindings = self.top_down_eval(delta_rule.body, 0, binding_list)
        self.log(event.table, "new bindings after top-down: {}".format(
            ",".join([str(x) for x in new_bindings])))

        # for each binding, compute generated tuple and group bindings
        #    by the tuple they generated
        new_tuples = {}
        for new_binding in new_bindings:
            new_tuple = tuple(plug(delta_rule.head, new_binding))
            if new_tuple not in new_tuples:
                new_tuples[new_tuple] = []
            new_tuples[new_tuple].append(new_binding)
        self.log(event.table, "new tuples generated: {}".format(
            str(new_tuples)))

        # enqueue each distinct generated tuple, recording appropriate bindings
        head_table = delta_rule.head.table
        for new_tuple in new_tuples:
            # self.log(event.table,
            #     "new_tuple {}: {}".format(str(new_tuple), str(new_tuples[new_tuple])))
            self.queue.enqueue(Event(table=head_table,
                                     tuple=new_tuple,
                                     proofs=new_tuples[new_tuple],
                                     insert=event.insert))

    def top_down_eval(self, atoms, atom_index, binding):
        """ Compute all instances of ATOMS (from ATOM_INDEX and above) that
            are true in the Database (after applying the dictionary binding
            BINDING to ATOMs).  Returns a list of dictionary bindings. """
        if atom_index > len(atoms) - 1:
            return [binding]
        atom = atoms[atom_index]
        self.log(atom.table, ("Top_down_eval(atoms={}, atom_index={}, "
                   "bindings={})").format(
                    "[" + ",".join(str(x) for x in atoms) + "]",
                    atom_index,
                    str(binding)))
        data_bindings = self.database.get_matches(atom, binding)
        self.log(atom.table, "data_bindings: " + str(data_bindings))
        if len(data_bindings) == 0:
            return []
        results = []
        for data_binding in data_bindings:
            # add new binding to current binding
            binding.update(data_binding)
            if atom_index == len(atoms) - 1:  # last element in atoms
                results.append(dict(binding))  # need to copy
            else:
                results.extend(self.top_down_eval(atoms, atom_index + 1, binding))
            # remove new binding from current bindings
            for var in data_binding:
                del binding[var]
        # self.log(atom.table, "Top_down_eval return value: {}".format(
        #     '[' + ", ".join([str(x) for x in results]) + ']'))

        return results

    def print_delta_rules(self):
        for table in self.delta_rules:
            print "{}:".format(table)
            for rule in self.delta_rules[table]:
                print "   {}".format(rule)


def index_delta_rules(delta_rules):
    indexed_delta_rules = {}
    for delta in delta_rules:
        if delta.trigger.table not in indexed_delta_rules:
            indexed_delta_rules[delta.trigger.table] = [delta]
        else:
            indexed_delta_rules[delta.trigger.table].append(delta)
    return indexed_delta_rules

def plug(atom, binding):
    """ Returns a tuple representing the arguments to ATOM after having
        applied BINDING to the variables in ATOM. """
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

def eliminate_dups_with_ref_counts(tuples):
    refcounts = {}
    for tuple in tuples:
        if tuple in refcounts:
            refcounts[tuple] += 1
        else:
            refcounts[tuple] = 0
    return refcounts


# def atom_arg_names(atom):
#     if atom.table not in database.schemas:
#         raise CongressRuntime("Table {} has no schema".format(atom.table))
#     schema = database.schemas[atom.table]
#     if len(atom.arguments) != len(schema.arguments):
#         raise CongressRuntime("Atom {} has wrong number of arguments for "
#                   " schema: {}".format(atom, str(schema)))
#     mapping = {}
#     for i in xrange(0, len(atom.arguments)):
#         mapping[schema.arguments[i]] = atom.arguments[i]
#     return mapping

def all_variables(atoms, atom_index):
    vars = set()
    for i in xrange(atom_index, len(atoms)):
        vars |= atoms[i].variable_names()
    return vars

# def var_bindings_to_named_bindings(atom, var_bindings):
#     new_bindings = {}
#     unbound_names = set()
#     schema = database.schemas[atom.table]
#     print "schema: " + str(schema.arguments)
#     assert(len(schema.arguments) == len(atom.arguments))
#     for i in xrange(0, len(atom.arguments)):
#         term = atom.arguments[i]
#         if term.is_object():
#             new_bindings[schema.arguments[i]] = term.name
#         elif term.name in var_bindings:
#             new_bindings[schema.arguments[i]] = var_bindings[term.name]
#         else:
#             unbound_names.add(schema.arguments[i])
#     print "new_bindings: {}, unbound_names: {}".format(new_bindings, unbound_names)
#     return (new_bindings, unbound_names)



