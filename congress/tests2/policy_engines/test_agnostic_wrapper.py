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

from congress.policy_engines import agnostic
from congress.tests import helper
import sys


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


class TestAgnostic(TestRuntime):
    def test_receive_data_no_sequence_num(self):
        '''Test receiving data without sequence numbers'''
        run = agnostic.Dse2Runtime('engine')
        run.always_snapshot = False
        run.create_policy('datasource1')

        # initialize with full table
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[1], [2]], seqnum=None, is_snapshot=True)
        actual = run.select('p(x)')
        correct = 'p(1) p(2)'
        self.assertTrue(helper.db_equal(actual, correct))

        # add data
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[3], [4]], []], seqnum=None, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1) p(2) p(3) p(4)'
        self.assertTrue(helper.db_equal(actual, correct))

        # remove data
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[], [[2], [4]]], seqnum=None, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1) p(3)'
        self.assertTrue(helper.db_equal(actual, correct))

        # add & remove data
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[4]], [[3]]], seqnum=None, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1) p(4)'
        self.assertTrue(helper.db_equal(actual, correct))

        # re-initialize with full table
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[1], [2]], seqnum=None, is_snapshot=True)
        actual = run.select('p(x)')
        correct = 'p(1) p(2)'
        self.assertTrue(helper.db_equal(actual, correct))

    def test_receive_data_in_order(self):
        '''Test receiving data with sequence numbers, in order'''
        run = agnostic.Dse2Runtime('engine')
        run.always_snapshot = False
        run.create_policy('datasource1')

        # initialize with full table
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[1], [2]], seqnum=0, is_snapshot=True)
        actual = run.select('p(x)')
        correct = 'p(1) p(2)'
        self.assertTrue(helper.db_equal(actual, correct))

        # add data
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[3], [4]], []], seqnum=1, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1) p(2) p(3) p(4)'
        self.assertTrue(helper.db_equal(actual, correct))

        # remove data
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[], [[2], [4]]], seqnum=2, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1) p(3)'
        self.assertTrue(helper.db_equal(actual, correct))

        # add & remove data
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[4]], [[3]]], seqnum=3, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1) p(4)'
        self.assertTrue(helper.db_equal(actual, correct))

        # re-initialize with full table
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[1], [2]], seqnum=4, is_snapshot=True)
        actual = run.select('p(x)')
        correct = 'p(1) p(2)'
        self.assertTrue(helper.db_equal(actual, correct))

    def test_receive_data_out_of_order(self):
        '''Test receiving data with sequence numbers, out of order'''
        run = agnostic.Dse2Runtime('engine')
        run.always_snapshot = False
        run.create_policy('datasource1')

        # update with lower seqnum than init snapshot is ignored
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[10]], []], seqnum=3, is_snapshot=False)

        # add & remove data
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[4]], [[3]]], seqnum=7, is_snapshot=False)
        actual = run.select('p(x)')
        correct = ''
        self.assertTrue(helper.db_equal(actual, correct))

        # remove data
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[], [[2], [4]]], seqnum=6, is_snapshot=False)
        actual = run.select('p(x)')
        correct = ''
        self.assertTrue(helper.db_equal(actual, correct))

        # add data
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[3], [4]], []], seqnum=5, is_snapshot=False)
        actual = run.select('p(x)')
        correct = ''
        self.assertTrue(helper.db_equal(actual, correct))

        # initialize with full table
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[1], [2]], seqnum=4, is_snapshot=True)
        actual = run.select('p(x)')
        correct = 'p(1) p(4)'
        self.assertTrue(helper.db_equal(actual, correct))

    def test_receive_data_arbitrary_start(self):
        '''Test receiving data with arbitrary starting sequence number'''
        run = agnostic.Dse2Runtime('engine')
        run.always_snapshot = False
        run.create_policy('datasource1')
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[1], [2]], seqnum=1234, is_snapshot=True)
        actual = run.select('p(x)')
        correct = 'p(1) p(2)'
        self.assertTrue(helper.db_equal(actual, correct))

    def test_receive_data_duplicate_sequence_number(self):
        '''Test receiving data with duplicate sequence number

        Only one message (arbitrary) should be processed.
        '''
        run = agnostic.Dse2Runtime('engine')
        run.always_snapshot = False
        run.create_policy('datasource1')

        # send three updates with the same seqnum
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[1]], []], seqnum=1, is_snapshot=False)
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[2]], []], seqnum=1, is_snapshot=False)
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[3]], []], seqnum=1, is_snapshot=False)

        # start with empty data
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[], seqnum=0, is_snapshot=True)

        # exactly one of the three updates should be applied
        actual = run.select('p(x)')
        correct1 = 'p(1)'
        correct2 = 'p(2)'
        correct3 = 'p(3)'
        self.assertTrue(
            helper.db_equal(actual, correct1) or
            helper.db_equal(actual, correct2) or
            helper.db_equal(actual, correct3))

    def test_receive_data_sequence_number_max_int(self):
        '''Test receiving data when sequence number goes over max int'''
        run = agnostic.Dse2Runtime('engine')
        run.always_snapshot = False
        run.create_policy('datasource1')

        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[1], [2]], seqnum=sys.maxsize, is_snapshot=True)
        actual = run.select('p(x)')
        correct = 'p(1) p(2)'
        self.assertTrue(helper.db_equal(actual, correct))

        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[], [[2]]], seqnum=sys.maxsize + 1, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1)'
        self.assertTrue(helper.db_equal(actual, correct))

        # test out-of-sequence update ignored
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[2]], []], seqnum=sys.maxsize, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1)'
        self.assertTrue(helper.db_equal(actual, correct))

        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[4]], []], seqnum=sys.maxsize + 3, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1)'
        self.assertTrue(helper.db_equal(actual, correct))

        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[3]], []], seqnum=sys.maxsize + 2, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1) p(3) p(4)'
        self.assertTrue(helper.db_equal(actual, correct))

    def test_receive_data_multiple_tables(self):
        '''Test receiving data with sequence numbers, multiple tables'''
        run = agnostic.Dse2Runtime('engine')
        run.always_snapshot = False
        run.create_policy('datasource1')

        # initialize p with full table
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[1]], seqnum=0, is_snapshot=True)
        actual = run.select('p(x)')
        correct = 'p(1)'
        self.assertTrue(helper.db_equal(actual, correct))

        # add data to p
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[2]], []], seqnum=1, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1) p(2)'
        self.assertTrue(helper.db_equal(actual, correct))

        # add data to q
        run.receive_data_sequenced(
            publisher='datasource1', table='q',
            data=[[[2]], []], seqnum=1, is_snapshot=False)
        actual = run.select('q(x)')
        correct = ''  # does not apply until initialize
        self.assertTrue(helper.db_equal(actual, correct))

        # initialize q with full table
        run.receive_data_sequenced(
            publisher='datasource1', table='q',
            data=[[1]], seqnum=0, is_snapshot=True)
        actual = run.select('q(x)')
        correct = 'q(1) q(2)'  # both initial data and preceding update applied
        self.assertTrue(helper.db_equal(actual, correct))

        # add data to q
        run.receive_data_sequenced(
            publisher='datasource1', table='q',
            data=[[[3]], []], seqnum=2, is_snapshot=False)
        actual = run.select('q(x)')
        correct = 'q(1) q(2) q(3)'
        self.assertTrue(helper.db_equal(actual, correct))

        # add data to p
        run.receive_data_sequenced(
            publisher='datasource1', table='p',
            data=[[[3]], []], seqnum=2, is_snapshot=False)
        actual = run.select('p(x)')
        correct = 'p(1) p(2) p(3)'
        self.assertTrue(helper.db_equal(actual, correct))

    # TODO(ekcs): receive data multiple publishers
