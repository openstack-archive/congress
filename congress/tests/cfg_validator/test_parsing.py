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

"""Tests for the unmarshaling of options by the driver"""

from oslo_config import cfg
from oslo_config import types
from oslo_log import log as logging

from congress.cfg_validator import parsing
from congress.tests import base

LOG = logging.getLogger(__name__)


OPT_TEST = {
    u'positional': False, u'kind': u'BoolOpt',
    u'deprecated_reason': None,
    u'help': u'Enables or disables inter-process locks.',
    u'default': False, u'type': {u'type': u'Boolean'},
    u'required': False, u'sample_default': None,
    u'deprecated_opts': [{u'group': u'DEFAULT', u'name': None}],
    u'deprecated_for_removal': False,
    u'dest': u'disable_process_locking',
    u'secret': False, u'short': None, u'mutable': False,
    u'deprecated_since': None, u'metavar': None,
    u'advanced': False, u'name': u'disable_process_locking'}
DICT_NS_TEST = {
    u'DEFAULT': {u'object': None, u'namespaces': []},
    u'oslo_concurrency': {
        u'object': None,
        u'namespaces': [[u'oslo.concurrency', [OPT_TEST]]]}}


class TestParsing(base.TestCase):
    """Tests for the unmarshaling of options by the driver"""

    def test_add_namespace(self):
        """Test for adding a namespace"""
        conf = cfg.ConfigOpts()
        initial_keys_len = len(conf.keys())
        parsing.add_namespace(conf, DICT_NS_TEST, 'abcde-12345')
        keys = conf.keys()
        self.assertEqual(initial_keys_len + 1, len(keys))
        self.assertIn(u'oslo_concurrency', keys)
        self.assertIsNotNone(
            conf.get(u'oslo_concurrency').get(u'disable_process_locking'))

    def test_construct_conf_manager(self):
        """Test for building a conf manager"""
        initial_keys_len = len(cfg.ConfigOpts().keys())
        conf = parsing.construct_conf_manager([DICT_NS_TEST])
        self.assertIsInstance(conf, cfg.ConfigOpts)
        keys = conf.keys()
        self.assertEqual(initial_keys_len + 1, len(keys))
        self.assertIn(u'oslo_concurrency', keys)

    def test_make_group(self):
        """Test for parsing a group"""
        grp = parsing.make_group('group', 'group_title', 'group help')
        self.assertIsInstance(grp, cfg.OptGroup)
        self.assertEqual("group", grp.name)
        self.assertEqual("group_title", grp.title)

    def test_make_opt(self):
        """Test for parsing an option"""
        descr = {
            u'positional': False,
            u'kind': u'Opt',
            u'deprecated_reason': None,
            u'help': u'Help me',
            u'default': None,
            u'type': {u'type': u'String'},
            u'required': False, u'sample_default': None,
            u'deprecated_opts': [], u'deprecated_for_removal': False,
            u'dest': u'name',
            u'secret': False,
            u'short': None,
            u'mutable': False,
            u'deprecated_since': None,
            u'metavar': None,
            u'advanced': False,
            u'name': u'name'}
        opt = parsing.make_opt(descr, 'abcd-1234', 'efgh-5678')
        self.assertIsInstance(opt, parsing.IdentifiedOpt)
        self.assertEqual("name", opt.name)
        self.assertEqual('abcd-1234', opt.id_)
        self.assertEqual('efgh-5678', opt.ns_id)

    def test_make_type(self):
        """Test for parsing a type"""
        typ1 = parsing.make_type({u'type': u'String'})
        self.assertIsInstance(typ1, types.String)
        typ2 = parsing.make_type({u'type': u'Integer'})
        self.assertIsInstance(typ2, types.Integer)
        typ3 = parsing.make_type(
            {u'item_type': {u'type': u'Boolean'}, u'type': u'List'})
        self.assertIsInstance(typ3, types.List)
        self.assertIsInstance(typ3.item_type, types.Boolean)
