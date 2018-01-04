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
"""Unit test for the marshalling of options"""
import mock

from oslo_config import cfg
from oslo_config import types
from oslo_log import log as logging

from congress.cfg_validator.agent import generator
from congress.tests import base

LOG = logging.getLogger(__name__)


class TestGenerator(base.TestCase):
    """Unit test for the marshalling of options"""

    @mock.patch("oslo_config.generator._list_opts")
    def test_encode(self, mock_list_opts):
        """Test the json encoding of options"""

        opt1 = cfg.StrOpt("o1"),
        opt2 = cfg.IntOpt("o2", default=10),
        opt3 = cfg.StrOpt("o3", default="a"),
        mock_list_opts.return_value = [
            ("ns", [("g1", [opt1, opt2]), ("g2", [opt3])])]
        namespace = "ns"

        def _mko(nam, typ, kind, defv):
            return (
                '{"advanced": false, "default": %s, "deprecated_for_removal":'
                ' false, "deprecated_opts": [], "deprecated_reason": null,'
                ' "deprecated_since": null, "dest": "%s", "help": null,'
                ' "kind": "%s", "metavar": null, "mutable": false,'
                ' "name": "%s", "positional": false, "required": false,'
                ' "sample_default": null, "secret": false, "short": null,'
                ' "type": {"type": "%s"}}') % (defv, nam, kind, nam, typ)
        ns_string = (
            ('{"DEFAULT": {"namespaces": [], "object": null}, "g1": '
             '{"namespaces": [["ns", [[') +
            _mko("o1", "String", "StrOpt", "null") +
            '], [' + _mko("o2", "Integer", "IntOpt", 10) +
            ']]]], "object": null}, "g2": {"namespaces": [["ns", [[' +
            _mko("o3", "String", "StrOpt", "\"a\"") + ']]]], "object": null}}')
        computed = generator.generate_ns_data(namespace)
        self.assertEqual(
            ns_string, computed,
            "not the expected encoding of namespace")

    @mock.patch("oslo_config.generator._list_opts")
    def _test_encode_specific(self, opt, expected, mock_list_opts=None):
        """Test an option and check an expected string in result"""
        mock_list_opts.return_value = [
            ("ns", [("g", [opt])])]
        namespace = "ns"
        computed = generator.generate_ns_data(namespace)
        self.assertIn(expected, computed)

    def test_encode_range(self):
        """Test the json encoding of range option"""
        opt = cfg.Opt('o', types.Range(min=123, max=456))
        expected = '"type": {"max": 456, "min": 123, "type": "Range"}'
        self._test_encode_specific(opt, expected)

    def test_encode_list(self):
        """Test the json encoding of list option"""
        opt = cfg.ListOpt('opt', types.Boolean)
        expected = '"type": {"item_type": {"type": "String"}, "type": "List"}'
        self._test_encode_specific(opt, expected)

    def test_encode_dict(self):
        """Test the json encoding of dict option"""
        opt = cfg.DictOpt('opt')
        expected = '"type": {"type": "Dict", "value_type": {"type": "String"}}'
        self._test_encode_specific(opt, expected)

    def test_encode_ip(self):
        """Test the json encoding of IP option"""
        opt = cfg.IPOpt('opt')
        expected = '"type": {"type": "IPAddress"}'
        self._test_encode_specific(opt, expected)

    def test_encode_uri(self):
        """Test the json encoding of a URI"""
        opt = cfg.URIOpt('opt', 100)
        expected = '"type": {"max_length": 100, "type": "URI"}'
        self._test_encode_specific(opt, expected)

    def test_encode_regex(self):
        """Test the json encoding of a string option with regex"""
        opt = cfg.StrOpt('opt', regex=r'abcd')
        expected = '"type": {"regex": "abcd", "type": "String"}'
        self._test_encode_specific(opt, expected)

    def test_encode_deprecated(self):
        """Test Deprecated Opt: this is not the way to use it"""
        dep = cfg.DeprecatedOpt('o_old', 'g_old')
        opt = cfg.Opt('opt', deprecated_opts=[dep])
        expected = '"deprecated_opts": [{"group": "g_old", "name": "o_old"}]'
        self._test_encode_specific(opt, expected)
