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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

# set test to run as distributed arch
from oslo_config import cfg
cfg.CONF.distributed_architecture = True

from congress.api import webservice
from congress.tests import base
from congress.tests2.api import base as api_base


class TestActionModel(base.SqlTestCase):
    def setUp(self):
        super(TestActionModel, self).setUp()
        services = api_base.setup_config()
        self.action_model = services['api']['api-action']
        self.datasource = services['data']

    def test_get_datasource_actions(self):
        context = {'ds_id': self.datasource.service_id}
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
