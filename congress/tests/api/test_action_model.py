# Copyright (c) 2015 Intel, Inc. All rights reserved.
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

from oslo_config import cfg

from congress.api import action_model
from congress.api import webservice
from congress import harness
from congress.managers import datasource as datasource_manager
from congress.tests import base
from congress.tests import helper


class TestActionModel(base.SqlTestCase):
    def setUp(self):
        super(TestActionModel, self).setUp()
        # Here we load the fake driver
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])

        # NOTE(arosen): this set of tests, tests to deeply. We don't have
        # any tests currently testing cage. Once we do we should mock out
        # cage so we don't have to create one here.

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
        engine = self.cage.service_object('engine')
        self.action_model = action_model.ActionsModel("action_schema", {},
                                                      policy_engine=engine)

    def test_get_datasource_actions(self):
        context = {'ds_id': self.datasource['id']}
        actions = self.action_model.get_items({}, context=context)
        expected_ret = {'results': [{'name': 'fake_act',
                        'args': [{'name': 'server_id',
                                  'description': 'server to act'}],
                        'description': 'fake action'}]}
        self.assertEqual(expected_ret, actions)

    def test_get_invalid_datasource_action(self):
        context = {'ds_id': 'invalid_id'}
        self.assertRaises(webservice.DataModelException,
                          self.action_model.get_items, {}, context=context)
