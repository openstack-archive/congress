# Copyright (c) 2014 Styra, Inc. All rights reserved.
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
#

import mock

from oslo_config import cfg
cfg.CONF.distributed_architecture = True

from congress.tests.policy_engines.test_agnostic import TestRuntime
from congress.tests2.api import base as api_base


class TestDse2Runtime(TestRuntime):
    def setUp(self):
        super(TestDse2Runtime, self).setUp()

    @mock.patch('congress.db.db_policy_rules.get_policy_rules')
    def test_enable_schema(self, patched_persisted_rules):
        class TestRule(object):
            def __init__(self, id, name, rule_str,
                         policy_name, comment=None):
                self.id = id
                self.name = name
                self.rule = rule_str
                self.policy_name = policy_name
                self.comment = comment

        persisted_rule = [
            TestRule('rule-id', 'rule-name',
                     "p(x):-nova:services(id=x)", 'classification'),
            ]
        patched_persisted_rules.return_value = persisted_rule

        services = api_base.setup_config()
        engine2 = services['engine']
        node = services['node']

        node.invoke_service_rpc = mock.MagicMock()
        node.invoke_service_rpc.return_value = [
            ['id1', 'name1', 'status1'],
            ['id2', 'name2', 'status2'],
            ]

        # loaded rule is disabled
        subscriptions = engine2.subscription_list()
        self.assertEqual([], subscriptions)

        nova_schema = {
            'services': [
                {'name': 'id', 'desc': 'id of the service'},
                {'name': 'name', 'desc': 'name of the service'},
                {'name': 'status', 'desc': 'status of the service'}]}

        engine2.initialize_datasource('nova', nova_schema)
        # loaded rule is enabled and subscribes the table
        subscriptions = engine2.subscription_list()
        self.assertEqual([('nova', 'services')], subscriptions)
