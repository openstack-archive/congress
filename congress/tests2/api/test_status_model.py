# Copyright (c) 2016 NTT
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

# import uuid

from oslo_config import cfg
cfg.CONF.distributed_architecture = True

from congress.api import policy_model
from congress.api import rule_model
from congress.api import status_model
# from congress.api import webservice
from congress.dse2 import dse_node
from congress.policy_engines import agnostic
from congress.tests import base
from congress.tests import fake_datasource
from congress.tests import helper


class TestStatusModel(base.SqlTestCase):
    def setUp(self):
        super(TestStatusModel, self).setUp()
        # Here we load the fake driver
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])

        result = self.create_service()
        self.node = result['node']
        self.policy_model = result['policy']
        self.rule_model = result['rule']
        self.status_model = result['status']
        self.datasource = result['datasource']

    def create_service(self):
        messaging_config = helper.generate_messaging_config()
        node = dse_node.DseNode(messaging_config, 'testnode', [])
        engine = agnostic.Dse2Runtime('engine')
        data = fake_datasource.FakeDataSource('fake-data')
        policy = policy_model.PolicyModel('api-policy',
                                          policy_engine='engine')
        rule = rule_model.RuleModel('api-rule',
                                    policy_engine='engine')
        status = status_model.StatusModel('api-status',
                                          policy_engine='engine')

        node.register_service(engine)
        node.register_service(data)
        node.register_service(policy)
        node.register_service(rule)
        node.register_service(status)

        node.start()

        return {'node': node, 'engine': engine, 'datasource': data,
                'policy': policy, 'rule': rule, 'status': status}

    def test_get_datasource_status(self):
        context = {'ds_id': self.datasource.service_id}
        status = self.status_model.get_item(None, {}, context=context)
        expected_status_keys = ['last_updated', 'subscriptions',
                                'last_error', 'subscribers',
                                'initialized', 'number_of_updates']
        self.assertEqual(set(expected_status_keys), set(status.keys()))

    # todo(dse2) Comment out thie test after enabling rpc to handle rpc call
    # for no-exist topic.
#     def test_get_invalid_datasource_status(self):
#         context = {'ds_id': 'invalid_id'}
#         self.assertRaises(webservice.DataModelException,
#                           self.status_model.get_item, None, {},
#                           context=context)

    def test_policy_id_status(self):
        result = self.policy_model.add_item({'name': 'test_policy'}, {})

        context = {'policy_id': result[0]}
        status = self.status_model.get_item(None, {}, context=context)
        expected_status = {'name': 'test_policy',
                           'id': result[0]}
        self.assertEqual(expected_status, status)

        # test with policy_name
        context = {'policy_id': result[1]['name']}
        status = self.status_model.get_item(None, {}, context=context)
        self.assertEqual(expected_status, status)

    # todo(dse2) Comment out this test after enabling rpc to retrieve
    # exception happened in remote node.
#     def test_invalid_policy_id_status(self):
#         invalid_id = uuid.uuid4()
#         context = {'policy_id': invalid_id}
#         self.assertRaises(webservice.DataModelException,
#                           self.status_model.get_item, None, {},
#                           context=context)

    def test_rule_status_policy_id(self):
        result = self.policy_model.add_item({'name': 'test_policy'}, {})
        policy_id = result[0]
        policy_name = result[1]['name']

        result = self.rule_model.add_item({'name': 'test_rule',
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

    # todo(dse2) Comment out this test after enabling rpc to retrieve
    # exception happened in remote node.
#     def test_rule_status_invalid_rule_policy_id(self):
#         result = self.policy_model.add_item({'name': 'test_policy'}, {})
#         policy_id = result[0]
#         invalid_rule = uuid.uuid4()

#         context = {'policy_id': policy_id, 'rule_id': invalid_rule}
#         self.assertRaises(webservice.DataModelException,
#                           self.status_model.get_item, None, {},
#                           context=context)

    # todo(dse2) Comment out this test after enabling rpc to retrieve
    # exception happened in remote node.
#     def test_rule_status_invalid_policy_id(self):
#         invalid_policy = uuid.uuid4()
#         invalid_rule = uuid.uuid4()

#         context = {'policy_id': invalid_policy, 'rule_id': invalid_rule}
#         self.assertRaises(webservice.DataModelException,
#                           self.status_model.get_item, None, {},
#                           context=context)
