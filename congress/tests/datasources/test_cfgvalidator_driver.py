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
"""Test the configuration validator driver"""

import mock
from oslo_config import cfg
from oslo_config import types
from oslo_log import log as logging
import six
from testtools.content import text_content

from congress.datasources import cfgvalidator_driver
from congress.tests import base
from congress.tests import base_rpc
from congress.tests import helper

LOG = logging.getLogger(__name__)


# pylint: disable=protected-access
def _fake_conf():
    conf = mock.MagicMock()
    conf._namespace = 'ns'
    opt1 = mock.MagicMock()
    opt1.id_ = 'ho1'
    opt1.name = 'o1'
    opt1.type = types.String
    opt1.ns_id = 'ns'
    opt2 = mock.MagicMock()
    opt2.id_ = 'ho2'
    opt2.name = 'o2'
    opt2.type = types.String
    opt2.ns_id = 'ns'
    group = mock.MagicMock()
    group._opts = {'o2': {'opt': opt2}}
    conf._groups = {'g': group}
    conf._opts = {'o1': {'opt': opt1}}
    return conf


class TestCfgValidatorDriver(base.TestCase):
    """Test the configuration validator driver"""
    def setUp(self):
        super(TestCfgValidatorDriver, self).setUp()
        args = helper.datasource_openstack_args()
        with mock.patch('congress.datasources.cfgvalidator_driver.'
                        'ValidatorAgentClient',
                        spec=cfgvalidator_driver.ValidatorAgentClient) as agm:
            self.driver = cfgvalidator_driver.ValidatorDriver(args=args)
            self.agent_mock = agm
        self.driver.node = mock.MagicMock()

        for table in cfgvalidator_driver.ValidatorDriver.get_schema():
            self.driver.state[table] = set()

    def test_get_info(self):
        """Test info retrieval on datasource. Minimal requirements"""
        info = self.driver.get_datasource_info()
        self.assertIsNotNone(info['id'])
        self.assertIsNotNone(info['description'])
        self.assertIsNotNone(info['config'])

    def test_translate_type(self):
        """Test the translation of type"""
        cases = [
            {
                'inputs': ['lorem',
                           types.String(choices=['foo'], max_length=4)],
                'expected': {
                    cfgvalidator_driver.STR_TYPE:
                        (u'lorem', u'', 4, u'False', u'False', u'[\'foo\']')}
            },
            {
                'inputs': ['lorem', types.Integer(choices=[1], min=1, max=2)],
                'expected': {
                    cfgvalidator_driver.INT_TYPE: (u'lorem', 1, 2, u'[1]')}
            },
            {
                'inputs': ['lorem', types.Float(min=1, max=2)],
                'expected': {cfgvalidator_driver.FLOAT_TYPE: (u'lorem', 1, 2)}
            },
            {
                'inputs': ['lorem', types.List(item_type=types.Float(min=1))],
                'expected': {
                    cfgvalidator_driver.LIST_TYPE: (
                        u'lorem', u'Float', u'False'),
                    cfgvalidator_driver.FLOAT_TYPE: (u'lorem', 1, u''), }
            },
            {
                'inputs': ['lorem', types.URI(max_length=2, schemes=['HTTP'])],
                'expected': {
                    cfgvalidator_driver.URI_TYPE: (u'lorem', 2, u'[\'HTTP\']')}
            },
            {
                'inputs': ['lorem', types.Range(min=1, max=2)],
                'expected': {cfgvalidator_driver.RANGE_TYPE: (u'lorem', 1, 2)}
            },
        ]

        for case in cases:
            self.driver.translate_type(*case['inputs'])

        for case in cases:
            for table_name, expected in six.iteritems(case['expected']):
                table = self.driver.state[table_name]

                if expected:
                    self.assertIn(expected, table)

    def test_translate_host(self):
        """Test the translation of host"""
        cases = [
            ('lorem', 'ipsum', (u'lorem', u'ipsum')),
            (None, 'ipsum', None),
            ('', 'ipsum', None),
            ('lorem', None, (u'lorem', u'')),
            ('lorem', '', (u'lorem', u'')),
        ]

        for host_id, host_name, _ in cases:
            self.driver.translate_host(host_id, host_name)

        table = self.driver.state[cfgvalidator_driver.HOST]

        for _, _, expected in cases:
            if expected:
                self.assertIn(expected, table)

        expected_size = len(set([c[-1] for c in cases if c[-1]]))
        self.assertEqual(len(table), expected_size)

    def test_translate_file(self):
        """Test the translation of file"""
        cases = [
            ('lorem', 'ipsum', 'dolor', 'sit',
             (u'lorem', u'ipsum', u'dolor', u'sit')),
            ('lorem', 'ipsum', None, '', (u'lorem', u'ipsum', u'', u'')),
            ('lorem', 'ipsum', '', None, (u'lorem', u'ipsum', u'', u'')),
            (None, 'ipsum', 'dolor', 'sit', None),
            ('', 'ipsum', 'dolor', 'sit', None),
            ('lorem', '', 'dolor', 'sit', None),
            ('lorem', None, 'dolor', 'sit', None),
        ]

        for file_id, host_id, template_h, file_name, _ in cases:
            self.driver.translate_file(file_id, host_id, template_h,
                                       file_name)

        table = self.driver.state[cfgvalidator_driver.FILE]

        for _, _, _, _, expected in cases:
            if expected:
                self.assertIn(expected, table)

        expected_size = len(set([c[-1] for c in cases if c[-1]]))
        self.assertEqual(len(table), expected_size)

    def test_translate_template_ns(self):
        """Test the translation of namespace"""
        cases = [
            {
                'inputs': [
                    'lorem',
                    '',
                    {None: 'sit', 'amet': 'consectetur'}
                ],
                'expected': {
                    cfgvalidator_driver.TEMPLATE: (u'lorem', u''),
                    cfgvalidator_driver.NAMESPACE: (u'amet', u'consectetur'),
                    cfgvalidator_driver.TEMPLATE_NS: (u'lorem', u'amet'),
                }
            },
            {
                'inputs': [
                    '',
                    'ipsum',
                    {'dolor': 'sit', 'amet': ''}
                ],
                'expected': {
                    cfgvalidator_driver.TEMPLATE: None,
                    cfgvalidator_driver.NAMESPACE: None,
                    cfgvalidator_driver.TEMPLATE_NS: None,
                }
            },
            {
                'inputs': [
                    'lorem',
                    'ipsum',
                    {'dolor': 'sit'}
                ],
                'expected': {
                    cfgvalidator_driver.TEMPLATE: (u'lorem', u'ipsum'),
                    cfgvalidator_driver.NAMESPACE: (u'dolor', u'sit'),
                    cfgvalidator_driver.TEMPLATE_NS: (u'lorem', u'dolor'),
                }
            }
        ]

        for case in cases:
            self.driver.translate_template_namespace(*case['inputs'])

        for case in cases:
            for table_name, expected in six.iteritems(case['expected']):
                table = self.driver.state[table_name]

                if expected:
                    self.assertIn(expected, table)

        for table_name in [cfgvalidator_driver.TEMPLATE,
                           cfgvalidator_driver.NAMESPACE,
                           cfgvalidator_driver.TEMPLATE_NS]:
            expected_size = len(
                set([c['expected'][table_name] for c in cases
                     if c['expected'][table_name]]))
            table = self.driver.state[table_name]
            self.addDetail('table name', text_content(table_name))
            self.assertEqual(len(table), expected_size)

    def test_translate_option(self):
        """Unit tests for the translation of option definitions"""
        opt = cfg.StrOpt('host', required=True)
        opt.id_ = 'hash_opt'
        opt.ns_id = 'hash_ns'
        self.driver.translate_option(opt, "group")
        self.assertIsNotNone(self.driver.state['option'])
        self.assertIsNotNone(self.driver.state['option_info'])
        self.assertEqual(1, len(self.driver.state['option']))
        self.assertEqual(1, len(self.driver.state['option_info']))

    def test_translate_value(self):
        """Unit tests for translation of option values"""
        self.driver.translate_value("fid", 'optid1', 0)
        self.driver.translate_value("fid", 'optid2', [1, 2, 3])
        self.driver.translate_value("fid", 'optid3', {'a': 4, 'b': 5})
        self.assertEqual(6, len(self.driver.state['binding']))

    def test_translate_service(self):
        """Unit tests for translation of services"""
        self.driver.translate_service("hid", "svc", "vname")
        self.assertEqual(1, len(self.driver.state['service']))

    def test_process_template_hashes(self):
        """Test processing of template hash"""
        agent = self.agent_mock.return_value
        agent.get_template.return_value = {'namespaces': ['ns']}
        self.driver.process_template_hashes(['t1', 't2'], 'h')
        self.assertEqual(2, agent.get_template.call_count)
        self.assertEqual(1, agent.get_namespace.call_count)

    def test_translate_conf(self):
        """Test translation of conf"""
        self.driver.translate_conf(_fake_conf(), 'fid')
        state = self.driver.state
        self.assertEqual(2, len(state['option']))
        self.assertEqual(2, len(state['option_info']))
        self.assertEqual(2, len(state['binding']))

    @mock.patch('congress.cfg_validator.parsing.construct_conf_manager')
    @mock.patch('congress.cfg_validator.parsing.add_parsed_conf')
    def test_process_config(self, parsing_ccm, _):
        """Test complete processing of a conf"""
        parsing_ccm.return_value = _fake_conf()
        conf = {
            'template': 't',
            'service': 's',
            'version': 'v',
            'path': '/path/to/c',
            'data': {}
        }
        self.driver.known_templates['t'] = mock.MagicMock()
        self.driver.process_config('fhash', conf, 'h')
        state = self.driver.state
        self.assertEqual(1, len(state['service']))
        self.assertEqual(1, len(state['host']))
        self.assertEqual(1, len(state['template']))
        self.assertEqual(1, len(state['file']))

    @mock.patch('congress.cfg_validator.parsing.construct_conf_manager')
    @mock.patch('congress.cfg_validator.parsing.add_parsed_conf')
    def test_process_config_hashes(self, parsing_ccm, _):
        """Test processing of configuration hashes"""
        parsing_ccm.return_value = _fake_conf()
        conf = {
            'template': 't',
            'service': 's',
            'version': 'v',
            'path': '/path/to/c',
            'data': {}
        }
        self.agent_mock.return_value.get_config.return_value = conf
        self.driver.known_templates['t'] = mock.MagicMock()
        self.driver.process_config_hashes(['c'], 'h')
        state = self.driver.state
        self.assertEqual(1, len(state['service']))
        self.assertEqual(1, len(state['host']))
        self.assertEqual(1, len(state['template']))
        self.assertEqual(1, len(state['file']))

    def test_poll(self):
        """Test poll"""
        self.driver.poll()
        agt = self.agent_mock.return_value
        self.assertEqual(1, agt.publish_templates_hashes.call_count)
        self.assertEqual(1, agt.publish_configs_hashes.call_count)


