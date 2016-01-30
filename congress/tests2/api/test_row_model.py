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

from congress.api import policy_model
from congress.api import row_model
from congress.api import rule_model
from congress.tests import base
from congress.tests import fake_datasource
from congress.tests import helper

from congress.dse2.dse_node import DseNode
from congress.policy_engines.agnostic import Dse2Runtime


class TestRowModel(base.SqlTestCase):

    def setUp(self):
        super(TestRowModel, self).setUp()
        # Here we load the fake driver
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])
        result = self.create_services()
        self.node = result['node']
        self.engine = result['engine']
        self.data = result['data']
        self.rule_model = result['rule_model']
        self.row_model = result['row_model']
        self.policy_model = result['policy_model']

    def create_services(self):
        messaging_config = helper.generate_messaging_config()
        node = DseNode(messaging_config, "testnode", [])
        engine = Dse2Runtime('engine')
        data = fake_datasource.FakeDataSource('data')
        api_policy = policy_model.PolicyModel(
            'api-policy', policy_engine='engine')
        api_rule = rule_model.RuleModel('api-rule', policy_engine='engine')
        api_row = row_model.RowModel('api-row', policy_engine='engine')
        node.register_service(engine)
        node.register_service(api_rule)
        node.register_service(api_row)
        node.register_service(api_policy)
        node.register_service(data)
        node.start()
        return {'node': node, 'engine': engine, 'data': data,
                'rule_model': api_rule, 'row_model': api_row,
                'policy_model': api_policy}

    def tearDown(self):
        super(TestRowModel, self).tearDown()
        self.node.stop()
        self.node.start()

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

    # TODO(dse2): Enable these tests once returning proper exceptions
    # def test_get_items_invalid_ds_name(self):
    #     context = {'ds_id': 'invalid-ds',
    #                'table_id': 'fake-table'}
    #     self.assertRaises(webservice.DataModelException,
    #                       self.row_model.get_items, {}, context)

    # def test_get_items_invalid_ds_table_name(self):
    #     context = {'ds_id': self.datasource['id'],
    #                'table_id': 'invalid-table'}
    #     self.assertRaises(webservice.DataModelException,
    #                       self.row_model.get_items, {}, context)

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

    # TODO(dse2): Enable these tests once returning proper exceptions
    # def test_get_items_invalid_policy_name(self):
    #     context = {'policy_id': 'invalid-policy',
    #                'table_id': 'p'}

    #     self.assertRaises(webservice.DataModelException,
    #                       self.row_model.get_items, {}, context)

    # TODO(dse2): Enable this once returning proper exceptions.
    # Note: modified it manually to not rely on default policies.  Untested.
    # def test_get_items_invalid_policy_table_name(self):
    #     # create policy
    #     policyname = 'test-policy'
    #     self.policy_model.add_item({"name": policyname}, {})

    #     context = {'policy_id': policyname,
    #                'table_id': 'invalid-table'}

    #     self.assertRaises(webservice.DataModelException,
    #                       self.row_model.get_items, {}, context)
