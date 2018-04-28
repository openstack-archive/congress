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
"""Tests for the config validator agent."""

from os import path

import json
import mock
import six

from oslo_config import cfg
from oslo_log import log as logging

from congress.cfg_validator.agent import agent
from congress.cfg_validator.agent import opts
from congress import opts as opts_congress
from congress.tests import base

# pylint: disable=protected-access

LOG = logging.getLogger(__name__)

NAMESPACE_FILE_CONTENT = """[DEFAULT]
output_file = etc/svc.conf.sample
wrap_width = 79
namespace = congress
namespace = congress-agent
"""

CONF_FILE1_CONTENT = """
[agent]
version:v0
"""

CONF_FILE2_CONTENT = """
[agent]
host:h0
"""

CONF_AGENT_CONTENT = """
[agent]
host:hhh
version:vvv
services: svc: {svc1.conf: svc.tpl}
"""

TEMPLATES = {
    "tpl1": agent.Template("TPL1", "out"),
    "tpl2": agent.Template("TPL2", "out")}
CONFIGS = {
    "cfg1": agent.Config("CFG1", TEMPLATES["tpl1"], "svc"),
    "cfg2": agent.Config("CFG2", TEMPLATES["tpl2"], "svc")}
NAMESPACES = {
    "ns1": agent.Namespace("NS1"),
    "ns2": agent.Namespace("NS2")}


def _gen_ns_data_fake(namespace):
    return u"{\"DEFAULT\": {\"namespaces\": [[\"" + namespace + u"\", []]]}}"


class TestTemplate(base.TestCase):

    "Test template loading"

    @mock.patch('oslo_config.cfg.open')
    def test_parse_template(self, mock_open):
        "Test loading a template"
        mock.mock_open(mock=mock_open, read_data=NAMESPACE_FILE_CONTENT)
        # Patch the mock_open file to support iteration.
        mock_open.return_value.__iter__ = lambda x: iter(x.readline, '')

        tpl, out_file = agent.Template._parse_template_conf('template')
        self.assertEqual(len(tpl), 2)
        self.assertEqual(out_file, 'etc/svc.conf.sample')


class TestCfgConfig(base.TestCase):

    "Test config handling"

    def test_sanitize(self):
        "test config sanitization"
        conf = cfg.ConfigOpts()
        conf._namespace = cfg._Namespace(conf)
        conf._namespace._normalized = []

        opt_1 = cfg.StrOpt(name='lorem', secret=True)
        opt_2 = cfg.StrOpt(name='ipsum', secret=False)
        conf.register_opts([opt_1, opt_2])

        parsed = {'DEFAULT': {'lorem': ['mysecret'], 'ipsum': ['notsecret']}}
        conf._namespace._normalized.append(parsed)

        agent.Config.sanitize_config(conf)

        self.assertNotIn('mysecret', json.dumps(conf._namespace._normalized))
        self.assertIn(
            'notsecret', json.dumps(conf._namespace._normalized))

        self.assertEqual(conf.lorem, '****')
        self.assertEqual(conf.ipsum, 'notsecret')

    def test_get_info(self):
        "test basic get_info"
        cfg_mock = mock.Mock(spec=agent.Config)
        tpl = mock.Mock()
        tpl.hash = 'lorem'
        cfg_mock.template = tpl
        cfg_mock.path = 'ipsum'
        cfg_mock.data = 'dolor'
        cfg_mock.service = 'svc'

        info = agent.Config.get_info(cfg_mock)

        self.assertIn('template', info)
        self.assertEqual(info['template'], 'lorem')
        self.assertIn('path', info)
        self.assertEqual(info['path'], 'ipsum')
        self.assertIn('data', info)
        self.assertEqual(info['data'], 'dolor')


class TestCfgNamespace(base.TestCase):
    "Test namespace handling"

    @mock.patch('congress.cfg_validator.agent.agent.'
                'validator_generator.generate_ns_data')
    def test_load(self, gen_ns_data_mock):
        "Test load namespace"
        gen_ns_data_mock.return_value = _gen_ns_data_fake('lorem')

        ns_mock = agent.Namespace.load('ipsum')

        self.assertEqual(ns_mock.name, 'ipsum')
        self.assertEqual(json.dumps(ns_mock.data), _gen_ns_data_fake('lorem'))
        self.assertIsNotNone(ns_mock.hash)

        same_data_ns = agent.Namespace.load('other_ipsum')
        self.assertEqual(same_data_ns.hash, ns_mock.hash)

        gen_ns_data_mock.return_value = _gen_ns_data_fake('other_lorem')
        other_data_ns = agent.Namespace.load('ipsum')
        self.assertNotEqual(ns_mock.hash, other_data_ns.hash)

    def test_get_info(self):
        "Test basic info on namespace"
        ns_mock = mock.Mock(spec=agent.Namespace)
        ns_mock.name = 'foo'
        ns_mock.data = 'bar'

        info = agent.Namespace.get_info(ns_mock)

        self.assertIn('name', info)
        self.assertEqual(info['name'], 'foo')
        self.assertIn('data', info)
        self.assertEqual(info['data'], 'bar')


