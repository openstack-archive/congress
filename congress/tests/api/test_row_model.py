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

from congress.api import row_model
from congress.api import webservice
from congress import harness
from congress.managers import datasource as datasource_manager
from congress.tests import base
from congress.tests import helper


class TestRowModel(base.SqlTestCase):

    def setUp(self):
        super(TestRowModel, self).setUp()
        # Here we load the fake driver
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])

        self.cage = harness.create(helper.root_path())
        self.datasource_mgr = datasource_manager.DataSourceManager
        self.datasource_mgr.validate_configured_drivers()
        req = {'driver': 'fake_datasource',
               'name': 'fake_datasource'}
        req['config'] = {'auth_url': 'foo',
                         'username': 'foo',
                         'password': 'password',
                         'tenant_name': 'foo'}
        self.datasource_mgr.add_datasource(req)
        self.datasource = self.cage.getservice(name='fake_datasource',
                                               type_='datasource_driver')
        self.engine = self.cage.service_object('engine')
        self.api_rule = self.cage.service_object('api-rule')
        self.policy_model = self.cage.service_object('api-policy')
        self.row_model = row_model.RowModel(
            "row_model", {},
            policy_engine=self.engine,
            datasource_mgr=self.datasource_mgr)

    def tearDown(self):
        super(TestRowModel, self).tearDown()

    @mock.patch.object(datasource_manager.DataSourceManager,
                       'get_row_data')
    def test_get_items_datasource_row(self, row_mock):
        context = {'ds_id': self.datasource['id'],
                   'table_id': 'fake_table'}
        data = [{'data': ('data1', 'data2')}]
        row_mock.return_value = data
        expected_ret = {'results': data}

        ret = self.row_model.get_items({}, context)
        self.assertEqual(expected_ret, ret)

    def test_get_items_invalid_ds_name(self):
        context = {'ds_id': 'invalid-ds',
                   'table_id': 'fake-table'}
        self.assertRaises(webservice.DataModelException,
                          self.row_model.get_items, {}, context)

    def test_get_items_invalid_ds_table_name(self):
        context = {'ds_id': self.datasource['id'],
                   'table_id': 'invalid-table'}
        self.assertRaises(webservice.DataModelException,
                          self.row_model.get_items, {}, context)

    def test_get_items_policy_row(self):
        # create policy
        policyname = 'test-policy'
        self.policy_model.add_item({"name": policyname}, {})

        # insert rules
        context = {'policy_id': policyname,
                   'table_id': 'p'}
        self.api_rule.add_item({'rule': 'p("x"):- true'}, {},
                               context=context)

        # check results
        row = ('x',)
        data = [{'data': row}]
        ret = self.row_model.get_items({}, context)
        self.assertEqual({'results': data}, ret)

    def test_get_items_invalid_policy_name(self):
        context = {'policy_id': 'invalid-policy',
                   'table_id': 'p'}

        self.assertRaises(webservice.DataModelException,
                          self.row_model.get_items, {}, context)

    def test_get_items_invalid_policy_table_name(self):
        context = {'policy_id': self.engine.DEFAULT_THEORY,
                   'table_id': 'invalid-table'}

        self.assertRaises(webservice.DataModelException,
                          self.row_model.get_items, {}, context)

    def test_update_items(self):
        context = {'ds_id': self.datasource['id'],
                   'table_id': 'fake_table'}
        objs = [
            {"id": 'id-1', "name": 'name-1'},
            {"id": 'id-2', "name": 'name-2'}
            ]
        expected_state = (('id-1', 'name-1'), ('id-2', 'name-2'))

        self.row_model.update_items(objs, {}, context=context)
        table_row = self.datasource['object'].state['fake_table']

        self.assertEqual(len(expected_state), len(table_row))
        for row in expected_state:
            self.assertTrue(row in table_row)

    def test_update_items_invalid_table(self):
        context = {'ds_id': self.datasource['id'],
                   'table_id': 'invalid-table'}
        objs = [
            {"id": 'id-1', "name": 'name-1'},
            {"id": 'id-2', "name": 'name-2'}
            ]
        self.assertRaises(webservice.DataModelException,
                          self.row_model.update_items, objs, {}, context)
