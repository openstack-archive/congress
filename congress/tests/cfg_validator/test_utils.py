# -*- coding: utf-8
#
# Copyright (c) 2017 Orange.
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

"""Test for utils"""

import re

from oslo_log import log as logging

from congress.cfg_validator import utils
from congress.tests import base

LOG = logging.getLogger(__name__)


class TestUtils(base.TestCase):
    """Test of generic utility functions"""

    def test_hash(self):
        """Test shape of hash generated"""
        re_hash = ('^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-'
                   '[0-9a-f]{4}-[0-9a-f]{8}')
        self.assertTrue(re.match(re_hash, utils.compute_hash('foo')))
        self.assertTrue(re.match(re_hash, utils.compute_hash('foo', 'bar')))

    def test_cfg_value_to_congress(self):
        """Test sanitization of values for congress"""
        self.assertEqual('aAdef', utils.cfg_value_to_congress('aA%def'))
        self.assertEqual(u'aAf', utils.cfg_value_to_congress(u'aAéf'))
        # Do not replace 0 with ''
        self.assertEqual(0, utils.cfg_value_to_congress(0))
        # Do not replace 0.0 with ''
        self.assertEqual(0.0, utils.cfg_value_to_congress(0.0))
        self.assertEqual('', utils.cfg_value_to_congress(None))

    def test_add_rules(self):
        """Test adding a rule via the bus"""
        class _bus(object):

            def rpc(self, svc, command, arg):
                "fake rpc"
                return {"svc": svc, "command": command, "arg": arg}

        res = utils.add_rule(_bus(), 'policy', ['r1', 'r2'])
        expected = {
            'arg': {'policy_rules_obj': {
                'kind': 'nonrecursive',
                'name': 'policy',
                'rules': ['r1', 'r2']}},
            'command': 'persistent_create_policy_with_rules',
            'svc': '__engine'}
        self.assertEqual(expected, res)