class TestCfgTemplate(base.TestCase):
    """Test the handling of templates"""

    @mock.patch('congress.cfg_validator.agent.agent.'
                'cfg.ConfigOpts._parse_config_files')
    def test_template_conf(self, parse_mock):
        """Test the parsing of template"""
        ns_mock = cfg._Namespace(None)
        ns_mock._normalized.append({
            'DEFAULT':
                {
                    'output_file': ['etc/congress.conf.sample'],
                    'wrap_width': ['79'],
                    'namespace': ['congress', 'oslo.log'],
                }
        })

        parse_mock.return_value = ns_mock

        namespace, out_file = agent.Template._parse_template_conf('somewhere')

        self.assertEqual(out_file, 'etc/congress.conf.sample')
        self.assertIn('congress', namespace)
        self.assertIn('oslo.log', namespace)

    @mock.patch('congress.cfg_validator.agent.agent.Namespace.load')
    @mock.patch('congress.cfg_validator.agent.agent.'
                'Template._parse_template_conf')
    def test_load(self, parse_tpl_conf_mock, load_ns_mock):
        """Test loading a template"""
        parse_tpl_conf_mock.return_value = (['congress_h', 'oslo.log'],
                                            'some/where.sample')

        load_ns_mock.side_effect = [mock.MagicMock(hash='lorem'),
                                    mock.MagicMock(hash='ipsum')]

        tpl = agent.Template.load('path/to/template')

        self.assertEqual(tpl.path, 'path/to/template')
        self.assertEqual(tpl.output_file, 'some/where.sample')
        self.assertEqual(tpl.name, 'where')
        self.assertIsNotNone(tpl.hash)
        self.assertTrue(tpl.namespaces)
        self.assertIn('lorem', [ns.hash for ns in tpl.namespaces])
        self.assertIn('ipsum', [ns.hash for ns in tpl.namespaces])

    def test_get_info(self):
        """Test basic info on template"""
        tpl = mock.Mock(spec=agent.Template)
        tpl.path = 'lorem'
        tpl.output_file = 'ipsum'
        tpl.name = 'dolor'
        ns_mock = mock.Mock()
        ns_mock.hash = 'sit'
        tpl.namespaces = [ns_mock]

        info = agent.Template.get_info(tpl)

        self.assertIn('name', info)
        self.assertEqual(info['name'], 'dolor')
        self.assertIn('path', info)
        self.assertEqual(info['path'], 'lorem')
        self.assertIn('output_file', info)
        self.assertEqual(info['output_file'], 'ipsum')
        self.assertIn('namespaces', info)
        self.assertEqual(info['namespaces'], ['sit'])


def _file_mock(file_spec):
    def _mk_content(spec):
        fval = mock.mock_open(read_data=spec)
        fval.return_value.__iter__ = lambda x: iter(x.readline, '')
        return fval
    file_map = {name: _mk_content(spec)
                for name, spec in six.iteritems(file_spec)}

    def _give_file(name):
        basename = path.basename(name)
        return file_map.get(basename, None)(name)

    return mock.MagicMock(name='open', spec=open, side_effect=_give_file)


def _fake_opt_loader(namespaces):
    def fake_entry_point(namespace):
        if namespace == 'congress':
            return opts_congress.list_opts
        if namespace == 'congress-agent':
            return opts.list_opts
        else:
            return None
    return [(ns, fake_entry_point(ns)) for ns in namespaces]


