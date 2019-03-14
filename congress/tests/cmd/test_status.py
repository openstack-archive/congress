# Copyright (c) 2018 NEC, Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_upgradecheck.upgradecheck import Code

from congress.cmd import status
from congress.tests.api import base as api_base
from congress.tests import base


class TestUpgradeChecks(base.SqlTestCase):

    def setUp(self):
        super(TestUpgradeChecks, self).setUp()
        self.cmd = status.Checks()

    def test__check_monasca_webhook_driver_success(self):
        check_result = self.cmd._check_monasca_webhook_driver()
        self.assertEqual(
            Code.SUCCESS, check_result.code)

    def test__check_monasca_webhook_driver_warning(self):
        services = api_base.setup_config(with_fake_datasource=False)
        self.datasource_model = services['api']['api-datasource']
        self.data = services['data']
        self.node = services['node']
        self.engine = services['engine']
        self.ds_manager = services['ds_manager']
        monasca_setting = {
            'name': 'datasource_name',
            'driver': 'monasca_webhook',
            'config': None,
        }
        self.ds_manager.add_datasource(monasca_setting)
        check_result = self.cmd._check_monasca_webhook_driver()
        self.assertEqual(
            Code.WARNING, check_result.code)
