#! /usr/bin/python

import collections
import logging
import compile
import unify
import copy

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
    def __init__(self, atom=None, insert=True, proofs=None):
        if proofs is None:
            proofs = []
        self.atom = atom
        self.proofs = proofs
        self.insert = insert
        logging.debug("EV: created event {}".format(str(self)))

    def is_insert(self):
        return self.insert

    def __str__(self):
        if self.is_insert():
            sign = '+'
        else:
            sign = '-'
        return "{}{}({}) with {}".format(self.atom.table, sign,
            ",".join([str(arg) for arg in self.atom.arguments]),
            iterstr(self.proofs))

def iterstr(iter):
    return "[" + ",".join([str(x) for x in iter]) + "]"

##############################################################################
## Logical Building Blocks
##############################################################################

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

    def leaves(self):
        if len(self.children) == 0:
            return [self.root]
        result = []
        for child in self.children:
            result.extend(child.leaves())
        return result

class DeltaRule(object):
    def __init__(self, trigger, head, body, original):
        self.trigger = trigger  # atom
        self.head = head  # atom
        self.body = body  # list of literals
        self.original = original # Rule from which SELF was derived

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
        vs = self.trigger.variables()
        vs |= self.head.variables()
        for atom in self.body:
            vs |= atom.variables()
        return vs


##############################################################################
## Abstract Theories
##############################################################################

