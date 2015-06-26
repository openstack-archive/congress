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
import contextlib
import logging as python_logging
import StringIO

from oslo_log import log as logging

from congress.datalog import utility
from congress.tests import base

LOG = logging.getLogger(__name__)


class TestGraph(base.TestCase):
    def test_nodes(self):
        """Test addition/deletion of nodes."""
        g = utility.Graph()
        g.add_node(1)
        g.add_node(2)
        g.add_node(3)
        g.add_node(1)
        self.assertTrue(g.node_in(1))
        self.assertTrue(g.node_in(2))
        self.assertTrue(g.node_in(3))
        self.assertEqual(len(g), 3)

        g.delete_node(1)
        self.assertFalse(g.node_in(1))
        self.assertTrue(g.node_in(2))
        self.assertTrue(g.node_in(3))
        self.assertEqual(len(g), 2)

        g.delete_node(1)
        self.assertFalse(g.node_in(1))
        self.assertTrue(g.node_in(2))
        self.assertTrue(g.node_in(3))
        self.assertEqual(len(g), 2)

        g.add_node(1)
        self.assertTrue(g.node_in(1))
        self.assertTrue(g.node_in(2))
        self.assertTrue(g.node_in(3))
        self.assertEqual(len(g), 3)

        g.delete_node(2)
        self.assertTrue(g.node_in(1))
        self.assertFalse(g.node_in(2))
        self.assertTrue(g.node_in(3))
        self.assertEqual(len(g), 2)

    def test_edges(self):
        """Test addition/deletion of edges."""
        g = utility.Graph()

        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(2, 4)
        g.add_edge(1, 2)
        self.assertTrue(g.edge_in(1, 2))
        self.assertTrue(g.edge_in(2, 3))
        self.assertTrue(g.edge_in(2, 4))
        self.assertEqual(len(g), 7)

        g.delete_edge(2, 4)
        self.assertTrue(g.edge_in(1, 2))
        self.assertTrue(g.edge_in(2, 3))
        self.assertFalse(g.edge_in(2, 4))
        self.assertEqual(len(g), 6)

        g.delete_edge(2, 3)
        self.assertTrue(g.edge_in(1, 2))
        self.assertFalse(g.edge_in(2, 3))
        self.assertFalse(g.edge_in(2, 4))
        self.assertEqual(len(g), 5)

        g.delete_edge(2, 3)
        self.assertTrue(g.edge_in(1, 2))
        self.assertFalse(g.edge_in(2, 3))
        self.assertFalse(g.edge_in(2, 4))
        self.assertEqual(len(g), 5)

        g.add_edge(2, 3)
        self.assertTrue(g.edge_in(1, 2))
        self.assertTrue(g.edge_in(2, 3))
        self.assertFalse(g.edge_in(2, 4))
        self.assertEqual(len(g), 6)

    def test_or(self):
        g1 = utility.Graph()
        g1.add_edge(1, 2)
        g1.add_edge(2, 3)

        g2 = utility.Graph()
        g2.add_edge(2, 3)
        g2.add_edge(3, 4)

        g = g1 | g2
        self.assertTrue(g.edge_in(1, 2))
        self.assertTrue(g.edge_in(2, 3))
        self.assertTrue(g.edge_in(3, 4))
        self.assertTrue(isinstance(g, utility.Graph))
        self.assertTrue(g1.edge_in(1, 2))
        self.assertTrue(g1.edge_in(2, 3))
        self.assertFalse(g1.edge_in(3, 4))
        self.assertFalse(g2.edge_in(1, 2))
        self.assertTrue(g2.edge_in(2, 3))
        self.assertTrue(g2.edge_in(3, 4))

    def test_ior(self):
        g1 = utility.Graph()
        g1.add_edge(1, 2)
        g1.add_edge(2, 3)

        g2 = utility.Graph()
        g2.add_edge(2, 3)
        g2.add_edge(3, 4)

        g1 |= g2
        self.assertTrue(g1.edge_in(1, 2))
        self.assertTrue(g1.edge_in(2, 3))
        self.assertTrue(g1.edge_in(3, 4))
        self.assertFalse(g2.edge_in(1, 2))
        self.assertTrue(g2.edge_in(2, 3))
        self.assertTrue(g2.edge_in(3, 4))

    def test_cycle(self):
        g1 = utility.Graph()
        g1.add_edge(1, 2)
        self.assertFalse(g1.has_cycle())
        g1.add_edge(2, 3)
        self.assertFalse(g1.has_cycle())
        g1.add_edge(2, 4)
        self.assertFalse(g1.has_cycle())
        g1.add_edge(4, 1)
        self.assertTrue(g1.has_cycle())
        g1.delete_edge(2, 3)
        self.assertTrue(g1.has_cycle())
        g1.delete_edge(2, 4)
        self.assertFalse(g1.has_cycle())

    def test_dependencies(self):
        g1 = utility.Graph()
        self.assertIsNone(g1.dependencies(1))
        g1.add_edge(0, 1)
        g1.add_edge(1, 2)
        g1.add_edge(2, 3)
        g1.add_edge(2, 4)
        g1.add_edge(3, 5)
        g1.add_edge(0, 6)
        g1.add_edge(7, 8)
        g1.add_edge(8, 9)
        g1.add_edge(10, 5)
        g1.add_edge(11, 12)
        self.assertTrue(g1.dependencies(1), set([1, 2, 3, 4, 5]))
        self.assertTrue(g1.dependencies(10), set([10, 5]))
        self.assertTrue(g1.dependencies(5), set([5]))
        self.assertTrue(g1.dependencies(11), set([11, 12]))