class TestCfgManager(base.TestCase):
    """Config manager tests"""

    @mock.patch(
        'oslo_config.generator._get_raw_opts_loaders', _fake_opt_loader)
    @mock.patch(
        'oslo_config.cfg.open',
        _file_mock({
            "svc.tpl": NAMESPACE_FILE_CONTENT,
            "svc1.conf": CONF_FILE1_CONTENT,
            "svc2.conf": CONF_FILE2_CONTENT}))
    def test_init(self):
        """Test the creation of the config manager"""
        cfg_manager = agent.ConfigManager(
            'host', {"svc": {"svc1.conf": "svc.tpl", "svc2.conf": "svc.tpl"}})
        self.assertEqual('host', cfg_manager.host)
        self.assertEqual(2, len(cfg_manager.configs))
        self.assertEqual(2, len(cfg_manager.namespaces))
        self.assertEqual(1, len(cfg_manager.templates))
        for conf in six.itervalues(cfg_manager.configs):
            self.assertIsInstance(conf, agent.Config)
        for nspc in six.itervalues(cfg_manager.namespaces):
            self.assertIsInstance(nspc, agent.Namespace)
        for tpl in six.itervalues(cfg_manager.templates):
            self.assertIsInstance(tpl, agent.Template)


def _setup_endpoint():
    with mock.patch(
        'oslo_config.cfg.open',
        _file_mock({"agent.conf": CONF_AGENT_CONTENT})),\
        mock.patch(
            'congress.cfg_validator.agent.agent.ConfigManager',
            autospec=True) as mock_manager,\
        mock.patch(
            'congress.cfg_validator.agent.rpc.ValidatorDriverClient',
            autospec=True) as mock_client:
        conf = cfg.ConfigOpts()
        opts.register_validator_agent_opts(conf)
        conf(args=['--config-file', 'agent.conf'])
        mock_manager.return_value.configs = CONFIGS
        mock_manager.return_value.templates = TEMPLATES
        mock_manager.return_value.namespaces = NAMESPACES
        endpoint = agent.ValidatorAgentEndpoint(conf=conf)
        return endpoint, mock_client, mock_manager


class TestValidatorAgentEndpoint(base.TestCase):
    """Test the endpoint for the agent communications"""

    # pylint: disable=no-self-use

    @mock.patch(
        'oslo_config.cfg.open',
        _file_mock({
            "agent.conf": CONF_AGENT_CONTENT}))
    @mock.patch(
        'congress.cfg_validator.agent.agent.ConfigManager',
        autospec=True)
    @mock.patch(
        'congress.cfg_validator.agent.rpc.ValidatorDriverClient',
        autospec=True)
    def test_publish_template_hashes(self, mock_client, mock_manager):
        "Test a request to publish hashes"
        conf = cfg.ConfigOpts()
        opts.register_validator_agent_opts(conf)
        conf(args=['--config-file', 'agent.conf'])
        templates = {"tpl1": {}, "tpl2": {}}
        mock_manager.return_value.templates = templates
        endpoint = agent.ValidatorAgentEndpoint(conf=conf)
        endpoint.publish_templates_hashes({})
        mock_client.return_value.process_templates_hashes.assert_called_with(
            {}, set(templates), "hhh")

    def test_publish_configs_hashes(self):
        "Test a request to publish hashes"
        endpoint, mock_client, _ = _setup_endpoint()
        endpoint.publish_configs_hashes({})
        mock_client.return_value.process_configs_hashes.assert_called_with(
            {}, set(CONFIGS), "hhh")

    def test_get_config(self):
        "Test reply to an explicit config request"
        endpoint, _, _ = _setup_endpoint()
        ret = endpoint.get_config({}, cfg_hash="cfg1")
        expected = {
            'data': None,
            'path': 'CFG1',
            'service': 'svc',
            'template': None,
            'version': 'vvv'}
        self.assertEqual(expected, ret)
        ret = endpoint.get_config({}, cfg_hash="XXX")
        self.assertEqual(None, ret)

    def test_get_namespace(self):
        "Test reply to an explicit config request"
        endpoint, _, _ = _setup_endpoint()
        ret = endpoint.get_namespace({}, ns_hash="ns1")
        expected = {
            'version': 'vvv',
            'data': None,
            'name': 'NS1'}
        self.assertEqual(expected, ret)
        ret = endpoint.get_namespace({}, ns_hash="XXX")
        self.assertEqual(None, ret)

    def test_get_template(self):
        "Test reply to an explicit config request"
        endpoint, _, _ = _setup_endpoint()
        ret = endpoint.get_template({}, tpl_hash="tpl1")
        expected = {
            'name': 'out',
            'namespaces': [],
            'output_file': 'out',
            'path': 'TPL1',
            'version': 'vvv'}
        self.assertEqual(expected, ret)
        ret = endpoint.get_template({}, tpl_hash="XXX")
        self.assertEqual(None, ret)
