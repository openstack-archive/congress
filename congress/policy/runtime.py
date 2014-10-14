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

import collections
import cStringIO
import os
from unify import bi_unify_lists

from builtin.congressbuiltin import CongressBuiltinCategoryMap
from builtin.congressbuiltin import start_builtin_map

# FIXME there is a circular import here because compile.py imports runtime.py
import compile
from congress.openstack.common import log as logging
import unify

LOG = logging.getLogger(__name__)


class Tracer(object):
    def __init__(self):
        self.expressions = []
        self.funcs = [LOG.debug]   # functions to call to trace

    def trace(self, table):
        self.expressions.append(table)

    def is_traced(self, table):
        return table in self.expressions or '*' in self.expressions

    def log(self, table, msg, depth=0):
        if self.is_traced(table):
            for func in self.funcs:
                func("{}{}".format(("| " * depth), msg))


class StringTracer(Tracer):
    def __init__(self):
        super(StringTracer, self).__init__()
        self.stream = cStringIO.StringIO()
        self.funcs.append(lambda x: self.stream.write(x + '\n'))

    def get_value(self):
        return self.stream.getvalue()


class CongressRuntime (Exception):
    pass


class ExecutionLogger(object):
    def __init__(self):
        self.messages = []

    def debug(self, msg):
        self.messages.append(msg)

    def info(self, msg):
        self.messages.append(msg)

    def warn(self, msg):
        self.messages.append(msg)

    def error(self, msg):
        self.messages.append(msg)

    def critical(self, msg):
        self.messages.append(msg)

    def content(self):
        return '\n'.join(self.messages)

    def empty(self):
        self.messages = []


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


class Event(object):
    def __init__(self, formula=None, insert=True, proofs=None, target=None):
        if proofs is None:
            proofs = []
        self.formula = formula
        self.proofs = proofs
        self.insert = insert
        self.target = target
        # LOG.debug("EV: created event {}".format(str(self)))

    def is_insert(self):
        return self.insert

    def tablename(self):
        return self.formula.tablename()

    def __str__(self):
        if self.insert:
            text = "insert"
        else:
            text = "delete"
        if self.target is None:
            target = ""
        elif isinstance(self.target, Theory):
            target = " for {}".format(self.target.name)
        else:
            target = " for {}".format(str(self.target))
        return "{}[{}]{}".format(
            text, str(self.formula), target)

    def lstr(self):
        return self.__str__() + " with proofs " + iterstr(self.proofs)

    def __hash__(self):
        return hash("Event(formula={}, proofs={}, insert={}".format(
            str(self.formula), str(self.proofs), str(self.insert)))

    def __eq__(self, other):
        return (self.formula == other.formula and
                self.proofs == other.proofs and
                self.insert == other.insert)


def iterstr(iter):
    return "[" + ";".join([str(x) for x in iter]) + "]"


def list_to_database(atoms):
    database = Database()
    for atom in atoms:
        if atom.is_atom():
            database.insert(atom)
    return database


def string_to_database(string, module_schemas=None):
    return list_to_database(compile.parse(
        string, module_schemas=module_schemas))


##############################################################################
# Logical Building Blocks
##############################################################################

