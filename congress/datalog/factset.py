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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from oslo_log import log as logging

from congress.datalog import utility


LOG = logging.getLogger(__name__)


class FactSet(object):
    """FactSet

    Maintains a set of facts, and provides indexing for efficient iteration,
    given a partial or full match.  Expects that all facts are the same width.
    """

    def __init__(self):
        self._facts = utility.OrderedSet()

        # key is a sorted tuple of column indices, values are dict mapping a
        # specific value for the key to a set of Facts.
        self._indicies = {}

    def __contains__(self, fact):
        return fact in self._facts

    def __len__(self):
        return len(self._facts)

    def __iter__(self):
        return self._facts.__iter__()

    def add(self, fact):
        """Add a fact to the FactSet

        Returns True if the fact is absent from this FactSet and adds the
        fact, otherwise returns False.
        """
        assert isinstance(fact, tuple)
        changed = self._facts.add(fact)
        if changed:
            # Add the fact to the indicies
            try:
                for index in self._indicies.keys():
                    self._add_fact_to_index(fact, index)
            except Exception as e:
                self._facts.discard(fact)
                raise e
        return changed

    def remove(self, fact):
        """Remove a fact from the FactSet

        Returns True if the fact is in this FactSet and removes the fact,
        otherwise returns False.
        """
        changed = self._facts.discard(fact)
        if changed:
            # Remove from indices
            try:
                for index in self._indicies.keys():
                    self._remove_fact_from_index(fact, index)
            except Exception as e:
                self._facts.add(fact)
                raise e
        return changed

    def create_index(self, columns):
        """Create an index

        @columns is a tuple of column indicies that index into the facts in
        self.  @columns must be sorted in ascending order, and each column
        index must be less than the width of a fact in self.  If the index
        exists, do nothing.
        """
        assert sorted(columns) == list(columns)
        assert len(columns)

        if columns in self._indicies:
            return

        for f in self._facts:
            self._add_fact_to_index(f, columns)

    def remove_index(self, columns):
        """Remove an index

        @columns is a tuple of column indicies that index into the facts in
        self.  @columns must be sorted in ascending order, and each column
        index must be less than the width of a fact in self.  If the index
        does not exists, raise KeyError.
        """
        assert sorted(columns) == list(columns)
        if columns in self._indicies:
            del self._indicies[columns]

    def has_index(self, columns):
        """Returns True if the index exists."""
        return columns in self._indicies

    def find(self, partial_fact, iterations=None):
        """Find Facts given a partial fact

        @partial_fact is a tuple of pair tuples.  The first item in each
        pair tuple is an index into a fact, and the second item is a value to
        match again self._facts.  Expects the pairs to be sorted by index in
        ascending order.

        @iterations is either an empty list or None.  If @iterations is an
        empty list, then find() will append the number of iterations find()
        used to compute the return value(this is useful for testing indexing).

        Returns matching Facts.
        """
        index = tuple([i for i, v in partial_fact])
        k = tuple([v for i, v in partial_fact])
        if index in self._indicies:
            if iterations is not None:
                iterations.append(1)
            if k in self._indicies[index]:
                return self._indicies[index][k]
            else:
                return set()

        # There is no index, so iterate.
        matches = set()
        for f in self._facts:
            match = True
            for i, v in partial_fact:
                if f[i] != v:
                    match = False
                    break
            if match:
                matches.add(f)

        if iterations is not None:
            iterations.append(len(self._facts))
        return matches

    def _compute_key(self, columns, fact):
        # assumes that @columns is sorted in ascending order.
        return tuple([fact[i] for i in columns])

    def _add_fact_to_index(self, fact, index):
        if index not in self._indicies:
            self._indicies[index] = {}

        k = self._compute_key(index, fact)
        if k not in self._indicies[index]:
            self._indicies[index][k] = set((fact,))
        else:
            self._indicies[index][k].add(fact)

    def _remove_fact_from_index(self, fact, index):
        k = self._compute_key(index, fact)
        self._indicies[index][k].remove(fact)
        if not len(self._indicies[index][k]):
            del self._indicies[index][k]
