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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from congress.datalog import factset
from congress.tests import base


class TestFactSet(base.TestCase):
    def setUp(self):
        super(TestFactSet, self).setUp()
        self.factset = factset.FactSet()

    def test_empty(self):
        self.assertFalse((1, 2, 3) in self.factset)
        self.assertEqual(0, len(self.factset))

    def test_add_one(self):
        f = (1, 2, 'a')
        self.factset.add(f)
        self.assertEqual(1, len(self.factset))
        self.assertEqual(set([f]), self.factset.find(((0, 1), (1, 2),
                                                      (2, 'a'))))

    def test_add_few(self):
        f1 = (1, 200, 'a')
        f2 = (2, 200, 'a')
        f3 = (3, 200, 'c')
        self.factset.add(f1)
        self.factset.add(f2)
        self.factset.add(f3)

        self.assertEqual(3, len(self.factset))
        self.assertEqual(set([f1, f2, f3]), self.factset.find(((1, 200),)))
        self.assertEqual(set([f1, f2]), self.factset.find(((2, 'a'),)))
        self.assertEqual(set([f1]), self.factset.find(((0, 1), (1, 200),
                                                       (2, 'a'),)))
        self.assertEqual(set(), self.factset.find(((0, 8),)))

    def test_remove(self):
        f1 = (1, 200, 'a')
        f2 = (2, 200, 'a')
        f3 = (3, 200, 'c')
        self.factset.add(f1)
        self.factset.add(f2)
        self.factset.add(f3)
        self.assertEqual(3, len(self.factset))

        self.assertTrue(self.factset.remove(f1))
        self.assertEqual(2, len(self.factset))
        self.assertEqual(set([f2, f3]), self.factset.find(((1, 200),)))

        self.assertTrue(self.factset.remove(f3))
        self.assertEqual(1, len(self.factset))
        self.assertEqual(set([f2]), self.factset.find(((1, 200),)))

        self.assertFalse(self.factset.remove(f3))

        self.assertTrue(self.factset.remove(f2))
        self.assertEqual(0, len(self.factset))
        self.assertEqual(set(), self.factset.find(((1, 200),)))

    def test_create_index(self):
        f1 = (1, 200, 'a')
        f2 = (2, 200, 'a')
        f3 = (3, 200, 'c')
        self.factset.add(f1)
        self.factset.add(f2)
        self.factset.add(f3)

        self.factset.create_index((1,))
        self.assertEqual(set([f1, f2, f3]), self.factset.find(((1, 200),)))
        self.assertEqual(set([f1, f2]), self.factset.find(((2, 'a'),)))
        self.assertEqual(set([f1, f2]), self.factset.find(((1, 200),
                                                           (2, 'a'))))
        self.assertEqual(set([f1]), self.factset.find(((0, 1), (1, 200),
                                                       (2, 'a'),)))
        self.assertEqual(set(), self.factset.find(((0, 8),)))

        self.factset.create_index((1, 2))
        self.assertEqual(set([f1, f2, f3]), self.factset.find(((1, 200),)))
        self.assertEqual(set([f1, f2]), self.factset.find(((2, 'a'),)))
        self.assertEqual(set([f1, f2]), self.factset.find(((1, 200),
                                                           (2, 'a'))))
        self.assertEqual(set([f1]), self.factset.find(((0, 1), (1, 200),
                                                       (2, 'a'),)))
        self.assertEqual(set(), self.factset.find(((0, 8),)))

    def test_remove_index(self):
        f1 = (1, 200, 'a')
        f2 = (2, 200, 'a')
        f3 = (3, 200, 'c')
        self.factset.add(f1)
        self.factset.add(f2)
        self.factset.add(f3)

        self.factset.create_index((1,))
        self.factset.create_index((1, 2))
        self.factset.remove_index((1,))
        self.factset.remove_index((1, 2))

        self.assertEqual(set([f1, f2, f3]), self.factset.find(((1, 200),)))
        self.assertEqual(set([f1, f2]), self.factset.find(((2, 'a'),)))
        self.assertEqual(set([f1, f2]), self.factset.find(((1, 200),
                                                           (2, 'a'))))
        self.assertEqual(set([f1]), self.factset.find(((0, 1), (1, 200),
                                                       (2, 'a'),)))
        self.assertEqual(set(), self.factset.find(((0, 8),)))

    def test_indexed_find(self):
        f1 = (1, 200, 'a')
        f2 = (2, 200, 'a')
        f3 = (3, 200, 'c')
        self.factset.add(f1)
        self.factset.add(f2)
        self.factset.add(f3)

        # Count iterations without index.
        iterations = []  # measure how many iterations find() uses.
        self.assertEqual(set([f1]), self.factset.find(((0, 1),), iterations))
        self.assertEqual(3, iterations[0])

        # Count iterations with index match.
        self.factset.create_index((0,))
        iterations = []
        self.assertEqual(set([f1]), self.factset.find(((0, 1),), iterations))
        self.assertEqual(1, iterations[0])

        # Count iterations when there is a matching index, but not match for
        # this particular key.
        iterations = []
        self.assertEqual(set(), self.factset.find(((0, 100),), iterations))
        self.assertEqual(1, iterations[0])

        # Count iterations after deleting index.
        self.factset.remove_index((0,))
        iterations = []
        self.assertEqual(set([f1]), self.factset.find(((0, 1),), iterations))
        self.assertEqual(3, iterations[0])
