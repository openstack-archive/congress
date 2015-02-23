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

from oslo.config import cfg

from congress.api import status_model
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

        self.cage = harness.create(helper.root_path(), helper.state_path())
        self.datasource_mgr = datasource_manager.DataSourceManager
        self.datasource_mgr.validate_configured_drivers()
        req = {'driver': 'fake_datasource',
               'name': 'fake_datasource'}
        req['config'] = {'auth_url': 'foo',
                         'password': 'password',
                         'tenant_name': 'foo'}
        self.datasource = self.datasource_mgr.add_datasource(req)
        engine = self.cage.service_object('engine')
        self.status_model = status_model.StatusModel("status_schema", {},
                                                     policy_engine=engine)

    def test_get_datasource_status(self):
        context = {'ds_id': self.datasource['id']}
        status = self.status_model.get_item(None, {}, context=context)
        expected_status_keys = ['last_updated', 'subscriptions',
                                'last_error', 'subscribers',
                                'initialized', 'number_of_updates']
        self.assertEqual(set(expected_status_keys), set(status.keys()))

    def test_get_invalid_datasource_status(self):
        context = {'ds_id': 'invalid_id'}
        try:
            self.status_model.get_item(None, {}, context=context)
        except webservice.DataModelException as e:
            self.assertEqual(e.error_code, 404)
        else:
            raise "Fail!"