class TopDownTheory(object):
    """ Class that holds the Top-Down evaluation routines.  Classes
    will inherit from this class if they want to import and specialize
    those routines. """
    class TopDownContext(object):
        """ Struct for storing the search state of top-down evaluation """
        def __init__(self, literals, literal_index, binding, context, depth):
            self.literals = literals
            self.literal_index = literal_index
            self.binding = binding
            self.previous = context
            self.depth = depth

        def __str__(self):
            return ("TopDownContext<literals={}, literal_index={}, binding={}, "
                    "previous={}, depth={}>").format(
                "[" + ",".join([str(x) for x in self.literals]) + "]",
                str(self.literal_index), str(self.binding),
                str(self.previous), str(self.depth))

    class TopDownResult(object):
        """ Stores a single result for top-down-evaluation """
        def __init__(self, binding, support):
            self.binding = binding
            self.support = support   # for abduction

        def __str__(self):
            return "TopDownResult(binding={}, support={})".format(
                unify.binding_str(self.binding), iterstr(self.support))

    class TopDownCaller(object):
        """ Struct for storing info about the original caller of top-down
        evaluation.
        VARIABLES is the list of variables (from the initial query)
            that we want bindings for.
        BINDING is the initially empty BiUnifier.
        FIND_ALL controls whether just the first or all answers are found.
        ANSWERS is populated by top-down evaluation: it is the list of
               VARIABLES instances that the search process proved true."""

        def __init__(self, variables, binding, find_all=True, save=None):
            # an iterable of variable objects
            self.variables = variables
            # a bi-unifier
            self.binding = binding
            # a boolean
            self.find_all = find_all
            # The results of top-down-eval: a list of TopDownResults
            self.results = []
            # a Function that takes a compile.Literal and a unifier and
            #   returns T iff that literal under the unifier should be
            #   saved as part of an abductive explanation
            self.save = save
            # A variable used to store explanations as they are constructed
            self.support = []

        def __str__(self):
            return ("TopDownCaller<variables={}, binding={}, find_all={}, "
                    "results={}, save={}, support={}>".format(
                iterstr(self.variables), str(self.binding), str(self.find_all),
                iterstr(self.results), repr(self.save), iterstr(self.support)))

    def select(self, query, find_all=True):
        """ Return list of instances of QUERY that are true.
            If FIND_ALL is False, the return list has at most 1 element."""
        assert (isinstance(query, compile.Atom) or
                isinstance(query, compile.Rule)), "Query must be atom/rule"
        if isinstance(query, compile.Atom):
            literals = [query]
        else:
            literals = query.body
        # Because our output is instances of QUERY, need all the variables
        #   in QUERY.
        bindings = self.top_down_evaluation(query.variables(), literals,
            find_all=find_all)
        logging.debug("Top_down_evaluation returned: {}".format(
            str(bindings)))
        if len(bindings) > 0:
            logging.debug("Found answer {}".format(
                "[" + ",".join([str(query.plug(x))
                                for x in bindings]) + "]"))
        return [query.plug(x) for x in bindings]

    def explain(self, query, tablenames, find_all=True):
        """ Same as select except stores instances of TABLENAMES
        that participated in each proof. If QUERY is an atom,
        returns list of rules with QUERY in the head and
        the stored instances of TABLENAMES in the body; if QUERY is
        a rule, the rules returned have QUERY's head in the head
        and the stored instances of TABLENAMES in the body. """
        # This is different than abduction because instead of replacing
        #   a proof attempt with saving a literal, we want to save a literal
        #   after a successful proof attempt.
        assert False, "Not yet implemented"

    def abduce(self, query, tablenames, find_all=True):
        """ Computes additional literals that if true would make
            (some instance of) QUERY true.  Returns a list of rules
            where the head represents an instance of the QUERY and
            the body is the collection of literals that must be true
            in order to make that instance true.  If QUERY is a rule,
            each result is an instance of the head of that rule, and
            the computed literals if true make the body of that rule
            (and hence the head) true.  If FIND_ALL is true, the
            return list has at most one element.
            Limitation: every negative literal relevant to a proof of
            QUERY is unconditionally true, i.e. no literals are saved
            when proving a negative literal is true."""
        assert (isinstance(query, compile.Atom) or
                isinstance(query, compile.Rule)), \
             "Explain requires a formula"
        if isinstance(query, compile.Atom):
            literals = [query]
            output = query
        else:
            literals = query.body
            output = query.head
        # We need all the variables we will be using in the output, which
        #   here is just the head of QUERY (or QUERY itself if it is an atom)
        abductions = self.top_down_abduction(output.variables(), literals,
            find_all=find_all, save=lambda lit,binding: lit.table in tablenames)
        results = [compile.Rule(output.plug(abd.binding), abd.support)
                        for abd in abductions]
        logging.debug("abduction result: " + iterstr(results))
        return results

    def top_down_evaluation(self, variables, literals,
            binding=None, find_all=True):
        """ Compute all bindings of VARIABLES that make LITERALS
            true according to the theory (after applying the unifier BINDING).
            If FIND_ALL is False, stops after finding one such binding.
            Returns a list of dictionary bindings. """
        # logging.debug("CALL: top_down_evaluation(vars={}, literals={}, "
        #               "binding={})".format(
        #         iterstr(variables), iterstr(literals),
        #         str(binding)))
        results = self.top_down_abduction(variables, literals,
            binding=binding, find_all=find_all, save=None)
        # logging.debug("EXIT: top_down_evaluation(vars={}, literals={}, "
        #               "binding={}) returned {}".format(
        #         iterstr(variables), iterstr(literals),
        #         str(binding), iterstr(results)))
        return [x.binding for x in results]

    def top_down_abduction(self, variables, literals, binding=None,
            find_all=True, save=None):
        """ Compute all bindings of VARIABLES that make LITERALS
            true according to the theory (after applying the
            unifier BINDING), if we add some number of additional
            literals.  Note: will not save any literals that are
            needed to prove a negated literal since the results
            would not make sense.  Returns a list of TopDownResults. """
        if binding is None:
            binding = self.new_bi_unifier()
        caller = self.TopDownCaller(variables, binding, find_all=find_all,
            save=save)
        if len(literals) == 0:
            self.top_down_finish(None, caller)
        else:
            # Note: must use same unifier in CALLER and CONTEXT
            context = self.TopDownContext(literals, 0, binding, None, 0)
            self.top_down_eval(context, caller)
        return list(set(caller.results))

    def top_down_eval(self, context, caller):
        """ Compute all instances of LITERALS (from LITERAL_INDEX and above)
            that are true according to the theory (after applying the
            unifier BINDING to LITERALS).  Returns False or an answer. """
        # no recursive rules, ever; this style of algorithm will not terminate
        lit = context.literals[context.literal_index]
        # logging.debug("CALL: top_down_eval({}, {})".format(str(context),
        #     str(caller)))

        # abduction
        if caller.save is not None and caller.save(lit, context.binding):
            self.print_call(lit, context.binding, context.depth)
            # save lit and binding--binding may not be fully flushed out
            #   when we save (or ever for that matter)
            caller.support.append((lit, context.binding))
            self.print_save(lit, context.binding, context.depth)
            success = self.top_down_finish(context, caller)
            caller.support.pop() # pop in either case
            if success:
                return True
            else:
                self.print_fail(lit, context.binding, context.depth)
                return False

        # regular processing
        if lit.is_negated():
            # logging.debug("{} is negated".format(str(lit)))
            # recurse on the negation of the literal
            assert lit.plug(context.binding).is_ground(), \
                "Negated literals must be ground when evaluated"
            self.print_call(lit, context.binding, context.depth)
            new_context = self.TopDownContext([lit.complement()],
                    0, context.binding, None, context.depth + 1)
            new_caller = self.TopDownCaller(caller.variables, caller.binding,
                find_all=False, save=None)
            # Make sure new_caller has find_all=False, so we stop as soon
            #    as we can.
            # Ensure save=None so that abduction does not save anything.
            #    Saving while performing NAF makes no sense.
            if self.top_down_includes(new_context, new_caller):
                self.print_fail(lit, context.binding, context.depth)
                return False
            else:
                # don't need bindings b/c LIT must be ground
                return self.top_down_finish(context, caller, redo=False)
        else:
            return self.top_down_includes(context, caller)

    def top_down_includes(self, context, caller):
        """ Top-down evaluation of all the theories included in this theory. """
        is_true = self.top_down_th(context, caller)
        if is_true and not caller.find_all:
            return True
        for th in self.includes:
            is_true = th.top_down_eval(context, caller)
            if is_true and not caller.find_all:
                return True
        return False

    def top_down_th(self, context, caller):
        """ Top-down evaluation for the rules in SELF.CONTENTS. """
        # logging.debug("top_down_th({})".format(str(context)))
        lit = context.literals[context.literal_index]
        self.print_call(lit, context.binding, context.depth)
        for rule in self.head_index(lit.table):
            unifier = self.new_bi_unifier()
            # Prefer to bind vars in rule head
            undo = self.bi_unify(self.head(rule), unifier, lit, context.binding)
            # self.log(lit.table, "Rule: {}, Unifier: {}, Undo: {}".format(
            #     str(rule), str(unifier), str(undo)))
            if undo is None:  # no unifier
                continue
            if len(self.body(rule)) == 0:
                if self.top_down_finish(context, caller):
                    unify.undo_all(undo)
                    if not caller.find_all:
                        return True
                else:
                    unify.undo_all(undo)
            else:
                new_context = self.TopDownContext(rule.body, 0,
                    unifier, context, context.depth + 1)
                if self.top_down_eval(new_context, caller):
                    unify.undo_all(undo)
                    if not caller.find_all:
                        return True
                else:
                    unify.undo_all(undo)
        self.print_fail(lit, context.binding, context.depth)
        return False

    def top_down_finish(self, context, caller, redo=True):
        """ Helper that is called once top_down successfully completes
            a proof for a literal.  Handles (i) continuing search
            for those literals still requiring proofs within CONTEXT,
            (ii) adding solutions to CALLER once all needed proofs have
            been found, and (iii) printing out Redo/Exit during tracing.
            Returns True if the search is finished and False otherwise.
            Temporary, transparent modification of CONTEXT."""
        if context is None:
            # Found an answer; now store it
            if caller is not None:
                # flatten bindings and store before we undo
                # copy caller.support and store before we undo
                binding = {}
                for var in caller.variables:
                    binding[var] = caller.binding.apply(var)
                result = self.TopDownResult(binding,
                    [support[0].plug(support[1], caller=caller)
                        for support in caller.support])
                caller.results.append(result)
            return True
        else:
            self.print_exit(context.literals[context.literal_index],
                context.binding, context.depth)
            # continue the search
            if context.literal_index < len(context.literals) - 1:
                context.literal_index += 1
                finished = self.top_down_eval(context, caller)
                context.literal_index -= 1  # in case answer is False
            else:
                finished = self.top_down_finish(context.previous, caller)
            # return search result (after printing a Redo if failure)
            if redo and (not finished or caller.find_all):
                self.print_redo(context.literals[context.literal_index],
                    context.binding, context.depth)
            return finished

    def print_call(self, literal, binding, depth):
        self.log(literal.table, "{}Call: {} with {}".format("| "*depth,
            literal.plug(binding), str(binding)))

    def print_exit(self, literal, binding, depth):
        self.log(literal.table, "{}Exit: {} with {}".format("| "*depth,
            literal.plug(binding), str(binding)))

    def print_save(self, literal, binding, depth):
        self.log(literal.table, "{}Save: {} with {}".format("| "*depth,
            literal.plug(binding), str(binding)))

    def print_fail(self, literal, binding, depth):
        self.log(literal.table, "{}Fail: {} with {}".format("| "*depth,
            literal.plug(binding), str(binding)))
        return False

    def print_redo(self, literal, binding, depth):
        self.log(literal.table, "{}Redo: {} with {}".format("| "*depth,
            literal.plug(binding), str(binding)))
        return False

    def log(self, table, msg, depth=0):
        self.tracer.log(table, "TDT: " + msg, depth)

    @classmethod
    def new_bi_unifier(cls, dictionary=None):
        """ Return a unifier compatible with unify.bi_unify """
        return unify.BiUnifier(dictionary=dictionary)
            # lambda (index):
            # compile.Variable("x" + str(index)), dictionary=dictionary)

    def head_index(self, table):
        """ This routine must return all the formulas pertinent for
        top-down evaluation when a literal with TABLE is at the top
        of the stack. """
        if table not in self.contents:
            return []
        return self.contents[table]

    def head(self, formula):
        """ Given a FORMULA, return the thing to unify against.
            Usually, FORMULA is a compile.Rule, but it could be anything
            returned by HEAD_INDEX."""
        return formula.head

    def body(self, formula):
        """ Given a FORMULA, return a list of things to push onto the
        top-down eval stack. """
        return formula.body

    def bi_unify(self, head, unifier1, body_element, unifier2):
        """ Given something returned by self.head HEAD and an element in
        the return of self.body BODY_ELEMENT, modify UNIFIER1 and UNIFIER2
        so that HEAD.plug(UNIFIER1) == BODY_ELEMENT.plug(UNIFIER2).
        Returns changes that can be undone via unify.undo-all. """
        return unify.bi_unify_atoms(head, unifier1, body_element, unifier2)

