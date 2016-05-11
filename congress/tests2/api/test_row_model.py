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

from congress.api import webservice
from congress.tests import base
from congress.tests2.api import base as api_base


class TestRowModel(base.SqlTestCase):

    def setUp(self):
        super(TestRowModel, self).setUp()
        services = api_base.setup_config()
        self.policy_model = services['api']['api-policy']
        self.rule_model = services['api']['api-rule']
        self.row_model = services['api']['api-row']
        self.node = services['node']
        self.data = services['data']

    def test_get_items_datasource_row(self):
        # adjust datasource to have required value
        row = ('data1', 'data2')
        self.data.state['fake_table'] = set([row])

        # check result
        context = {'ds_id': self.data.service_id,
                   'table_id': 'fake_table'}
        data = [{'data': row}]
        expected_ret = {'results': data}
        ret = self.row_model.get_items({}, context)
        self.assertEqual(expected_ret, ret)

    def test_get_items_invalid_ds_name(self):
        context = {'ds_id': 'invalid-ds',
                   'table_id': 'fake-table'}
        self.assertRaises(webservice.DataModelException,
                          self.row_model.get_items, {}, context)

    def test_get_items_invalid_ds_table_name(self):
        context = {'ds_id': self.data.service_id,
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
        self.rule_model.add_item({'rule': 'p("x"):- true'}, {},
                                 context=context)

        # check results
        row = ('x',)
        data = [{'data': row}]
        ret = self.row_model.get_items({}, context)
        self.assertEqual({'results': data}, ret)

        # Enable trace and check
        ret = self.row_model.get_items({'trace': 'true'}, context=context)
        s = frozenset([tuple(x['data']) for x in ret['results']])
        t = frozenset([('x',)])
        self.assertEqual(s, t, "Rows with tracing")
        self.assertTrue('trace' in ret, "Rows should have trace")
        self.assertEqual(len(ret['trace'].split('\n')), 9)

    def test_get_items_invalid_policy_name(self):
        context = {'policy_id': 'invalid-policy',
                   'table_id': 'p'}

        self.assertRaises(webservice.DataModelException,
                          self.row_model.get_items, {}, context)

    def test_get_items_invalid_policy_table_name(self):
        # create policy
        policyname = 'test-policy'
        self.policy_model.add_item({"name": policyname}, {})

        context = {'policy_id': policyname,
                   'table_id': 'invalid-table'}

        self.assertRaises(webservice.DataModelException,
                          self.row_model.get_items, {}, context)

    def test_update_items(self):
        context = {'ds_id': self.data.service_id,
                   'table_id': 'fake_table'}
        objs = [
            {"id": 'id-1', "name": 'name-1'},
            {"id": 'id-2', "name": 'name-2'}
            ]
        expected_state = (('id-1', 'name-1'), ('id-2', 'name-2'))

        self.row_model.update_items(objs, {}, context=context)
        table_row = self.data.state['fake_table']

        self.assertEqual(len(expected_state), len(table_row))
        for row in expected_state:
            self.assertTrue(row in table_row)

    def test_update_items_invalid_table(self):
        context = {'ds_id': self.data.service_id,
                   'table_id': 'invalid-table'}
        objs = [
            {"id": 'id-1', "name": 'name-1'},
            {"id": 'id-2', "name": 'name-2'}
            ]
        self.assertRaises(webservice.DataModelException,
                          self.row_model.update_items, objs, {}, context)
