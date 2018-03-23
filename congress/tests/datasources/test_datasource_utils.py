# Copyright (c) 2018 Canonical Ltd
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

from __future__ import print_function

from congress.datasources import constants
from congress.datasources import datasource_utils
from congress.tests import base


class TestDatasourceDriver(base.TestCase):

    def test_get_openstack_required_config(self):
        expected_required = ['auth_url', 'password', 'project_name',
                             'username']
        expected_optional = ['endpoint', 'poll_time', 'project_domain_name',
                             'region', 'tenant_name', 'user_domain_name']
        config = datasource_utils.get_openstack_required_config()
        required = []
        optional = []
        for k, v in config.items():
            if v == constants.REQUIRED:
                required.append(k)
            elif v == constants.OPTIONAL:
                optional.append(k)
        self.assertEqual(sorted(required), expected_required)
        self.assertEqual(sorted(optional), expected_optional)
