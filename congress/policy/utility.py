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


class Graph(object):
    """A standard graph data structure,
    with routines applicable to analysis of policy.
    """
    class dfs_data(object):
        """Data for each node in graph during depth-first-search."""
        def __init__(self, begin=None, end=None):
            self.begin = begin
            self.end = end

    class edge_data(object):
        """Data for each edge in graph."""
        def __init__(self, node=None, label=None):
            self.node = node
            self.label = label

        def __str__(self):
            return "<Label:{}, Node:{}>".format(self.label, self.node)

    def __init__(self):
        self.edges = {}   # dict from node to list of nodes
        self.nodes = {}   # dict from node to info about node
        self.cycles = None

    def add_node(self, val):
        """Add node VAL to graph."""
        if val not in self.nodes:
            self.nodes[val] = None

    def add_edge(self, val1, val2, label=None):
        """Add edge from VAL1 to VAL2 with label LABEL to graph.
        Also adds the nodes, if they are not already present.
        """
        self.cycles = None  # so that has_cycles knows it needs to rerun
        self.add_node(val1)
        self.add_node(val2)
        val = self.edge_data(node=val2, label=label)
        if val1 in self.edges:
            self.edges[val1].append(val)
        else:
            self.edges[val1] = [val]

    def depth_first_search(self):
        """Run depth first search on the graph, modifying self.nodes,
        self.counter, and self.cycle.
        """
        for node in self.nodes:
            self.nodes[node] = self.dfs_data()
        self.counter = 0
        self.cycles = []
        self.backpath = {}
        for node in self.nodes:
            if self.nodes[node].begin is None:
                self.dfs(node)

    def dfs(self, node):
        """DFS implementation. Assumes data structures have been properly
        prepared.  Creates start/begin times on nodes and adds
        to self.cycles.
        """
        self.nodes[node].begin = self.next_counter()
        if node in self.edges:
            for edge in self.edges[node]:
                self.backpath[edge.node] = node
                if self.nodes[edge.node].begin is None:
                    self.dfs(edge.node)
                elif self.nodes[edge.node].end is None:
                    cycle = self.construct_cycle(edge.node, self.backpath)
                    self.cycles.append(cycle)
        self.nodes[node].end = self.next_counter()

    def construct_cycle(self, node, history):
        """Construct a cycle ending at node NODE after having traversed
        the nodes in the list HISTORY.
        """
        prev = history[node]
        sofar = [prev]
        while prev != node:
            prev = history[prev]
            sofar.append(prev)
        sofar.append(node)
        sofar.reverse()
        return sofar

    def stratification(self, labels):
        """Return mapping of node name to integer indicating the
        stratum to which that node is assigned.  LABELS is the list
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
        """Checks if there are cycles, running depth_first_search only if it
        has not already been run.
        """
        if self.cycles is None:
            self.depth_first_search()
        return len(self.cycles) > 0

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
