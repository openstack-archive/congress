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

import mox
import neutronclient.v2_0
import os

from congress.api import webservice
from congress.common import config
from congress.datasources.neutron_driver import NeutronDriver
import congress.datasources.tests.unit.test_neutron_driver as test_neutron
from congress import harness
from congress.openstack.common import log as logging
from congress.policy import compile
from congress.policy import runtime
from congress.tests import base
from congress.tests import helper


LOG = logging.getLogger(__name__)


class TestCongress(base.SqlTestCase):
    @staticmethod
    def state_path():
        """Return path to the dir at which policy contents are stored."""
        path = helper.state_path()
        if not os.path.exists(path):
            os.makedirs(path)
        return path

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
        override = {}
        override['neutron'] = {'client': neutron_mock, 'poll_time': 0}
        override['neutron2'] = {'client': neutron_mock2, 'poll_time': 0}
        override['nova'] = {'poll_time': 0}

        cage = harness.create(helper.root_path(), self.state_path(),
                              helper.datasource_config_path(), override)
        engine = cage.service_object('engine')
        api = {'policy': cage.service_object('api-policy'),
               'rule': cage.service_object('api-rule'),
               'table': cage.service_object('api-table'),
               'row': cage.service_object('api-row'),
               'datasource': cage.service_object('api-datasource'),
               'status': cage.service_object('api-status'),
               'schema': cage.service_object('api-schema')}

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
        # Send formula
        formula = create_network_group('p')
        LOG.debug("Sending formula: {}".format(str(formula)))
        api['rule'].publish('policy-update', [runtime.Event(formula)])
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
        # Send formula
        formula = test_neutron.create_network_group('p')
        LOG.debug("Sending formula: {}".format(str(formula)))
        api['rule'].publish('policy-update', [runtime.Event(formula)])
        helper.retry_check_nonempty_last_policy_change(engine)
        LOG.debug("All services: " + str(cage.services.keys()))
        neutron = cage.service_object('neutron')
        neutron.poll()
        ans = ('p("240ff9df-df35-43ae-9df5-27fae87f2492") ')
        helper.retry_check_db_equal(engine, 'p(x)', ans)

    def test_multiple(self):
        """Test polling and publishing of multiple neutron instances."""
        api = self.api
        cage = self.cage
        engine = self.engine

        # Send formula
        formula = create_networkXnetwork_group('p')
        api['rule'].publish('policy-update', [runtime.Event(formula)])
        helper.retry_check_nonempty_last_policy_change(engine)
        # poll datasources
        neutron = cage.service_object('neutron')
        neutron2 = cage.service_object('neutron2')
        neutron.poll()
        neutron2.poll()
        # check answer
        ans = ('p("240ff9df-df35-43ae-9df5-27fae87f2492",  '
               '  "240ff9df-df35-43ae-9df5-27fae87f2492") ')
        helper.retry_check_db_equal(engine, 'p(x,y)', ans)

    def test_rule_api_model(self):
        """Test the rule api model.  Same as test_multiple except
        we use the api interface instead of the DSE interface.
        """
        api = self.api
        cage = self.cage
        engine = self.engine

        # Insert formula
        net_formula = create_networkXnetwork_group('p')
        LOG.debug("Sending formula: {}".format(str(net_formula)))
        engine.debug_mode()
        context = {'policy_id': engine.DEFAULT_THEORY}
        (id1, rule) = api['rule'].add_item(
            {'rule': str(net_formula)}, {}, context=context)
        # Poll
        neutron = cage.service_object('neutron')
        neutron2 = cage.service_object('neutron2')
        neutron.poll()
        neutron2.poll()
        # Insert a second formula
        other_formula = compile.parse1('q(x,y) :- p(x,y)')
        (id2, rule) = api['rule'].add_item(
            {'rule': str(other_formula)}, {}, context=context)
        ans1 = ('p("240ff9df-df35-43ae-9df5-27fae87f2492",  '
                '  "240ff9df-df35-43ae-9df5-27fae87f2492") ')
        ans2 = ('q("240ff9df-df35-43ae-9df5-27fae87f2492",  '
                '  "240ff9df-df35-43ae-9df5-27fae87f2492") ')
        # Wait for first query so messages can be delivered.
        #    But once the p table has its data, no need to wait anymore.
        helper.retry_check_db_equal(engine, 'p(x,y)', ans1)
        e = helper.db_equal(engine.select('q(x,y)'), ans2)
        self.assertTrue(e, "Insert rule-api 2")
        # Get formula
        ruleobj = api['rule'].get_item(id1, {}, context=context)
        self.assertTrue(e, net_formula == compile.parse1(ruleobj['rule']))
        # Get all formulas
        ds = api['rule'].get_items({}, context=context)['results']
        self.assertEqual(len(ds), 2)
        ids = set([x['id'] for x in ds])
        rules = set([compile.parse1(x['rule']) for x in ds])
        self.assertEqual(ids, set([id1, id2]))
        self.assertEqual(rules, set([net_formula, other_formula]))
        # Delete formula
        api['rule'].delete_item(id1, {}, context=context)
        # Get all formulas
        ds = api['rule'].get_items({}, context=context)['results']
        self.assertEqual(len(ds), 1)
        ids = sorted([x['id'] for x in ds])
        self.assertEqual(ids, sorted([id2]))

    def test_rule_api_model_extended(self):
        """Test extended rule syntax."""
        api = self.api
        engine = self.engine
        engine.set_schema(
            'nova', compile.Schema({'q': ("name", "status", "year")}))

        # insert/retrieve rule with column references
        # just testing that no errors are thrown--correctness tested elsewhere
        # Assuming that api-models are pass-throughs to functionality
        context = {'policy_id': engine.DEFAULT_THEORY}
        (id1, rule) = api['rule'].add_item(
            {'rule': 'p(x) :- nova:q(name=x)'}, {}, context=context)
        api['rule'].get_item(id1, {}, context=context)

    def test_rule_api_model_errors(self):
        """Test that syntax errors thrown by the policy runtime
        are returned properly to the user so they can see the
        error messages.
        """
        api = self.api
        engine = self.engine

        context = {'policy_id': engine.DEFAULT_THEORY}

        # lexer error
        with self.assertRaisesRegexp(
                webservice.DataModelException,
                "Lex failure"):
            api['rule'].add_item(
                {'rule': 'p#'}, {}, context=context)

        # parser error
        with self.assertRaisesRegexp(
                webservice.DataModelException,
                "Parse failure"):
            api['rule'].add_item(
                {'rule': 'p('}, {}, context=context)

        # single-rule error: safety in the head
        with self.assertRaisesRegexp(
                webservice.DataModelException,
                "Variable x found in head but not in body"):
            api['rule'].add_item(
                {'rule': 'p(x,y) :- q(y)'}, {}, context=context)

        # multi-rule error: recursion through negation
        api['rule'].add_item(
            {'rule': 'p(x) :- q(x), not r(x)'}, {}, context=context)
        with self.assertRaisesRegexp(
                webservice.DataModelException,
                "Rules are recursive"):
            api['rule'].add_item(
                {'rule': 'r(x) :- q(x), not p(x)'}, {}, context=context)

        # duplicate rules
        api['rule'].add_item(
            {'rule': 'p(x) :- q(x)'}, {}, context=context)
        with self.assertRaisesRegexp(
                webservice.DataModelException,
                "Rule already exists"):
            api['rule'].add_item(
                {'rule': 'p(x) :- q(x)'}, {}, context=context)

    def test_table_api_model(self):
        """Test the table api model."""
        api = self.api
        engine = self.engine

        # add some rules defining tables
        context = {'policy_id': engine.DEFAULT_THEORY}
        api['rule'].add_item(
            {'rule': 'p(x) :- q(x)'},
            {}, context=context)
        api['rule'].add_item(
            {'rule': 'q(x) :- r(x)'},
            {}, context=context)
        tables = api['table'].get_items({}, context=context)['results']
        tables = [t['id'] for t in tables]
        self.assertEqual(set(tables), set(['p', 'q', 'r']))

    def test_policy_api_model(self):
        """Test the policy api model."""
        api = self.api
        engine = self.engine

        context = {'policy_id': engine.DEFAULT_THEORY}
        policies = api['policy'].get_items({}, context=context)['results']
        policies = [p['id'] for p in policies]
        self.assertEqual(sorted(policies), sorted(engine.theory.keys()))

    def test_policy_api_model_simulate(self):
        def check_err(params, context, emsg, msg):
            try:
                api['policy'].simulate_action(params, context, None)
                self.fail(msg + ":: Error should have been thrown: " + emsg)
            except webservice.DataModelException as e:
                if emsg not in str(e):
                    emsg = "Expected error: {}. Actual error: {}".format(
                        emsg, str(e))
                    self.fail(msg + ":: " + emsg)

        api = self.api
        engine = self.engine
        context = {'policy_id': engine.ACTION_THEORY}

        # add actions to the action theory
        api['rule'].add_item({'rule': 'action("q")'}, {}, context=context)
        api['rule'].add_item({'rule': 'p+(x) :- q(x)'}, {}, context=context)

        # run simulation
        params = {'query': 'p(x)',
                  'action_policy': engine.ACTION_THEORY,
                  'sequence': 'q(1)'}
        result = api['policy'].simulate_action(params, context, None)['result']
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "p(1)")

        # run simulation with delta
        params = {'query': 'p(x)',
                  'action_policy': engine.ACTION_THEORY,
                  'sequence': 'q(1)',
                  'delta': 'true'}
        result = api['policy'].simulate_action(params, context, None)['result']
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "p+(1)")

        # run simulation with trace
        params = {'query': 'p(x)',
                  'action_policy': engine.ACTION_THEORY,
                  'sequence': 'q(1)',
                  'trace': 'true'}
        dresult = api['policy'].simulate_action(params, context, None)
        result = dresult['result']
        trace = dresult['trace']
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "p(1)")
        self.assertTrue(len(trace) > 10)

        # run simulation with delta and trace
        params = {'query': 'p(x)',
                  'action_policy': engine.ACTION_THEORY,
                  'sequence': 'q(1)',
                  'trace': 'true',
                  'delta': 'true'}
        dresult = api['policy'].simulate_action(params, context, None)
        result = dresult['result']
        trace = dresult['trace']
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "p+(1)")
        self.assertTrue(len(trace) > 10)

    def test_policy_api_model_simulate_errors(self):
        def check_err(params, context, emsg, msg):
            try:
                api['policy'].simulate_action(params, context, None)
                self.fail(msg + ":: Error should have been thrown: " + emsg)
            except webservice.DataModelException as e:
                if emsg not in str(e):
                    emsg = "Expected error: {}. Actual error: {}".format(
                        emsg, str(e))
                    self.fail(msg + ":: " + emsg)

        api = self.api
        engine = self.engine
        context = {'policy_id': engine.ACTION_THEORY}

        # Missing query
        params = {
            'action_policy': engine.ACTION_THEORY,
            'sequence': 'q(1)'}
        check_err(params, context,
                  'Simulate requires parameters', 'Missing query')

        # Invalid query
        params = {
            'query': 'p(x',
            'action_policy': engine.ACTION_THEORY,
            'sequence': 'q(1)'}
        check_err(params, context, 'Syntax error for rule', 'Invalid query')

        # Multiple querys
        params = {
            'query': 'p(x) q(x)',
            'action_policy': engine.ACTION_THEORY,
            'sequence': 'q(1)'}
        check_err(params, context, 'more than 1 rule', 'Multiple queries')

        # Missing action_policy
        params = {
            'query': 'p(x)',
            'sequence': 'q(1)'}
        check_err(params, context,
                  'Simulate requires parameters', 'Missing action policy')

        # Invalid action_policy
        params = {
            'query': 'p(x)',
            'action_policy': "nonexistent",
            'sequence': 'q(1)'}
        check_err(params, context, 'Unknown policy', 'Invalid action policy')

        # Missing sequence
        params = {
            'query': 'p(x)',
            'action_policy': engine.ACTION_THEORY}
        check_err(params, context,
                  'Simulate requires parameters', 'Missing sequence')

        # Syntactically invalid sequence
        params = {
            'query': 'p(x)',
            'action_policy': engine.ACTION_THEORY,
            'sequence': 'q(1'}
        check_err(params, context, 'Syntax error for rule',
                  'Syntactically invalid sequence')

        # Semantically invalid sequence
        params = {
            'query': 'p(x)',
            'action_policy': engine.ACTION_THEORY,
            'sequence': 'r(1)'}  # r is not an action
        check_err(params, context, 'non-action, non-update',
                  'Semantically invalid sequence')

    def test_datasource_api_model(self):
        """Test the datasource api model.  Same as test_multiple except
        we use the api interface instead of the DSE interface.
        """
        api = self.api
        engine = self.engine
        # Insert formula (which creates neutron services)
        net_formula = create_networkXnetwork_group('p')
        LOG.debug("Sending formula: {}".format(str(net_formula)))
        context = {'policy_id': engine.DEFAULT_THEORY}
        (id1, rule) = api['rule'].add_item(
            {'rule': str(net_formula)}, {}, context=context)
        datasources = api['datasource'].get_items({})['results']
        datasources = [d['id'] for d in datasources]
        self.assertEqual(set(datasources),
                         set(['neutron', 'neutron2', 'nova']))

    def test_status_api_model(self):
        """Test the datasource api model.  Same as test_multiple except
        we use the api interface instead of the DSE interface.
        """
        api = self.api
        context = {'ds_id': 'neutron'}

        # get_items
        # list of key-value dicts: [{'key': x, 'value': y}, ...]
        result = api['status'].get_items({}, context=context)['results']
        d = {x['key']: x['value'] for x in result}
        self.assertTrue('last_updated' in d)
        self.assertTrue('last_error' in d)

        # get_item
        self.assertIsNotNone(api['status'].get_item(
            'last_updated', {}, context=context))
        self.assertIsNotNone(api['status'].get_item(
            'last_error', {}, context=context))

    def test_schema_api_model(self):
        """Test the datasource api model.  Same as test_multiple except
        we use the api interface instead of the DSE interface.
        """
        api = self.api
        neutron_schema = self.cage.service_object('neutron').get_schema()

        # .../data-sources/neutron/schema
        context = {'ds_id': 'neutron'}

        # a list of table objects: [{'table_id': x, 'columns': y}]
        result = api['schema'].get_item(None, {}, context=context)['tables']
        self.assertEqual(len(neutron_schema.keys()), len(result))
        result = dict([(tableobj['table_id'],
                        tuple([col['name'] for col in tableobj['columns']]))
                       for tableobj in result])
        self.assertEqual(result, neutron_schema)

        # .../data-sources/neutron/schema/<table-id>
        # .../data-sources/neutron/tables/<table-id>/schema

        # with table-id this time
        for table in neutron_schema:
            context['table_id'] = table
            tableobj = api['schema'].get_item(None, {}, context=context)
            self.assertEqual(tableobj['table_id'], table)
            colnames = tuple([col['name'] for col in tableobj['columns']])
            self.assertEqual(colnames, neutron_schema[table])

    def test_row_api_model(self):
        """Test the row api model."""
        api = self.api
        engine = self.engine
        # add some rules defining tables
        context = {'policy_id': engine.DEFAULT_THEORY}
        api['rule'].add_item(
            {'rule': 'p(x) :- q(x)'},
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


def create_network_group(tablename):
    """Return rule of the form TABLENAME(x) :- neutron:network(..., x, ...)
    """
    network_key_to_index = NeutronDriver.get_column_map(
        NeutronDriver.NETWORKS)
    network_id_index = network_key_to_index['id']
    network_max_index = max(network_key_to_index.values())
    net_args = ['x' + str(i) for i in xrange(0, network_max_index + 1)]
    formula = compile.parse1(
        '{}({}) :- neutron:networks({})'.format(
        tablename,
        'x' + str(network_id_index),
        ",".join(net_args)))
    return formula


def create_networkXnetwork_group(tablename):
    """Return rule of the form
    TABLENAME(x,y) :- neutron:network(...,x,...),neutron:network(...,y,...)
    """
    network_key_to_index = NeutronDriver.get_column_map(
        NeutronDriver.NETWORKS)
    network_id_index = network_key_to_index['id']
    network_max_index = max(network_key_to_index.values())
    net1_args = ['x' + str(i) for i in xrange(0, network_max_index + 1)]
    net2_args = ['y' + str(i) for i in xrange(0, network_max_index + 1)]
    formula = compile.parse1(
        '{}({},{}) :- neutron:networks({}), neutron2:networks({})'.format(
        tablename,
        'x' + str(network_id_index),
        'y' + str(network_id_index),
        ",".join(net1_args),
        ",".join(net2_args)))
    return formula
