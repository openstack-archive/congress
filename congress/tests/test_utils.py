# Copyright (c) 2014, 2019 VMware
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from os import path
import shutil
import sys
import tempfile

import testtools

import congress.utils as utils


class UtilsTest(testtools.TestCase):

    def test_value_to_congress(self):
        self.assertEqual("abc", utils.value_to_congress("abc"))
        self.assertEqual("True", utils.value_to_congress(True))
        self.assertEqual("False", utils.value_to_congress(False))
        self.assertEqual(0, utils.value_to_congress(0))
        self.assertEqual(1, utils.value_to_congress(1))
        self.assertEqual(123, utils.value_to_congress(123))
        if sys.version < '3':
            self.assertEqual(456.0, utils.value_to_congress(456.0))

    def test_pretty_rule(self):
        test_rule = "\t \n  head(1, 2)\t \n  "
        expected = "head(1, 2)"
        self.assertEqual(utils.pretty_rule(test_rule), expected)

        test_rule = "\t \n  head(1, 2)\t \n  :- \t \n"
        expected = "head(1, 2)"
        self.assertEqual(utils.pretty_rule(test_rule), expected)

        test_rule = ("\t \n server_with_bad_flavor(id)\t \n  :- \t \n  "
                     "nova:servers(id=id,flavor_id=flavor_id), \t \n "
                     "nova:flavors(id=flavor_id, name=flavor), "
                     "not permitted_flavor(flavor)\t \n ")
        expected = ("server_with_bad_flavor(id) :-\n"
                    "  nova:servers(id=id,flavor_id=flavor_id),\n"
                    "  nova:flavors(id=flavor_id, name=flavor),\n"
                    "  not permitted_flavor(flavor)")
        self.assertEqual(utils.pretty_rule(test_rule), expected)


YAML1 = """
name: nova
poll: 1
authentication:
  type: keystone
  username: admin
  auth_url: http://127.0.0.1/identity
  project_name: admin
  password: password
api_endpoint: http://127.0.0.1/compute/v2.1/
tables:
  flavors:
    api_path: flavors/detail
    api_verb: get
    jsonpath: $.flavors[:]
  servers:
    api_path: servers/detail
    api_verb: get
    jsonpath: $.servers[:]
---
name: nova2
poll: 1
authentication:
  type: keystone
  username: admin
  auth_url: http://127.0.0.1/identity
  project_name: admin
  password: password
api_endpoint: http://127.0.0.1/compute/v2.1/
tables:
  flavors:
    api_path: flavors/detail
    api_verb: get
    jsonpath: $.flavors[:]
  servers:
    api_path: servers/detail
    api_verb: get
    jsonpath: $.servers[:]
"""

YAML_DUP_NAME = """
name: nova
poll: 2
authentication:
  type: keystone
api_endpoint: http://127.0.0.1/compute/v2.1/
tables:
  flavors:
    api_path: flavors/detail
    api_verb: get
    jsonpath: $.flavors[:]
"""

BAD_YAML = """
name:--- bad
"""


class TestYamlConfigs(testtools.TestCase):

    def setUp(self):
        super(TestYamlConfigs, self).setUp()
        self.yaml_dir = tempfile.mkdtemp()
        with open(path.join(self.yaml_dir, '1.yaml'), 'w') as f:
            f.write(YAML1)
        self.test_yaml_configs = utils.YamlConfigs(
            self.yaml_dir, key_attrib='name')

    def tearDown(self):
        shutil.rmtree(self.yaml_dir)
        super(TestYamlConfigs, self).tearDown()

    def test_loading(self):
        file_error_count = self.test_yaml_configs.load_from_files()
        self.assertEqual(file_error_count, 0)
        self.assertEqual(len(self.test_yaml_configs.loaded_structures), 2)

    def test_loading_duplicate_key_rejected(self):
        # write duplicate yamls
        with open(path.join(self.yaml_dir, 'dupe.yaml'), 'w') as f:
            f.write(YAML_DUP_NAME)
        file_error_count = self.test_yaml_configs.load_from_files()
        self.assertEqual(file_error_count, 1)
        self.assertEqual(len(self.test_yaml_configs.loaded_structures), 2)

    def test_loading_bad_yaml(self):
        # write bad yaml
        with open(path.join(self.yaml_dir, 'bad.yaml'), 'w') as f:
            f.write(BAD_YAML)
        file_error_count = self.test_yaml_configs.load_from_files()
        self.assertEqual(file_error_count, 1)
        self.assertEqual(len(self.test_yaml_configs.loaded_structures), 2)
