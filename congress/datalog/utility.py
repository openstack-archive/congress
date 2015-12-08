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
from functools import reduce


class Graph(object):
    """A standard graph data structure.

    With routines applicable to analysis of policy.
    """
    class dfs_data(object):
        """Data for each node in graph during depth-first-search."""
        def __init__(self, begin=None, end=None):
            self.begin = begin
            self.end = end

        def __str__(self):
            return "<begin: %s, end: %s>" % (self.begin, self.end)

    class edge_data(object):
        """Data for each edge in graph."""
        def __init__(self, node=None, label=None):
            self.node = node
            self.label = label

        def __str__(self):
            return "<Label:%s, Node:%s>" % (self.label, self.node)

        def __eq__(self, other):
            return self.node == other.node and self.label == other.label

        def __hash__(self):
            return hash(str(self))

    def __init__(self, graph=None):
        self.edges = {}   # dict from node to list of nodes
        self.nodes = {}   # dict from node to info about node
        self._cycles = None

    def __or__(self, other):
        # do this the simple way so that subclasses get this code for free
        g = self.__class__()
        for node in self.nodes:
            g.add_node(node)
        for node in other.nodes:
            g.add_node(node)

        for name in self.edges:
            for edge in self.edges[name]:
                g.add_edge(name, edge.node, label=edge.label)
        for name in other.edges:
            for edge in other.edges[name]:
                g.add_edge(name, edge.node, label=edge.label)
        return g

    def __ior__(self, other):
        if len(other) == 0:
            # no changes if other is empty
            return self
        self._cycles = None
        for name in other.nodes:
            self.add_node(name)
        for name in other.edges:
            for edge in other.edges[name]:
                self.add_edge(name, edge.node, label=edge.label)
        return self

    def __len__(self):
        return (len(self.nodes) +
                reduce(lambda x, y: x+y,
                       (len(x) for x in self.edges.values()),
                       0))

    def add_node(self, val):
        """Add node VAL to graph."""
        if val not in self.nodes:  # preserve old node info
            self.nodes[val] = None
            return True
        return False

    def delete_node(self, val):
        """Delete node VAL from graph and all edges."""
        try:
            del self.nodes[val]
            del self.edges[val]
        except KeyError:
            assert val not in self.edges

    def add_edge(self, val1, val2, label=None):
        """Add edge from VAL1 to VAL2 with label LABEL to graph.

        Also adds the nodes.
        """
        self._cycles = None  # so that has_cycles knows it needs to rerun
        self.add_node(val1)
        self.add_node(val2)
        val = self.edge_data(node=val2, label=label)
        try:
            self.edges[val1].add(val)
        except KeyError:
            self.edges[val1] = set([val])

    def delete_edge(self, val1, val2, label=None):
        """Delete edge from VAL1 to VAL2 with label LABEL.

        LABEL must match (even if None).  Does not delete nodes.
        """
        try:
            edge = self.edge_data(node=val2, label=label)
            self.edges[val1].remove(edge)
        except KeyError:
            # KeyError either because val1 or edge
            return
        self._cycles = None

    def node_in(self, val):
        return val in self.nodes

    def edge_in(self, val1, val2, label=None):
        return (val1 in self.edges and
                self.edge_data(val2, label) in self.edges[val1])

    def reset_nodes(self):
        for node in self.nodes:
            self.nodes[node] = None

    def depth_first_search(self, roots=None):
        """Run depth first search on the graph.

        Also modify self.nodes, self.counter, and self.cycle.
        """
        self.reset()
        roots = roots or self.nodes
        for node in roots:
            if node in self.nodes and self.nodes[node].begin is None:
                self.dfs(node)

    def _enumerate_cycles(self):
        self.reset()
        for node in self.nodes.keys():
            self._reset_dfs_data()
            self.dfs(node, target=node)
            for path in self.__target_paths:
                self._cycles.add(Cycle(path))

    def reset(self, roots=None):
        """Return nodes to pristine state."""
        self._reset_dfs_data()
        roots = roots or self.nodes
        self._cycles = set()

    def _reset_dfs_data(self):
        for node in self.nodes.keys():
            self.nodes[node] = self.dfs_data()
        self.counter = 0
        self.__target_paths = []

    def dfs(self, node, target=None, dfs_stack=None):
        """DFS implementation.

        Assumes data structures have been properly prepared.
        Creates start/begin times on nodes.
        Adds paths from node to target to self.__target_paths
        """
        if dfs_stack is None:
            dfs_stack = []
        dfs_stack.append(node)
        if (target is not None and node == target and
                len(dfs_stack) > 1):  # non-trival path to target found
            self.__target_paths.append(list(dfs_stack))  # record
        if self.nodes[node].begin is None:
            self.nodes[node].begin = self.next_counter()
            if node in self.edges:
                for edge in self.edges[node]:
                    self.dfs(edge.node, target=target, dfs_stack=dfs_stack)
            self.nodes[node].end = self.next_counter()
        dfs_stack.pop()

    def stratification(self, labels):
        """Return the stratification result.

        Return mapping of node name to integer indicating the
        stratum to which that node is assigned. LABELS is the list
        of edge labels that dictate a change in strata.
        """
        stratum = {}
        for node in self.nodes:
            stratum[node] = 1
        changes = True
        while changes:
            changes = False
            for node in self.edges:
                for edge in self.edges[node]:
                    oldp = stratum[node]
                    if edge.label in labels:
                        stratum[node] = max(stratum[node],
                                            1 + stratum[edge.node])
                    else:
                        stratum[node] = max(stratum[node],
                                            stratum[edge.node])
                    if oldp != stratum[node]:
                        changes = True
                    if stratum[node] > len(self.nodes):
                        return None
        return stratum

    def roots(self):
        """Return list of nodes with no incoming edges."""
        possible_roots = set(self.nodes)
        for node in self.edges:
            for edge in self.edges[node]:
                if edge.node in possible_roots:
                    possible_roots.remove(edge.node)
        return possible_roots

    def has_cycle(self):
        """Checks if there are cycles.

        Run depth_first_search only if it has not already been run.
        """
        if self._cycles is None:
            self._enumerate_cycles()
        return len(self._cycles) > 0

    def cycles(self):
        """Return list of cycles. None indicates unknown. """
        if self._cycles is None:
            self._enumerate_cycles()
        cycles_list = []
        for cycle_graph in self._cycles:
            cycles_list.append(cycle_graph.list_repr())
        return cycles_list

    def dependencies(self, node):
        """Returns collection of node names reachable from NODE.

        If NODE does not exist in graph, returns None.
        """
        if node not in self.nodes:
            return None
        self.reset()
        node_obj = self.nodes[node]

        if node_obj is None or node_obj.begin is None or node_obj.end is None:
            self.depth_first_search([node])
            node_obj = self.nodes[node]
        return set([n for n, dfs_obj in self.nodes.items()
                    if dfs_obj.begin is not None])

    def next_counter(self):
        """Return next counter value and increment the counter."""
        self.counter += 1
        return self.counter - 1

    def __str__(self):
        s = "{"
        for node in self.nodes:
            s += "(" + str(node) + " : ["
            if node in self.edges:
                s += ", ".join([str(x) for x in self.edges[node]])
            s += "],\n"
        s += "}"
        return s

    def find_dependent_nodes(self, nodes):
        """Return all nodes dependent on @nodes.

        Node T is dependent on node T.
        Node T is dependent on node R if there is an edge from node S to T,
            and S is dependent on R.
        """
        # TODO(thinrichs): is it equivalent/better to invert all the edges
        #   and run depth-first-search?
        marked = set(nodes)  # copy so we can modify
        changed = True
        while changed:
            changed = False
            for node in self.edges:
                hasmarked = any(x.node in marked for x in self.edges[node])
                if hasmarked:
                    if node not in marked:
                        marked.add(node)
                        changed = True
        return marked

    def find_reachable_nodes(self, roots):
        """Return all nodes reachable from @roots."""
        self.depth_first_search(roots)
        result = [x for x in self.nodes if self.nodes[x].begin is not None]
        self.reset_nodes()
        return set(result)


