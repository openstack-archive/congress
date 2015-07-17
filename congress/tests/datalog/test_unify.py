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
from oslo_log import log as logging

from congress.datalog import compile
from congress.datalog import topdown
from congress.datalog import unify
from congress.tests import base

LOG = logging.getLogger(__name__)


NREC_THEORY = 'non-recursive theory'
DB_THEORY = 'database'
MAT_THEORY = 'materialized'


class TestUnify(base.TestCase):
    def open(self, msg):
        LOG.debug("** Started: %s **", msg)

    def close(self, msg):
        LOG.debug("** Finished: %s **", msg)

    def create_unify(self, atom_string1, atom_string2, msg, change_num,
                     unifier1=None, unifier2=None, recursive_str=False):
        """Create unification and check basic results."""
        def str_uni(u):
            if recursive_str:
                return u.recur_str()
            else:
                return str(u)

        def print_unifiers(changes=None):
            LOG.debug("unifier1: %s", str_uni(unifier1))
            LOG.debug("unifier2: %s", str_uni(unifier2))
            if changes is not None:
                LOG.debug("changes: %s",
                          ";".join([str(x) for x in changes]))

        if msg is not None:
            self.open(msg)
        if unifier1 is None:
            # LOG.debug("Generating new unifier1")
            unifier1 = topdown.TopDownTheory.new_bi_unifier()
        if unifier2 is None:
            # LOG.debug("Generating new unifier2")
            unifier2 = topdown.TopDownTheory.new_bi_unifier()
        p1 = compile.parse(atom_string1)[0]
        p2 = compile.parse(atom_string2)[0]
        changes = unify.bi_unify_atoms(p1, unifier1, p2, unifier2)
        self.assertTrue(changes is not None)
        print_unifiers(changes)
        p1p = p1.plug(unifier1)
        p2p = p2.plug(unifier2)
        print_unifiers(changes)
        if not p1p == p2p:
            LOG.debug("Failure: bi-unify(%s, %s) produced %s and %s",
                      p1, p2, str_uni(unifier1), str_uni(unifier2))
            LOG.debug("plug(%s, %s) = %s", p1, str_uni(unifier1), p1p)
            LOG.debug("plug(%s, %s) = %s", p2, str_uni(unifier2), p2p)
            self.fail()
        if change_num is not None and len(changes) != change_num:
            LOG.debug("Failure: bi-unify(%s, %s) produced %s and %s",
                      p1, p2, str_uni(unifier1), str_uni(unifier2))
            LOG.debug("plug(%s, %s) = %s", p1, str_uni(unifier1), p1p)
            LOG.debug("plug(%s, %s) = %s", p2, str_uni(unifier2), p2p)
            LOG.debug("Expected %s changes; computed %s changes",
                      change_num, len(changes))
            self.fail()
        LOG.debug("unifier1: %s", str_uni(unifier1))
        LOG.debug("unifier2: %s", str_uni(unifier2))
        if msg is not None:
            self.open(msg)
        return (p1, unifier1, p2, unifier2, changes)

    def check_unify(self, atom_string1, atom_string2, msg, change_num,
                    unifier1=None, unifier2=None, recursive_str=False):
        self.open(msg)
        (p1, unifier1, p2, unifier2, changes) = self.create_unify(
            atom_string1, atom_string2, msg, change_num,
            unifier1=unifier1, unifier2=unifier2, recursive_str=recursive_str)
        unify.undo_all(changes)
        self.assertTrue(p1.plug(unifier1) == p1)
        self.assertTrue(p2.plug(unifier2) == p2)
        self.close(msg)

    def check_unify_fail(self, atom_string1, atom_string2, msg):
        """Check that the bi-unification fails."""
        self.open(msg)
        unifier1 = topdown.TopDownTheory.new_bi_unifier()
        unifier2 = topdown.TopDownTheory.new_bi_unifier()
        p1 = compile.parse(atom_string1)[0]
        p2 = compile.parse(atom_string2)[0]
        changes = unify.bi_unify_atoms(p1, unifier1, p2, unifier2)
        if changes is not None:
            LOG.debug("Failure failure: bi-unify(%s, %s) produced %s and %s",
                      p1, p2, unifier1, unifier2)
            LOG.debug("plug(%s, %s) = %s", p1, unifier1, p1.plug(unifier1))
            LOG.debug("plug(%s, %s) = %s", p2, unifier2, p2.plug(unifier2))
            self.fail()
        self.close(msg)

    def test_instance(self):
        """Test whether the INSTANCE computation is correct."""
        def assertIsNotNone(x):
            self.assertTrue(x is not None)

        def assertIsNone(x):
            self.assertTrue(x is None)

        assertIsNotNone(unify.instance(str2form('p(1)'), str2form('p(y)')))
        assertIsNotNone(unify.instance(str2form('p(1,2)'), str2form('p(x,y)')))
        assertIsNotNone(unify.instance(str2form('p(1,x)'), str2form('p(x,y)')))
        assertIsNotNone(unify.instance(str2form('p(1,x,1)'),
                        str2form('p(x,y,x)')))
        assertIsNotNone(unify.instance(str2form('p(1,x,1)'),
                        str2form('p(x,y,z)')))
        assertIsNone(unify.instance(str2form('p(1,2)'), str2form('p(x,x)')))

    def test_same(self):
        """Test whether the SAME computation is correct."""
        def assertIsNotNone(x):
            self.assertTrue(x is not None)

        def assertIsNone(x):
            self.assertTrue(x is None)

        assertIsNotNone(unify.same(str2form('p(x)'), str2form('p(y)')))
        assertIsNotNone(unify.same(str2form('p(x)'), str2form('p(x)')))
        assertIsNotNone(unify.same(str2form('p(x,y)'), str2form('p(x,y)')))
        assertIsNotNone(unify.same(str2form('p(x,y)'), str2form('p(y,x)')))
        assertIsNone(unify.same(str2form('p(x,x)'), str2form('p(x,y)')))
        assertIsNone(unify.same(str2form('p(x,y)'), str2form('p(x,x)')))
        assertIsNotNone(unify.same(str2form('p(x,x)'), str2form('p(y,y)')))
        assertIsNotNone(unify.same(str2form('p(x,y,x)'), str2form('p(y,x,y)')))
        assertIsNone(unify.same(str2form('p(x,y,z)'), str2form('p(x,y,1)')))

    def test_bi_unify(self):
        """Test the bi-unification routine and its supporting routines."""
        def var(x):
            return compile.Term.create_from_python(x, force_var=True)

        def obj(x):
            return compile.Term.create_from_python(x)

        def new_uni():
            return topdown.TopDownTheory.new_bi_unifier()

        # apply, add
        u1 = new_uni()
        u1.add(var('x'), obj(1), None)
        self.assertEqual(u1.apply(var('x')), obj(1))

        u1 = new_uni()
        u2 = new_uni()
        u1.add(var('y'), var('x'), u2)
        self.assertEqual(u1.apply(var('y')), var('x'))
        u2.add(var('x'), obj(2), None)
        self.assertEqual(u1.apply(var('y')), obj(2))

        # delete
        u1.delete(var('y'))
        self.assertEqual(u1.apply(var('y')), var('y'))

        u1 = new_uni()
        u2 = new_uni()
        u1.add(var('y'), var('x'), u2)
        u2.add(var('x'), obj(2), None)
        u2.delete(var('x'))
        self.assertEqual(u1.apply(var('y')), var('x'))
        u1.delete(var('y'))
        self.assertEqual(u1.apply(var('y')), var('y'))

        # bi_unify
        self.check_unify("p(x)", "p(1)",
                         "Matching", 1)
        self.check_unify("p(x,y)", "p(1,2)",
                         "Binary Matching", 2)
        self.check_unify("p(1,2)", "p(x,y)",
                         "Binary Matching Reversed", 2)
        self.check_unify("p(1,1)", "p(x,y)",
                         "Binary Matching Many-to-1", 2)
        self.check_unify_fail("p(1,2)", "p(x,x)",
                              "Binary Matching Failure")
        self.check_unify("p(1,x)", "p(1,y)",
                         "Simple Unification", 1)
        self.check_unify("p(1,x)", "p(y,1)",
                         "Separate Namespace Unification", 2)
        self.check_unify("p(1,x)", "p(x,2)",
                         "Namespace Collision Unification", 2)
        self.check_unify("p(x,y,z)", "p(t,u,v)",
                         "Variable-only Unification", 3)
        self.check_unify("p(x,y,y)", "p(t,u,t)",
                         "Repeated Variable Unification", 3)
        self.check_unify_fail("p(x,y,y,x,y)", "p(t,u,t,1,2)",
                              "Repeated Variable Unification Failure")
        self.check_unify(
            "p(x,y,y)", "p(x,y,x)",
            "Repeated Variable Unification Namespace Collision", 3)
        self.check_unify_fail(
            "p(x,y,y,x,y)", "p(x,y,x,1,2)",
            "Repeated Variable Unification Namespace Collision Failure")

        # test sequence of changes
        (p1, u1, p2, u2, changes) = self.create_unify(
            "p(x)", "p(x)", "Step 1", 1)   # 1 since the two xs are different
        self.create_unify(
            "p(x)", "p(1)", "Step 2", 1, unifier1=u1, recursive_str=True)
        self.create_unify(
            "p(x)", "p(1)", "Step 3", 0, unifier1=u1, recursive_str=True)


