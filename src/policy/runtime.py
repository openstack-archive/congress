#! /usr/bin/python

import collections

class Tracer(object):
    def __init__(self):
        self.expressions = []
    def trace(self, table):
        self.expressions.append(table)
    def is_traced(self, table):
        return table in self.expressions or '?' in self.expressions

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
    def __init__(self, table=None, tuple=None, insert=True):
        self.table = table
        self.tuple = tuple
        self.insert = insert

    def is_insert(self):
        return self.insert

    def __str__(self):
        return "{}({})".format(self.table,
            ",".join([str(x) for x in self.tuple]))

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
    class DBTuple(object):
        def __init__(self, tuple):
            self.tuple = tuple

        def __eq__(self, other):
            return self.tuple == other.tuple

        def __str__(self):
            return str(self.tuple)

        def match(self, atom, binding):
            print "Checking if tuple {} matches atom {} with binding {}".format(
                str(self), str(atom), str(binding))
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
            print "Check succeeded with binding {}".format(str(new_binding))
            return new_binding

    class Schema (object):
        def __init__(self, column_names):
            self.arguments = column_names
        def __str__(self):
            return str(self.arguments)

    def __init__(self):
        self.data = {'p': [], 'q': [], 'r': [self.DBTuple((1,))]}
        self.schemas = {'p': Database.Schema([1]),
                        'q': Database.Schema([1]),
                        'r': Database.Schema([1])}

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

        return "<data: {}, \nschemas: {}>".format(
            hashlist2str(self.data), hash2str(self.schemas))

    def get_matches(self, atom, binding):
        """ Returns a list of binding lists for the variables in ATOM
            not bound in BINDING: one binding list for each tuple in
            the database matching ATOM under BINDING. """
        if atom.table not in self.data:
            raise CongressRuntime("Table not found ".format(table))
        result = []
        for tuple in self.data[atom.table]:
            print "Matching database tuple {}".format(str(tuple))
            new_binding = tuple.match(atom, binding)
            if new_binding is not None:
                result.append(new_binding)
        return result

    def insert(self, table, tuple):
        print "Inserting table {} tuple {} into DB".format(table, str(tuple))
        if table not in self.data:
            raise CongressRuntime("Table not found ".format(table))
        # if already present, ignore
        if any([dbtuple.tuple == tuple for dbtuple in self.data[table]]):
            return
        self.data[table].append(self.DBTuple(tuple))

    def delete(self, table, binding):
        print "Deleting table {} tuple {} from DB".format(table, str(tuple))
        if table not in self.data:
            raise CongressRuntime("Table not found ".format(table))
        locs = [i for i in xrange(0,len(self.data[table]))
                    if self.data[table][i].tuple == tuple]
        for loc in locs:
            del self.data[loc]


# queue of events left to process
queue = EventQueue()
# collection of all tables
database = Database()
# update rules, indexed by trigger table name
delta_rules = {}
# tracing construct
tracer = Tracer()

def handle_insert(table, tuple):
    """ Event handler for an insertion. """
    if tracer.is_traced(table):
        print "Inserting into queue: {} with {}".format(table, str(tuple))
    # insert tuple into actual table before propagating or else self-join bug.
    #   Self-joins harder to fix when multi-threaded.
    queue.enqueue(Event(table, tuple, insert=True))
    process_queue()

def handle_delete(table, tuple):
    """ Event handler for a deletion. """
    if tracer.is_traced(table):
        print "Inserting into queue: {} with {}".format(table, str(tuple))
    queue.enqueue(Event(table, tuple, insert=False))
    process_queue()

def process_queue():
    """ Toplevel evaluation routine. """
    while len(queue) > 0:
        event = queue.dequeue()
        if event.is_insert():
            database.insert(event.table, event.tuple)
        else:
            database.delete(event.table, event.tuple)
        propagate(event)

def propagate(event):
    """ Computes events generated by EVENT and the DELTA_RULES,
        and enqueues them. """
    if tracer.is_traced(event.table):
        print "Processing event: {}".format(str(event))
    if event.table not in delta_rules.keys():
        print "event.table: {}".format(event.table)
        print_delta_rules()
        print "No applicable delta rule"
        return
    for delta_rule in delta_rules[event.table]:
        propagate_rule(event, delta_rule)

def propagate_rule(event, delta_rule):
    """ Compute and enqueue new events generated by EVENT and DELTA_RULE. """
    assert(not delta_rule.trigger.is_negated())
    if tracer.is_traced(event.table):
        print "Processing event {} with rule {}".format(str(event), str(delta_rule))

    # compute tuples generated by event (either for insert or delete)
    binding_list = match(event.tuple, delta_rule.trigger)
    if binding_list is None:
        return
    print "binding_list for event-tuple and delta_rule trigger: " + str(binding_list)
    # vars_in_head = delta_rule.head.variable_names()
    # print "vars_in_head: " + str(vars_in_head)
    # needed_vars = set(vars_in_head)
    # print "needed_vars: " + str(needed_vars)
    new_bindings = top_down_eval(delta_rule.body, 0, binding_list)
    print "new bindings after top-down: " + ",".join([str(x) for x in new_bindings])

    # enqueue effects of Event
    head_table = delta_rule.head.table
    for new_binding in new_bindings:
        queue.enqueue(Event(table=head_table,
            tuple=plug(delta_rule.head, new_binding),
            insert=event.insert))

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

def top_down_eval(atoms, atom_index, binding):
    """ Compute all instances of ATOMS (from ATOM_INDEX and above) that
        are true in the Database (after applying the dictionary binding
        BINDING to ATOMs).  Returns a list of dictionary bindings. """
    atom = atoms[atom_index]
    if tracer.is_traced(atom.table):
        print ("Top-down eval(atoms={}, atom_index={}, "
               "bindings={})").format(
                "[" + ",".join(str(x) for x in atoms) + "]",
                atom_index,
                str(binding))
    data_bindings = database.get_matches(atom, binding)
    print "data_bindings: " + str(data_bindings)
    if len(data_bindings) == 0:
        return []
    results = []
    for data_binding in data_bindings:
        # add this binding to var_bindings
        binding.update(data_binding)
        if atom_index == len(atoms) - 1:  # last element in atoms
            # construct result
            # output_binding = {}
            # for var in projection:
            #     output_binding[var] = binding[var]
            # results.append(output_binding)
            results.append(dict(binding))  # need to copy
        else:
            # recurse
            results.extend(top_down_eval(atoms, atom_index + 1, binding))
        # remove this binding from var_bindings
        for var in data_binding:
            del binding[var]
    if tracer.is_traced(atom.table):
        print "Return value: {}".format([str(x) for x in results])

    return results

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

def print_delta_rules():
    print "runtime's delta rules"
    for table in delta_rules:
        print "{}:".format(table)
        for rule in delta_rules[table]:
            print "   {}".format(rule)