##############################################################################
## Concrete Theory: Database
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

        def __ge__(self, iterable):
            for proof in iterable:
                if proof not in self.contents:
                    logging.debug("Proof {} makes {} not >= {}".format(
                        str(proof), str(self), iterstr(iterable)))
                    return False
            return True

        def __le__(self, iterable):
            for proof in self.contents:
                if proof not in iterable:
                    logging.debug("Proof {} makes {} not <= {}".format(
                        str(proof), str(self), iterstr(iterable)))
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
            # logging.debug("DBTuple matching {} against atom {} in {}".format(
            #     str(self), iterstr(atom.arguments), str(unifier)))
            if len(self.tuple) != len(atom.arguments):
                return None
            changes = []
            for i in xrange(0, len(atom.arguments)):
                val, binding = unifier.apply_full(atom.arguments[i])
                # logging.debug("val({})={} at {}; comparing to object {}".format(
                #     str(atom.arguments[i]), str(val), str(binding),
                #     str(self.tuple[i])))
                if val.is_variable():
                    changes.append(binding.add(val,
                        compile.Term.create_from_python(self.tuple[i]),
                        None))
                else:
                    if val.name != self.tuple[i]:
                        unify.undo_all(changes)
                        return None
            return changes

    def __init__(self):
        self.data = {}
        self.tracer = Tracer()
        self.includes = []

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

    def is_noop(self, event):
        """ Returns T if EVENT is a noop on the database. """
        # insert/delete same code but with flipped return values
        # Code below is written as insert, except noop initialization.
        if event.is_insert():
            noop = True
        else:
            noop = False
        if event.atom.table not in self.data:
            return not noop
        event_data = self.data[event.atom.table]
        raw_tuple = tuple(event.atom.argument_names())
        for dbtuple in event_data:
            if dbtuple.tuple == raw_tuple:
                if event.proofs <= dbtuple.proofs:
                    return noop
        return not noop

    def explain(self, atom):
        if atom.table not in self.data or not atom.is_ground():
            return self.ProofCollection()
        args = tuple([x.name for x in atom.arguments])
        for dbtuple in self.data[atom.table]:
            if dbtuple.tuple == args:
                return dbtuple.proofs

    # overloads for TopDownTheory so we can properly use the
    #    top_down_evaluation routines
    def head_index(self, table):
        if table not in self.data:
            return []
        return self.data[table]

    def head(self, thing):
        return thing

    def body(self, thing):
        return []

    def bi_unify(self, dbtuple, unifier1, atom, unifier2):
        """ THING1 is always a ground DBTuple and THING2 is always an ATOM. """
        return dbtuple.match(atom, unifier2)

    def atom_to_internal(self, atom, proofs=None):
        return atom.table, self.DBTuple(atom.argument_names(), proofs)

    def insert(self, atom, proofs=None):
        assert isinstance(atom, compile.Atom), "Insert requires compile.Atom"
        table, dbtuple = self.atom_to_internal(atom, proofs)
        self.log(table, "Insert: table {} tuple {}".format(
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


    def delete(self, atom, proofs=None):
        assert isinstance(atom, compile.Atom), "Delete requires compile.Atom"
        self.log(atom.table, "Delete: {}".format(str(atom)))
        table, dbtuple = self.atom_to_internal(atom, proofs)
        self.log(table, "Delete: table {} tuple {}".format(
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
## Concrete Theories: other
##############################################################################

class NonrecursiveRuleTheory(TopDownTheory):
    """ A non-recursive collection of Rules. """

    def __init__(self, rules=None):
        # dictionary from table name to list of rules with that table in head
        self.contents = {}
        # list of other theories that are implicitly included in this one
        self.includes = []
        self.tracer = Tracer()
        if rules is not None:
            for rule in rules:
                self.insert(rule)

    def __str__(self):
        return str(self.contents)

    def insert(self, rule):
        if isinstance(rule, compile.Atom):
            rule = compile.Rule(rule, [], rule.location)
        self.log(rule.head.table, "Insert: {}".format(str(rule)))
        table = rule.head.table
        if table in self.contents:
            if rule not in self.contents[table]:  # eliminate dups
                self.contents[table].append(rule)
        else:
            self.contents[table] = [rule]

    def delete(self, rule):
        if isinstance(rule, compile.Atom):
            rule = compile.Rule(rule, [], rule.location)
        self.log(rule.head.table, "Delete: {}".format(str(rule)))
        table = rule.head.table
        if table in self.contents:
            self.contents[table].remove(rule)

    def log(self, table, msg, depth=0):
        self.tracer.log(table, "NRT: " + msg, depth)

class DeltaRuleTheory (object):
    """ A collection of DeltaRules. """
    def __init__(self, rules=None):
        # dictionary from table name to list of rules with that table as trigger
        self.contents = {}
        # list of theories implicitly included in this one
        self.includes = []
        # dictionary from table name to number of rules with that table in head
        self.views = {}
        if rules is not None:
            for rule in rules:
                self.insert(rule)

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

    def modify(self, delta, is_insert):
        if is_insert is True:
            return self.insert(delta)
        else:
            return self.delete(delta)

    def __str__(self):
        return str(self.contents)

    def rules_with_trigger(self, table):
        if table not in self.contents:
            return []
        else:
            return self.contents[table]

    def is_view(self, x):
        return x in self.views

class MaterializedRuleTheory(TopDownTheory):
    """ A theory that stores the table contents explicitly.
        Recursive rules are allowed. """

    def __init__(self):
        # queue of events left to process
        self.queue = EventQueue()
        # collection of all tables
        self.database = Database()
        # tracer object
        self.tracer = Tracer()
        # rules that dictate how database changes in response to events
        self.delta_rules = DeltaRuleTheory()

    ############### External Interface ###############

    def select(self, query):
        assert (isinstance(query, compile.Atom) or
                isinstance(query, compile.Rule)), \
             "Select requires a formula"
        return self.database.select(query)

    def insert(self, formula):
        assert (isinstance(formula, compile.Atom) or
                isinstance(formula, compile.Rule)), \
             "Insert requires a formula"
        return self.modify(formula, is_insert=True)

    def delete(self, formula):
        assert (isinstance(formula, compile.Atom) or
                isinstance(formula, compile.Rule)), \
             "Delete requires a formula"
        return self.modify(formula, is_insert=False)

    def explain(self, query, tablenames, find_all):
        assert isinstance(query, compile.Atom), \
            "Explain requires an atom"
        # ignoring TABLENAMES and FIND_ALL
        #    except that we return the proper type.
        proof = self.explain_aux(query, 0)
        return [proof]

    ############### Interface implementation ###############

    def log(self, table, msg, depth=0):
        self.tracer.log(table, "MRT: " + msg, depth)

    def explain_aux(self, query, depth):
        self.log(query.table, "Explaining {}".format(str(query)), depth)
        # Bail out on negated literals.  Need different
        #   algorithm b/c we need to introduce quantifiers.
        if query.is_negated():
            return Proof(query, [])
        # grab first local proof, since they're all equally good
        localproofs = self.database.explain(query)
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

    def modify(self, formula, is_insert=True):
        """ Event handler for arbitrary insertion/deletion (rules and facts). """
        if is_insert:
            text = "Insert"
        else:
            text = "Delete"
        if formula.is_atom():
            assert not self.is_view(formula.table), \
                "Cannot directly modify tables computed from other tables"
            self.log(formula.table, "{}: {}".format(text, str(formula)))
            self.modify_tables_with_atom(formula, is_insert=is_insert)
            return None
        else:
            self.modify_tables_with_rule(
                formula, is_insert=is_insert)
            self.log(formula.head.table, "{}: {}".format(text, str(formula)))
            for delta_rule in compile.compute_delta_rules([formula]):
                self.delta_rules.modify(delta_rule, is_insert=is_insert)
            return None

    def modify_tables_with_rule(self, rule, is_insert):
        """ Add rule (not a DeltaRule) to collection and update
            tables as appropriate. """
        # don't have separate queue since inserting/deleting a rule doesn't generate any
        #   new rule insertion/deletion events
        bindings = self.database.top_down_evaluation(
            rule.variables(), rule.body)
        self.log(None, "new bindings after top-down: {}".format(
            ",".join([str(x) for x in bindings])))
        self.process_new_bindings(bindings, rule.head, is_insert, rule)
        self.process_queue()

    # def modify_tables_with_tuple(self, table, row, is_insert):
    #     """ Event handler for a tuple insertion/deletion.
    #     TABLE is the name of a table (a string).
    #     TUPLE is a Python tuple.
    #     IS_INSERT is True or False."""
    #     if is_insert:
    #         text = "Inserting into queue"
    #     else:
    #         text = "Deleting from queue"
    #     self.log(table, "{}: table {} with tuple {}".format(
    #         text, table, str(row)))
    #     if not isinstance(row, Database.DBTuple):
    #         row = Database.DBTuple(row)
    #     self.log(table, "{}: table {} with tuple {}".format(
    #         text, table, str(row)))
    #     self.queue.enqueue(Event(table, row, insert=is_insert))
    #     self.process_queue()

    def modify_tables_with_atom(self, atom, is_insert):
        """ Event handler for atom insertion/deletion.
        IS_INSERT is True or False."""
        if is_insert:
            text = "Inserting into queue"
        else:
            text = "Deleting from queue"
        self.log(atom.table, "{}: {}".format(text, str(atom)))
        self.queue.enqueue(Event(atom=atom, insert=is_insert))
        self.process_queue()

    ############### Data manipulation ###############

    def process_queue(self):
        """ Toplevel data evaluation routine. """
        while len(self.queue) > 0:
            event = self.queue.dequeue()
            if self.database.is_noop(event):
                self.log(event.atom.table, "is noop")
                continue
            self.log(event.atom.table, "is not noop")
            if event.is_insert():
                self.propagate(event)
                self.database.insert(event.atom, event.proofs)
            else:
                self.propagate(event)
                self.database.delete(event.atom, event.proofs)

    def propagate(self, event):
        """ Computes events generated by EVENT and the DELTA_RULES,
            and enqueues them. """
        self.log(event.atom.table, "Processing event: {}".format(str(event)))
        applicable_rules = self.delta_rules.rules_with_trigger(event.atom.table)
        if len(applicable_rules) == 0:
            self.log(event.atom.table, "No applicable delta rule")
        for delta_rule in applicable_rules:
            self.propagate_rule(event, delta_rule)

    def propagate_rule(self, event, delta_rule):
        """ Compute and enqueue new events generated by EVENT and DELTA_RULE. """
        self.log(event.atom.table, "Processing event {} with rule {}".format(
            str(event), str(delta_rule)))

        # compute tuples generated by event (either for insert or delete)
        # print "event: {}, event.tuple: {}, event.tuple.rawtuple(): {}".format(
        #     str(event), str(event.tuple), str(event.tuple.raw_tuple()))
        # binding_list is dictionary

        # Save binding for delta_rule.trigger; throw away binding for event
        #   since event is ground.
        binding = self.new_bi_unifier()
        assert isinstance(delta_rule.trigger, compile.Atom)
        assert isinstance(event.atom, compile.Atom)
        undo = self.bi_unify(delta_rule.trigger, binding,
                             event.atom, self.new_bi_unifier())
        if undo is None:
            return
        self.log(event.atom.table,
            "binding list for event and delta-rule trigger: {}".format(
                str(binding)))
        bindings = self.database.top_down_evaluation(
            delta_rule.variables(), delta_rule.body, binding)
        self.log(event.atom.table, "new bindings after top-down: {}".format(
            ",".join([str(x) for x in bindings])))

        if delta_rule.trigger.is_negated():
            insert_delete = not event.insert
        else:
            insert_delete = event.insert
        self.process_new_bindings(bindings, delta_rule.head,
            insert_delete, delta_rule.original)

    def process_new_bindings(self, bindings, atom, insert, original_rule):
        """ For each of BINDINGS, apply to ATOM, and enqueue it as an insert if
            INSERT is True and as a delete otherwise. """
        # for each binding, compute generated tuple and group bindings
        #    by the tuple they generated
        new_atoms = {}
        for binding in bindings:
            new_atom = atom.plug(binding)
            if new_atom not in new_atoms:
                new_atoms[new_atom] = []
            new_atoms[new_atom].append(Database.Proof(
                binding, original_rule))
        self.log(atom.table, "new tuples generated: {}".format(
            ", ".join([str(x) for x in new_atoms])))

        # enqueue each distinct generated tuple, recording appropriate bindings
        for new_atom in new_atoms:
            # self.log(event.table,
            #     "new_tuple {}: {}".format(str(new_tuple), str(new_tuples[new_tuple])))
            # Only enqueue if new data.
            # Putting the check here is necessary to support recursion.
            self.queue.enqueue(Event(atom=new_atom,
                                     proofs=new_atoms[new_atom],
                                     insert=insert))

    def is_view(self, x):
        return self.delta_rules.is_view(x)

    def base_tables(self):
        return [table for table in self.database.table_names()
                if not self.is_view(table)]

    def top_down_eval(self, context, caller):
        return self.database.top_down_eval(context, caller)

##############################################################################
## Runtime
##############################################################################

class Runtime (object):
    """ Runtime for the Congress policy language.  Only have one instantiation
        in practice, but using a class is natural and useful for testing. """
    # Names of theories
    CLASSIFY_THEORY = "classification"
    SERVICE_THEORY = "service"
    ACTION_THEORY = "action"

    def __init__(self):

        # tracer object
        self.tracer = Tracer()
        # collection of theories
        self.theory = {}
        # CLASSIFY_THEORY: the policy
        #  Allow negation for sure.  Currently supports recursion.
        self.theory[self.CLASSIFY_THEORY] = MaterializedRuleTheory()
        # ACTION_THEORY: describes how actions affect tables
        #  non-recursive, with semi-positive negation over base tables
        #    of CLASSIFY_THEORY, i.e. no negation over views of
        #    either ACTION_THEORY or CLASSIFY_THEORY.
        #    (Why?: Using top-down eval, hence no recursion, and abduction
        #    saves no literal under a negated literal.)
        #  The +/- atoms (a) should only appear in the head and (b)
        #    should only be for the basetables of CLASSIFY_THEORY, i.e.
        #    no action should change a table that exists only in the policy.
        #  Can reference tables defined in CLASSIFY_THEORY in the body
        #    of rules or any other tables defined in ACTION_THEORY.
        #    Should throw warning if referencing table not appearing
        #    in either and provide special table False.
        self.theory[self.ACTION_THEORY] = NonrecursiveRuleTheory()
        self.theory[self.ACTION_THEORY].includes.append(
            self.theory[self.CLASSIFY_THEORY])
        # SERVICE_THEORY: describes bindings for tables to real-world
        #    software.
        #  Need bindings for every base-table in CLASSIFY_THEORY
        #   and every action in ACTION_THEORY.
        self.theory[self.SERVICE_THEORY] = NonrecursiveRuleTheory()

    def get_target(self, name):
        if name is None:
            name = self.CLASSIFY_THEORY
        assert name in self.theory, "Unknown target {}".format(name)
        return self.theory[name]

    def log(self, table, msg, depth=0):
        self.tracer.log(table, "RT: " + msg, depth)

    ############### External interface ###############
    def load_file(self, filename, target=None):
        """ Compile the given FILENAME and insert each of the statements
            into the runtime. """
        for formula in compile.parse_file(filename):
            self.insert(formula, target=target)

    def select(self, query, target=None):
        """ Event handler for arbitrary queries. Returns the set of
            all instantiated QUERY that are true. """
        if isinstance(query, basestring):
            return self.select_string(query, self.get_target(target))
        elif isinstance(query, tuple):
            return self.select_tuple(query, self.get_target(target))
        else:
            return self.select_obj(query, self.get_target(target))

    def explain(self, query, tablenames=None, find_all=False, target=None):
        """ Event handler for explanations.  Given a ground query and
            a collection of tablenames that we want the explanation in
            terms of, return proof(s) that the query is true. If
            FIND_ALL is True, returns list; otherwise, returns single proof."""
        if isinstance(query, basestring):
            return self.explain_string(
                query, tablenames, find_all, self.get_target(target))
        elif isinstance(query, tuple):
            return self.explain_tuple(
                query, tablenames, find_all, self.get_target(target))
        else:
            return self.explain_obj(
                query, tablenames, find_all, self.get_target(target))

    def insert(self, formula, target=None):
        """ Event handler for arbitrary insertion (rules and facts). """
        if isinstance(formula, basestring):
            return self.insert_string(formula, self.get_target(target))
        elif isinstance(formula, tuple):
            return self.insert_tuple(formula, self.get_target(target))
        else:
            return self.insert_obj(formula, self.get_target(target))

    def delete(self, formula, target=None):
        """ Event handler for arbitrary deletion (rules and facts). """
        if isinstance(formula, basestring):
            return self.delete_string(formula, self.get_target(target))
        elif isinstance(formula, tuple):
            return self.delete_tuple(formula, self.get_target(target))
        else:
            return self.delete_obj(formula, self.get_target(target))

    def remediate(self, formula, target=None):
        """ Event handler for remediation. """
        if isinstance(formula, basestring):
            return self.remediate_string(formula, self.get_target(target))
        elif isinstance(formula, tuple):
            return self.remediate_tuple(formula, self.get_target(target))
        else:
            return self.remediate_obj(formula, self.get_target(target))

    # Maybe implement one day
    # def select_if(self, query, temporary_data):
    #     """ Event handler for hypothetical queries.  Returns the set of
    #     all instantiated QUERYs that would be true IF
    #     TEMPORARY_DATA were true. """
    #     if isinstance(query, basestring):
    #         return self.select_if_string(query, temporary_data)
    #     else:
    #         return self.select_if_obj(query, temporary_data)

    ############### Internal interface ###############
    ## Translate different representations of formulas into
    ##   the compiler's internal representation and then invoke
    ##   appropriate theory's version of the API.
    ## Arguments that are strings are suffixed with _string.
    ## All other arguments are instances of Theory, Atom, etc.

    def select_obj(self, query, theory):
        return theory.select(query)

    def select_string(self, policy_string, theory):
        policy = compile.parse(policy_string)
        assert len(policy) == 1, \
                "Queries can have only 1 statement: {}".format(
                    [str(x) for x in policy])
        results = self.select_obj(policy[0], theory)
        return compile.formulas_to_string(results)

    def select_tuple(self, tuple, theory):
        return self.select_obj(compile.Atom.create_from_iter(tuple), theory)

    def explain_obj(self, query, tablenames, find_all, theory):
        return theory.explain(query, tablenames, find_all)

    def explain_string(self, query_string, tablenames, find_all, theory):
        policy = compile.parse(query_string)
        assert len(policy) == 1, "Queries can have only 1 statement"
        results = self.explain_obj(policy[0], tablenames, find_all, theory)
        return compile.formulas_to_string(results)

    def explain_tuple(self, tuple, tablenames, find_all, theory):
        self.explain_obj(compile.Atom.create_from_iter(tuple),
            tablenames, find_all, theory)

    def insert_obj(self, formula, theory):
        return theory.insert(formula)

    def insert_string(self, policy_string, theory):
        policy = compile.parse(policy_string)
        # TODO: send entire parsed theory so that e.g. self-join elim
        #    is more efficient.
        for formula in policy:
            #logging.debug("Parsed {}".format(str(formula)))
            self.insert_obj(formula, theory)

    def insert_tuple(self, tuple, theory):
        self.insert_obj(compile.Atom.create_from_iter(tuple), theory)

    def delete_obj(self, formula, theory):
        theory.delete(formula)

    def delete_string(self, policy_string, theory):
        policy = compile.parse(policy_string)
        for formula in policy:
            self.delete_obj(formula, theory)

    def delete_tuple(self, tuple, theory):
        self.delete_obj(compile.Atom.create_from_iter(tuple), theory)

    def remediate_obj(self, formula, theory):
        """ Find a collection of action invocations that if executed
        result in FORMULA becoming false. """
        actionth = self.theory[self.ACTION_THEORY]
        classifyth = self.theory[self.CLASSIFY_THEORY]
        # look at FORMULA
        if isinstance(formula, compile.Atom):
            output = formula
        elif isinstance(formula, compile.Rule):
            output = formula.head
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
                    if (isinstance(leaf, compile.Literal) and
                        leaf.table in base_tables)]
        logging.debug("Leaves: {}".format(iterstr(leaves)))
        # Query action theory for abductions of negated base tables
        actions = actionth.select(compile.parse1('action(x)'))
        actions = [action.arguments[0].name for action in actions]
        results = []
        for lit in leaves:
            goal = lit.make_positive()
            if lit.is_negated():
                goal.table = goal.table + "+"
            else:
                goal.table = goal.table + "-"
            # return is a list of goal :- act1, act2, ...
            # Turn it into a list of output :- act1, act2, ...
            for abduction in actionth.abduce(goal, actions, False):
                results.append(compile.Rule(output, abduction.body))
        return results

    def remediate_string(self, policy_string, theory):
        policy = compile.parse(policy_string)
        assert len(policy) == 1, "Queries can have only 1 statement"
        return compile.formulas_to_string(self.remediate_obj(policy[0], theory))

    def remediate_tuple(self, tuple, theory):
        self.remediate_obj(compile.Atom.create_from_iter(tuple), theory)