class Proof(object):
    """A single proof. Differs semantically from Database's
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
        tables.add(self.head.table)
        tables.add(self.trigger.table)
        for atom in self.body:
            tables.add(atom.table)
        return tables


##############################################################################
# Abstract Theories
##############################################################################

class Theory(object):
    def __init__(self, name=None, abbr=None, module_schemas=None):
        # reference to Runtime class, for cross-theory info
        #  Especially for testing, we don't always need
        self.module_schemas = module_schemas

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
        self.cbcmap = CongressBuiltinCategoryMap(start_builtin_map)

    def set_tracer(self, tracer):
        self.tracer = tracer

    def get_tracer(self):
        return self.tracer

    def log(self, table, msg, depth=0):
        self.tracer.log(table, self.trace_prefix + ": " + msg, depth)

    def policy(self):
        """Return a list of the policy statements in this theory."""
        raise NotImplementedError()

    def content(self):
        """Return a list of the contents of this theory: may be rules
        and/or data.  Note: do not change name to CONTENTS, as this
        is reserved for a dictionary of stuff used by TopDownTheory.
        """
        raise NotImplementedError()

    def tablenames(self):
        tablenames = set()
        for rule in self.policy():
            tablenames |= rule.tablenames()
        return tablenames

    def __str__(self):
        s = ""
        for p in self.content():
            s += str(p) + '\n'
        return s + '\n'

    def get_rule(self, ident):
        for p in self.policy():
            if hasattr(p, 'id') and p.id == ident:
                return p
        return

    def get_arity_self(self, tablename):
        """Returns the number of arguments for the given TABLENAME
        or None if the table is not defined by SELF.
        A table is defined-by SELF if this theory believes it is
        the source of truth for that table, i.e. this is a Database
        theory and we store the contents of that table or this is
        a rule theory, and that tablename is in the head of a rule.
        """
        raise NotImplementedError

    def get_arity_includes(self, tablename):
        """Returns the number of arguments for the given TABLENAME
        or None.  Ignores the global_schema.
        """
        result = self.get_arity_self(tablename)
        if result is not None:
            return result
        if not hasattr(self, "includes"):
            return None
        for th in self.includes:
            result = th.get_arity_includes(tablename)
            if result is not None:
                return result
        return None

    def get_arity(self, tablename):
        """Returns the number of arguments for the given TABLENAME or None."""
        if self.module_schemas is None:
            return self.get_arity_includes(tablename)
        (module, name) = self.module_schemas.partition(tablename)
        if module is None:
            return self.get_arity_includes(tablename)
        if module in self.module_schemas:
            return self.module_schemas[module].arity(tablename)


class TopDownTheory(Theory):
    """Class that holds the Top-Down evaluation routines.  Classes
    will inherit from this class if they want to import and specialize
    those routines.
    """
    class TopDownContext(object):
        """Struct for storing the search state of top-down evaluation."""
        def __init__(self, literals, literal_index, binding, context, depth):
            self.literals = literals
            self.literal_index = literal_index
            self.binding = binding
            self.previous = context
            self.depth = depth

        def __str__(self):
            return (
                "TopDownContext<literals={}, literal_index={}, binding={}, "
                "previous={}, depth={}>").format(
                    "[" + ",".join([str(x) for x in self.literals]) + "]",
                    str(self.literal_index), str(self.binding),
                    str(self.previous), str(self.depth))

    class TopDownResult(object):
        """Stores a single result for top-down-evaluation."""
        def __init__(self, binding, support):
            self.binding = binding
            self.support = support   # for abduction

        def __str__(self):
            return "TopDownResult(binding={}, support={})".format(
                unify.binding_str(self.binding), iterstr(self.support))

    class TopDownCaller(object):
        """Struct for storing info about the original caller of top-down
        evaluation.
        VARIABLES is the list of variables (from the initial query)
            that we want bindings for.
        BINDING is the initially empty BiUnifier.
        FIND_ALL controls whether just the first or all answers are found.
        ANSWERS is populated by top-down evaluation: it is the list of
               VARIABLES instances that the search process proved true.
        """

        def __init__(self, variables, binding, theory,
                     find_all=True, save=None):
            # an iterable of variable objects
            self.variables = variables
            # a bi-unifier
            self.binding = binding
            # the top-level theory (for included theories)
            self.theory = theory
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
            return (
                "TopDownCaller<variables={}, binding={}, find_all={}, "
                "results={}, save={}, support={}>".format(
                    iterstr(self.variables), str(self.binding),
                    str(self.find_all), iterstr(self.results), repr(self.save),
                    iterstr(self.support)))

    #########################################
    # External interface

    def __init__(self, name=None, abbr=None, module_schemas=None):
        super(TopDownTheory, self).__init__(
            name=name, abbr=abbr, module_schemas=module_schemas)
        self.includes = []

    def select(self, query, find_all=True):
        """Return list of instances of QUERY that are true.
        If FIND_ALL is False, the return list has at most 1 element.
        """
        assert compile.is_datalog(query), "Query must be atom/rule"
        if compile.is_atom(query):
            literals = [query]
        else:
            literals = query.body
        # Because our output is instances of QUERY, need all the variables
        #   in QUERY.
        bindings = self.top_down_evaluation(query.variables(), literals,
                                            find_all=find_all)
        # LOG.debug("Top_down_evaluation returned: {}".format(
        #     str(bindings)))
        if len(bindings) > 0:
            self.log(query.tablename(), "Found answer {}".format(
                "[" + ",".join([str(query.plug(x))
                                for x in bindings]) + "]"))
        return [query.plug(x) for x in bindings]

    def explain(self, query, tablenames, find_all=True):
        """Same as select except stores instances of TABLENAMES
        that participated in each proof. If QUERY is an atom,
        returns list of rules with QUERY in the head and
        the stored instances of TABLENAMES in the body; if QUERY is
        a rule, the rules returned have QUERY's head in the head
        and the stored instances of TABLENAMES in the body.
        """
        # This is different than abduction because instead of replacing
        #   a proof attempt with saving a literal, we want to save a literal
        #   after a successful proof attempt.
        assert False, "Not yet implemented"

    def abduce(self, query, tablenames, find_all=True):
        """Computes additional literals that if true would make
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
        when proving a negative literal is true.
        """
        assert compile.is_datalog(query), "Explain requires a formula"
        if compile.is_atom(query):
            literals = [query]
            output = query
        else:
            literals = query.body
            output = query.head
        # We need all the variables we will be using in the output, which
        #   here is just the head of QUERY (or QUERY itself if it is an atom)
        abductions = self.top_down_abduction(
            output.variables(), literals, find_all=find_all,
            save=lambda lit, binding: lit.table in tablenames)
        results = [compile.Rule(output.plug(abd.binding), abd.support)
                   for abd in abductions]
        self.log(query.tablename(), "abduction result:")
        self.log(query.tablename(), "\n".join([str(x) for x in results]))
        return results

    def consequences(self, filter=None, tablenames=None):
        """Return all the true instances of any table that is defined
        in this theory.  Default tablenames is DEFINED_TABLENAMES.
        """
        if tablenames is None:
            tablenames = self.defined_tablenames()
        results = set()
        # create queries: need table names and arities
        for table in tablenames:
            if filter is None or filter(table):
                arity = self.arity(table)
                vs = []
                for i in xrange(0, arity):
                    vs.append("x" + str(i))
                vs = [compile.Variable(var) for var in vs]
                query = compile.Literal(table, vs)
                results |= set(self.select(query))
        return results

    def top_down_evaluation(self, variables, literals,
                            binding=None, find_all=True):
        """Compute all bindings of VARIABLES that make LITERALS
        true according to the theory (after applying the unifier BINDING).
        If FIND_ALL is False, stops after finding one such binding.
        Returns a list of dictionary bindings.
        """
        # LOG.debug("CALL: top_down_evaluation(vars={}, literals={}, "
        #               "binding={})".format(
        #         iterstr(variables), iterstr(literals),
        #         str(binding)))
        results = self.top_down_abduction(variables, literals,
                                          binding=binding, find_all=find_all,
                                          save=None)
        # LOG.debug("EXIT: top_down_evaluation(vars={}, literals={}, "
        #               "binding={}) returned {}".format(
        #         iterstr(variables), iterstr(literals),
        #         str(binding), iterstr(results)))
        return [x.binding for x in results]

    def top_down_abduction(self, variables, literals, binding=None,
                           find_all=True, save=None):
        """Compute all bindings of VARIABLES that make LITERALS
        true according to the theory (after applying the
        unifier BINDING), if we add some number of additional
        literals.  Note: will not save any literals that are
        needed to prove a negated literal since the results
        would not make sense.  Returns a list of TopDownResults.
        """
        if binding is None:
            binding = self.new_bi_unifier()
        caller = self.TopDownCaller(variables, binding, self,
                                    find_all=find_all, save=save)
        if len(literals) == 0:
            self.top_down_finish(None, caller)
        else:
            # Note: must use same unifier in CALLER and CONTEXT
            context = self.TopDownContext(literals, 0, binding, None, 0)
            self.top_down_eval(context, caller)
        return list(set(caller.results))

    #########################################
    # Internal implementation

    def top_down_eval(self, context, caller):
        """Compute all instances of LITERALS (from LITERAL_INDEX and above)
        that are true according to the theory (after applying the
        unifier BINDING to LITERALS).  Returns False or an answer.
        """
        # no recursive rules, ever; this style of algorithm will not terminate
        lit = context.literals[context.literal_index]
        # LOG.debug("CALL: top_down_eval({}, {})".format(str(context),
        #     str(caller)))

        # abduction
        if caller.save is not None and caller.save(lit, context.binding):
            self.print_call(lit, context.binding, context.depth)
            # save lit and binding--binding may not be fully flushed out
            #   when we save (or ever for that matter)
            caller.support.append((lit, context.binding))
            self.print_save(lit, context.binding, context.depth)
            success = self.top_down_finish(context, caller)
            caller.support.pop()  # pop in either case
            if success:
                return True
            else:
                self.print_fail(lit, context.binding, context.depth)
                return False

        # regular processing
        if lit.is_negated():
            # LOG.debug("{} is negated".format(str(lit)))
            # recurse on the negation of the literal
            plugged = lit.plug(context.binding)
            assert plugged.is_ground(), \
                "Negated literal not ground when evaluated: " + str(plugged)
            self.print_call(lit, context.binding, context.depth)
            new_context = self.TopDownContext(
                [lit.complement()], 0, context.binding, None,
                context.depth + 1)
            new_caller = self.TopDownCaller(caller.variables, caller.binding,
                                            caller.theory, find_all=False,
                                            save=None)
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
        elif lit.tablename() == 'true':
            self.print_call(lit, context.binding, context.depth)
            return self.top_down_finish(context, caller, redo=False)
        elif lit.tablename() == 'false':
            self.print_fail(lit, context.binding, context.depth)
            return False
        elif self.cbcmap.check_if_builtin_by_name(lit.tablename(),
                                                  len(lit.arguments)):
            self.print_call(lit, context.binding, context.depth)
            cbc = self.cbcmap.return_builtin_pred(lit.tablename())
            builtin_code = cbc.code
            # copy arguments into variables
            # PLUGGED is an instance of compile.Literal
            plugged = lit.plug(context.binding)
            # print "plugged: " + str(plugged)
            # PLUGGED.arguments is a list of compile.Term
            # create args for function
            args = []
            for i in xrange(0, cbc.num_inputs):
                assert plugged.arguments[i].is_object(), \
                    ("Builtins must be evaluated only after their "
                     "inputs are ground: {} with num-inputs {}".format(
                         str(plugged), cbc.num_inputs))
                args.append(plugged.arguments[i].name)
            # evaluate builtin: must return number, string, or iterable
            #    of numbers/strings
            # print "args: " + str(args)
            try:
                result = self.cbcmap.eval_builtin(builtin_code, args)
            except Exception as e:
                errmsg = "Error in builtin: " + str(e)
                self.print_note(lit, context.binding, context.depth, errmsg)
                self.print_fail(lit, context.binding, context.depth)
                return False

            # self.print_note(lit, context.binding, context.depth,
            #                 "Result: " + str(result))
            success = None
            undo = []
            if self.cbcmap.builtin_num_outputs(lit.table) > 0:
                # with return values, local success means we can bind
                #  the results to the return value arguments
                if isinstance(result, (int, long, float, basestring)):
                    result = [result]
                # Turn result into normal objects
                result = [compile.Term.create_from_python(x) for x in result]
                # adjust binding list
                unifier = self.new_bi_unifier()
                undo = bi_unify_lists(result,
                                      unifier,
                                      lit.arguments[cbc.num_inputs:],
                                      context.binding)
                # print "unifier: " + str(undo)
                success = undo is not None
            else:
                # without return values, local success means
                #   result was True according to Python
                success = bool(result)

            # print "success: " + str(success)

            if not success:
                self.print_fail(lit, context.binding, context.depth)
                unify.undo_all(undo)
                return False

            # otherwise, try to finish proof.  If success, return True
            if self.top_down_finish(context, caller, redo=False):
                unify.undo_all(undo)
                return True
            # if fail, return False.
            else:
                unify.undo_all(undo)
                self.print_fail(lit, context.binding, context.depth)
                return False
        else:
            return self.top_down_truth(context, caller)

    def top_down_truth(self, context, caller):
        """Do top-down evaluation over the root theory at which
        the call was made and all the included theories.
        """
        return caller.theory.top_down_includes(context, caller)

    def top_down_includes(self, context, caller):
        """Top-down evaluation of all the theories included in this theory."""
        is_true = self.top_down_th(context, caller)
        if is_true and not caller.find_all:
            return True
        for th in self.includes:
            is_true = th.top_down_includes(context, caller)
            if is_true and not caller.find_all:
                return True
        return False

    def top_down_th(self, context, caller):
        """Top-down evaluation for the rules in SELF.CONTENTS."""
        # LOG.debug("top_down_th({})".format(str(context)))
        lit = context.literals[context.literal_index]
        self.print_call(lit, context.binding, context.depth)
        for rule in self.head_index(lit.table):
            unifier = self.new_bi_unifier()
            # Prefer to bind vars in rule head
            undo = self.bi_unify(self.head(rule), unifier, lit,
                                 context.binding)
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
                new_context = self.TopDownContext(
                    rule.body, 0, unifier, context, context.depth + 1)
                if self.top_down_eval(new_context, caller):
                    unify.undo_all(undo)
                    if not caller.find_all:
                        return True
                else:
                    unify.undo_all(undo)
        self.print_fail(lit, context.binding, context.depth)
        return False

    def top_down_finish(self, context, caller, redo=True):
        """Helper that is called once top_down successfully completes
        a proof for a literal.  Handles (i) continuing search
        for those literals still requiring proofs within CONTEXT,
        (ii) adding solutions to CALLER once all needed proofs have
        been found, and (iii) printing out Redo/Exit during tracing.
        Returns True if the search is finished and False otherwise.
        Temporary, transparent modification of CONTEXT.
        """
        if context is None:
            # Found an answer; now store it
            if caller is not None:
                # flatten bindings and store before we undo
                # copy caller.support and store before we undo
                binding = {}
                for var in caller.variables:
                    binding[var] = caller.binding.apply(var)
                result = self.TopDownResult(
                    binding, [support[0].plug(support[1], caller=caller)
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
        self.log(literal.table, "{}Call: {}".format("| " * depth,
                 literal.plug(binding)))

    def print_exit(self, literal, binding, depth):
        self.log(literal.table, "{}Exit: {}".format("| " * depth,
                 literal.plug(binding)))

    def print_save(self, literal, binding, depth):
        self.log(literal.table, "{}Save: {}".format("| " * depth,
                 literal.plug(binding)))

    def print_fail(self, literal, binding, depth):
        self.log(literal.table, "{}Fail: {}".format("| " * depth,
                 literal.plug(binding)))
        return False

    def print_redo(self, literal, binding, depth):
        self.log(literal.table, "{}Redo: {}".format("| " * depth,
                 literal.plug(binding)))
        return False

    def print_note(self, literal, binding, depth, msg):
        self.log(literal.table, "{}Note: {}".format("| " * depth,
                 msg))

    #########################################
    # Routines for specialization

    @classmethod
    def new_bi_unifier(cls, dictionary=None):
        """Return a unifier compatible with unify.bi_unify."""
        return unify.BiUnifier(dictionary=dictionary)
            # lambda (index):
            # compile.Variable("x" + str(index)), dictionary=dictionary)

    def arity(self, tablename):
        """Return the number of arguments TABLENAME takes or None if
        unknown because TABLENAME is not defined here.
        """
        # assuming a fixed arity for all tables
        formulas = self.head_index(tablename)
        if len(formulas) == 0:
            return None
        first = formulas[0]
        # should probably have an overridable function for computing
        #   the arguments of a head.  Instead we assume heads have .arguments
        return len(self.head(first).arguments)

    def defined_tablenames(self):
        """This routine returns the list of all table names that are
        defined/written to in this theory.
        """
        return self.contents.keys()

    def head_index(self, table):
        """This routine must return all the formulas pertinent for
        top-down evaluation when a literal with TABLE is at the top
        of the stack.
        """
        if table not in self.contents:
            return []
        return self.contents[table]

    def head(self, formula):
        """Given a FORMULA, return the thing to unify against.
        Usually, FORMULA is a compile.Rule, but it could be anything
        returned by HEAD_INDEX.
        """
        return formula.head

    def body(self, formula):
        """Given a FORMULA, return a list of things to push onto the
        top-down eval stack.
        """
        return formula.body

    def bi_unify(self, head, unifier1, body_element, unifier2):
        """Given something returned by self.head HEAD and an element in
        the return of self.body BODY_ELEMENT, modify UNIFIER1 and UNIFIER2
        so that HEAD.plug(UNIFIER1) == BODY_ELEMENT.plug(UNIFIER2).
        Returns changes that can be undone via unify.undo-all.
        """
        return unify.bi_unify_atoms(head, unifier1, body_element, unifier2)


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
            # LOG.debug("Pf: Comparing {} and {}: {}".format(
            #     str(self), str(other), result))
            # LOG.debug("Pf: {} == {} is {}".format(
            #     str(self.binding), str(other.binding),
            #     self.binding == other.binding))
            # LOG.debug("Pf: {} == {} is {}".format(
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
            # LOG.debug("PC: Subtracting {} and {}".format(str(self),
            #               str(other)))
            remaining = []
            for proof in self.contents:
                if proof not in other.contents:
                    remaining.append(proof)
            self.contents = remaining
            return self

        def __ior__(self, other):
            if other is None:
                return
            # LOG.debug("PC: Unioning {} and {}".format(str(self),
            #               str(other)))
            for proof in other.contents:
                # LOG.debug("PC: Considering {}".format(str(proof)))
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
                    # LOG.debug("Proof {} makes {} not >= {}".format(
                    #     str(proof), str(self), iterstr(iterable)))
                    return False
            return True

        def __le__(self, iterable):
            for proof in self.contents:
                if proof not in iterable:
                    # LOG.debug("Proof {} makes {} not <= {}".format(
                    #     str(proof), str(self), iterstr(iterable)))
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
            # LOG.debug("DBTuple matching {} against atom {} in {}".format(
            #     str(self), iterstr(atom.arguments), str(unifier)))
            if len(self.tuple) != len(atom.arguments):
                return None
            changes = []
            for i in xrange(0, len(atom.arguments)):
                val, binding = unifier.apply_full(atom.arguments[i])
                # LOG.debug(
                #     "val({})={} at {}; comparing to object {}".format(
                #     str(atom.arguments[i]), str(val), str(binding),
                #     str(self.tuple[i])))
                if val.is_variable():
                    changes.append(binding.add(
                        val, compile.Term.create_from_python(self.tuple[i]),
                        None))
                else:
                    if val.name != self.tuple[i]:
                        unify.undo_all(changes)
                        return None
            return changes

    def __init__(self, name=None, abbr=None, module_schemas=None):
        super(Database, self).__init__(
            name=name, abbr=abbr, module_schemas=module_schemas)
        self.data = {}

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
        """Return all table names occurring in this theory.
        """
        return self.data.keys()

    # overloads for TopDownTheory so we can properly use the
    #    top_down_evaluation routines
    def defined_tablenames(self):
        return self.data.keys()

    def head_index(self, table):
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
        """Applies all of EVENTS to the DB.  Each event
        is either an insert or a delete.
        """
        changes = []
        for event in events:
            changes.extend(self.modify(event))
        return changes

    def update_would_cause_errors(self, events):
        """Return a list of compile.CongressException if we were
        to apply the events EVENTS to the current policy.
        """
        self.log(None, "update_would_cause_errors " + iterstr(events))
        errors = []
        for event in events:
            if not compile.is_atom(event.formula):
                errors.append(compile.CongressException(
                    "Non-atomic formula is not permitted: {}".format(
                        str(event.formula))))
            else:
                errors.extend(compile.fact_errors(
                    event.formula, self.module_schemas))
        return errors

    def modify(self, event):
        """Inserts/deletes ATOM and returns a list of changes that
        were caused. That list contains either 0 or 1 Event.
        """
        assert compile.is_atom(event.formula), "Modify requires Atom"
        atom = event.formula
        self.log(atom.table, "Modify: {}".format(str(atom)))
        if self.is_noop(event):
            self.log(atom.table, "Event {} is a noop".format(str(event)))
            return []
        if event.insert:
            self.insert_actual(atom, proofs=event.proofs)
        else:
            self.delete_actual(atom, proofs=event.proofs)
        return [event]

    def insert_actual(self, atom, proofs=None):
        """Workhorse for inserting ATOM into the DB, along with proofs
        explaining how ATOM was computed from other tables.
        """
        assert compile.is_atom(atom), "Insert requires Atom"
        table, dbtuple = self.atom_to_internal(atom, proofs)
        self.log(table, "Insert: {}".format(str(atom)))
        if table not in self.data:
            self.data[table] = [dbtuple]
            self.log(atom.table, "First tuple in table {}".format(table))
            return
        else:
            for existingtuple in self.data[table]:
                assert(existingtuple.proofs is not None)
                if existingtuple.tuple == dbtuple.tuple:
                    assert(existingtuple.proofs is not None)
                    existingtuple.proofs |= dbtuple.proofs
                    assert(existingtuple.proofs is not None)
                    return
            self.data[table].append(dbtuple)

    def delete_actual(self, atom, proofs=None):
        """Workhorse for deleting ATOM from the DB, along with the proofs
        that are no longer true.
        """
        assert compile.is_atom(atom), "Delete requires Atom"
        self.log(atom.table, "Delete: {}".format(str(atom)))
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

class NonrecursiveRuleTheory(TopDownTheory):
    """A non-recursive collection of Rules."""

    def __init__(self, rules=None, name=None, abbr=None, module_schemas=None):
        super(NonrecursiveRuleTheory, self).__init__(
            name=name, abbr=abbr, module_schemas=module_schemas)
        # dictionary from table name to list of rules with that table in head
        self.contents = {}
        if rules is not None:
            for rule in rules:
                self.insert(rule)

    # External Interface

    # SELECT implemented by TopDownTheory

    def insert(self, rule):
        changes = self.update([Event(formula=rule, insert=True)])
        return [event.formula for event in changes]

    def delete(self, rule):
        changes = self.update([Event(formula=rule, insert=False)])
        return [event.formula for event in changes]

    def update(self, events):
        """Apply EVENTS and return the list of EVENTS that actually
           changed the theory.  Each event is the insert or delete of
           a policy statement.
           """
        changes = []
        self.log(None, "Update " + iterstr(events))
        for event in events:
            if event.insert:
                if self.insert_actual(event.formula):
                    changes.append(event)
            else:
                if self.delete_actual(event.formula):
                    changes.append(event)
        return changes

    def update_would_cause_errors(self, events):
        """Return a list of compile.CongressException if we were
        to apply the insert/deletes of policy statements dictated by
        EVENTS to the current policy.
        """
        self.log(None, "update_would_cause_errors " + iterstr(events))
        errors = []
        current = set(self.policy())
        for event in events:
            if not compile.is_datalog(event.formula):
                errors.append(compile.CongressException(
                    "Non-formula found: {}".format(
                        str(event.formula))))
            else:
                if event.formula.is_atom():
                    errors.extend(compile.fact_errors(
                        event.formula, self.module_schemas))
                else:
                    errors.extend(compile.rule_errors(
                        event.formula, self.module_schemas))
                if event.insert:
                    current.add(event.formula)
                else:
                    current.discard(event.formula)
        if compile.is_recursive(current):
            errors.append(compile.CongressException(
                "Rules are recursive"))
        return errors

    def define(self, rules):
        """Empties and then inserts RULES.
        """
        self.empty()
        return self.update([Event(formula=rule, insert=True)
                            for rule in rules])

    def empty(self):
        """Deletes contents of theory.
        """
        self.contents = {}

    def policy(self):
        # eliminate all rules with empty bodies
        return [p for p in self.content() if len(p.body) > 0]

    def get_arity_self(self, tablename):
        if tablename not in self.contents:
            return None
        if len(self.contents[tablename]) == 0:
            return None
        return len(self.contents[tablename][0].head.arguments)

    # Internal Interface

    def insert_actual(self, rule):
        """Insert RULE and return True if there was a change.
        """
        if compile.is_atom(rule):
            rule = compile.Rule(rule, [], rule.location)
        self.log(rule.head.table, "Insert: {}".format(str(rule)))
        table = rule.head.table
        if table in self.contents:
            if rule not in self.contents[table]:  # eliminate dups
                self.contents[table].append(rule)
                return True
            return False
        else:
            self.contents[table] = [rule]
            return True

    def delete_actual(self, rule):
        """Delete RULE and return True if there was a change.
        """
        if compile.is_atom(rule):
            rule = compile.Rule(rule, [], rule.location)
        self.log(rule.head.table, "Delete: {}".format(str(rule)))
        table = rule.head.table
        if table in self.contents:
            try:
                self.contents[table].remove(rule)
                return True
            except ValueError:
                return False
        return False

    def content(self, tablenames=None):
        if tablenames is None:
            tablenames = self.contents.keys()
        results = []
        for table in tablenames:
            if table in self.contents:
                results.extend(self.contents[table])
        return results


class ActionTheory(NonrecursiveRuleTheory):
    """Same as NonrecursiveRuleTheory except it has fewer
    constraints on the permitted rules.  Still working out the details.
    """
    def update_would_cause_errors(self, events):
        """Return a list of compile.CongressException if we were
        to apply the events EVENTS to the current policy.
        """
        self.log(None, "update_would_cause_errors " + iterstr(events))
        errors = []
        current = set(self.policy())
        for event in events:
            if not compile.is_datalog(event.formula):
                errors.append(compile.CongressException(
                    "Non-formula found: {}".format(
                        str(event.formula))))
            else:
                if event.formula.is_atom():
                    errors.extend(compile.fact_errors(
                        event.formula, self.module_schemas))
                else:
                    pass
                    # Should put this back in place, but there are some
                    # exceptions that we don't handle right now.
                    # Would like to mark some tables as only being defined
                    #   for certain bound/free arguments and take that into
                    #   account when doing error checking.
                    # errors.extend(compile.rule_negation_safety(event.formula))
                if event.insert:
                    current.add(event.formula)
                else:
                    current.remove(event.formula)
        if compile.is_recursive(current):
            errors.append(compile.CongressException(
                "Rules are recursive"))
        return errors


class DeltaRuleTheory (Theory):
    """A collection of DeltaRules.  Not useful by itself as a policy."""
    def __init__(self, name=None, abbr=None, module_schemas=None):
        super(DeltaRuleTheory, self).__init__(
            name=name, abbr=abbr, module_schemas=module_schemas)
        # dictionary from table name to list of rules with that table as
        # trigger
        self.contents = {}
        # dictionary from delta_rule to the rule from which it was derived
        self.originals = set()
        # dictionary from table name to number of rules with that table in
        # head
        self.views = {}
        # all tables
        self.all_tables = {}

    def modify(self, event):
        """Insert/delete the compile.Rule RULE into the theory.
        Return list of changes (either the empty list or
        a list including just RULE).
        """
        self.log(None, "DeltaRuleTheory.modify " + str(event.formula))
        self.log(None, "originals: " + iterstr(self.originals))
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
        assert compile.is_regular_rule(rule), \
            "DeltaRuleTheory only takes rules"
        self.log(rule.tablename(), "Insert: {}".format(str(rule)))
        if rule in self.originals:
            self.log(None, iterstr(self.originals))
            return False
        self.log(rule.tablename(), "Insert 2: {}".format(str(rule)))
        for delta in self.compute_delta_rules([rule]):
            self.reorder(delta)
            self.insert_delta(delta)
        self.originals.add(rule)
        return True

    def insert_delta(self, delta):
        """Insert a delta rule."""
        self.log(None, "Inserting delta rule {}".format(str(delta)))
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
        if delta.trigger.table not in self.contents:
            self.contents[delta.trigger.table] = [delta]
        else:
            self.contents[delta.trigger.table].append(delta)

    def delete(self, rule):
        """Delete a compile.Rule from theory.
        Assumes that COMPUTE_DELTA_RULES is deterministic.
        Returns True iff the theory changed.
        """
        self.log(rule.tablename(), "Delete: {}".format(str(rule)))
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
        if delta.trigger.table not in self.contents:
            return
        self.contents[delta.trigger.table].remove(delta)

    def policy(self):
        return self.originals

    def get_arity_self(self, tablename):
        for p in self.originals:
            if p.head.table == tablename:
                return len(p.head.arguments)
        return None

    def __str__(self):
        return str(self.contents)

    def rules_with_trigger(self, table):
        """Return the list of DeltaRules that trigger on the given TABLE."""
        if table not in self.contents:
            return []
        else:
            return self.contents[table]

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
        """Return new list of formulas that is equivalent to
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
            LOG.debug("eliminating self joins from {}".format(rule))
            occurrences = {}  # for just this rule
            for atom in rule.body:
                table = atom.table
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
                        global_self_joins[tablearity] = \
                            max(occurrences[tablearity] - 1,
                                global_self_joins[tablearity])
            results.append(rule)
            LOG.debug("final rule: {}".format(str(rule)))
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
                LOG.debug("Adding rule {}".format(results[-1]))
        return results

    @classmethod
    def compute_delta_rules(cls, formulas):
        """Assuming FORMULAS has no self-joins, return a list of DeltaRules
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
            for literal in rule.body:
                newbody = [lit for lit in rule.body if lit is not literal]
                delta_rules.append(
                    DeltaRule(literal, rule.head, newbody, rule))
        return delta_rules

    @classmethod
    def reorder(cls, delta):
        """Given a delta rule DELTA, re-order its body for efficient
        and correct computation.
        """
        # ensure negatives come after positives
        positives = [lit for lit in delta.body if not lit.is_negated()]
        negatives = [lit for lit in delta.body if lit.is_negated()]
        positives.extend(negatives)
        delta.body = positives


class MaterializedViewTheory(TopDownTheory):
    """A theory that stores the table contents of views explicitly.
    Relies on included theories to define the contents of those
    tables not defined by the rules of the theory.
    Recursive rules are allowed.
    """

    def __init__(self, name=None, abbr=None, module_schemas=None):
        super(MaterializedViewTheory, self).__init__(
            name=name, abbr=abbr, module_schemas=module_schemas)
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
            assert compile.is_datalog(event.formula), \
                "Non-formula not allowed: {}".format(str(event.formula))
            self.enqueue_any(event)
        changes = self.process_queue()
        return changes

    def update_would_cause_errors(self, events):
        """Return a list of compile.CongressException if we were
        to apply the events EVENTS to the current policy.
        """
        self.log(None, "update_would_cause_errors " + iterstr(events))
        errors = []
        current = set(self.policy())  # copy so can modify and discard
        # compute new rule set
        for event in events:
            assert compile.is_datalog(event.formula), \
                "update_would_cause_errors operates only on objects"
            self.log(None, "Updating {}".format(event.formula))
            if event.formula.is_atom():
                errors.extend(compile.fact_errors(
                    event.formula, self.module_schemas))
            else:
                errors.extend(compile.rule_errors(
                    event.formula, self.module_schemas))
            if event.insert:
                current.add(event.formula)
            elif event.formula in current:
                current.remove(event.formula)
        # check for stratified
        if not compile.is_stratified(current):
            errors.append(compile.CongressException(
                "Rules are not stratified"))
        return errors

    def explain(self, query, tablenames, find_all):
        """Returns None if QUERY is False in theory.  Otherwise returns
        a list of proofs that QUERY is true.
        """
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
        self.log(query.table, "Explaining {}".format(str(query)), depth)
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
                 "modify returns {}".format(iterstr(changes)))
        return changes

    def enqueue_any(self, event):
        """Processing rules is a bit different than processing atoms
        in that they generate additional events that we want
        to process either before the rule is deleted or after
        it is inserted.  PROCESS_QUEUE is similar but assumes
        that only the data will cause propagations (and ignores
        included theories).
        """
        # Note: all included theories must define MODIFY
        formula = event.formula
        if formula.is_atom():
            self.log(formula.tablename(),
                     "compute/enq: atom {}".format(str(formula)))
            assert not self.is_view(formula.table), \
                "Cannot directly modify tables computed from other tables"
            # self.log(formula.table, "{}: {}".format(text, str(formula)))
            self.enqueue(event)
            return []
        else:
            # rules do not need to talk to included theories because they
            #   only generate events for views
            # need to eliminate self-joins here so that we fill all
            #   the tables introduced by self-join elimination.
            for rule in DeltaRuleTheory.eliminate_self_joins([formula]):
                DeltaRuleTheory.reorder(rule)
                new_event = Event(formula=rule, insert=event.insert,
                                  target=event.target)
                self.enqueue(new_event)
            return []

    def enqueue(self, event):
        self.log(event.tablename(), "Enqueueing: {}".format(str(event)))
        self.queue.enqueue(event)

    def process_queue(self):
        """Data and rule propagation routine.
        Returns list of events that were not noops
        """
        self.log(None, "Processing queue")
        history = []
        while len(self.queue) > 0:
            event = self.queue.dequeue()
            self.log(event.tablename(), "Dequeued " + str(event))
            if compile.is_regular_rule(event.formula):
                changes = self.delta_rules.modify(event)
                if len(changes) > 0:
                    history.extend(changes)
                    bindings = self.top_down_evaluation(
                        event.formula.variables(), event.formula.body)
                    self.log(event.formula.tablename(),
                             ("new bindings after top-down: " +
                              iterstr(bindings)))
                    self.process_new_bindings(bindings, event.formula.head,
                                              event.insert, event.formula)
            else:
                self.propagate(event)
                history.extend(self.database.modify(event))
            self.log(event.tablename(), "History: " + iterstr(history))
        return history

    def propagate(self, event):
        """Computes events generated by EVENT and the DELTA_RULES,
        and enqueues them.
        """
        self.log(event.formula.table,
                 "Processing event: {}".format(str(event)))
        applicable_rules = self.delta_rules.rules_with_trigger(
            event.formula.table)
        if len(applicable_rules) == 0:
            self.log(event.formula.table, "No applicable delta rule")
        for delta_rule in applicable_rules:
            self.propagate_rule(event, delta_rule)

    def propagate_rule(self, event, delta_rule):
        """Compute and enqueue new events generated by EVENT and DELTA_RULE.
        """
        self.log(event.formula.table,
                 "Processing event {} with rule {}".format(
                 str(event), str(delta_rule)))

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
                 "binding list for event and delta-rule trigger: {}".format(
                 str(binding)))
        bindings = self.top_down_evaluation(
            delta_rule.variables(), delta_rule.body, binding)
        self.log(event.formula.table, "new bindings after top-down: {}".format(
            ",".join([str(x) for x in bindings])))

        if delta_rule.trigger.is_negated():
            insert_delete = not event.insert
        else:
            insert_delete = event.insert
        self.process_new_bindings(bindings, delta_rule.head,
                                  insert_delete, delta_rule.original)

    def process_new_bindings(self, bindings, atom, insert, original_rule):
        """For each of BINDINGS, apply to ATOM, and enqueue it as an insert if
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
        self.log(atom.table, "new tuples generated: " + iterstr(new_atoms))

        # enqueue each distinct generated tuple, recording appropriate bindings
        for new_atom in new_atoms:
            # self.log(event.table,
            #          "new_tuple {}: {}".format(str(new_tuple),
            #          str(new_tuples[new_tuple])))
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
        """Return the list of tables that are mentioned in the rules but
        for which there are no rules with those tables in the head.
        """
        return self.delta_rules.base_tables()

    def top_down_th(self, context, caller):
        return self.database.top_down_th(context, caller)

    def content(self, tablenames=None):
        return self.database.content(tablenames=tablenames)


