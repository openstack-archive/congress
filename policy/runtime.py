#! /usr/bin/python

import collections

# Todo:
#   Add to Atom: is_negated, variable_names()
#    Actually, make Literal inherit from Atom and change is_negated


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

class Database(object):
    class Dicttuple(object):
        def __init__(self, binding, refcount=1):
            self.binding = binding
            self.refcount = refcount

        def __eq__(self, other):
            return self.binding == other.binding

        def __str__(self):
            return "<binding: {}, refcount: {}>".format(
                str(self.binding), self.refcount)

    class Schema (object):
        def __init__(self, column_names):
            self.arguments = column_names
        def __str__(self):
            return str(self.arguments)

    def __init__(self):
        self.data = {'p': [], 'q': [], 'r': [Database.Dicttuple({1: 1})]}
        # self.data = {'p': [Dicttuple({1: 'a'}),
        #                    Dicttuple({1: 'b'}),
        #                    Dicttuple({1, 'c'})],
        #              'q': [Dicttuple({1: 'b'}),
        #                    Dicttuple({1: 'c'}),
        #                    Dicttuple({1, 'd'})],
        #              'r': [Dicttuple({1: 'c'}),
        #                    Dicttuple({1: 'd'}),
        #                    Dicttuple({1, 'e'})]
        #              }
        self.schemas = {'p': Database.Schema([1]),
                        'q': Database.Schema([1]),
                        'r': Database.Schema([1])}

    def __str__(self):
        return "<data: {}, schemas: {}>".format(
            str(self.data), str(self.schemas))

    def get_matches(table, binding, columns=None):
        if table not in self.data:
            raise CongressRuntime("Table not found ".format(table))
        result = []
        for dicttuple in self.data[table]:
            for col in binding:
                if dicttuple[col] == binding[col]:
                    result.append(dicttuple)

    def insert(table, binding, refcount):
        if table not in self.data:
            raise CongressRuntime("Table not found ".format(table))
        for dicttuple in self.data[table]:
            if dicttuple.binding == binding:
                dicttuple.refcount += refcount
                return
        self.data[table].append(dicttuple(binding, refcount))

    def delete(table, binding, refcount):
        if table not in self.data:
            raise CongressRuntime("Table not found ".format(table))
        for dicttuple in self.data[table]:
            if dicttuple.binding == binding:
                dicttuple.refcount -= refcount
                if dicttuple.refcount < 0:
                    raise CongressRuntime("Deleted more tuples than existed")
                return
        raise CongressRuntime("Deleted tuple that didn't exist")

# queue of events left to process
queue = EventQueue()
# collection of all tables
database = Database()
# update rules, indexed by trigger table name
delta_rules = {}
# tracing construct
tracer = Tracer()

def handle_insert(table, tuple):
    if tracer.is_traced(table):
        print "Inserting into queue: {} with {}".format(table, str(tuple))
    queue.enqueue(Event(table, tuple, insert=True))
    process_queue()

def handle_delete(table, tuple):
    if tracer.is_traced(table):
        print "Inserting into queue: {} with {}".format(table, str(tuple))
    queue.enqueue(Event(table, tuple, insert=False))
    process_queue()

def process_queue():
    while len(queue) > 0:
        propagate(queue.dequeue())

def propagate(event):
    if tracer.is_traced(event.table):
        print "Processing event: {}".format(str(event))
    if event.table not in delta_rules:
        print "event.table: {}".format(event.table)
        print_delta_rules()
        print "No applicable delta rule"
        return
    for delta_rule in delta_rules[event.table]:
        propagate_rule(delta_rule, event)

def propagate_rule(event, delta_rule):
    assert(not delta_rule.trigger.is_negated())
    if tracer.is_traced(event.table):
        print "Processing event {} with rule {}".format(str(event), str(delta_rule))

    # compute tuples generated by event (either for insert or delete)
    binding_list = match(event.tuple, delta_rule.trigger)
    vars_in_head = delta_rule.head.variable_names()
    needed_vars = set(vars_in_head) - set(binding_list.keys())
    new_tuples = top_down_eval(needed_vars, delta_rule.body, binding_list)
    no_dups = eliminate_dups_with_ref_counts(new_tuples)

    # enqueue effects of Event
    head_table = delta_rule.head.operator
    for (tuple, refcount) in new_tuples.items():
        queue.enqueue(Event(table=head_table, tuple=tuple, insert=event.insert,
                            refcount=refcount))

    # insert tuple into actual table
    if event.is_insert():
        database.insert(event.table, event.tuple)
    else:
        database.delete(event.table, event.tuple)

