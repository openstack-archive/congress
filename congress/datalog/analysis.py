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

# TODO(thinrichs): move algorithms from compile.py that do analysis
# into this file.

import copy


class ModalIndex(object):
    def __init__(self):
        # Dict mapping modal name to a ref-counted list of tablenames
        # Refcounted list of tablenames is a dict from tablename to count
        self.index = {}

    def add(self, modal, tablename):
        if modal not in self.index:
            self.index[modal] = {}
        if tablename not in self.index[modal]:
            self.index[modal][tablename] = 0
        self.index[modal][tablename] += 1

    def remove(self, modal, tablename):
        if modal not in self.index:
            raise KeyError("Modal %s has no entries" % modal)
        if tablename not in self.index[modal]:
            raise KeyError("Tablename %s for modal %s does not exist" %
                           (tablename, modal))
        self.index[modal][tablename] -= 1
        self._clean_up(modal, tablename)

    def modals(self):
        return self.index.keys()

    def tables(self, modal):
        if modal not in self.index:
            return []
        return self.index[modal].keys()

    def __isub__(self, other):
        changes = []
        for modal in self.index:
            if modal not in other.index:
                continue
            for table in self.index[modal]:
                if table not in other.index[modal]:
                    continue
                self.index[modal][table] -= other.index[modal][table]
                changes.append((modal, table))

        for (modal, table) in changes:
            self._clean_up(modal, table)
        return self

    def __iadd__(self, other):
        for modal in other.index:
            if modal not in self.index:
                self.index[modal] = other.index[modal]
                continue
            for table in other.index[modal]:
                if table not in self.index[modal]:
                    self.index[modal][table] = other.index[modal][table]
                    continue
                self.index[modal][table] += other.index[modal][table]
        return self

    def _clean_up(self, modal, table):
        if self.index[modal][table] <= 0:
            del self.index[modal][table]
        if not len(self.index[modal]):
            del self.index[modal]

    def __eq__(self, other):
        return self.index == other.index

    def __neq__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new = ModalIndex()
        new.index = copy.deepcopy(self.index)
        return new

    def __str__(self):
        return str(self.index)

    def __contains__(self, modal):
        return modal in self.index
