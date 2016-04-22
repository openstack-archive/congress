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


class TestTableModel(base.SqlTestCase):
    def setUp(self):
        super(TestTableModel, self).setUp()
        services = api_base.setup_config()
        self.policy_model = services['api']['api-policy']
        self.table_model = services['api']['api-table']
        self.api_rule = services['api']['api-rule']
        self.node = services['node']
        self.engine = services['engine']
        self.data = services['data']
        # create test policy
        self._create_test_policy()

    def _create_test_policy(self):
        # create policy
        self.policy_model.add_item({"name": 'test-policy'}, {})

    def test_get_datasource_table_with_id(self):
        context = {'ds_id': self.data.service_id,
                   'table_id': 'fake_table'}
        expected_ret = {'id': 'fake_table'}
        ret = self.table_model.get_item('fake_table', {}, context)
        self.assertEqual(expected_ret, ret)

    def test_get_datasource_table_with_name(self):
        context = {'ds_id': self.data.service_id,
                   'table_id': 'fake_table'}
        expected_ret = {'id': 'fake_table'}
        ret = self.table_model.get_item('fake_table', {}, context)
        self.assertEqual(expected_ret, ret)

    def test_get_invalid_datasource(self):
        context = {'ds_id': 'invalid-id',
                   'table_id': 'fake_table'}
        self.assertRaises(webservice.DataModelException,
                          self.table_model.get_item, 'fake_table',
                          {}, context)

    def test_get_invalid_datasource_table(self):
        context = {'ds_id': self.data.service_id,
                   'table_id': 'invalid-table'}
        expected_ret = None
        ret = self.table_model.get_item('invalid-table', {}, context)
        self.assertEqual(expected_ret, ret)

    def test_get_policy_table(self):
        context = {'policy_id': 'test-policy',
                   'table_id': 'p'}
        expected_ret = {'id': 'p'}

        self.api_rule.add_item({'rule': 'p(x) :- q(x)'}, {}, context=context)
        self.api_rule.add_item({'rule': 'q(x) :- r(x)'}, {}, context=context)

        ret = self.table_model.get_item('p', {}, context)
        self.assertEqual(expected_ret, ret)

    def test_get_invalid_policy(self):
        context = {'policy_id': 'test-policy',
                   'table_id': 'fake-table'}
        invalid_context = {'policy_id': 'invalid-policy',
                           'table_id': 'fake-table'}
        expected_ret = None

        self.api_rule.add_item({'rule': 'p(x) :- q(x)'}, {}, context=context)
        self.api_rule.add_item({'rule': 'q(x) :- r(x)'}, {}, context=context)

        ret = self.table_model.get_item('test-policy',
                                        {}, invalid_context)
        self.assertEqual(expected_ret, ret)

    def test_get_invalid_policy_table(self):
        context = {'policy_id': 'test-policy',
                   'table_id': 'fake-table'}
        invalid_context = {'policy_id': 'test-policy',
                           'table_id': 'invalid-name'}
        expected_ret = None

        self.api_rule.add_item({'rule': 'p(x) :- q(x)'}, {}, context=context)
        self.api_rule.add_item({'rule': 'q(x) :- r(x)'}, {}, context=context)

        ret = self.table_model.get_item('test-policy', {},
                                        invalid_context)
        self.assertEqual(expected_ret, ret)

    def test_get_items_datasource_table(self):
        context = {'ds_id': self.data.service_id}
        expected_ret = {'results': [{'id': 'fake_table'}]}

        ret = self.table_model.get_items({}, context)
        self.assertEqual(expected_ret, ret)

    def test_get_items_invalid_datasource(self):
        context = {'ds_id': 'invalid-id',
                   'table_id': 'fake-table'}

        self.assertRaises(webservice.DataModelException,
                          self.table_model.get_items, {}, context)

    def _get_id_list_from_return(self, result):
        return [r['id'] for r in result['results']]

    def test_get_items_policy_table(self):
        context = {'policy_id': 'test-policy'}
        expected_ret = {'results': [{'id': x} for x in ['q', 'p', 'r']]}

        self.api_rule.add_item({'rule': 'p(x) :- q(x)'}, {}, context=context)
        self.api_rule.add_item({'rule': 'q(x) :- r(x)'}, {}, context=context)

        ret = self.table_model.get_items({}, context)
        self.assertEqual(set(self._get_id_list_from_return(expected_ret)),
                         set(self._get_id_list_from_return(ret)))

    def test_get_items_invalid_policy(self):
        context = {'policy_id': 'test-policy'}
        invalid_context = {'policy_id': 'invalid-policy'}
        expected_ret = None

        self.api_rule.add_item({'rule': 'p(x) :- q(x)'}, {}, context=context)
        self.api_rule.add_item({'rule': 'q(x) :- r(x)'}, {}, context=context)

        ret = self.table_model.get_items({}, invalid_context)
        self.assertEqual(expected_ret, ret)
