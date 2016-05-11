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

import mock

from oslo_config import cfg
cfg.CONF.distributed_architecture = True

from congress.api import webservice
from congress.datasources import nova_driver
from congress import exception
from congress.tests import base
from congress.tests import helper
from congress.tests2.api import base as api_base


class TestDatasourceModel(base.SqlTestCase):
    def setUp(self):
        super(TestDatasourceModel, self).setUp()
        services = api_base.setup_config()
        self.datasource_model = services['api']['api-datasource']
        self.data = services['data']
        self.node = services['node']
        self.engine = services['engine']
        self.datasource = self._get_datasource_request()
        self.node.add_datasource(self.datasource)

    def tearDown(self):
        super(TestDatasourceModel, self).tearDown()
        self.node.stop()
        self.node.start()

    def _get_datasource_request(self):
        # leave ID out--generated during creation
        return {'name': 'datasource1',
                'driver': 'fake_datasource',
                'description': 'hello world!',
                'enabled': True,
                'type': None,
                'config': {'auth_url': 'foo',
                           'username': 'armax',
                           'password': '<hidden>',
                           'tenant_name': 'armax'}}

    def test_get_items(self):
        dinfo = self.datasource_model.get_items(None)['results']
        self.assertEqual(1, len(dinfo))
        datasource2 = self._get_datasource_request()
        datasource2['name'] = 'datasource2'
        self.node.add_datasource(datasource2)
        dinfo = self.datasource_model.get_items(None)['results']
        self.assertEqual(2, len(dinfo))
        del dinfo[0]['id']
        self.assertEqual(self.datasource, dinfo[0])

    def test_add_item(self):
        datasource3 = self._get_datasource_request()
        datasource3['name'] = 'datasource-test-3'
        self.datasource_model.add_item(datasource3, {})
        obj = self.engine.policy_object('datasource-test-3')
        self.assertIsNotNone(obj.schema)
        self.assertEqual('datasource-test-3', obj.name)

    def test_add_item_duplicate(self):
        self.assertRaises(webservice.DataModelException,
                          self.datasource_model.add_item,
                          self.datasource, {})

    def test_delete_item(self):
        datasource = self._get_datasource_request()
        datasource['name'] = 'test-datasource'
        d_id, dinfo = self.datasource_model.add_item(datasource, {})
        self.assertTrue(self.engine.assert_policy_exists('test-datasource'))
        context = {'ds_id': d_id}
        self.datasource_model.delete_item(None, {}, context=context)
        self.assertRaises(exception.PolicyRuntimeException,
                          self.engine.assert_policy_exists, 'test-datasource')
        self.assertRaises(exception.DatasourceNotFound,
                          self.node.get_datasource, d_id)

    def test_delete_item_invalid_datasource(self):
        context = {'ds_id': 'fake'}
        self.assertRaises(webservice.DataModelException,
                          self.datasource_model.delete_item,
                          None, {}, context=context)

    def test_datasource_api_model_execute(self):
        def _execute_api(client, action, action_args):
            positional_args = action_args.get('positional', [])
            named_args = action_args.get('named', {})
            method = reduce(getattr, action.split('.'), client)
            method(*positional_args, **named_args)

        class NovaClient(object):
            def __init__(self, testkey):
                self.testkey = testkey

            def _get_testkey(self):
                return self.testkey

            def disconnect(self, arg1, arg2, arg3):
                self.testkey = "arg1=%s arg2=%s arg3=%s" % (arg1, arg2, arg3)

            def disconnect_all(self):
                self.testkey = "action_has_no_args"

        nova_client = NovaClient("testing")
        args = helper.datasource_openstack_args()
        nova = nova_driver.NovaDriver('nova', args=args)
        self.node.register_service(nova)
        nova.update_from_datasource = mock.MagicMock()
        nova._execute_api = _execute_api
        nova.nova_client = nova_client

        execute_action = self.datasource_model.execute_action

        # Positive test: valid body args, ds_id
        context = {'ds_id': 'nova'}
        body = {'name': 'disconnect',
                'args': {'positional': ['value1', 'value2'],
                         'named': {'arg3': 'value3'}}}
        request = helper.FakeRequest(body)
        result = execute_action({}, context, request)
        self.assertEqual(result, {})
        expected_result = "arg1=value1 arg2=value2 arg3=value3"
        f = nova.nova_client._get_testkey
        helper.retry_check_function_return_value(f, expected_result)

        # Positive test: no body args
        context = {'ds_id': 'nova'}
        body = {'name': 'disconnect_all'}
        request = helper.FakeRequest(body)
        result = execute_action({}, context, request)
        self.assertEqual(result, {})
        expected_result = "action_has_no_args"
        f = nova.nova_client._get_testkey
        helper.retry_check_function_return_value(f, expected_result)

        # Negative test: invalid ds_id
        context = {'ds_id': 'unknown_ds'}
        self.assertRaises(webservice.DataModelException, execute_action,
                          {}, context, request)

        # Negative test: no ds_id
        context = {}
        self.assertRaises(webservice.DataModelException, execute_action,
                          {}, context, request)

        # Negative test: empty body
        context = {'ds_id': 'nova'}
        bad_request = helper.FakeRequest({})
        self.assertRaises(webservice.DataModelException, execute_action,
                          {}, context, bad_request)

        # Negative test: no body name/action
        context = {'ds_id': 'nova'}
        body = {'args': {'positional': ['value1', 'value2'],
                         'named': {'arg3': 'value3'}}}
        bad_request = helper.FakeRequest(body)
        self.assertRaises(webservice.DataModelException, execute_action,
                          {}, context, bad_request)