def match(tuple, atom):
    """ Returns a binding dictionary """
    if len(tuple) != len(atom.arguments):
        return False
    binding = {}
    for i in xrange(0, len(tuple)):
        arg = atom.arguments[i]
        if arg.is_variable():
            if arg.name in binding:
                oldval = binding[arg.name]
                if oldval != tuple[i]:
                    return False
            else:
                bindings[arg.name] = tuple[i]
    return binding

def eliminate_dups_with_ref_counts(tuples):
    refcounts = {}
    for tuple in tuples:
        if tuple in refcounts:
            refcounts[tuple] += 1
        else:
            refcounts[tuple] = 0
    return refcounts

def top_down_eval(projection, atoms, atom_index, var_bindings):
    """ Compute all tuples making the conjunction of the list of atoms ATOMS
        true under the variable bindings of dictionary BINDING_LIST,
        where we only care about the variables in the list PROJECTION. """
    atom = atoms[atom_index]
    if tracer.is_traced(atom.table):
        print ("Top-down eval(projection={}, atoms={}, atom_index={}, "
               "bindings={})").format(
                str(projection),
                "[" + ",".join(str(x) for x in atoms) + "]",
                atom_index,
                str(bindings))
    # compute name-binding for table lookup
    (name_bindings, missing_names) = \
        var_bindings_to_named_bindings(atom, var_bindings)
    needed_names = missing_names & \
                        (all_variables(atoms, atom_index + 1) | projection)
    needed_names = list(needed_names)
    # do lookup and get name-bindings back
    dictbindings = database.get_matches(
        atom.table, binding_list, columns=needed_names)
    # turn name-bindings into var-bindings
    name_var_bindings = atom_arg_names(atom)
    new_var_bindings = []
    for dictbinding in dictbindings:
        var_binding = {}
        for name_val in dictbinding.binding:
            var_binding[name_var_bindings[name_val]] = dictbinding.binding[name_val]
    # turn each resulting tuple into a new binding list
    results = []
    for binding in new_var_bindings:
        # add this binding to var_bindings
        var_bindings.update(binding)
        # recurse
        results.extend(TOP_DOWN_EVAL(projection, atoms, atom_index+1, binding))
        # remove this binding from var_bindings
        for var in binding:
            del var_bindings[var]
    return results

def atom_arg_names(atom):
    if atom.table not in database.schemas:
        raise CongressRuntime("Table {} has no schema".format(atom.table))
    schema = database.schemas[atom.table]
    if len(atom.arguments) != len(schema.arguments):
        raise CongressRuntime("Atom {} has wrong number of arguments for "
                  " schema: {}".format(atom, str(schema)))
    mapping = {}
    for i in xrange(0, len(atom.arguments) - 1):
        mapping[schema.arguments[i]] = atom.arguments[i]
    return mapping

def all_variables(atoms, atom_index):
    vars = set()
    for i in xrange(atom_index, len(atoms) - 1):
        vars |= atoms[i].variable_names()
    return vars

def var_bindings_to_named_bindings(atom, var_bindings):
    new_bindings = {}
    unbound_names = set()
    schema = database.schemas[atom.table]
    assert(len(schema.arguments) == len(atom.arguments))
    for i in xrange(0, len(atom.arguments) - 1):
        term = atom.arguments[i]
        if term.is_object():
            new_bindings[schema.arguments[i]] = term.name
        elif term in binding_list:
            new_bindings[schema.arguments[i]] = binding_list[term]
        else:
            unbound_names.add(schema.arguments[i])
    return (new_bindings, unbound_names)

def print_delta_rules():
    print "runtime's delta rules"
    for table in delta_rules:
        print "{}:".format(table)
        for rule in delta_rules[table]:
            print "   {}".format(rule)


