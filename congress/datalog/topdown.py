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
import six
from six.moves import range

from congress.datalog import base
from congress.datalog.builtin import congressbuiltin
from congress.datalog import compile
from congress.datalog import unify
from congress.datalog import utility

LOG = logging.getLogger(__name__)


class TopDownTheory(base.Theory):
    """Class that holds the Top-Down evaluation routines.

    Classes will inherit from this class if they want to import and specialize
    those routines.
    """
    class TopDownContext(object):
        """Struct for storing the search state of top-down evaluation."""
        def __init__(self, literals, literal_index, binding, context, theory,
                     depth):
            self.literals = literals
            self.literal_index = literal_index
            self.binding = binding
            self.previous = context
            self.theory = theory   # a theory object, not just its name
            self.depth = depth

        def __str__(self):
            return (
                "TopDownContext<literals={}, literal_index={}, binding={}, "
                "previous={}, theory={}, depth={}>").format(
                    "[" + ",".join([str(x) for x in self.literals]) + "]",
                    str(self.literal_index), str(self.binding),
                    str(self.previous), self.theory.name, str(self.depth))

    class TopDownResult(object):
        """Stores a single result for top-down-evaluation."""
        def __init__(self, binding, support):
            self.binding = binding
            self.support = support   # for abduction

        def __str__(self):
            return "TopDownResult(binding={}, support={})".format(
                unify.binding_str(self.binding), utility.iterstr(self.support))

    class TopDownCaller(object):
        """Struct for info about the original caller of top-down evaluation.

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
                    utility.iterstr(self.variables), str(self.binding),
                    str(self.find_all), utility.iterstr(self.results),
                    repr(self.save), utility.iterstr(self.support)))

    #########################################
    # External interface

    def __init__(self, name=None, abbr=None, theories=None, schema=None,
                 desc=None, owner=None):
        super(TopDownTheory, self).__init__(
            name=name, abbr=abbr, theories=theories, schema=schema,
            desc=desc, owner=owner)
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
        # LOG.debug("Top_down_evaluation returned: %s", bindings)
        if len(bindings) > 0:
            self.log(query.tablename(), "Found answer %s",
                     "[" + ",".join([str(query.plug(x))
                                    for x in bindings]) + "]")
        return [query.plug(x) for x in bindings]

    def explain(self, query, tablenames, find_all=True):
        """Return list of instances of QUERY that are true.

        Same as select except stores instances of TABLENAMES
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
        """Compute additional literals.

        Computes additional literals that if true would make
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
        assert compile.is_datalog(query), "abduce requires a formula"
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
            save=lambda lit, binding: lit.tablename() in tablenames)
        results = [compile.Rule(output.plug(abd.binding), abd.support)
                   for abd in abductions]
        self.log(query.tablename(), "abduction result:")
        self.log(query.tablename(), "\n".join([str(x) for x in results]))
        return results

    def consequences(self, filter=None, table_theories=None):
        """Return all the true instances of any table in this theory."""
        # find all table, theory pairs defined in this theory
        if table_theories is None:
            table_theories = set()
            for key in self.rules.keys():
                table_theories |= set([(rule.head.table.table,
                                        rule.head.table.service)
                                       for rule in self.rules.get_rules(key)])
        results = set()
        # create queries: need table names and arities
        # TODO(thinrichs): arity computation will need to ignore
        #   modals once we start using insert[p(x)] instead of p+(x)
        for (table, theory) in table_theories:
            if filter is None or filter(table):
                tablename = compile.Tablename(table, theory)
                arity = self.arity(tablename)
                vs = []
                for i in range(0, arity):
                    vs.append("x" + str(i))
                vs = [compile.Variable(var) for var in vs]
                tablename = table
                if theory:
                    tablename = theory + ":" + tablename
                query = compile.Literal(tablename, vs)
                results |= set(self.select(query))
        return results

    def top_down_evaluation(self, variables, literals,
                            binding=None, find_all=True):
        """Compute bindings.

        Compute all bindings of VARIABLES that make LITERALS
        true according to the theory (after applying the unifier BINDING).
        If FIND_ALL is False, stops after finding one such binding.
        Returns a list of dictionary bindings.
        """
        # LOG.debug("CALL: top_down_evaluation(vars=%s, literals=%s, "
        #               "binding=%s)",
        #         ";".join(str(x) for x in variables),
        #         ";".join(str(x) for x in literals),
        #         str(binding))
        results = self.top_down_abduction(variables, literals,
                                          binding=binding, find_all=find_all,
                                          save=None)
        # LOG.debug("EXIT: top_down_evaluation(vars=%s, literals=%s, "
        #               "binding=%s) returned %s",
        #         iterstr(variables), iterstr(literals),
        #         str(binding), iterstr(results))
        return [x.binding for x in results]

    def top_down_abduction(self, variables, literals, binding=None,
                           find_all=True, save=None):
        """Compute bindings.

        Compute all bindings of VARIABLES that make LITERALS
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
            self._top_down_finish(None, caller)
        else:
            # Note: must use same unifier in CALLER and CONTEXT
            context = self.TopDownContext(literals, 0, binding, None, self, 0)
            self._top_down_eval(context, caller)
        return list(set(caller.results))

    #########################################
    # Internal implementation

    def _top_down_eval(self, context, caller):
        """Compute instances.

        Compute all instances of LITERALS (from LITERAL_INDEX and above)
        that are true according to the theory (after applying the
        unifier BINDING to LITERALS).
        Returns True if done searching and False otherwise.
        """
        # no recursive rules, ever; this style of algorithm will not terminate
        lit = context.literals[context.literal_index]
        # LOG.debug("CALL: %s._top_down_eval(%s, %s)",
        #     self.name, context, caller)

        # abduction
        if caller.save is not None and caller.save(lit, context.binding):
            self._print_call(lit, context.binding, context.depth)
            # save lit and binding--binding may not be fully flushed out
            #   when we save (or ever for that matter)
            caller.support.append((lit, context.binding))
            self._print_save(lit, context.binding, context.depth)
            success = self._top_down_finish(context, caller)
            caller.support.pop()  # pop in either case
            if success:
                return True
            else:
                self._print_fail(lit, context.binding, context.depth)
                return False

        # regular processing
        if lit.is_negated():
            # LOG.debug("%s is negated", lit)
            # recurse on the negation of the literal
            plugged = lit.plug(context.binding)
            assert plugged.is_ground(), (
                "Negated literal not ground when evaluated: " +
                str(plugged))
            self._print_call(lit, context.binding, context.depth)
            new_context = self.TopDownContext(
                [lit.complement()], 0, context.binding, None,
                self, context.depth + 1)
            new_caller = self.TopDownCaller(caller.variables, caller.binding,
                                            caller.theory, find_all=False,
                                            save=None)
            # Make sure new_caller has find_all=False, so we stop as soon
            #    as we can.
            # Ensure save=None so that abduction does not save anything.
            #    Saving while performing NAF makes no sense.
            self._top_down_eval(new_context, new_caller)
            if len(new_caller.results) > 0:
                self._print_fail(lit, context.binding, context.depth)
                return False   # not done searching, b/c we failed
            else:
                # don't need bindings b/c LIT must be ground
                return self._top_down_finish(context, caller, redo=False)
        elif lit.tablename() == 'true':
            self._print_call(lit, context.binding, context.depth)
            return self._top_down_finish(context, caller, redo=False)
        elif lit.tablename() == 'false':
            self._print_fail(lit, context.binding, context.depth)
            return False
        elif lit.is_builtin():
            return self._top_down_builtin(context, caller)
        elif (self.theories is not None and
              lit.table.service is not None and
              lit.table.modal is None and  # not a modal
              lit.table.service != self.name and
              not lit.is_update()):  # not a pseudo-modal
            return self._top_down_module(context, caller)
        else:
            return self._top_down_truth(context, caller)

    def _top_down_builtin(self, context, caller):
        """Evaluate a table with a builtin semantics.

        Returns True if done searching and False otherwise.
        """
        lit = context.literals[context.literal_index]
        self._print_call(lit, context.binding, context.depth)
        builtin = congressbuiltin.builtin_registry.builtin(lit.table)
        # copy arguments into variables
        # PLUGGED is an instance of compile.Literal
        plugged = lit.plug(context.binding)
        # PLUGGED.arguments is a list of compile.Term
        # create args for function
        args = []
        for i in range(0, builtin.num_inputs):
            # save builtins with unbound vars during evaluation
            if not plugged.arguments[i].is_object() and caller.save:
                # save lit and binding--binding may not be fully flushed out
                #   when we save (or ever for that matter)
                caller.support.append((lit, context.binding))
                self._print_save(lit, context.binding, context.depth)
                success = self._top_down_finish(context, caller)
                caller.support.pop()  # pop in either case
                if success:
                    return True
                else:
                    self._print_fail(lit, context.binding, context.depth)
                    return False
            assert plugged.arguments[i].is_object(), (
                ("Builtins must be evaluated only after their "
                 "inputs are ground: {} with num-inputs {}".format(
                     str(plugged), builtin.num_inputs)))
            args.append(plugged.arguments[i].name)
        # evaluate builtin: must return number, string, or iterable
        #    of numbers/strings
        try:
            result = builtin.code(*args)
        except Exception as e:
            errmsg = "Error in builtin: " + str(e)
            self._print_note(lit, context.binding, context.depth, errmsg)
            self._print_fail(lit, context.binding, context.depth)
            return False

        # self._print_note(lit, context.binding, context.depth,
        #                 "Result: " + str(result))
        success = None
        undo = []
        if builtin.num_outputs > 0:
            # with return values, local success means we can bind
            #  the results to the return value arguments
            if (isinstance(result,
                           (six.integer_types, float, six.string_types))):
                result = [result]
            # Turn result into normal objects
            result = [compile.Term.create_from_python(x) for x in result]
            # adjust binding list
            unifier = self.new_bi_unifier()
            undo = unify.bi_unify_lists(result,
                                        unifier,
                                        lit.arguments[builtin.num_inputs:],
                                        context.binding)
            success = undo is not None
        else:
            # without return values, local success means
            #   result was True according to Python
            success = bool(result)

        if not success:
            self._print_fail(lit, context.binding, context.depth)
            unify.undo_all(undo)
            return False

        # otherwise, try to finish proof.  If success, return True
        if self._top_down_finish(context, caller, redo=False):
            unify.undo_all(undo)
            return True
        # if fail, return False.
        else:
            unify.undo_all(undo)
            self._print_fail(lit, context.binding, context.depth)
            return False

    def _top_down_module(self, context, caller):
        """Move to another theory and continue evaluation."""
        # LOG.debug("%s._top_down_module(%s)", self.name, context)
        lit = context.literals[context.literal_index]
        if lit.table.service not in self.theories:
            self._print_call(lit, context.binding, context.depth)
            errmsg = "No such policy: %s" % lit.table.service
            self._print_note(lit, context.binding, context.depth, errmsg)
            self._print_fail(lit, context.binding, context.depth)
            return False
        return self.theories[lit.table.service]._top_down_eval(context, caller)

    def _top_down_truth(self, context, caller):
        """Top down evaluation.

        Do top-down evaluation over the root theory at which
        the call was made and all the included theories.
        """
        # return self._top_down_th(context, caller)
        return self._top_down_includes(context, caller)

    def _top_down_includes(self, context, caller):
        """Top-down evaluation of all the theories included in this theory."""
        is_true = self._top_down_th(context, caller)
        if is_true and not caller.find_all:
            return True
        for th in self.includes:
            is_true = th._top_down_includes(context, caller)
            if is_true and not caller.find_all:
                return True
        return False

    def _top_down_th(self, context, caller):
        """Top-down evaluation for the rules in self."""
        # LOG.debug("%s._top_down_th(%s)", self.name, context)
        lit = context.literals[context.literal_index]
        self._print_call(lit, context.binding, context.depth)
        for rule in self.head_index(lit.table.table,
                                    lit.plug(context.binding)):
            unifier = self.new_bi_unifier()
            self._print_note(lit, context.binding, context.depth,
                             "Trying %s" % rule)
            # Prefer to bind vars in rule head
            undo = self.bi_unify(self.head(rule), unifier, lit,
                                 context.binding, self.name)
            if undo is None:  # no unifier
                continue
            if len(self.body(rule)) == 0:
                if self._top_down_finish(context, caller):
                    unify.undo_all(undo)
                    if not caller.find_all:
                        return True
                else:
                    unify.undo_all(undo)
            else:
                new_context = self.TopDownContext(
                    rule.body, 0, unifier, context, self, context.depth + 1)
                if self._top_down_eval(new_context, caller):
                    unify.undo_all(undo)
                    if not caller.find_all:
                        return True
                else:
                    unify.undo_all(undo)
        self._print_fail(lit, context.binding, context.depth)
        return False

    def _top_down_finish(self, context, caller, redo=True):
        """Helper function.

        This is called once top_down successfully completes
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
            self._print_exit(context.literals[context.literal_index],
                             context.binding, context.depth)
            # continue the search
            if context.literal_index < len(context.literals) - 1:
                context.literal_index += 1
                finished = context.theory._top_down_eval(context, caller)
                context.literal_index -= 1  # in case answer is False
            else:
                finished = self._top_down_finish(context.previous, caller)
            # return search result (after printing a Redo if failure)
            if redo and (not finished or caller.find_all):
                self._print_redo(context.literals[context.literal_index],
                                 context.binding, context.depth)
            return finished

    def _print_call(self, literal, binding, depth):
        msg = "{}Call: %s".format("| " * depth)
        self.log(literal.tablename(), msg, literal.plug(binding))

    def _print_exit(self, literal, binding, depth):
        msg = "{}Exit: %s".format("| " * depth)
        self.log(literal.tablename(), msg, literal.plug(binding))

    def _print_save(self, literal, binding, depth):
        msg = "{}Save: %s".format("| " * depth)
        self.log(literal.tablename(), msg, literal.plug(binding))

    def _print_fail(self, literal, binding, depth):
        msg = "{}Fail: %s".format("| " * depth)
        self.log(literal.tablename(), msg, literal.plug(binding))
        return False

    def _print_redo(self, literal, binding, depth):
        msg = "{}Redo: %s".format("| " * depth)
        self.log(literal.tablename(), msg, literal.plug(binding))
        return False

    def _print_note(self, literal, binding, depth, msg):
        self.log(literal.tablename(), "{}Note: {}".format("| " * depth,
                 msg))

    #########################################
    # Routines for specialization

    @classmethod
    def new_bi_unifier(cls, dictionary=None):
        """Return a unifier compatible with unify.bi_unify."""
        return unify.BiUnifier(dictionary=dictionary)
        # lambda (index):
        # compile.Variable("x" + str(index)), dictionary=dictionary)

    def defined_tablenames(self):
        """Returns list of table names defined in/written to this theory."""
        raise NotImplementedError

    def head_index(self, table, match_literal=None):
        """Return head index.

        This routine must return all the formulas pertinent for
        top-down evaluation when a literal with TABLE is at the top
        of the stack.
        """
        raise NotImplementedError

    def head(self, formula):
        """Given the output from head_index(), return the formula head.

        Given a FORMULA, return the thing to unify against.
        Usually, FORMULA is a compile.Rule, but it could be anything
        returned by HEAD_INDEX.
        """
        raise NotImplementedError

    def body(self, formula):
        """Return formula body.

        Given a FORMULA, return a list of things to push onto the
        top-down eval stack.
        """
        raise NotImplementedError

    def bi_unify(self, head, unifier1, body_element, unifier2, theoryname):
        """Unify atoms.

        Given something returned by self.head HEAD and an element in
        the return of self.body BODY_ELEMENT, modify UNIFIER1 and UNIFIER2
        so that HEAD.plug(UNIFIER1) == BODY_ELEMENT.plug(UNIFIER2).
        Returns changes that can be undone via unify.undo-all.
        THEORYNAME is the name of the theory for HEAD.
        """
        return unify.bi_unify_atoms(head, unifier1, body_element, unifier2,
                                    theoryname)

    #########################################
    # Routines for unknowns

    def instances(self, rule, possibilities=None):
        results = set([])
        possibilities = possibilities or []
        self._instances(rule, 0, self.new_bi_unifier(), results, possibilities)
        return results

    def _instances(self, rule, index, binding, results, possibilities):
        """Return all instances of the given RULE without evaluating builtins.

        Assumes self.head_index returns rules with empty bodies.
        """
        if index >= len(rule.body):
            results.add(rule.plug(binding))
            return
        lit = rule.body[index]
        self._print_call(lit, binding, 0)
        # if already ground or a builtin, go to the next literal
        if (lit.is_ground() or lit.is_builtin()):
            self._instances(rule, index + 1, binding, results, possibilities)
            return
        # Otherwise, find instances in this theory
        if lit.tablename() in possibilities:
            options = possibilities[lit.tablename()]
        else:
            options = self.head_index(lit.tablename(), lit.plug(binding))
        for data in options:
            self._print_note(lit, binding, 0, "Trying: %s" % repr(data))
            undo = unify.match_atoms(lit, binding, self.head(data))
            if undo is None:  # no unifier
                continue
            self._print_exit(lit, binding, 0)
            # recurse on the rest of the literals in the rule
            self._instances(rule, index + 1, binding, results, possibilities)
            if undo is not None:
                unify.undo_all(undo)
            self._print_redo(lit, binding, 0)
        self._print_fail(lit, binding, 0)
