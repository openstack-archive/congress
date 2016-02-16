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
cfg.CONF.distributed_architecture = True

from congress.api import datasource_model
from congress.api import webservice
from congress import exception
from congress.tests import base
from congress.tests2.api import base as api_base


class TestDatasourceModel(base.SqlTestCase):
    def setUp(self):
        super(TestDatasourceModel, self).setUp()
        self.datasource_model = datasource_model.DatasourceModel(
            'test_datasource', policy_engine='engine')
        self.config = api_base.setup_config([self.datasource_model])
        self.data = self.config['data']
        self.node = self.config['node']
        self.engine = self.config['engine']
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

# TODO(ramineni): Migrate request_refresh and exeucte_action tests