class TestMatch(base.TestCase):

    def check(self, atom1, atom2):
        atom1 = compile.parse1(atom1)
        atom2 = compile.parse1(atom2)
        unifier = unify.BiUnifier()
        changes = unify.match_atoms(atom1, unifier, atom2)
        self.assertIsNotNone(changes)
        self.assertEqual(atom1.plug(unifier), atom2)

    def cherr(self, atom1, atom2):
        atom1 = compile.parse1(atom1)
        atom2 = compile.parse1(atom2)
        unifier = unify.BiUnifier()
        self.assertIsNone(unify.match_atoms(atom1, unifier, atom2))

    def test_atoms(self):
        self.check('p(x, y)', 'p(1, 2)')
        self.check('p(x, x)', 'p(1, 1)')
        self.cherr('p(x, x)', 'p(1, 2)')
        self.check('p(x, y, z)', 'p(1, 2, 1)')
        self.check('p(x, y, x, z)', 'p(1, 2, 1, 3)')
        self.cherr('p(x, y, x, y)', 'p(1, 2, 1, 3)')
        self.cherr('p(x, y, x, y)', 'p(1, 2, 2, 1)')
        self.check('p(x, y, x, y)', 'p(1, 1, 1, 1)')

    def test_sequence(self):
        atom1 = compile.parse1('p(x, y)')
        atom2 = compile.parse1('p(1, 2)')
        unifier = unify.BiUnifier()
        changes = unify.match_atoms(atom1, unifier, atom2)
        self.assertIsNotNone(changes)

        atom3 = compile.parse1('q(y, z)')
        atom4 = compile.parse1('q(2, 3)')
        changes = unify.match_atoms(atom3, unifier, atom4)
        self.assertIsNotNone(changes)

        atom5 = compile.parse1('r(x, y, z, z)')
        atom6 = compile.parse1('r(1, 2, 3, 3)')
        changes = unify.match_atoms(atom5, unifier, atom6)
        self.assertIsNotNone(changes)

        self.assertEqual(atom1.plug(unifier), atom2)
        self.assertEqual(atom3.plug(unifier), atom4)
        self.assertEqual(atom5.plug(unifier), atom6)


def str2form(formula_string):
    return compile.parse1(formula_string)


def str2pol(policy_string):
    return compile.parse(policy_string)


def pol2str(policy):
    return " ".join(str(x) for x in policy)


def form2str(formula):
    return str(formula)
