# Copyright (c) 2015 OpenStack Foundation
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

from oslo_config import cfg

from congress.api import webservice
from congress.tests.api import base as api_base
from congress.tests import base
from congress.tests import helper


class TestDriverModel(base.SqlTestCase):
    def setUp(self):
        super(TestDriverModel, self).setUp()
        services = api_base.setup_config()
        self.node = services['node']
        self.driver_model = services['api']['api-system']

    def tearDown(self):
        super(TestDriverModel, self).tearDown()

    def test_drivers_list(self):
        context = {}
        drivers = helper.supported_drivers()
        expected_ret = sorted(drivers, key=lambda d: d['id'])
        ret = self.driver_model.get_items({}, context)['results']
        actual_ret = sorted(ret, key=lambda d: d['id'])
        self.assertEqual(expected_ret, actual_ret)

    def test_drivers_list_with_disabled_drivers(self):
        cfg.CONF.set_override('disabled_drivers', 'plexxi')
        services = api_base.setup_config(node_id='test-node-1')
        driver_api = services['api']['api-system']
        drivers = [d['id'] for d in helper.supported_drivers()]
        drivers.remove('plexxi')
        ret = [d['id'] for d in driver_api.get_items({}, {})['results']]
        self.assertEqual(sorted(drivers), sorted(ret))

    def test_drivers_list_with_custom_drivers(self):
        cfg.CONF.set_override(
            'custom_driver_endpoints',
            'test=congress.tests.test_custom_driver:TestCustomDriver')
        services = api_base.setup_config(node_id='test-node-2')
        driver_api = services['api']['api-system']
        ret = [d['id'] for d in driver_api.get_items({}, {})['results']]
        self.assertIn('test', ret)

    def test_driver_details(self):
        context = {
            "driver_id": "fake_datasource"
        }
        expected_ret = {
            "config": {
                "auth_url": "required",
                "endpoint": "(optional)",
                "password": "required",
                "poll_time": "(optional)",
                "region": "(optional)",
                'project_domain_name': '(optional)',
                'user_domain_name': '(optional)',
                "project_name": "required",
                "tenant_name": "(optional)",
                "username": "required"
            },
            "description": "This is a fake driver used for testing",
            "id": "fake_datasource",
            "secret": ["password"],
            "tables": [{'columns': [
                {'description': None, 'name': 'id'},
                {'description': None, 'name': 'name'}],
                'table_id': 'fake_table'}
            ]
        }

        ret = self.driver_model.get_item('fake_datasource', {}, context)
        self.assertEqual(expected_ret, ret)

    def test_invalid_driver_details(self):
        context = {
            "driver_id": "invalid-id"
        }
        self.assertRaises(webservice.DataModelException,
                          self.driver_model.get_item,
                          'invalid-id', {}, context)
