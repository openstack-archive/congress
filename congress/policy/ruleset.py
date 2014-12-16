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
    def __init__(self):
        self.contents = {}

    def __str__(self):
        return str(self.contents)

    def add_rule(self, key, rule):
        # returns True on change
        if key in self.contents:
            return self.contents[key].add(rule)
        else:
            self.contents[key] = utility.OrderedSet([rule])
            return True

    def discard_rule(self, key, rule):
        # returns True on change
        if key in self.contents:
            changed = self.contents[key].discard(rule)
            if len(self.contents[key]) == 0:
                del self.contents[key]
            return changed
        return False

    def keys(self):
        return self.contents.keys()

    def __contains__(self, key):
        return key in self.contents

    def get_rules(self, key):
        return list(self.contents[key])

    def clear(self):
        self.contents = {}
