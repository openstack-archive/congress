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
import unittest

from congress.api import webservice
from congress.datasources.neutron_driver import NeutronDriver
import congress.datasources.tests.unit.test_neutron_driver as test_neutron
from congress import harness
from congress.openstack.common import log as logging
from congress.policy import compile
from congress.policy import runtime
from congress.tests import helper


LOG = logging.getLogger(__name__)


class TestCongress(unittest.TestCase):
    def check_subscriptions(self, deepsix, subscription_list):
        """Check that the instance DEEPSIX is subscribed to all of the
        (key, dataindex) pairs in KEY_DATAINDEX_LIST.
        """
        failed = False
        for subkey, subdata in subscription_list:
            foundkey = False
            for value in deepsix.subdata.values():
                if subkey == value.key and subdata == value.dataindex:
                    foundkey = True
                    break
            if not foundkey:
                failed = True
                LOG.info(
                    "Was not subscribed to key/dataindex: {}/{}".format(
                        subkey, subdata))

        if failed:
            LOG.debug("Subscriptions: " + str(deepsix.subscription_list()))
            self.assertTrue(False, "Subscription check for {} failed".format(
                deepsix.name))

    def check_subscribers(self, deepsix, subscriber_list):
        """Check that the instance DEEPSIX includes subscriptions for all of
        the (name, dataindex) pairs in SUBSCRIBER_LIST.
        """
        failed = False
        for name, dataindex in subscriber_list:
            found_dataindex = False
            for pubdata in deepsix.pubdata.values():
                if pubdata.dataindex == dataindex:
                    found_dataindex = True
                    if name not in pubdata.subscribers:
                        failed = True
                        LOG.info("Subscriber test failed for {} on "
                                 "dataindex {} and name {}".format(
                                     deepsix.name, dataindex, name))
            if not found_dataindex:
                failed = True
                LOG.info(
                    "Subscriber test failed for {} on dataindex {}".format(
                    deepsix.name, dataindex))
        if failed:
            LOG.debug("Subscribers: " + str(deepsix.subscriber_list()))
            self.assertTrue(False, "Subscriber check for {} failed".format(
                            deepsix.name))

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
               'datasource': cage.service_object('api-datasource')}

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

        helper.pause()

        self.cage = cage
        self.engine = engine
        self.api = api

    def test_startup(self):
        """Test that everything is properly loaded at startup."""
        engine = self.engine
        api = self.api
        self.check_subscriptions(engine, [(api['rule'].name, 'policy-update')])
        self.check_subscribers(api['rule'], [(engine.name, 'policy-update')])

    def test_policy_subscriptions(self):
        """Test that policy engine subscriptions adjust to policy changes."""
        engine = self.engine
        api = self.api
        cage = self.cage
        # Send formula
        helper.pause()
        formula = compile.parse1("p(y) :- neutron:networks(y)")
        LOG.debug("Sending formula: {}".format(str(formula)))
        api['rule'].publish('policy-update', [runtime.Event(formula)])
        helper.pause()  # give time for messages/creation of services
        # check we have the proper subscriptions
        self.assertTrue('neutron' in cage.services)
        neutron = cage.service_object('neutron')
        self.check_subscriptions(engine, [('neutron', 'networks')])
        self.check_subscribers(neutron, [(engine.name, 'networks')])

    def test_neutron(self):
        """Test polling and publishing of neutron updates."""
        engine = self.engine
        api = self.api
        cage = self.cage
        helper.pause()
        # Send formula
        formula = test_neutron.create_network_group('p')
        LOG.debug("Sending formula: {}".format(str(formula)))
        api['rule'].publish('policy-update', [runtime.Event(formula)])
        helper.pause()  # give time for messages/creation of services
        LOG.debug("All services: " + str(cage.services.keys()))
        neutron = cage.service_object('neutron')
        neutron.poll()
        helper.pause()
        ans = ('p("240ff9df-df35-43ae-9df5-27fae87f2492") ')
        e = helper.db_equal(engine.select('p(x)'), ans)
        self.assertTrue(e, "Neutron datasource")

    def test_multiple(self):
        """Test polling and publishing of multiple neutron instances."""
        api = self.api
        cage = self.cage
        engine = self.engine

        # Send formula
        formula = create_networkXnetwork_group('p')
        api['rule'].publish('policy-update', [runtime.Event(formula)])
        helper.pause()  # give time for messages/creation of services
        # poll datasources
        neutron = cage.service_object('neutron')
        neutron2 = cage.service_object('neutron2')
        neutron.poll()
        neutron2.poll()
        helper.pause()
        # check answer
        ans = ('p("240ff9df-df35-43ae-9df5-27fae87f2492",  '
               '  "240ff9df-df35-43ae-9df5-27fae87f2492") ')
        e = helper.db_equal(engine.select('p(x,y)'), ans)
        self.assertTrue(e, "Multiple neutron datasources")

    def test_rule_api_model(self):
        """Test the rule api model.  Same as test_multiple except
        we use the api interface instead of the DSE interface.
        """
        api = self.api
        cage = self.cage
        engine = self.engine

        # Insert formula (which creates neutron services)
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
        helper.pause()
        # Insert a second formula
        other_formula = compile.parse1('q(x,y) :- p(x,y)')
        (id2, rule) = api['rule'].add_item(
            {'rule': str(other_formula)}, {}, context=context)
        helper.pause()  # give time for messages/creation of services
        ans1 = ('p("240ff9df-df35-43ae-9df5-27fae87f2492",  '
                '  "240ff9df-df35-43ae-9df5-27fae87f2492") ')
        ans2 = ('q("240ff9df-df35-43ae-9df5-27fae87f2492",  '
                '  "240ff9df-df35-43ae-9df5-27fae87f2492") ')
        e = helper.db_equal(engine.select('p(x,y)'), ans1)
        self.assertTrue(e, "Insert rule-api 1")
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

    def test_rule_api_model_errors(self):
        """Test that syntax errors thrown by the policy runtime
        are returned properly to the user so they can see the
        error messages.
        """
        api = self.api
        engine = self.engine

        context = {'policy_id': engine.DEFAULT_THEORY}

        # lexer error
        with self.assertRaises(
                webservice.DataModelException,
                msg="Lexer error not properly thrown"):
            api['rule'].add_item(
                {'rule': 'p#'}, {}, context=context)

        # parser error
        with self.assertRaises(
                webservice.DataModelException,
                msg="Parser error not properly thrown"):
            api['rule'].add_item(
                {'rule': 'p('}, {}, context=context)

        # single-rule error: safety in the head
        with self.assertRaises(
                webservice.DataModelException,
                msg="Single-rule error not properly thrown"):
            api['rule'].add_item(
                {'rule': 'p(x,y) :- q(y)'}, {}, context=context)

        # multi-rule error: recursion through negation
        api['rule'].add_item(
            {'rule': 'p(x) :- q(x), not r(x)'}, {}, context=context)
        with self.assertRaises(
                webservice.DataModelException,
                msg="Multi-rule error not properly thrown"):
            api['rule'].add_item(
                {'rule': 'r(x) :- q(x), not p(x)'}, {}, context=context)

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

        context = {'ds_id': engine.DEFAULT_THEORY}
        policies = api['policy'].get_items({}, context=context)['results']
        policies = [p['id'] for p in policies]
        self.assertEqual(sorted(policies), sorted(engine.theory.keys()))

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


def create_networkXnetwork_group(tablename):
    network_key_to_index = NeutronDriver.network_key_position_map()
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
