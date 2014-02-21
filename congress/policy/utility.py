#! /usr/bin/python
#
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


class Graph(object):
    """A standard graph data structure,
    with routines applicable to analysis of policy.
    """
    class dfs_data(object):
        def __init__(self, begin=None, end=None):
            self.begin = begin
            self.end = end

    class edge_data(object):
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
        if val not in self.nodes:
            self.nodes[val] = None

    def add_edge(self, val1, val2, label=None):
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
        possible_roots = set(self.nodes)
        for node in self.edges:
            for edge in self.edges[node]:
                if edge.node in possible_roots:
                    possible_roots.remove(edge.node)
        return possible_roots

    def has_cycle(self):
        if self.cycles is None:
            self.depth_first_search()
        return len(self.cycles) > 0

    def next_counter(self):
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
