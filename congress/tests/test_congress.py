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
from functools import reduce

import os

import mock
from mox3 import mox
import neutronclient.v2_0
from oslo_log import log as logging

from congress.api import webservice
from congress.common import config
from congress.datalog import compile
from congress import harness
from congress.tests import base
import congress.tests.datasources.test_neutron_driver as test_neutron
from congress.tests import helper


LOG = logging.getLogger(__name__)


class TestCongress(base.SqlTestCase):

    def setUp(self):
        """Setup tests that use multiple mock neutron instances."""
        super(TestCongress, self).setUp()
        # create neutron mock and tell cage to use that mock
        #  https://code.google.com/p/pymox/wiki/MoxDocumentation
        mock_factory = mox.Mox()
        neutron_mock = mock_factory.CreateMock(
            neutronclient.v2_0.client.Client)
        neutron_mock2 = mock_factory.CreateMock(
            neutronclient.v2_0.client.Client)

        config_override = {'neutron2': {'username': 'demo', 'tenant_name':
                                        'demo', 'password': 'password',
                                        'auth_url':
                                            'http://127.0.0.1:5000/v2.0',
                                        'module':
                                            'datasources/neutron_driver.py'},
                           'nova': {'username': 'demo',
                                    'tenant_name': 'demo',
                                    'password': 'password',
                                    'auth_url': 'http://127.0.0.1:5000/v2.0',
                                    'module': 'datasources/nova_driver.py'},
                           'neutron': {'username': 'demo',
                                       'tenant_name': 'demo',
                                       'password': 'password',
                                       'auth_url':
                                            'http://127.0.0.1:5000/v2.0',
                                       'module':
                                            'datasources/neutron_driver.py'}}

        cage = harness.create(helper.root_path(), config_override)
        # Disable synchronizer because the this test creates
        # datasources without also inserting them into the database.
        # The synchronizer would delete these datasources.
        cage.service_object('synchronizer').set_poll_time(0)

        engine = cage.service_object('engine')

        api = {'policy': cage.service_object('api-policy'),
               'rule': cage.service_object('api-rule'),
               'table': cage.service_object('api-table'),
               'row': cage.service_object('api-row'),
               'datasource': cage.service_object('api-datasource'),
               'status': cage.service_object('api-status'),
               'schema': cage.service_object('api-schema')}

        config = {'username': 'demo',
                  'auth_url': 'http://127.0.0.1:5000/v2.0',
                  'tenant_name': 'demo',
                  'password': 'password',
                  'module': 'datasources/neutron_driver.py',
                  'poll_time': 0}

        # FIXME(arosen): remove all this code
        # monkey patch
        engine.create_policy('neutron')
        engine.create_policy('neutron2')
        engine.create_policy('nova')
        harness.load_data_service(
            'neutron', config, cage,
            os.path.join(helper.root_path(), "congress"), 1)
        service = cage.service_object('neutron')
        engine.set_schema('neutron', service.get_schema())
        harness.load_data_service(
            'neutron2', config, cage,
            os.path.join(helper.root_path(), "congress"), 2)

        engine.set_schema('neutron2', service.get_schema())
        config['module'] = 'datasources/nova_driver.py'
        harness.load_data_service(
            'nova', config, cage,
            os.path.join(helper.root_path(), "congress"), 3)
        engine.set_schema('nova', service.get_schema())

        cage.service_object('neutron').neutron = neutron_mock
        cage.service_object('neutron2').neutron = neutron_mock2
        # delete all policies that aren't builtin, so we have clean slate
        names = set(engine.policy_names()) - engine.builtin_policy_names
        for name in names:
            try:
                api['policy'].delete_item(name, {})
            except KeyError:
                pass

        # Turn off schema checking
        engine.module_schema = None

        # initialize neutron_mocks
        network1 = test_neutron.network_response
        port_response = test_neutron.port_response
        router_response = test_neutron.router_response
        sg_group_response = test_neutron.security_group_response
        neutron_mock.list_networks().InAnyOrder().AndReturn(network1)
        neutron_mock.list_ports().InAnyOrder().AndReturn(port_response)
        neutron_mock.list_routers().InAnyOrder().AndReturn(router_response)
        neutron_mock.list_security_groups().InAnyOrder().AndReturn(
            sg_group_response)
        neutron_mock2.list_networks().InAnyOrder().AndReturn(network1)
        neutron_mock2.list_ports().InAnyOrder().AndReturn(port_response)
        neutron_mock2.list_routers().InAnyOrder().AndReturn(router_response)
        neutron_mock2.list_security_groups().InAnyOrder().AndReturn(
            sg_group_response)
        mock_factory.ReplayAll()

        self.cage = cage
        self.engine = engine
        self.api = api

    def setup_config(self):
        args = ['--config-file', helper.etcdir('congress.conf.test')]
        config.init(args)

    def test_startup(self):
        """Test that everything is properly loaded at startup."""
        engine = self.engine
        api = self.api
        helper.retry_check_subscriptions(
            engine, [(api['rule'].name, 'policy-update')])
        helper.retry_check_subscribers(
            api['rule'], [(engine.name, 'policy-update')])

    def test_policy_subscriptions(self):
        """Test that policy engine subscriptions adjust to policy changes."""
        engine = self.engine
        api = self.api
        cage = self.cage
        policy = engine.DEFAULT_THEORY

        # Send formula
        formula = test_neutron.create_network_group('p')
        LOG.debug("Sending formula: %s", formula)
        api['rule'].publish(
            'policy-update', [compile.Event(formula, target=policy)])
        # check we have the proper subscriptions
        self.assertTrue('neutron' in cage.services)
        neutron = cage.service_object('neutron')
        helper.retry_check_subscriptions(engine, [('neutron', 'networks')])
        helper.retry_check_subscribers(neutron, [(engine.name, 'networks')])

    def test_neutron(self):
        """Test polling and publishing of neutron updates."""
        engine = self.engine
        api = self.api
        cage = self.cage
        policy = engine.DEFAULT_THEORY

        # Send formula
        formula = test_neutron.create_network_group('p')
        LOG.debug("Sending formula: %s", formula)
        api['rule'].publish(
            'policy-update', [compile.Event(formula, target=policy)])
        helper.retry_check_nonempty_last_policy_change(engine)
        LOG.debug("All services: %s", cage.services.keys())
        neutron = cage.service_object('neutron')
        neutron.poll()
        ans = ('p("240ff9df-df35-43ae-9df5-27fae87f2492") ')
        helper.retry_check_db_equal(engine, 'p(x)', ans, target=policy)

    def test_multiple(self):
        """Test polling and publishing of multiple neutron instances."""
        api = self.api
        cage = self.cage
        engine = self.engine
        policy = engine.DEFAULT_THEORY

        # Send formula
        formula = test_neutron.create_networkXnetwork_group('p')
        api['rule'].publish(
            'policy-update', [compile.Event(formula, target=policy)])
        helper.retry_check_nonempty_last_policy_change(engine)
        # poll datasources
        neutron = cage.service_object('neutron')
        neutron2 = cage.service_object('neutron2')
        neutron.poll()
        neutron2.poll()
        # check answer
        ans = ('p("240ff9df-df35-43ae-9df5-27fae87f2492",  '
               '  "240ff9df-df35-43ae-9df5-27fae87f2492") ')
        helper.retry_check_db_equal(engine, 'p(x,y)', ans, target=policy)

    def test_datasource_api_model(self):
        """Test the datasource api model.

        Same as test_multiple except we use the api interface
        instead of the DSE interface.
        """
        self.skipTest("Move to test/api/api_model and use fake driver...")
        # FIXME(arosen): we should break out these tests into
        # congress/tests/api/test_datasource.py
        with mock.patch("congress.managers.datasource.DataSourceDriverManager."
                        "get_datasource_drivers_info") as get_info:
            get_info.return_value = [{'datasource_driver': 'neutron'},
                                     {'datasource_driver': 'neutron2'},
                                     {'datasource_driver': 'nova'}]
            api = self.api
            engine = self.engine
            # Insert formula (which creates neutron services)
            net_formula = test_neutron.create_networkXnetwork_group('p')
            LOG.debug("Sending formula: %s", net_formula)
            context = {'policy_id': engine.DEFAULT_THEORY}
            api['rule'].add_item(
                {'rule': str(net_formula)}, {}, context=context)
            datasources = api['datasource'].get_items({})['results']
            datasources = [d['datasource_driver'] for d in datasources]
            self.assertEqual(set(datasources),
                             set(['neutron', 'neutron2', 'nova']))

    def test_row_api_model(self):
        """Test the row api model."""
        self.skipTest("Move to test/api/test_row_api_model..")
        api = self.api
        engine = self.engine
        # add some rules defining tables
        context = {'policy_id': engine.DEFAULT_THEORY}
        api['rule'].add_item(
            {'rule': 'p(x) :- q(x)'},
            {}, context=context)
        api['rule'].add_item(
            {'rule': 'p(x) :- r(x)'},
            {}, context=context)
        api['rule'].add_item(
            {'rule': 'q(x) :- r(x)'},
            {}, context=context)
        api['rule'].add_item(
            {'rule': 'r(1) :- true'},
            {}, context=context)

        # without tracing
        context['table_id'] = 'p'
        ans = api['row'].get_items({}, context=context)
        s = frozenset([tuple(x['data']) for x in ans['results']])
        t = frozenset([(1,)])
        self.assertEqual(s, t, "Rows without tracing")
        self.assertTrue('trace' not in ans, "Rows should have no Trace")
        self.assertEqual(len(ans['results']), 1)  # no duplicates

        # with tracing
        ans = api['row'].get_items({'trace': 'true'}, context=context)
        s = frozenset([tuple(x['data']) for x in ans['results']])
        t = frozenset([(1,)])
        self.assertEqual(s, t, "Rows with tracing")
        self.assertTrue('trace' in ans, "Rows should have trace")
        self.assertEqual(len(ans['trace'].split('\n')), 16)

        # unknown policy table
        context = {'policy_id': engine.DEFAULT_THEORY, 'table_id': 'unktable'}
        ans = api['row'].get_items({}, context=context)
        self.assertEqual(len(ans['results']), 0)

        # unknown policy
        context = {'policy_id': 'unkpolicy', 'table_id': 'unktable'}
        ans = api['row'].get_items({}, context=context)
        self.assertEqual(len(ans['results']), 0)

        # unknown datasource table
        context = {'ds_id': 'neutron', 'table_id': 'unktable'}
        ans = api['row'].get_items({}, context=context)
        self.assertEqual(len(ans['results']), 0)

        # unknown datasource
        context = {'ds_id': 'unkds', 'table_id': 'unktable'}
        ans = api['row'].get_items({}, context=context)
        self.assertEqual(len(ans['results']), 0)

    def test_policy_api_model_execute(self):
        def _execute_api(client, action, action_args):
            LOG.info("_execute_api called on %s and %s", action, action_args)
            positional_args = action_args['positional']
            named_args = action_args['named']
            method = reduce(getattr, action.split('.'), client)
            method(*positional_args, **named_args)

        class NovaClient(object):
            def __init__(self, testkey):
                self.testkey = testkey

            def _get_testkey(self):
                return self.testkey

            def disconnectNetwork(self, arg1, arg2, arg3):
                self.testkey = "arg1=%s arg2=%s arg3=%s" % (arg1, arg2, arg3)

        nova_client = NovaClient("testing")
        nova = self.cage.service_object('nova')
        nova._execute_api = _execute_api
        nova.nova_client = nova_client

        api = self.api
        body = {'name': 'nova:disconnectNetwork',
                'args': {'positional': ['value1', 'value2'],
                         'named': {'arg3': 'value3'}}}

        request = helper.FakeRequest(body)
        result = api['policy'].execute_action({}, {}, request)
        self.assertEqual(result, {})

        expected_result = "arg1=value1 arg2=value2 arg3=value3"
        f = nova.nova_client._get_testkey
        helper.retry_check_function_return_value(f, expected_result)

    def test_rule_insert_delete(self):
        self.api['policy'].add_item({'name': 'alice'}, {})
        context = {'policy_id': 'alice'}
        (id1, _) = self.api['rule'].add_item(
            {'rule': 'p(x) :- plus(y, 1, x), q(y)'}, {}, context=context)
        ds = self.api['rule'].get_items({}, context)['results']
        self.assertEqual(len(ds), 1)
        self.api['rule'].delete_item(id1, {}, context)
        ds = self.engine.policy_object('alice').content()
        self.assertEqual(len(ds), 0)

    # TODO(thinrichs): Clean up this file.  In particular, make it possible
    #   to group all of the policy-execute tests into their own class.
    # Execute[...] tests
    def test_policy_execute(self):
        class NovaClient(object):
            def __init__(self, testkey):
                self.testkey = testkey

            def disconnectNetwork(self, arg1):
                LOG.info("disconnectNetwork called on %s", arg1)
                self.testkey = "arg1=%s" % arg1

        nova_client = NovaClient(None)
        nova = self.cage.service_object('nova')
        nova.nova_client = nova_client

        # insert rule and data
        self.api['policy'].add_item({'name': 'alice'}, {})
        (id1, _) = self.api['rule'].add_item(
            {'rule': 'execute[nova:disconnectNetwork(x)] :- q(x)'}, {},
            context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 0)
        (id2, _) = self.api['rule'].add_item(
            {'rule': 'q(1)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)
        ans = "arg1=1"
        f = lambda: nova.nova_client.testkey
        helper.retry_check_function_return_value(f, ans)

        # insert more data
        self.api['rule'].add_item(
            {'rule': 'q(2)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 2)
        ans = "arg1=2"
        f = lambda: nova.nova_client.testkey
        helper.retry_check_function_return_value(f, ans)

        # insert irrelevant data
        self.api['rule'].add_item(
            {'rule': 'r(3)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 2)

        # delete relevant data
        self.api['rule'].delete_item(
            id2, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 2)

        # delete policy rule
        self.api['rule'].delete_item(
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
        nova = self.cage.service_object('nova')
        nova.nova_client = nova_client

        # insert rule and data
        self.api['policy'].add_item({'name': 'alice'}, {})
        self.api['rule'].add_item(
            {'rule': 'q(1)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 0)
        self.api['rule'].add_item(
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
        nova = self.cage.service_object('nova')
        nova.nova_client = nova_client

        self.api['policy'].add_item({'name': 'alice'}, {})
        self.api['rule'].add_item(
            {'rule': 'execute[nova:servers.ServerManager.pause(x)] :- q(x)'},
            {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 0)
        self.api['rule'].add_item(
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
        nova = self.cage.service_object('nova')
        nova.nova_client = nova_client

        # Note: this probably isn't the behavior we really want.
        #  But at least we have a test documenting that behavior.

        # insert rule and data
        self.api['policy'].add_item({'name': 'alice'}, {})
        (id1, rule1) = self.api['rule'].add_item(
            {'rule': 'execute[nova:disconnectNetwork()] :- q(x)'}, {},
            context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 0)
        (id2, rule2) = self.api['rule'].add_item(
            {'rule': 'q(1)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)
        ans = "noargs"
        f = lambda: nova.nova_client.testkey
        helper.retry_check_function_return_value(f, ans)

        # insert more data (which DOES NOT cause an execution)
        (id3, rule3) = self.api['rule'].add_item(
            {'rule': 'q(2)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)

        # delete all data
        self.api['rule'].delete_item(
            id2, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)

        self.api['rule'].delete_item(
            id3, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)

        # insert data (which now DOES cause an execution)
        (id4, rule3) = self.api['rule'].add_item(
            {'rule': 'q(3)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 2)
        ans = "noargs"
        f = lambda: nova.nova_client.testkey
        helper.retry_check_function_return_value(f, ans)

        # delete policy rule
        self.api['rule'].delete_item(
            id1, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 2)

    def test_datasource_request_refresh(self):
        # Remember that neutron does not poll automatically here, which
        #   is why this test actually testing request_refresh
        neutron = self.cage.service_object('neutron')
        LOG.info("neutron.state: %s", neutron.state)
        self.assertEqual(len(neutron.state['ports']), 0)
        # TODO(thinrichs): Seems we can't test the datasource API at all.
        # api['datasource'].request_refresh_action(
        #     {}, context, helper.FakeRequest({}))
        neutron.request_refresh()
        f = lambda: len(neutron.state['ports'])
        helper.retry_check_function_return_value_not_eq(f, 0)

    def test_neutron_policy_execute(self):
        class NeutronClient(object):
            def __init__(self, testkey):
                self.testkey = testkey

            def disconnectNetwork(self, arg1):
                LOG.info("disconnectNetwork called on %s", arg1)
                self.testkey = "arg1=%s" % arg1

        neutron_client = NeutronClient(None)
        neutron = self.cage.service_object('neutron')
        neutron.neutron = neutron_client

        # insert rule and data
        self.api['policy'].add_item({'name': 'alice'}, {})
        (id1, _) = self.api['rule'].add_item(
            {'rule': 'execute[neutron:disconnectNetwork(x)] :- q(x)'}, {},
            context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 0)
        (id2, _) = self.api['rule'].add_item(
            {'rule': 'q(1)'}, {}, context={'policy_id': 'alice'})
        self.assertEqual(len(self.engine.logger.messages), 1)
        ans = "arg1=1"
        f = lambda: neutron.neutron.testkey
        helper.retry_check_function_return_value(f, ans)

    def test_datasource_api_model_execute(self):
        def _execute_api(client, action, action_args):
            positional_args = action_args.get('positional', [])
            named_args = action_args.get('named', {})
            method = reduce(getattr, action.split('.'), client)
            method(*positional_args, **named_args)

        class NovaClient(object):
            def __init__(self, testkey):
                self.testkey = testkey

            def _get_testkey(self):
                return self.testkey

            def disconnect(self, arg1, arg2, arg3):
                self.testkey = "arg1=%s arg2=%s arg3=%s" % (arg1, arg2, arg3)

            def disconnect_all(self):
                self.testkey = "action_has_no_args"

        nova_client = NovaClient("testing")
        nova = self.cage.service_object('nova')
        nova._execute_api = _execute_api
        nova.nova_client = nova_client

        execute_action = self.api['datasource'].execute_action

        # Positive test: valid body args, ds_id
        context = {'ds_id': 'nova'}
        body = {'name': 'disconnect',
                'args': {'positional': ['value1', 'value2'],
                         'named': {'arg3': 'value3'}}}
        request = helper.FakeRequest(body)
        result = execute_action({}, context, request)
        self.assertEqual(result, {})
        expected_result = "arg1=value1 arg2=value2 arg3=value3"
        f = nova.nova_client._get_testkey
        helper.retry_check_function_return_value(f, expected_result)

        # Positive test: no body args
        context = {'ds_id': 'nova'}
        body = {'name': 'disconnect_all'}
        request = helper.FakeRequest(body)
        result = execute_action({}, context, request)
        self.assertEqual(result, {})
        expected_result = "action_has_no_args"
        f = nova.nova_client._get_testkey
        helper.retry_check_function_return_value(f, expected_result)

        # Negative test: invalid ds_id
        context = {'ds_id': 'unknown_ds'}
        self.assertRaises(webservice.DataModelException, execute_action,
                          {}, context, request)

        # Negative test: no ds_id
        context = {}
        self.assertRaises(webservice.DataModelException, execute_action,
                          {}, context, request)

        # Negative test: empty body
        context = {'ds_id': 'nova'}
        bad_request = helper.FakeRequest({})
        self.assertRaises(webservice.DataModelException, execute_action,
                          {}, context, bad_request)

        # Negative test: no body name/action
        context = {'ds_id': 'nova'}
        body = {'args': {'positional': ['value1', 'value2'],
                         'named': {'arg3': 'value3'}}}
        bad_request = helper.FakeRequest(body)
        self.assertRaises(webservice.DataModelException, execute_action,
                          {}, context, bad_request)