class TestValidatorAgentClient(base_rpc.BaseTestRpcClient):
    """Unit tests for the RPC calls on the agent side"""
    def test_publish_config_hashes(self):
        "Test publish_config_hashes"
        rpcapi = cfgvalidator_driver.ValidatorAgentClient()
        self._test_rpc_api(
            rpcapi,
            None,
            'publish_configs_hashes',
            rpc_method='cast', fanout=True
        )

    def test_publish_templates_hashes(self):
        "Test publish_templates_hashes"
        rpcapi = cfgvalidator_driver.ValidatorAgentClient()
        self._test_rpc_api(
            rpcapi,
            None,
            'publish_templates_hashes',
            rpc_method='cast', fanout=True
        )

    def test_get_namespace(self):
        "test get_namespace"
        rpcapi = cfgvalidator_driver.ValidatorAgentClient()
        self._test_rpc_api(
            rpcapi,
            None,
            'get_namespace',
            rpc_method='call', server="host",
            ns_hash='fake_hash'
        )

    # block calling thread
    def test_get_template(self):
        "test get_template"
        rpcapi = cfgvalidator_driver.ValidatorAgentClient()
        self._test_rpc_api(
            rpcapi,
            None,
            'get_template',
            rpc_method='call', server="host",
            tpl_hash='fake_hash'
        )

    # block calling thread
    def test_get_config(self):
        "test get_config"
        rpcapi = cfgvalidator_driver.ValidatorAgentClient()
        self._test_rpc_api(
            rpcapi,
            None,
            'get_config',
            rpc_method='call', server="host",
            cfg_hash='fake_hash'
        )