class TestBagGraph(base.TestCase):
    def test_nodes(self):
        """Test addition/deletion of nodes."""
        g = utility.BagGraph()
        g.add_node(1)
        g.add_node(2)
        g.add_node(3)
        g.add_node(1)
        self.assertTrue(g.node_in(1))
        self.assertTrue(g.node_in(2))
        self.assertTrue(g.node_in(3))
        self.assertEqual(len(g), 4)

        g.delete_node(1)
        self.assertTrue(g.node_in(1))
        self.assertTrue(g.node_in(2))
        self.assertTrue(g.node_in(3))
        self.assertEqual(len(g), 3)

        g.delete_node(1)
        self.assertFalse(g.node_in(1))
        self.assertTrue(g.node_in(2))
        self.assertTrue(g.node_in(3))
        self.assertEqual(len(g), 2)

        g.add_node(1)
        self.assertTrue(g.node_in(1))
        self.assertTrue(g.node_in(2))
        self.assertTrue(g.node_in(3))
        self.assertEqual(len(g), 3)

        g.delete_node(2)
        self.assertTrue(g.node_in(1))
        self.assertFalse(g.node_in(2))
        self.assertTrue(g.node_in(3))
        self.assertEqual(len(g), 2)

    def test_edges(self):
        """Test addition/deletion of edges."""
        g = utility.BagGraph()

        g.add_edge(1, 2)
        g.add_edge(2, 3)
        g.add_edge(2, 4)
        g.add_edge(1, 2)
        self.assertTrue(g.edge_in(1, 2))
        self.assertTrue(g.edge_in(2, 3))
        self.assertTrue(g.edge_in(2, 4))
        self.assertEqual(len(g), 12)

        g.delete_edge(1, 2)
        self.assertTrue(g.edge_in(1, 2))
        self.assertTrue(g.edge_in(2, 3))
        self.assertTrue(g.edge_in(2, 4))
        self.assertEqual(len(g), 9)

        g.delete_edge(1, 2)
        self.assertFalse(g.edge_in(1, 2))
        self.assertTrue(g.edge_in(2, 3))
        self.assertTrue(g.edge_in(2, 4))
        self.assertEqual(len(g), 6)

        g.delete_edge(2, 3)
        self.assertFalse(g.edge_in(1, 2))
        self.assertFalse(g.edge_in(2, 3))
        self.assertTrue(g.edge_in(2, 4))
        self.assertEqual(len(g), 3)

        g.add_edge(1, 2)
        self.assertTrue(g.edge_in(1, 2))
        self.assertFalse(g.edge_in(2, 3))
        self.assertTrue(g.edge_in(2, 4))
        self.assertEqual(len(g), 6)

        g.add_node(1)
        self.assertEqual(g.node_count(1), 2)

    def test_edge_labels(self):
        g = utility.BagGraph()

        g.add_edge(1, 2)
        g.add_edge(1, 2, "label1")
        g.add_edge(1, 2, "label1")
        g.add_edge(1, 2, "label2")
        self.assertTrue(g.edge_in(1, 2))
        self.assertTrue(g.edge_in(1, 2, "label1"))
        self.assertTrue(g.edge_in(1, 2, "label2"))
        self.assertFalse(g.edge_in(1, 2, "non-existent"))
        self.assertEqual(g.edge_count(1, 2, "label1"), 2)

        g.delete_edge(1, 2, "label1")
        self.assertTrue(g.edge_in(1, 2))
        self.assertTrue(g.edge_in(1, 2, "label1"))
        self.assertTrue(g.edge_in(1, 2, "label2"))
        self.assertFalse(g.edge_in(1, 2, "non-existent"))
        self.assertEqual(g.edge_count(1, 2, "label1"), 1)

        g.delete_edge(1, 2, "label1")
        self.assertTrue(g.edge_in(1, 2))
        self.assertFalse(g.edge_in(1, 2, "label1"))
        self.assertTrue(g.edge_in(1, 2, "label2"))
        self.assertFalse(g.edge_in(1, 2, "non-existent"))
        self.assertEqual(g.edge_count(1, 2, "label1"), 0)

        g.delete_edge(1, 2, "label2")
        self.assertTrue(g.edge_in(1, 2))
        self.assertFalse(g.edge_in(1, 2, "label1"))
        self.assertFalse(g.edge_in(1, 2, "label2"))
        self.assertFalse(g.edge_in(1, 2, "non-existent"))
        self.assertEqual(g.edge_count(1, 2, "label1"), 0)

    def test_or(self):
        g1 = utility.BagGraph()
        g1.add_edge(1, 2)
        g1.add_edge(2, 3)

        g2 = utility.BagGraph()
        g2.add_edge(2, 3)
        g2.add_edge(3, 4)

        g = g1 | g2
        self.assertTrue(g.edge_in(1, 2))
        self.assertTrue(g.edge_in(2, 3))
        self.assertTrue(g.edge_in(3, 4))
        self.assertEqual(g.edge_count(2, 3), 2)
        self.assertTrue(isinstance(g, utility.Graph))
        self.assertTrue(g1.edge_in(1, 2))
        self.assertTrue(g1.edge_in(2, 3))
        self.assertFalse(g1.edge_in(3, 4))
        self.assertEqual(g1.edge_count(2, 3), 1)
        self.assertFalse(g2.edge_in(1, 2))
        self.assertTrue(g2.edge_in(2, 3))
        self.assertTrue(g2.edge_in(3, 4))
        self.assertEqual(g2.edge_count(2, 3), 1)

    def test_ior(self):
        g1 = utility.BagGraph()
        g1.add_edge(1, 2)
        g1.add_edge(2, 3)

        g2 = utility.BagGraph()
        g2.add_edge(2, 3)
        g2.add_edge(3, 4)

        g1 |= g2
        self.assertTrue(g1.edge_in(1, 2))
        self.assertTrue(g1.edge_in(2, 3))
        self.assertTrue(g1.edge_in(3, 4))
        self.assertTrue(isinstance(g1, utility.BagGraph))
        self.assertEqual(g1.edge_count(2, 3), 2)
        self.assertFalse(g2.edge_in(1, 2))
        self.assertTrue(g2.edge_in(2, 3))
        self.assertTrue(g2.edge_in(3, 4))
        self.assertEqual(g2.edge_count(2, 3), 1)

    def test_cycle(self):
        g1 = utility.BagGraph()
        g1.add_edge(1, 2)
        self.assertFalse(g1.has_cycle())
        g1.add_edge(2, 3)
        self.assertFalse(g1.has_cycle())
        g1.add_edge(2, 4)
        self.assertFalse(g1.has_cycle())
        g1.add_edge(2, 4)
        self.assertFalse(g1.has_cycle())
        g1.add_edge(4, 1)
        self.assertTrue(g1.has_cycle())
        g1.delete_edge(2, 3)
        self.assertTrue(g1.has_cycle())
        g1.delete_edge(2, 4)
        self.assertTrue(g1.has_cycle())
        g1.delete_edge(2, 4)
        self.assertFalse(g1.has_cycle())


