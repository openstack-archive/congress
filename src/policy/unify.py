#! /usr/bin/python

import logging
import compile

# A unifier designed for the bi_unify_atoms routine
# which is used by a backward-chaining style datalog implementation.
# Main goal: minimize memory allocation by manipulating only unifiers
#   to keep variable namespaces separate.

class BiUnifier(object):
    """ A unifier designed for bi_unify_atoms.  Recursive
        datastructure.  When adding a binding variable u to
        variable v, keeps a reference to the unifier for v.
        A variable's identity is its name plus its unification context.
        This enables a variable with the same name but from two
        different atoms to be treated as different variables. """
    class Value(object):
        def __init__(self, value, unifier):
            # actual value
            self.value = value
            # unifier context
            self.unifier = unifier

        def __str__(self):
            return "<{},{}>".format(
                str(self.value), repr(self.unifier))

        def recur_str(self):
            if self.unifier is None:
                recur = str(self.unifier)
            else:
                recur = self.unifier.recur_str()
            return "<{},{}>".format(
                str(self.value), recur)

        def __eq__(self, other):
            return self.value == other.value and self.unifer == other.unifier

        def __repr__(self):
            return "Value(value={}, unifier={})".format(
                repr(self.value), repr(self.unifier))

    class Undo(object):
        def __init__(self, var, unifier):
            self.var = var
            self.unifier = unifier

        def __str__(self):
            return "<var: {}, unifier: {}>".format(
                str(self.var), str(self.unifier))

        def __eq__(self, other):
            return self.var == other.var and self.unifier == other.unifier

    def __init__(self, new_variable_factory, dictionary=None):
        # each value is a Value
        self.contents = {}
        self.new_variable_counter = 0
        self.new_variable_factory = new_variable_factory
        if dictionary is not None:
            for var, value in dictionary.iteritems():
                self.add(var, value, None)

    def add(self, var, value, unifier):
        value = self.Value(value, unifier)
        # logging.debug("Adding {} -> {} to unifier {}".format(
        #      str(var), str(value), str(self)))
        self.contents[var] = value
        return self.Undo(var, self)

    def delete(self, var):
        if var in self.contents:
            del self.contents[var]

    def value(self, term):
        if term in self.contents:
            return self.contents[term]
        else:
            return None

    def apply(self, term):
        return self.apply_full(term)[0]

    def apply_full(self, term):
        """ Recursively apply unifiers to TERM and return
            (i) the final value and (ii) the final unifier. """
        # logging.debug("apply_full({}, {})".format(str(term), str(self)))
        val = self.value(term)
        if val is None:
            return (term, self)
        elif val.unifier is None or not val.value.is_variable():
            return (val.value, val.unifier)
        else:
            return val.unifier.apply_full(val.value)

    def __str__(self):
        s = repr(self)
        s += "={"
        s += ",".join(["{}:{}".format(var, str(val))
            for var, val in self.contents.iteritems()])
        s += "}"
        return s

    def recur_str(self):
        s = repr(self)
        s += "={"
        s += ",".join(["{}:{}".format(var, val.recur_str())
            for var, val in self.contents.iteritems()])
        s += "}"
        return s

    def __eq__(self, other):
        return self.contents == other.contents


def undo_all(changes):
    """ Undo all the changes in CHANGES. """
    # logging.debug("undo_all({})".format(
    #     "[" + ",".join([str(x) for x in changes]) + "]"))
    for change in changes:
        if change.unifier is not None:
            change.unifier.delete(change.var)

def bi_unify_atoms(atom1, unifier1, atom2, unifier2):
    """ If possible, modify BiUnifier UNIFIER1 and BiUnifier UNIFIER2 so that
        ATOM1.plug(UNIFIER1) == ATOM2.plug(UNIFIER2).
        Returns None if not possible; otherwise, returns
        a list of changes to unifiers that can be undone
        with undo-all. May alter unifiers besides UNIFIER1 and UNIFIER2. """
    # logging.debug("Unifying {} under {} and {} under {}".format(
    #      str(atom1), str(unifier1), str(atom2), str(unifier2)))
    if atom1.table != atom2.table:
        return None
    if len(atom1.arguments) != len(atom2.arguments):
        return None
    changes = []
    for i in xrange(0, len(atom1.arguments)):
        assert isinstance(atom1.arguments[i], compile.Term)
        assert isinstance(atom2.arguments[i], compile.Term)
        # grab values for args
        val1, binding1 = unifier1.apply_full(atom1.arguments[i])
        val2, binding2 = unifier2.apply_full(atom2.arguments[i])
        # logging.debug("val({})={} at {}, val({})={} at {}".format(
        #     str(atom1.arguments[i]), str(val1), str(binding1),
        #     str(atom2.arguments[i]), str(val2), str(binding2)))
        # assign variable (if necessary) or fail
        if val1.is_variable() and val2.is_variable():
            # logging.debug("1 and 2 are variables")
            if val1 == val2 and binding1 is binding2:
                continue
            else:
                changes.append(binding1.add(val1, val2, binding2))
        elif val1.is_variable() and not val2.is_variable():
            # logging.debug("Left arg is a variable")
            changes.append(binding1.add(val1, val2, binding2))
        elif not val1.is_variable() and val2.is_variable():
            # logging.debug("Right arg is a variable")
            changes.append(binding2.add(val2, val1, binding1))
        elif val1 == val2:
            continue
        else:
            # logging.debug("Unify failure: undoing")
            undo_all(changes)
            return None
    return changes

# def plug(atom, binding, withtable=False):
#     """ Returns a tuple representing the arguments to ATOM after having
#         applied BINDING to the variables in ATOM. """
#     if withtable is True:
#         result = [atom.table]
#     else:
#         result = []
#     for i in xrange(0, len(atom.arguments)):
#         if atom.arguments[i].is_variable() and atom.arguments[i].name in binding:
#             result.append(binding[atom.arguments[i].name])
#         else:
#             result.append(atom.arguments[i].name)
#     return tuple(result)

def match_tuple_atom(tuple, atom):
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



