#! /usr/bin/python

import logging

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

    class Undo(object):
        def __init__(self, var, unifier):
            self.var = var
            self.unifier = unifier

        def __str__(self):
            return "<var: {}, unifier: {}>".format(
                str(self.var), str(self.unifier))

    def __init__(self, new_variable_factory):
        # each value is a Value
        self.contents = {}
        self.new_variable_counter = 0
        self.new_variable_factory = new_variable_factory

    def add(self, var, value, unifier):
        value = self.Value(value, unifier)
        self.contents[var] = value
        # logging.debug("Adding {} -> {} to unifier {}".format(
        #     str(var), str(value), str(self)))
        return self.Undo(var, self)

    def delete(self, var):
        if var in self.contents:
            del self.contents[var]

    def apply(self, term):
        return self.apply_full(term)[0]

    def apply_full(self, term):
        """ Recursively apply unifiers to TERM and return
            (i) the final value and (ii) the final unifier. """
        if not term.is_variable() or term not in self.contents:
            return (term, self)
        value = self.contents[term]
        # logging.debug("Apply({}): has contents: {}".format(term, str(value)))
        if value.unifier is not None:
            return value.unifier.apply_full(value.value)
        else:
            return (value.value, self)

    def __str__(self):
        s = repr(self)
        s += "={"
        s += ",".join(["{}:{}".format(var, str(val))
            for var, val in self.contents.iteritems()])
        s += "}"
        return s

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
        val1, binding1 = unifier1.apply_full(atom1.arguments[i])
        val2, binding2 = unifier2.apply_full(atom2.arguments[i])
        # logging.debug("val({})={} at {}, val({})={} at {}".format(
        #     str(atom1.arguments[i]), str(val1), str(unifier1),
        #     str(atom2.arguments[i]), str(val2), str(unifier2)))
        if not val1.is_variable() and val1 == val2:
            continue
        elif val1 is val2 and binding1 is binding2:
            continue
        elif val1.is_variable():
            changes.append(binding1.add(val1, val2, binding2))
        elif val2.is_variable():
            changes.append(binding2.add(val2, val1, binding1))
        else:
            undo_all(changes)
            return None
    return changes