class TestIterstr(base.TestCase):
    class X(object):
        def __init__(self, v):
            self.v = v

        def __str__(self):
            return "%s" % self.v

        def __repr__(self):
            return "X:%s" % self.v

    @contextlib.contextmanager
    def get_logging_fixtures(self):
        stream = StringIO.StringIO()
        handler = python_logging.StreamHandler(stream)
        try:
            logger = python_logging.getLogger(self.__class__.__name__)
            logger.setLevel(python_logging.INFO)
            handler.setLevel(python_logging.INFO)
            logger.addHandler(handler)
            try:
                yield (stream, handler, logger)
            finally:
                logger.removeHandler(handler)
        finally:
            handler.close()

    def test__str__returns_informal_representation(self):
        xs = map(TestIterstr.X, range(5))
        observed = utility.iterstr(xs)
        self.assertEqual("[0;1;2;3;4]", str(observed))
        self.assertEqual("[0;1;2;3;4]", "{}".format(observed))
        self.assertEqual("[0;1;2;3;4]", "%s" % observed)

    def test__repr__returns_formal_representation(self):
        xs = map(TestIterstr.X, range(5))
        observed = utility.iterstr(xs)
        self.assertEqual("[X:0;X:1;X:2;X:3;X:4]", repr(observed))
        self.assertEqual("[X:0;X:1;X:2;X:3;X:4]", "{!r}".format(observed))
        self.assertEqual("[X:0;X:1;X:2;X:3;X:4]", "%r" % observed)

    def test_empty(self):
        xs = map(TestIterstr.X, range(0))
        observed = utility.iterstr(xs)
        self.assertEqual("[]", str(observed))
        self.assertEqual("[]", repr(observed))

    def test_logging_basic_integration(self):
        with self.get_logging_fixtures() as (stream, handler, logger):
            iterable = utility.iterstr(map(TestIterstr.X, range(5)))
            logger.info("some message %s", iterable)
            handler.flush()
            self.assertEqual("some message [0;1;2;3;4]\n", stream.getvalue())

    def test_logging_skips_interpolation(self):
        with self.get_logging_fixtures() as (stream, handler, logger):
            iterable = utility.iterstr(map(TestIterstr.X, range(5)))
            logger.debug("some message %s", iterable)
            self.assertIsNone(iterable._str_interp)
