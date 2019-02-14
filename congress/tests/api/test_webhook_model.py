# Copyright (c) 2018 VMware Inc
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

from congress.tests.api import base as api_base
from congress.tests import base


class TestWebhookModel(base.SqlTestCase):
    def setUp(self):
        super(TestWebhookModel, self).setUp()
        services = api_base.setup_config(with_fake_json_ingester=True)
        self.webhook_model = services['api']['api-webhook']
        self.node = services['node']
        self.data = services['data']
        self.json_ingester = services['json_ingester']

    def test_add_item(self):
        context = {'ds_id': self.data.service_id}
        payload = {'test_payload': 'test_payload'}
        self.webhook_model.add_item(payload, {}, context=context)
        self.assertEqual(self.data.webhook_payload, payload)

    def test_add_json_ingester(self):
        context = {'ds_id': self.json_ingester.name, 'table_name': 'table1'}
        payload = {'test_payload': 'test_payload'}
        self.webhook_model.add_item(payload, {}, context=context)
        self.assertEqual(self.json_ingester.webhook_payload, payload)
        self.assertEqual(
            self.json_ingester.webhook_table_name, context['table_name'])