##############################################################################
# Runtime
##############################################################################

class Runtime (object):
    """Runtime for the Congress policy language.  Only have one instantiation
    in practice, but using a class is natural and useful for testing.
    """
    # Names of theories
    CLASSIFY_THEORY = "classification"
    SERVICE_THEORY = "service"
    ACTION_THEORY = "action"
    ENFORCEMENT_THEORY = "enforcement"
    DATABASE = "database"
    ACCESSCONTROL_THEORY = "accesscontrol"
    DEFAULT_THEORY = CLASSIFY_THEORY

    def __init__(self):
        # tracer object
        self.tracer = Tracer()
        # record execution
        self.logger = ExecutionLogger()
        # collection of theories
        self.theory = {}
        # schemas for each module
        self.module_schemas = compile.ModuleSchemas()

        # DEFAULT_THEORY
        self.theory[self.DEFAULT_THEORY] = NonrecursiveRuleTheory(
            name=self.CLASSIFY_THEORY, abbr='Clas',
            module_schemas=self.module_schemas)

        # ACTION_THEORY
        self.theory[self.ACTION_THEORY] = ActionTheory(
            name=self.ACTION_THEORY, abbr='Action')

    def get_target(self, name):
        if name is None:
            name = self.CLASSIFY_THEORY
        if name not in self.theory:
            raise compile.CongressException("Unknown policy " + str(name))
        return self.theory[name]

    def get_action_names(self, target):
        """Return a list of the names of action tables."""
        if target not in self.theory:
            return []
        actionth = self.theory[target]
        actions = actionth.select(compile.parse1('action(x)'))
        return [action.arguments[0].name for action in actions]

    def log(self, table, msg, depth=0):
        self.tracer.log(table, "RT    : " + msg, depth)

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
        """Dump each theory into its own file within the
        directory PATH. The name of the file is the name of
        the theory.
        """
        for name in self.theory:
            self.dump_file(os.path.join(path, name), name)

    def dump_file(self, filename, target):
        """Dump the contents of the theory called TARGET into
        the filename FILENAME.
        """
        d = os.path.dirname(filename)
        if not os.path.exists(d):
            os.makedirs(d)
        with open(filename, "w") as f:
            f.write(str(self.theory[target]))

    def load_dir(self, path):
        """Load each of the files appearing in directory PATH
        into its own theory, named the same as the filename.
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
        """Compile the given FILENAME and insert each of the statements
        into the runtime.  Assumes that FILENAME includes no modals.
        """
        formulas = compile.parse_file(
            filename, module_schemas=self.module_schemas)
        return self.update(
            [Event(formula=x, insert=True) for x in formulas], target)

    def set_schema(self, name, schema):
        """Set the schema for module NAME to be SCHEMA."""
        self.module_schemas[name] = compile.Schema(schema)

    def select(self, query, target=None, trace=False):
        """Event handler for arbitrary queries. Returns the set of
        all instantiated QUERY that are true.
        """
        if isinstance(query, basestring):
            return self.select_string(query, self.get_target(target), trace)
        elif isinstance(query, tuple):
            return self.select_tuple(query, self.get_target(target), trace)
        else:
            return self.select_obj(query, self.get_target(target), trace)

    def explain(self, query, tablenames=None, find_all=False, target=None):
        """Event handler for explanations.  Given a ground query and
        a collection of tablenames that we want the explanation in
        terms of, return proof(s) that the query is true. If
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

    def initialize(self, tablenames, formulas, target=None):
        """Event handler for (re)initializing a collection of tables."""
        # translate FORMULAS into list of formula objects
        if isinstance(formulas, basestring):
            actual_formulas = self.parse(formulas)
        else:
            actual_formulas = []
            for formula in formulas:
                if isinstance(formula, basestring):
                    formula = self.parse1(formula)
                elif isinstance(formula, tuple):
                    formula = compile.Literal.create_from_iter(formula)
                actual_formulas.append(formula)
        assert all(x.is_atom() for x in actual_formulas)
        formula_tables = set([x.table for x in actual_formulas])
        tablenames = set(tablenames) | formula_tables
        self.log(None, "Initializing tables {} with {}".format(
            iterstr(tablenames), iterstr(actual_formulas)))
        # implement initialization by computing the requisite
        #   update.
        theory = self.get_target(target)
        old = set(theory.content(tablenames=tablenames))
        new = set(actual_formulas)
        to_add = new - old
        to_rem = old - new
        to_add = [Event(formula) for formula in to_add]
        to_rem = [Event(formula, insert=False) for formula in to_rem]
        self.log(None, "Initialize converted to update with {} and {}".format(
            iterstr(to_add), iterstr(to_rem)))
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
        """Event handler for applying an arbitrary sequence
        of insert/deletes.  If TARGET is supplied, it overrides
        the targets in SEQUENCE.
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

    def remediate(self, formula):
        """Event handler for remediation."""
        if isinstance(formula, basestring):
            return self.remediate_string(formula)
        elif isinstance(formula, tuple):
            return self.remediate_tuple(formula)
        else:
            return self.remediate_obj(formula)

    def simulate(self, query, theory, sequence, action_theory, delta=False,
                 trace=False):
        """Event handler for simulation: the computation of a query given an
        action sequence.  That sequence can include updates to atoms,
        updates to rules, and action invocations.  Returns a collection
        of Literals (as a string if the query and sequence are strings
        or as a Python collection otherwise).
        If delta is True, the return is a collection of Literals where
        each tablename ends with either + or - to indicate whether
        that fact was added or deleted.
        Example atom update: q+(1) or q-(1)
        Example rule update: p+(x) :- q(x) or p-(x) :- q(x)
        Example action invocation:
           create_network(17), options:value(17, "name", "net1") :- true
        """
        assert self.get_target(theory) is not None, "Theory must be known"
        assert self.get_target(action_theory) is not None, \
            "Action theory must be known"
        if isinstance(query, basestring) and isinstance(sequence, basestring):
            return self.simulate_string(query, theory, sequence, action_theory,
                                        delta, trace)
        else:
            return self.simulate_obj(query, theory, sequence, action_theory,
                                     delta, trace)

    def execute(self, action_sequence):
        """Event handler for execute: execute a sequence of ground actions
        in the real world.
        """
        if isinstance(action_sequence, basestring):
            return self.execute_string(action_sequence)
        else:
            return self.execute_obj(action_sequence)

    def access_control(self, action, support=''):
        """Event handler for making access_control request.  ACTION
        is an atom describing a proposed action instance.
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
        """Checks if applying EVENTS is permitted and if not
           returns a list of errors.  If it is permitted, it
           applies it and then returns a list of changes.
           In both cases, the return is a 2-tuple (if-permitted, list).
           """
        self.log(None, "Updating with " + iterstr(events))
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
        """Return a dictionary mapping event.target to the list of events
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
        """Given list of events with different event.target values,
        change each event.target so that the events are routed to the
        proper place.
        """
        by_target = self.group_events_by_target(events)
        for target, target_events in by_target.items():
            newth = self.compute_route(target_events, target)
            for event in target_events:
                event.target = newth

    ##########################
    # Execute actions

    def execute_string(self, actions_string):
        self.execute_obj(self.parse(actions_string))

    def execute_obj(self, actions):
        """Executes the list of ACTION instances one at a time.
        For now, our execution is just logging.
        """
        LOG.debug("Executing: " + iterstr(actions))
        assert all(compile.is_atom(action) and action.is_ground()
                   for action in actions)
        action_names = self.get_action_names()
        assert all(action.table in action_names for action in actions)
        for action in actions:
            if not action.is_ground():
                if self.logger is not None:
                    self.logger.warn("Unground action to execute: {}".format(
                                     str(action)))
                continue
            if self.logger is not None:
                self.logger.info(str(action))

    ##########################
    # Analyze (internal) state

    # select
    def select_string(self, policy_string, theory, trace):
        policy = self.parse(policy_string)
        assert len(policy) == 1, \
            "Queries can have only 1 statement: {}".format(
            [str(x) for x in policy])
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
        """Find a collection of action invocations that if executed
        result in FORMULA becoming false.
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
        self.log(None, "Leaves: {}".format(iterstr(leaves)))
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
        """Both THEORY and ACTION_THEORY are names of theories.
        Both QUERY and SEQUENCE are parsed.
        """
        assert compile.is_datalog(query), "Query must be formula"
        # Each action is represented as a rule with the actual action
        #    in the head and its supporting data (e.g. options) in the body
        assert all(compile.is_extended_datalog(x) for x in sequence), \
            "Sequence must be an iterable of Rules"
        th_object = self.get_target(theory)

        if trace:
            old_tracer = self.get_tracer()
            tracer = StringTracer()  # still LOG.debugs trace
            tracer.trace('*')     # trace everything
            self.set_tracer(tracer)

        # if computing delta, query the current state
        if delta:
            self.log(query.tablename(), "** Simulate: Querying {}".format(
                str(query)))
            oldresult = th_object.select(query)
            self.log(query.tablename(), "Original result of {} is {}".format(
                str(query), iterstr(oldresult)))

        # apply SEQUENCE
        self.log(query.tablename(), "** Simulate: Applying sequence {}".format(
            iterstr(sequence)))
        undo = self.project(sequence, theory, action_theory)

        # query the resulting state
        self.log(query.tablename(), "** Simulate: Querying {}".format(
            str(query)))
        result = th_object.select(query)
        self.log(query.tablename(), "Result of {} is {}".format(
            str(query), iterstr(result)))
        # rollback the changes
        self.log(query.tablename(), "** Simulate: Rolling back")
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
        # LOG.debug("react to: " + iterstr(changes))
        actions = self.get_action_names()
        formulas = [change.formula for change in changes
                    if (isinstance(change, Event)
                        and change.is_insert()
                        and change.formula.is_atom()
                        and change.tablename() in actions)]
        # LOG.debug("going to execute: " + iterstr(formulas))
        self.execute(formulas)

    def data_listeners(self):
        return [self.theory[self.ENFORCEMENT_THEORY]]

    def compute_route(self, events, theory):
        """When a formula is inserted/deleted (in OPERATION) into a THEORY,
        it may need to be rerouted to another theory.  This function
        computes that rerouting.  Returns a Theory object.
        """
        self.log(None, "Computing route for theory {} and events {}".format(
            theory.name, iterstr(events)))
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
        """Apply the list of updates SEQUENCE, where actions are described
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
        self.log(None, "Actions: " + iterstr(actions))
        undos = []         # a list of updates that will undo SEQUENCE
        self.log(None, "Project: " + iterstr(sequence))
        last_results = []
        for formula in sequence:
            self.log(None, "** Updating with {}".format(str(formula)))
            self.log(None, "Actions: " + iterstr(actions))
            self.log(None, "Last_results: " + iterstr(last_results))
            tablename = formula.tablename()
            if tablename not in actions:
                if not formula.is_update():
                    raise compile.CongressException(
                        "Sequence contained non-action, non-update: " +
                        str(formula))
                updates = [formula]
            else:
                self.log(tablename, "Projecting " + str(formula))
                # define extension of current Actions theory
                if formula.is_atom():
                    assert formula.is_ground(), \
                        "Projection atomic updates must be ground"
                    assert not formula.is_negated(), \
                        "Projection atomic updates must be positive"
                    newth.define([formula])
                else:
                    # instantiate action using prior results
                    newth.define(last_results)
                    self.log(tablename,
                             "newth (with prior results) {} ".format(
                             iterstr(newth.content())))
                    bindings = actth.top_down_evaluation(
                        formula.variables(), formula.body, find_all=False)
                    if len(bindings) == 0:
                        continue
                    grounds = formula.plug_heads(bindings[0])
                    grounds = [act for act in grounds if act.is_ground()]
                    assert all(not lit.is_negated() for lit in grounds)
                    newth.define(grounds)
                self.log(tablename,
                         "newth contents (after action insertion): {}".format(
                         iterstr(newth.content())))
                # self.log(tablename, "action contents: {}".format(
                #     iterstr(actth.content())))
                # self.log(tablename, "action.includes[1] contents: {}".format(
                #     iterstr(actth.includes[1].content())))
                # self.log(tablename, "newth contents: {}".format(
                #     iterstr(newth.content())))
                # compute updates caused by action
                updates = actth.consequences(compile.is_update)
                updates = self.resolve_conflicts(updates)
                updates = unify.skolemize(updates)
                self.log(tablename, "Computed updates: " + iterstr(updates))
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
        """Takes an atom/rule DELTA with update head table
        (i.e. ending in + or -) and inserts/deletes, respectively,
        that atom/rule into THEORY after stripping
        the +/-. Returns None if DELTA had no effect on the
        current state.
        """
        self.log(None, "Applying update {} to {}".format(str(delta), theory))
        th_obj = self.theory[theory]
        insert = delta.tablename().endswith('+')
        newdelta = delta.drop_update()
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
        return compile.parse(string, module_schemas=self.module_schemas)

    def parse1(self, string):
        return compile.parse1(string, module_schemas=self.module_schemas)
