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
import uuid

from oslo_config import cfg

from congress.api import status_model as st_model
from congress.api import webservice
from congress import harness
from congress.managers import datasource as datasource_manager
from congress.tests import base
from congress.tests import helper


class TestStatusModel(base.SqlTestCase):
    def setUp(self):
        super(TestStatusModel, self).setUp()
        # Here we load the fake driver
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])

        # NOTE(arosen): this set of tests, tests to deeply. We don't have
        # any tests currently testing cage. Once we do we should mock out
        # cage so we don't have to create one here.

        self.cage = harness.create(helper.root_path())
        self.ds_mgr = datasource_manager.DataSourceManager
        self.ds_mgr.validate_configured_drivers()
        req = {'driver': 'fake_datasource',
               'name': 'fake_datasource'}
        req['config'] = {'auth_url': 'foo',
                         'username': 'foo',
                         'password': 'password',
                         'tenant_name': 'foo'}
        self.datasource = self.ds_mgr.add_datasource(req)
        engine = self.cage.service_object('engine')
        self.status_model = st_model.StatusModel("status_schema", {},
                                                 policy_engine=engine,
                                                 datasource_mgr=self.ds_mgr)

    def test_get_datasource_status(self):
        context = {'ds_id': self.datasource['id']}
        status = self.status_model.get_item(None, {}, context=context)
        expected_status_keys = ['last_updated', 'subscriptions',
                                'last_error', 'subscribers',
                                'initialized', 'number_of_updates']
        self.assertEqual(set(expected_status_keys), set(status.keys()))

    def test_get_invalid_datasource_status(self):
        context = {'ds_id': 'invalid_id'}
        self.assertRaises(webservice.DataModelException,
                          self.status_model.get_item, None, {},
                          context=context)

    def test_policy_id_status(self):
        policy_model = self.cage.getservice(name='api-policy')['object']
        result = policy_model.add_item({'name': 'test_policy'}, {})

        context = {'policy_id': result[0]}
        status = self.status_model.get_item(None, {}, context=context)
        expected_status = {'name': 'test_policy',
                           'id': result[0]}
        self.assertEqual(expected_status, status)

        # test with policy_name
        context = {'policy_id': result[1]['name']}
        status = self.status_model.get_item(None, {}, context=context)
        self.assertEqual(expected_status, status)

    def test_invalid_policy_id_status(self):
        invalid_id = uuid.uuid4()
        context = {'policy_id': invalid_id}
        self.assertRaises(webservice.DataModelException,
                          self.status_model.get_item, None, {},
                          context=context)

    def test_rule_status_policy_id(self):
        policy_model = self.cage.getservice(name='api-policy')['object']
        result = policy_model.add_item({'name': 'test_policy'}, {})
        policy_id = result[0]
        policy_name = result[1]['name']

        rule_model = self.cage.getservice(name='api-rule')['object']
        result = rule_model.add_item({'name': 'test_rule',
                                      'rule': 'p(x) :- q(x)'}, {},
                                     context={'policy_id': 'test_policy'})

        context = {'policy_id': policy_id, 'rule_id': result[0]}
        status = self.status_model.get_item(None, {}, context=context)
        expected_status = {'name': 'test_rule',
                           'id': result[0],
                           'comment': '',
                           'original_str': 'p(x) :- q(x)'}
        self.assertEqual(expected_status, status)

        # test with policy_name
        context = {'policy_id': policy_name, 'rule_id': result[0]}
        status = self.status_model.get_item(None, {}, context=context)
        expected_status = {'name': 'test_rule',
                           'id': result[0],
                           'comment': '',
                           'original_str': 'p(x) :- q(x)'}
        self.assertEqual(expected_status, status)

    def test_rule_status_invalid_rule_policy_id(self):
        policy_model = self.cage.getservice(name='api-policy')['object']
        result = policy_model.add_item({'name': 'test_policy'}, {})
        policy_id = result[0]
        invalid_rule = uuid.uuid4()

        context = {'policy_id': policy_id, 'rule_id': invalid_rule}
        self.assertRaises(webservice.DataModelException,
                          self.status_model.get_item, None, {},
                          context=context)

    def test_rule_status_invalid_policy_id(self):
        invalid_policy = uuid.uuid4()
        invalid_rule = uuid.uuid4()

        context = {'policy_id': invalid_policy, 'rule_id': invalid_rule}
        self.assertRaises(webservice.DataModelException,
                          self.status_model.get_item, None, {},
                          context=context)
