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

from congress.datalog.compile import Fact
from congress.datalog.compile import Literal
from congress.datalog.compile import Rule
from congress.datalog.factset import FactSet
from congress.datalog import utility
from congress.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class RuleSet(object):
    """RuleSet

    Keeps track of all rules for all tables.
    """

    # Internally:
    #  An index_name looks like this: (p, (2, 4)) which means this index is
    #  on table 'p' and it specifies columns 2 and 4.
    #
    #  An index_key looks like this: (p, (2, 'abc'), (4, 'def'))

    def __init__(self):
        self.rules = {}
        self.facts = {}

    def __str__(self):
        return str(self.rules) + " " + str(self.facts)

    def add_rule(self, key, rule):
        """Add a rule to the Ruleset

        @rule can be a Rule or a Fact. Returns True if add_rule() changes the
        RuleSet.
        """
        if isinstance(rule, Fact):
            # If the rule is a Fact, then add it to self.facts.
            if key not in self.facts:
                self.facts[key] = FactSet()
            return self.facts[key].add(rule)

        elif len(rule.body) == 0 and not rule.head.is_negated():
            # If the rule is a Rule, with no body, then it's a Fact, so
            # convert the Rule to a Fact to a Fact and add to self.facts.
            f = Fact(key, (a.name for a in rule.head.arguments))
            if key not in self.facts:
                self.facts[key] = FactSet()
            return self.facts[key].add(f)

        else:
            # else the rule is a regular rule, so add it to self.rules.
            if key in self.rules:
                return self.rules[key].add(rule)
            else:
                self.rules[key] = utility.OrderedSet([rule])
                return True

    def discard_rule(self, key, rule):
        """Remove a rule from the Ruleset

        @rule can be a Rule or a Fact. Returns True if discard_rule() changes
        the RuleSet.
        """
        if isinstance(rule, Fact):
            # rule is a Fact, so remove from self.facts
            if key in self.facts:
                changed = self.facts[key].remove(rule)
                if len(self.facts[key]) == 0:
                    del self.facts[key]
                return changed
            return False

        elif not len(rule.body):
            # rule is a Rule, but without a body so it will be in self.facts.
            if key in self.facts:
                fact = Fact(key, [a.name for a in rule.head.arguments])
                changed = self.facts[key].remove(fact)
                if len(self.facts[key]) == 0:
                    del self.facts[key]
                return changed
            return False

        else:
            # rule is a Rule with a body, so remove from self.rules.
            if key in self.rules:
                changed = self.rules[key].discard(rule)
                if len(self.rules[key]) == 0:
                    del self.rules[key]
                return changed
            return False

    def keys(self):
        return self.facts.keys() + self.rules.keys()

    def __contains__(self, key):
        return key in self.facts or key in self.rules

    def get_rules(self, key, match_literal=None):
        facts = []

        if (match_literal and not match_literal.is_negated() and
                key in self.facts):
            # If the caller supplies a literal to match against, then use an
            # index to find the matching rules.
            bound_arguments = tuple([i for i, arg
                                     in enumerate(match_literal.arguments)
                                     if not arg.is_variable()])
            if (bound_arguments and
                    not self.facts[key].has_index(bound_arguments)):
                # The index does not exist, so create it.
                self.facts[key].create_index(bound_arguments)

            partial_fact = tuple(
                [(i, arg.name)
                 for i, arg in enumerate(match_literal.arguments)
                 if not arg.is_variable()])
            facts = list(self.facts[key].find(partial_fact))
        else:
            # There is no usable match_literal, so get all facts for the
            # table.
            facts = list(self.facts.get(key, ()))

        # Convert native tuples to Rule objects.

        # TODO(alex): This is inefficient because it creates Literal and Rule
        # objects.  It would be more efficient to change the TopDownTheory and
        # unifier to handle Facts natively.
        fact_rules = []
        for fact in facts:
            literal = Literal.create_from_table_tuple(key, fact)
            fact_rules.append(Rule(literal, ()))

        return fact_rules + list(self.rules.get(key, ()))

    def clear(self):
        self.rules = {}
        self.facts = {}

    def clear_table(self, table):
        self.rules[table] = utility.OrderedSet()
        self.facts[table] = FactSet()
