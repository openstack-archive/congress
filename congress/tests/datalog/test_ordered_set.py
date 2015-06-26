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

from congress.datalog import utility
from congress.tests import base

LOG = logging.getLogger(__name__)


class TestOrderedSet(base.TestCase):
    def test_creation_simple(self):
        """"Test basic OrderedSet instantiation."""
        contents = ["foo", "bar", "baz"]
        os = utility.OrderedSet(contents)
        self.assertEqual(list(os), contents)
        self.assertEqual(len(os), len(contents))
        self.assertEqual(set(os), set(contents))

    def test_creation_with_duplicates(self):
        """"Test that OrderedSet instantiation removes duplicates."""
        contents = ["foo", "bar", "foo", "baz"]
        os = utility.OrderedSet(contents)
        self.assertNotEqual(list(os), contents)
        self.assertEqual(len(os), len(contents) - 1)
        self.assertEqual(set(os), set(contents))

    def test_contains(self):
        """Test that basic OrderedSet.__contains__ functionality works."""
        contents = ["foo", "bar", "baz"]
        missing = "qux"
        os = utility.OrderedSet(contents)
        self.assertTrue(all(x in os for x in contents))
        self.assertTrue(missing not in os)

        discarded = contents[1]
        os.discard(discarded)
        self.assertTrue(all(x in os for x in contents if x != discarded))
        self.assertTrue(discarded not in os)

    def test_add_known_item(self):
        """Test that OrderedSet.add(known) returns False."""
        contents = ["foo", "bar", "baz"]
        known = contents[1]
        os = utility.OrderedSet(contents)
        self.assertFalse(os.add(known))
        self.assertEqual(list(os), contents)

    def test_add_unknown_item(self):
        """Test that OrderedSet.add(unknown) returns True."""
        contents = ["foo", "bar", "baz"]
        unknown = "qux"
        os = utility.OrderedSet(contents)
        self.assertTrue(os.add(unknown))
        self.assertEqual(list(os), contents + [unknown])

    def test_discard_known_item(self):
        """Test that OrderedSet.discard(known) returns True."""
        contents = ["foo", "bar", "baz"]
        known = contents[1]
        new_contents = [x for x in contents if x != known]
        os = utility.OrderedSet(contents)
        self.assertTrue(os.discard(known))
        self.assertEqual(list(os), new_contents)

    def test_discard_unknown_item(self):
        """Test that OrderedSet.discard(unknown) returns False."""
        contents = ["foo", "bar", "baz"]
        unknown = "qux"
        os = utility.OrderedSet(contents)
        self.assertFalse(os.discard(unknown))
        self.assertEqual(list(os), contents)

    def test_pop_last_item(self):
        """Test that OrderedSet.pop() returns the final item."""
        contents = ["foo", "bar", "baz"]
        os = utility.OrderedSet(contents)
        self.assertEqual(os.pop(), contents[-1])
        self.assertEqual(list(os), contents[:-1])

    def test_pop_not_first_item(self):
        """Test that OrderedSet.pop(last=False) returns the first item."""
        contents = ["foo", "bar", "baz"]
        os = utility.OrderedSet(contents)
        self.assertEqual(os.pop(last=False), contents[0])
        self.assertEqual(list(os), contents[1:])

    def test_reversed_reverses_order(self):
        """Test that reversed(OrderedSet()) reverses correctly."""
        contents = ["foo", "bar", "baz"]
        os = utility.OrderedSet(contents)
        self.assertEqual(list(reversed(os)), list(reversed(contents)))

    def test_equals_other_ordered_set(self):
        """Test that OrderedSet equality accounts for order."""
        contents = ["foo", "bar", "baz"]
        os = utility.OrderedSet(contents)
        self.assertNotEqual(os, utility.OrderedSet(reversed(os)))
        self.assertEqual(os, utility.OrderedSet(contents))

    def test_equals_other_iterable(self):
        """Test that OrderedSet-to-other-iterable equality returns False."""
        contents = ["foo", "bar", "baz"]
        os = utility.OrderedSet(contents)
        self.assertNotEqual(os, set(os))
        self.assertNotEqual(os, frozenset(os))
        self.assertNotEqual(os, list(os))
        self.assertNotEqual(os, tuple(os))
        self.assertNotEqual(os, {x: 0 for x in os})