class Cycle(frozenset):
    """An immutable set of 2-tuples to represent a directed cycle

    Extends frozenset, adding a list_repr method to represent a cycle as an
    ordered list of nodes.

    The set representation facilicates identity of cycles regardless of order.
    The list representation is much more readable.
    """
    def __new__(cls, cycle):
        edge_list = []
        for i in range(1, len(cycle)):
            edge_list.append((cycle[i - 1], cycle[i]))
        new_obj = super(Cycle, cls).__new__(cls, edge_list)
        new_obj.__list_repr = list(cycle)  # save copy as list_repr
        return new_obj

    def list_repr(self):
        """Return list-of-nodes representation of cycle"""
        return self.__list_repr


class BagGraph(Graph):
    """A graph data structure with bag semantics for nodes and edges.

    Keeps track of the number of times each node/edge has been inserted.
    A node/edge is removed from the graph only once it has been deleted
    the same number of times it was inserted.  Deletions when no node/edge
    already exist are ignored.
    """
    def __init__(self, graph=None):
        super(BagGraph, self).__init__(graph)
        self._node_refcounts = {}  # dict from node to counter
        self._edge_refcounts = {}  # dict from edge to counter

    def add_node(self, val):
        """Add node VAL to graph."""
        super(BagGraph, self).add_node(val)
        if val in self._node_refcounts:
            self._node_refcounts[val] += 1
        else:
            self._node_refcounts[val] = 1

    def delete_node(self, val):
        """Delete node VAL from graph (but leave all edges)."""
        if val not in self._node_refcounts:
            return
        self._node_refcounts[val] -= 1
        if self._node_refcounts[val] == 0:
            super(BagGraph, self).delete_node(val)
            del self._node_refcounts[val]

    def add_edge(self, val1, val2, label=None):
        """Add edge from VAL1 to VAL2 with label LABEL to graph.

        Also adds the nodes VAL1 and VAL2 (important for refcounting).
        """
        super(BagGraph, self).add_edge(val1, val2, label=label)
        edge = (val1, val2, label)
        if edge in self._edge_refcounts:
            self._edge_refcounts[edge] += 1
        else:
            self._edge_refcounts[edge] = 1

    def delete_edge(self, val1, val2, label=None):
        """Delete edge from VAL1 to VAL2 with label LABEL.

        LABEL must match (even if None).  Also deletes nodes
        whenever the edge exists.
        """
        edge = (val1, val2, label)
        if edge not in self._edge_refcounts:
            return
        self.delete_node(val1)
        self.delete_node(val2)
        self._edge_refcounts[edge] -= 1
        if self._edge_refcounts[edge] == 0:
            super(BagGraph, self).delete_edge(val1, val2, label=label)
            del self._edge_refcounts[edge]

    def node_in(self, val):
        return val in self._node_refcounts

    def edge_in(self, val1, val2, label=None):
        return (val1, val2, label) in self._edge_refcounts

    def node_count(self, node):
        if node in self._node_refcounts:
            return self._node_refcounts[node]
        else:
            return 0

    def edge_count(self, val1, val2, label=None):
        edge = (val1, val2, label)
        if edge in self._edge_refcounts:
            return self._edge_refcounts[edge]
        else:
            return 0

    def __len__(self):
        return (reduce(lambda x, y: x+y, self._node_refcounts.values(), 0) +
                reduce(lambda x, y: x+y, self._edge_refcounts.values(), 0))

    def __str__(self):
        s = "{"
        for node in self.nodes:
            s += "(%s *%s: [" % (str(node), self._node_refcounts[node])
            if node in self.edges:
                s += ", ".join(
                    ["%s *%d" %
                        (str(x), self.edge_count(node, x.node, x.label))
                        for x in self.edges[node]])
            s += "],\n"
        s += "}"
        return s


class OrderedSet(collections.MutableSet):
    """Provide sequence capabilities with rapid membership checks.

    Mostly lifted from the activestate recipe[1] linked at Python's collections
    documentation[2]. Some modifications, such as returning True or False from
    add(key) and discard(key) if a change is made.

    [1] - http://code.activestate.com/recipes/576694/
    [2] - https://docs.python.org/2/library/collections.html
    """
    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]         # sentinel node for doubly linked list
        self.map = {}                   # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]
            return True
        return False

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev
            return True
        return False

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('pop from an empty set')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        else:
            return False


class iterstr(object):
    """Lazily provides informal string representation of iterables.

    Calling __str__ directly on iterables returns a string containing the
    formal representation of the elements. This class wraps the iterable and
    instead returns the informal representation of the elements.
    """

    def __init__(self, iterable):
        self.iterable = iterable
        self._str_interp = None
        self._repr_interp = None

    def __str__(self):
        if self._str_interp is None:
            self._str_interp = "[" + ";".join(map(str, self.iterable)) + "]"
        return self._str_interp

    def __repr__(self):
        if self._repr_interp is None:
            self._repr_interp = "[" + ";".join(map(repr, self.iterable)) + "]"
        return self._repr_interp
