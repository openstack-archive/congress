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

from congress.api import action_model
from congress.dse2.dse_node import DseNode
from congress.policy_engines.agnostic import Dse2Runtime
from congress.tests import base
from congress.tests.fake_datasource import FakeDataSource
from congress.tests import helper


class TestActionModel(base.SqlTestCase):
    def setUp(self):
        super(TestActionModel, self).setUp()
        # Here we load the fake driver
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])

        services = self.create_services()
        self.action_model = services['action_model']
        self.datasource = services['data']

    def create_services(self):
        messaging_config = helper.generate_messaging_config()
        node = DseNode(messaging_config, "testnode", [])
        engine = Dse2Runtime('engine')
        fake = FakeDataSource('test1')
        action = action_model.ActionsModel(
            'api-action', policy_engine='engine')
        node.register_service(engine)  # not strictly necessary
        node.register_service(fake)
        node.register_service(action)
        node.start()
        return {'node': node,
                'engine': engine,
                'action_model': action,
                'data': fake}

    def test_get_datasource_actions(self):
        context = {'ds_id': self.datasource.service_id}
        actions = self.action_model.get_items({}, context=context)
        expected_ret = {'results': [{'name': 'fake_act',
                        'args': [{'name': 'server_id',
                                  'description': 'server to act'}],
                        'description': 'fake action'}]}
        self.assertEqual(expected_ret, actions)

    # TODO(dse2): enable once oslo-messaging returning proper error
    # codes
    # def test_get_invalid_datasource_action(self):
    #     context = {'ds_id': 'invalid_id'}
    #     self.assertRaises(webservice.DataModelException,
    #                       self.action_model.get_items, {}, context=context)
