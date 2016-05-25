# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 VMware, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
test_congress
----------------------------------

Tests for `congress` module.
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import mock

from oslo_config import cfg
cfg.CONF.distributed_architecture = True
import neutronclient.v2_0
from oslo_log import log as logging

from congress.common import config
from congress.datasources import neutronv2_driver
from congress.datasources import nova_driver
from congress import harness
from congress.tests import base
from congress.tests.datasources import test_neutron_driver as test_neutron
from congress.tests import helper
from congress.tests2.api import base as api_base


LOG = logging.getLogger(__name__)


class TestCongress(base.SqlTestCase):

    def setUp(self):
        """Setup tests that use multiple mock neutron instances."""
        super(TestCongress, self).setUp()
        self.services = api_base.setup_config(with_fake_datasource=False)
        self.api = self.services['api']
        self.node = self.services['node']
        self.engine = self.services['engine']

        self.neutronv2 = self._create_neutron_mock('neutron')

    def _create_neutron_mock(self, name):
        # Register Neutron service
        args = helper.datasource_openstack_args()
        neutronv2 = neutronv2_driver.NeutronV2Driver(name, args=args)
        self.node.register_service(neutronv2)
        neutron_mock = mock.MagicMock(spec=neutronclient.v2_0.client.Client)
        neutronv2.neutron = neutron_mock

        # initialize neutron_mocks
        network1 = test_neutron.network_response
        port_response = test_neutron.port_response
        router_response = test_neutron.router_response
        sg_group_response = test_neutron.security_group_response
        neutron_mock.list_networks.return_value = network1
        neutron_mock.list_ports.return_value = port_response
        neutron_mock.list_routers.return_value = router_response
        neutron_mock.list_security_groups.return_value = sg_group_response
        return neutronv2

    def setup_config(self):
        args = ['--config-file', helper.etcdir('congress.conf.test')]
        config.init(args)

    def test_startup(self):
        self.assertIsNotNone(self.services['api'])
        self.assertIsNotNone(self.services[harness.ENGINE_SERVICE_NAME])
        self.assertIsNotNone(self.services[harness.ENGINE_SERVICE_NAME].node)

    def test_policy(self):
        self.create_policy('alpha')
        self.insert_rule('q(1, 2) :- true', 'alpha')
        self.insert_rule('q(2, 3) :- true', 'alpha')
        helper.retry_check_function_return_value(
            lambda: sorted(self.query('q', 'alpha')['results']),
            sorted([{'data': (1, 2)}, {'data': (2, 3)}]))
        helper.retry_check_function_return_value(
            lambda: list(self.query('q', 'alpha').keys()),
            ['results'])

    def test_policy_datasource(self):
        self.create_policy('alpha')
        self.create_fake_datasource('fake')
        data = self.node.service_object('fake')
        data.state = {'fake_table': set([(1, 2)])}

        data.poll()
        self.insert_rule('q(x) :- fake:fake_table(x,y)', 'alpha')
        helper.retry_check_function_return_value(
            lambda: self.query('q', 'alpha'), {'results': [{'data': (1,)}]})

        # TODO(dse2): enable rules to be inserted before data created.
        #  Maybe just have subscription handle errors gracefull when
        #  asking for a snapshot and return [].
        # self.insert_rule('p(x) :- fake:fake_table(x)', 'alpha')

    def create_policy(self, name):
        self.api['api-policy'].add_item({'name': name}, {})

    def insert_rule(self, rule, policy):
        context = {'policy_id': policy}
        return self.api['api-rule'].add_item(
            {'rule': rule}, {}, context=context)

    def create_fake_datasource(self, name):
        item = {'name': name,
                'driver': 'fake_datasource',
                'description': 'hello world!',
                'enabled': True,
                'type': None,
                'config': {'auth_url': 'foo',
                           'username': 'armax',
                           'password': '<hidden>',
                           'tenant_name': 'armax'}}

        return self.api['api-datasource'].add_item(item, params={})

    def query(self, tablename, policyname):
        context = {'policy_id': policyname,
                   'table_id': tablename}
        return self.api['api-row'].get_items({}, context)

    def test_rule_insert_delete(self):
        self.api['api-policy'].add_item({'name': 'alice'}, {})
        context = {'policy_id': 'alice'}
        (id1, _) = self.api['api-rule'].add_item(
            {'rule': 'p(x) :- plus(y, 1, x), q(y)'}, {}, context=context)
        ds = self.api['api-rule'].get_items({}, context)['results']
        self.assertEqual(len(ds), 1)
        self.api['api-rule'].delete_item(id1, {}, context)
        ds = self.engine.policy_object('alice').content()
        self.assertEqual(len(ds), 0)

    def test_datasource_request_refresh(self):
        # Remember that neutron does not poll automatically here, which
        #   is why this test actually testing request_refresh
        neutron = self.neutronv2
        LOG.info("neutron.state: %s", neutron.state)
        self.assertEqual(len(neutron.state['ports']), 0)
        # TODO(thinrichs): Seems we can't test the datasource API at all.
        # api['datasource-model'].request_refresh_action(
        #     {}, context, helper.FakeRequest({}))
        neutron.request_refresh()
        f = lambda: len(neutron.state['ports'])
        helper.retry_check_function_return_value_not_eq(f, 0)


