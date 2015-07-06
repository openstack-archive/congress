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

import mock
from oslo_config import cfg

from congress.api import row_model
from congress.api import webservice
from congress import harness
from congress.managers import datasource as datasource_manager
from congress.tests import base
from congress.tests import helper


class TestRuleModel(base.SqlTestCase):

    def setUp(self):
        super(TestRuleModel, self).setUp()
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
        self.datasource = self.datasource_mgr.add_datasource(req)
        self.engine = self.cage.service_object('engine')
        self.api_rule = self.cage.service_object('api-rule')
        self.row_model = row_model.RowModel("row_model", {},
                                            policy_engine=self.engine)

    def tearDown(self):
        super(TestRuleModel, self).tearDown()

    def test_get_items_datasource_row(self):
        context = {'ds_id': self.datasource['id'],
                   'table_id': 'fake-table'}
        fake_obj = helper.FakeServiceObj()
        fake_obj.state = {'fake-table': set([('data1', 'data2'),
                                             ('data2-1', 'data2-2')])}
        expected_ret = {'results':
                        [{'data': d} for d in fake_obj.state['fake-table']]}

        self.engine.d6cage.service_object = mock.Mock()
        self.engine.d6cage.service_object.return_value = fake_obj

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
        fake_obj = helper.FakeServiceObj()
        fake_obj.state = {'fake-table': set([('data1', 'data2'),
                                             ('data2-1', 'data2-2')])}

        self.engine.d6cage.service_object = mock.Mock()
        self.engine.d6cage.service_object.return_value = fake_obj

        self.assertRaises(webservice.DataModelException,
                          self.row_model.get_items, {}, context)

    def test_get_items_policy_row(self):
        context = {'policy_id': self.engine.DEFAULT_THEORY,
                   'table_id': 'p'}
        expected_ret = [['x'], ['y']]

        self.api_rule.add_item({'rule': 'p("x"):- true'}, {}, context=context)
        self.api_rule.add_item({'rule': 'p("y"):- true'}, {}, context=context)

        ret = self.row_model.get_items({}, context)
        self.assertTrue(all(d['data'] in expected_ret for d in ret['results']))

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
