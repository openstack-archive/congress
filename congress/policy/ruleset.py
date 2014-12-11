# Copyright (c) 2014 VMware, Inc. All rights reserved.
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

from congress.openstack.common import log as logging
from congress.policy import utility

LOG = logging.getLogger(__name__)


class RuleSet(object):
    """RuleSet

    Keeps track of all rules for all tables.  Also manages indicies that allow
    a caller to get all rules that match a certain literal pattern.
    """

    # Internally:
    #  An index_name looks like this: (p, (2, 4)) which means this index is
    #  on table 'p' and it specifies columns 2 and 4.
    #
    #  An index_key looks like this: (p, (2, 'abc'), (4, 'def'))

    def __init__(self):
        self.rules = {}
        self.literals = {}
        self.indicies = {}

    def __str__(self):
        return str(self.rules) + " " + str(self.literals)

    def add_rule(self, key, rule):
        # rule can be a rule or a literal
        # returns True on change

        if len(rule.body):
            dest = self.rules
        else:
            dest = self.literals
            # Update indicies
            for index_name in self.indicies.keys():
                if key == index_name[0]:
                    self._add_literal_to_index(rule, index_name)

        if key in dest:
            return dest[key].add(rule)
        else:
            dest[key] = utility.OrderedSet([rule])
            return True

    def discard_rule(self, key, rule):
        # rule can be a rule or a literal
        # returns True on change

        if len(rule.body):
            dest = self.rules
        else:
            dest = self.literals
            # Update indicies
            for index_name in self.indicies.keys():
                if key == index_name[0]:
                    self._remove_literal_from_index(rule, index_name)

        if key in dest:
            changed = dest[key].discard(rule)
            if len(dest[key]) == 0:
                del dest[key]
            return changed
        return False

    def keys(self):
        return self.literals.keys() + self.rules.keys()

    def __contains__(self, key):
        return key in self.literals or key in self.rules

    def get_rules(self, key, match_literal=None):
        literals = []

        if match_literal and not match_literal.is_negated():
            bound_arguments = tuple([i for i, arg
                                     in enumerate(match_literal.arguments)
                                     if not arg.is_variable()])
            index_name = (key,) + bound_arguments

            index_key = tuple([(i, arg.name) for i, arg
                               in enumerate(match_literal.arguments)
                               if not arg.is_variable()])
            index_key = (key,) + index_key

            if index_name not in self.indicies:
                self._create_index(index_name)

            literals = list(self.indicies[index_name].get(index_key, ()))
        else:
            literals = list(self.literals.get(key, ()))

        return literals + list(self.rules.get(key, ()))

    def clear(self):
        self.rules = {}
        self.literals = {}

    def _create_index(self, index_name):
        # Make an index over literals.  An index is an OrderedSet of rules.
        self.indicies[index_name] = {}  # utility.OrderedSet()
        if index_name[0] in self.literals:
            for literal in self.literals[index_name[0]]:
                self._add_literal_to_index(literal, index_name)

    def _add_literal_to_index(self, literal, index_name):
        index_key = ((index_name[0],) +
                     tuple([(i, literal.head.arguments[i].name)
                            for i in index_name[1:]]))

        # Populate the index
        if index_key not in self.indicies[index_name]:
            self.indicies[index_name][index_key] = utility.OrderedSet()
        self.indicies[index_name][index_key].add(literal)

    def _remove_literal_from_index(self, literal, index_name):
        index_key = ((index_name[0],) +
                     tuple([(i, literal.head.arguments[i].name)
                            for i in index_name[1:]]))

        self.indicies[index_name][index_key].discard(literal)
        if len(self.indicies[index_name][index_key]) == 0:
            del self.indicies[index_name][index_key]