class TestPolicyExecute(TestCongress):

    def setUp(self):
        super(TestPolicyExecute, self).setUp()
        self.nova = self._register_test_datasource('nova')

    def _register_test_datasource(self, name):
        args = helper.datasource_openstack_args()
        if name == 'nova':
            ds = nova_driver.NovaDriver('nova', args=args)
        if name == 'neutron':
            ds = neutronv2_driver.NeutronV2Driver('neutron', args=args)
        self.node.register_service(ds)
        ds.update_from_datasource = mock.MagicMock()
        return ds

    def test_policy_execute(self):
        class NovaClient(object):
            def __init__(self, testkey):
                self.testkey = testkey

            def disconnectNetwork(self, arg1):
                LOG.info("disconnectNetwork called on %s", arg1)
                self.testkey = "arg1=%s" % arg1

        nova_client = NovaClient("testing")
        nova = self.nova
        nova.nova_client = nova_client

        # insert rule and data
        self.api['api-policy'].add_item({'name': 'alice'}, {})
        (id1, _) = self.api['api-rule'].add_item(
            {'rule': 'execute[nova:disconnectNetwork(x)] :- q(x)'}, {},
            context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 0)
        (id2, _) = self.api['api-rule'].add_item(
            {'rule': 'q(1)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)
        ans = "arg1=1"
        f = lambda: nova.nova_client.testkey
        helper.retry_check_function_return_value(f, ans)

        # insert more data
        self.api['api-rule'].add_item(
            {'rule': 'q(2)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 2)
        ans = "arg1=2"
        f = lambda: nova.nova_client.testkey
        helper.retry_check_function_return_value(f, ans)

        # insert irrelevant data
        self.api['api-rule'].add_item(
            {'rule': 'r(3)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 2)

        # delete relevant data
        self.api['api-rule'].delete_item(
            id2, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 2)

        # delete policy rule
        self.api['api-rule'].delete_item(
            id1, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 2)

    def test_policy_execute_data_first(self):
        class NovaClient(object):
            def __init__(self, testkey):
                self.testkey = testkey

            def disconnectNetwork(self, arg1):
                LOG.info("disconnectNetwork called on %s", arg1)
                self.testkey = "arg1=%s" % arg1

        nova_client = NovaClient(None)
        nova = self.nova
        nova.nova_client = nova_client

        # insert rule and data
        self.api['api-policy'].add_item({'name': 'alice'}, {})
        self.api['api-rule'].add_item(
            {'rule': 'q(1)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 0)
        self.api['api-rule'].add_item(
            {'rule': 'execute[nova:disconnectNetwork(x)] :- q(x)'}, {},
            context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)
        ans = "arg1=1"
        f = lambda: nova.nova_client.testkey
        helper.retry_check_function_return_value(f, ans)

    def test_policy_execute_dotted(self):
        class NovaClient(object):
            def __init__(self, testkey):
                self.testkey = testkey
                self.servers = ServersClass()

        class ServersClass(object):
            def __init__(self):
                self.ServerManager = ServerManagerClass()

        class ServerManagerClass(object):
            def __init__(self):
                self.testkey = None

            def pause(self, id_):
                self.testkey = "arg1=%s" % id_

        nova_client = NovaClient(None)
        nova = self.nova
        nova.nova_client = nova_client

        self.api['api-policy'].add_item({'name': 'alice'}, {})
        self.api['api-rule'].add_item(
            {'rule': 'execute[nova:servers.ServerManager.pause(x)] :- q(x)'},
            {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 0)
        self.api['api-rule'].add_item(
            {'rule': 'q(1)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)
        ans = "arg1=1"
        f = lambda: nova.nova_client.servers.ServerManager.testkey
        helper.retry_check_function_return_value(f, ans)

    def test_policy_execute_no_args(self):
        class NovaClient(object):
            def __init__(self, testkey):
                self.testkey = testkey

            def disconnectNetwork(self):
                LOG.info("disconnectNetwork called")
                self.testkey = "noargs"

        nova_client = NovaClient(None)
        nova = self.nova
        nova.nova_client = nova_client

        # Note: this probably isn't the behavior we really want.
        #  But at least we have a test documenting that behavior.

        # insert rule and data
        self.api['api-policy'].add_item({'name': 'alice'}, {})
        (id1, rule1) = self.api['api-rule'].add_item(
            {'rule': 'execute[nova:disconnectNetwork()] :- q(x)'}, {},
            context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 0)
        (id2, rule2) = self.api['api-rule'].add_item(
            {'rule': 'q(1)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)
        ans = "noargs"
        f = lambda: nova.nova_client.testkey
        helper.retry_check_function_return_value(f, ans)

        # insert more data (which DOES NOT cause an execution)
        (id3, rule3) = self.api['api-rule'].add_item(
            {'rule': 'q(2)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)

        # delete all data
        self.api['api-rule'].delete_item(
            id2, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)

        self.api['api-rule'].delete_item(
            id3, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)

        # insert data (which now DOES cause an execution)
        (id4, rule3) = self.api['api-rule'].add_item(
            {'rule': 'q(3)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 2)
        ans = "noargs"
        f = lambda: nova.nova_client.testkey
        helper.retry_check_function_return_value(f, ans)

        # delete policy rule
        self.api['api-rule'].delete_item(
            id1, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 2)

    def test_neutron_policy_execute(self):
        class NeutronClient(object):
            def __init__(self, testkey):
                self.testkey = testkey

            def disconnectNetwork(self, arg1):
                LOG.info("disconnectNetwork called on %s", arg1)
                self.testkey = "arg1=%s" % arg1

        neutron_client = NeutronClient(None)
        neutron = self.neutronv2
        neutron.neutron = neutron_client

        # insert rule and data
        self.api['api-policy'].add_item({'name': 'alice'}, {})
        (id1, _) = self.api['api-rule'].add_item(
            {'rule': 'execute[neutron:disconnectNetwork(x)] :- q(x)'}, {},
            context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 0)
        (id2, _) = self.api['api-rule'].add_item(
            {'rule': 'q(1)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)
        ans = "arg1=1"
        f = lambda: neutron.neutron.testkey
        helper.retry_check_function_return_value(f, ans)

    def test_neutron_policy_poll_and_subscriptions(self):
        """Test polling and publishing of neutron updates."""
        policy = self.engine.DEFAULT_THEORY
        neutron2 = self._create_neutron_mock('neutron2')
        self.engine.initialize_datasource('neutron',
                                          self.neutronv2.get_schema())
        self.engine.initialize_datasource('neutron2',
                                          self.neutronv2.get_schema())
        str_rule = ('p(x0, y0) :- neutron:networks(x0, x1, x2, x3, x4, x5), '
                    'neutron2:networks(y0, y1, y2, y3, y4, y5)')
        rule = {'rule': str_rule, 'name': 'testrule1', 'comment': 'test'}
        self.api['api-rule'].add_item(rule, {}, context={'policy_id': policy})
        # Test policy subscriptions
        subscriptions = self.engine.subscription_list()
        self.assertEqual(sorted([('neutron', 'networks'),
                         ('neutron2', 'networks')]), sorted(subscriptions))
        # Test multiple instances
        self.neutronv2.poll()
        neutron2.poll()
        ans = ('p("240ff9df-df35-43ae-9df5-27fae87f2492", '
               '  "240ff9df-df35-43ae-9df5-27fae87f2492") ')
        helper.retry_check_db_equal(self.engine, 'p(x, y)', ans, target=policy)
