# Copyright (c) 2013 VMware, Styra.  All rights reserved.
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
import tenacity
import time

# Note(ekcs): this is needed for direct unit test because Dse2Runtime import,
#             which takes place before the confFixture is setup, fails w/o it
from novaclient import client as nova_client
from oslo_config import cfg
cfg.CONF.datasource_sync_period = 0
from oslo_messaging import conffixture

from congress.api import base as api_base
from congress.datalog import base as datalog_base
from congress.datalog import compile
from congress.datasources import nova_driver
from congress import exception as congressException
from congress.policy_engines import agnostic
from congress.tests.api import base as test_api_base
from congress.tests import base
from congress.tests import fake_datasource
from congress.tests import helper


class TestDSE(base.TestCase):

    def setUp(self):
        super(TestDSE, self).setUp()
        mc_fixture = conffixture.ConfFixture(cfg.CONF)
        mc_fixture.conf.transport_url = 'kombu+memory://'
        self.messaging_config = mc_fixture.conf
        self.messaging_config.rpc_response_timeout = 1

    def test_intranode_pubsub(self):
        node = helper.make_dsenode_new_partition('testnode')
        test1 = fake_datasource.FakeDataSource('test1')
        test2 = fake_datasource.FakeDataSource('test2')
        node.register_service(test1)
        node.register_service(test2)

        test1.subscribe('test2', 'p')
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        test2.publish('p', [42], use_snapshot=True)
        helper.retry_check_function_return_value(
            lambda: test1.last_msg['data'], [42])
        self.assertFalse(hasattr(test2, "last_msg"))
        node.stop()

    def test_intranode_pubsub2(self):
        # same as test_intranode_pubsub but with opposite ordering.
        # (Ordering does matter with internode_pubsub).
        node = helper.make_dsenode_new_partition('testnode')
        test1 = fake_datasource.FakeDataSource('test1')
        test2 = fake_datasource.FakeDataSource('test2')
        node.register_service(test1)
        node.register_service(test2)

        test2.subscribe('test1', 'p')
        helper.retry_check_function_return_value(
            lambda: hasattr(test2, 'last_msg'), True)
        test1.publish('p', [42], use_snapshot=True)
        helper.retry_check_function_return_value(
            lambda: test2.last_msg['data'], [42])
        self.assertFalse(hasattr(test1, "last_msg"))
        node.stop()

    def test_intranode_partial_unsub(self):
        node = helper.make_dsenode_new_partition('testnode')
        test1 = fake_datasource.FakeDataSource('test1')
        test2 = fake_datasource.FakeDataSource('test2')
        node.register_service(test1)
        node.register_service(test2)

        test1.subscribe('test2', 'p')
        test1.subscribe('test2', 'q')
        test1.unsubscribe('test2', 'q')  # unsub from q should not affect p
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        test2.publish('p', [42], use_snapshot=True)
        helper.retry_check_function_return_value(
            lambda: test1.last_msg['data'], [42])
        self.assertFalse(hasattr(test2, "last_msg"))
        node.stop()

    def test_sub_before_service_exists(self):
        node = helper.make_dsenode_new_partition('testnode')
        test1 = fake_datasource.FakeDataSource('test1')
        node.register_service(test1)

        test1.subscribe('test2', 'p')
        self.assertFalse(hasattr(test1, "last_msg"))
        test2 = fake_datasource.FakeDataSource('test2')
        node.register_service(test2)
        test2.publish('p', [42], use_snapshot=True)
        helper.retry_check_function_return_value(
            lambda: test1.last_msg['data'], [42])
        self.assertFalse(hasattr(test2, "last_msg"))
        node.stop()
        node.wait()

    def test_internode_pubsub(self):
        node1 = helper.make_dsenode_new_partition('testnode1')
        test1 = fake_datasource.FakeDataSource('test1')
        node1.register_service(test1)
        node2 = helper.make_dsenode_same_partition(node1, 'testnode2')
        test2 = fake_datasource.FakeDataSource('test2')
        node2.register_service(test2)

        test1.subscribe('test2', 'p')
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        test2.publish('p', [42], use_snapshot=True)
        helper.retry_check_function_return_value(
            lambda: test1.last_msg['data'], [42])
        self.assertFalse(hasattr(test2, "last_msg"))
        node1.stop()
        node2.stop()

    def test_internode_partial_unsub(self):
        node1 = helper.make_dsenode_new_partition('testnode1')
        node2 = helper.make_dsenode_same_partition(node1, 'testnode2')
        test1 = fake_datasource.FakeDataSource('test1')
        test2 = fake_datasource.FakeDataSource('test2')
        node1.register_service(test1)
        node2.register_service(test2)

        test1.subscribe('test2', 'p')
        test1.subscribe('test2', 'q')
        test1.unsubscribe('test2', 'q')  # unsub from q should not affect p
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        test2.publish('p', [42], use_snapshot=True)
        helper.retry_check_function_return_value(
            lambda: test1.last_msg['data'], [42])
        self.assertFalse(hasattr(test2, "last_msg"))
        node1.stop()
        node2.stop()

    def test_multiservice_pubsub(self):
        node1 = helper.make_dsenode_new_partition('testnode1')
        test1 = fake_datasource.FakeDataSource('test1')
        test2 = fake_datasource.FakeDataSource('test2')
        node1.register_service(test1)
        node1.register_service(test2)
        node2 = helper.make_dsenode_same_partition(node1, 'testnode2')
        test3 = fake_datasource.FakeDataSource('test3')
        node2.register_service(test3)

        test1.subscribe('test3', 'p')
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        test3.publish('p', [42], use_snapshot=True)
        helper.retry_check_function_return_value(
            lambda: test1.last_msg['data'], [42])
        self.assertFalse(hasattr(test2, "last_msg"))
        self.assertFalse(hasattr(test3, "last_msg"))
        node1.stop()
        node2.stop()

    def test_subscribe_snapshot(self):
        node = helper.make_dsenode_new_partition('testnode')
        test1 = fake_datasource.FakeDataSource('test1')
        test2 = fake_datasource.FakeDataSource('test2')
        node.register_service(test1)
        node.register_service(test2)

        test1.subscribe('test2', 'fake_table')
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        self.assertEqual(test1.last_msg['data'], test2.state['fake_table'])
        node.stop()

    @mock.patch.object(nova_client, 'Client', spec_set=True, autospec=True)
    def test_datasource_sub(self, nova_mock):
        node = helper.make_dsenode_new_partition('testnode')
        nova = nova_driver.NovaDriver(
            name='nova', args=helper.datasource_openstack_args())
        test = fake_datasource.FakeDataSource('test')
        node.register_service(nova)
        node.register_service(test)

        nova.subscribe('test', 'p')
        helper.retry_check_function_return_value(
            lambda: hasattr(nova, 'last_msg'), True)
        test.publish('p', [42], use_snapshot=True)
        helper.retry_check_function_return_value(
            lambda: nova.last_msg['data'], [42])
        self.assertFalse(hasattr(test, "last_msg"))
        node.stop()

    @mock.patch.object(nova_client, 'Client', spec_set=True, autospec=True)
    def test_datasource_unsub(self, nova_mock):
        node = helper.make_dsenode_new_partition('testnode')
        nova = nova_driver.NovaDriver(
            name='nova', args=helper.datasource_openstack_args())
        test = fake_datasource.FakeDataSource('test')
        node.register_service(nova)
        node.register_service(test)

        nova.subscribe('test', 'p')
        helper.retry_check_function_return_value(
            lambda: hasattr(nova, 'last_msg'), True)
        test.publish('p', [42], use_snapshot=True)
        helper.retry_check_function_return_value(
            lambda: nova.last_msg['data'], [42])
        self.assertFalse(hasattr(test, "last_msg"))
        nova.unsubscribe('test', 'p')
        test.publish('p', [43], use_snapshot=True)
        # hard to test that the message is never delivered
        time.sleep(0.2)
        self.assertEqual(nova.last_msg['data'], [42])
        node.stop()

    @mock.patch.object(nova_client, 'Client', spec_set=True, autospec=True)
    def test_datasource_pub(self, nova_mock):
        node = helper.make_dsenode_new_partition('testnode')
        nova = nova_driver.NovaDriver(
            name='nova', args=helper.datasource_openstack_args())
        test = fake_datasource.FakeDataSource('test')
        node.register_service(nova)
        node.register_service(test)

        test.subscribe('nova', 'p')
        helper.retry_check_function_return_value(
            lambda: hasattr(test, 'last_msg'), True)
        nova.publish('p', [42], use_snapshot=True)
        helper.retry_check_function_return_value(
            lambda: test.last_msg['data'], [42])
        self.assertFalse(hasattr(nova, "last_msg"))
        node.stop()

    def test_auto_resub(self):
        config = test_api_base.setup_config(with_fake_datasource=False,
                                            api=False, policy=False)
        node = config['node']
        config['ds_manager'].synchronizer.start()
        sub = fake_datasource.FakeDataSource('sub')
        pub = fake_datasource.FakeDataSource('pub')
        node.register_service(sub)
        node.register_service(pub)
        sub.subscribe('pub', 'p')

        helper.retry_check_function_return_value(
            lambda: hasattr(sub, 'last_msg'), True)
        helper.retry_check_function_return_value(
            lambda: sub.last_msg['data'], set([]))

        sub.receive_data_sequenced(
            'pub', 'p', [[1, 1]], 1, is_snapshot=True)
        helper.retry_check_function_return_value(
            lambda: sub.last_msg['data'], set([(1, 1)]))
        # skipping seqnum 2
        sub.receive_data_sequenced(
            'pub', 'p', [[3, 3]], 3, is_snapshot=True)
        # check that out-of-sequence update not applied
        self.assertRaises(
            tenacity.RetryError,
            helper.retry_check_function_return_value,
            lambda: sub.last_msg['data'], set([(3, 3)]))
        # check that resub takes place, setting data to initial state
        helper.retry_check_function_return_value(
            lambda: sub.last_msg['data'], set([]))
        node.stop()

    def test_datasource_poll(self):
        node = helper.make_dsenode_new_partition('testnode')
        pub = fake_datasource.FakeDataSource('pub')
        sub = fake_datasource.FakeDataSource('sub')
        node.register_service(pub)
        node.register_service(sub)

        sub.subscribe('pub', 'fake_table')
        pub.state = {'fake_table': set([(1, 2)])}
        pub.poll()

        helper.retry_check_function_return_value(
            lambda: sub.last_msg,
            {'publisher': 'pub',
             'data': (set(pub.state['fake_table']), set([])),
             'table': 'fake_table'})
        self.assertFalse(hasattr(pub, "last_msg"))
        node.stop()

    def test_policy_data(self):
        """Test policy correctly processes initial data snapshot."""
        node = helper.make_dsenode_new_partition('testnode')
        data = fake_datasource.FakeDataSource('data')
        engine = agnostic.DseRuntime(api_base.ENGINE_SERVICE_ID)
        node.register_service(data)
        node.register_service(engine)

        engine.create_policy('policy1')
        engine.create_policy('data', kind=datalog_base.DATASOURCE_POLICY_TYPE)
        self.insert_rule(engine, 'p(x) :- data:fake_table(x)', 'policy1')
        data.state = {'fake_table': set([(1,), (2,)])}
        data.poll()
        helper.retry_check_db_equal(
            engine, 'p(x)', 'p(1) p(2)', target='policy1')
        self.assertFalse(hasattr(engine, "last_msg"))
        node.stop()

    def test_policy_data_update(self):
        """Test policy correctly processes initial data snapshot and update."""
        node = helper.make_dsenode_new_partition('testnode')
        data = fake_datasource.FakeDataSource('data')
        engine = agnostic.DseRuntime(api_base.ENGINE_SERVICE_ID)
        node.register_service(data)
        node.register_service(engine)

        engine.create_policy('policy1')
        engine.create_policy('data', kind=datalog_base.DATASOURCE_POLICY_TYPE)
        self.insert_rule(engine, 'p(x) :- data:fake_table(x)', 'policy1')
        data.state = {'fake_table': set([(1,), (2,)])}
        data.poll()
        helper.retry_check_db_equal(
            engine, 'p(x)', 'p(1) p(2)', target='policy1')
        data.state = {'fake_table': set([(1,), (2,), (3,)])}
        data.poll()
        helper.retry_check_db_equal(
            engine, 'p(x)', 'p(1) p(2) p(3)', target='policy1')
        self.assertFalse(hasattr(engine, "last_msg"))
        node.stop()

    def test_policy_data_late_sub(self):
        """Test policy correctly processes data on late subscribe."""
        node = helper.make_dsenode_new_partition('testnode')
        data = fake_datasource.FakeDataSource('data')
        engine = agnostic.DseRuntime(api_base.ENGINE_SERVICE_ID)
        node.register_service(data)
        node.register_service(engine)

        engine.create_policy('policy1')
        engine.create_policy('data', kind=datalog_base.DATASOURCE_POLICY_TYPE)
        data.state = {'fake_table': set([(1,), (2,)])}
        data.poll()
        self.insert_rule(engine, 'p(x) :- data:fake_table(x)', 'policy1')
        helper.retry_check_db_equal(
            engine, 'p(x)', 'p(1) p(2)', target='policy1')
        data.state = {'fake_table': set([(1,), (2,), (3,)])}
        data.poll()
        helper.retry_check_db_equal(
            engine, 'p(x)', 'p(1) p(2) p(3)', target='policy1')
        self.assertFalse(hasattr(engine, "last_msg"))
        node.stop()

    def insert_rule(self, engine, statement, target=None):
        statement = compile.parse1(statement)
        if target is None:
            e = compile.Event(statement)
        else:
            e = compile.Event(statement, target=target)
        engine.process_policy_update([e])

    def test_unregister(self):
        node = helper.make_dsenode_new_partition('testnode')
        test1 = fake_datasource.FakeDataSource('test1')
        node.register_service(test1)
        obj = node.invoke_service_rpc(
            'test1', 'get_status', {'source_id': None, 'params': None})
        self.assertIsNotNone(obj)
        node.unregister_service('test1')
        helper.retry_til_exception(
            congressException.NotFound,
            lambda: node.invoke_service_rpc(
                'test1', 'get_status', {'source_id': None, 'params': None}))
        node.stop()

    def _create_node_with_services(self, nodes, services, num, partition_id):
        nid = 'cbd_node%s' % num
        nodes.append(helper.make_dsenode_same_partition(partition_id, nid))
        ns = []
        for s in range(num):
            # intentionally starting different number services
            ns.append(
                fake_datasource.FakeDataSource('cbd-%d_svc-%d' % (num, s)))
            nodes[-1].register_service(ns[-1])
        services.append(ns)
        return nodes[-1]

    def test_subs_list_update_aggregated_by_service(self):
        part = helper.get_new_partition()
        nodes = []
        services = []
        num_nodes = 3

        for i in range(num_nodes):
            n = self._create_node_with_services(nodes, services, i, part)
            n.start()

        # add subscriptions
        for i in range(2, num_nodes):
            for s2 in services[i]:
                for s1 in services[i-1]:
                    s1.subscribe(s2.service_id, 'table-A')
                    s2.subscribe(s1.service_id, 'table-B')
        services[1][0].subscribe(services[2][0].service_id, 'table-C')
        services[2][1].subscribe(services[2][0].service_id, 'table-D')

        # constructed expected results
        expected_subbed_tables = {}
        expected_subbed_tables[nodes[1].node_id] = {}
        expected_subbed_tables[nodes[2].node_id] = {}
        expected_subbed_tables[nodes[1].node_id][
            services[1][0].service_id] = set(['table-B'])
        expected_subbed_tables[nodes[2].node_id][
            services[2][0].service_id] = set(['table-A', 'table-C', 'table-D'])
        expected_subbed_tables[nodes[2].node_id][
            services[2][1].service_id] = set(['table-A'])

        # validate
        def _validate_subbed_tables(node):
            for s in node.get_services():
                sid = s.service_id
                subscribed_tables = node.service_object(
                    sid)._published_tables_with_subscriber
                self.assertEqual(
                    subscribed_tables,
                    expected_subbed_tables[node.node_id][sid],
                    '%s has incorrect subscribed tables list' % sid)
            return True
        for n in nodes:
            helper.retry_check_function_return_value(
                lambda: _validate_subbed_tables(n), True)

        # selectively unsubscribe
        services[1][0].unsubscribe(services[2][0].service_id, 'table-A')
        # note that services[2][1] still subscribes to 'table-B'
        services[2][0].unsubscribe(services[1][0].service_id, 'table-B')
        # extraneous unsubscribe
        services[2][0].unsubscribe(services[1][0].service_id, 'table-None')

        # update expected results
        expected_subbed_tables[nodes[2].node_id][
            services[2][0].service_id] = set(['table-C', 'table-D'])

        for n in nodes:
            helper.retry_check_function_return_value(
                lambda: _validate_subbed_tables(n), True)

        # resubscribe
        services[1][0].subscribe(services[2][0].service_id, 'table-A')
        services[2][0].subscribe(services[1][0].service_id, 'table-B')

        # update expected results
        expected_subbed_tables[nodes[2].node_id][
            services[2][0].service_id] = set(['table-A', 'table-C', 'table-D'])

        for n in nodes:
            helper.retry_check_function_return_value(
                lambda: _validate_subbed_tables(n), True)

    # TODO(dse2): the policy table subscription feature is not ready in DSE2
    #     the problem is that compile and agnostic are not ready to deal with
    #     the double qualifier publishing_policy_engine:policy_name:table_name
    #     that the receiving policy engine needs to handle when subscribing to
    #     policy_name:table_name from publishing_policy_engine.
    #     This feature is not urgent because Congress currently does not have
    #     one policy engine subscribing from another policy engine
    #     (only from data source)
    # def test_policy_table_publish(self):
    #     """Policy table result publish
    #
    #     Test basic DSE functionality with policy engine and table result
    #     publish.
    #     """
    #     node = helper.make_dsenode_new_partition('testnode')
    #     data = fake_datasource.FakeDataSource('data')
    #     policy = agnostic.DseRuntime('policy')
    #     policy2 = agnostic.DseRuntime('policy2')
    #     node.register_service(data)
    #     node.register_service(policy)
    #     node.register_service(policy2)
    #     policy.synchronizer = mock.MagicMock()
    #     policy2.synchronizer = mock.MagicMock()
    #
    #     policy.create_policy(
    #         'data', kind=datalog_base.DATASOURCE_POLICY_TYPE)
    #     policy.create_policy('classification')
    #     policy.set_schema('data', compile.Schema({'q': (1,)}))
    #     policy.insert('p(x):-data:q(x),gt(x,2)', target='classification')
    #
    #     policy.insert('q(3)', target='data')
    #     # TODO(ekcs): test that no publish triggered (because no subscribers)
    #
    #     policy2.create_policy('policy')
    #     policy2.subscribe('policy', 'classification:p')
    #     helper.retry_check_function_return_value(
    #         lambda: 'classification:p' in
    #         policy._published_tables_with_subscriber, True)
    #     self.assertEqual(list(policy.policySubData.keys()),
    #                      [('p', 'classification', None)])
    #
    #     helper.retry_check_db_equal(
    #         policy2, 'policy:classification:p(x)',
    #         'policy:classification:p(3)')
    #
    #     policy.insert('q(4)', target='data')
    #     helper.retry_check_db_equal(
    #         policy2, 'policy:classification:p(x)',
    #         ('policy:classification:p(3)'
    #          ' policy:classification:p(4)'))
    #
    #     # test that no change to p means no publish triggered
    #     policy.insert('q(2)', target='data')
    #     # TODO(ekcs): test no publish triggered
    #
    #     policy.delete('q(4)', target='data')
    #     helper.retry_check_db_equal(
    #         policy2, 'policy:classification:p(x)',
    #         'policy:classification:p(3)')
    #
    #     policy2.unsubscribe('policy', 'classification:p')
    #     # trigger removed
    #     helper.retry_check_function_return_value(
    #         lambda: len(policy._published_tables_with_subscriber) == 0, True)
    #     self.assertEqual(list(policy.policySubData.keys()), [])
    #
    #     policy.insert('q(4)', target='data')
    #     # TODO(ekcs): test that no publish triggered (because no subscribers)
    #     node.stop()

    def test_replicated_pe_exec(self):
        """Test correct local leader behavior with 2 PEs requesting exec"""
        node1 = helper.make_dsenode_new_partition('testnode1')
        node2 = helper.make_dsenode_same_partition(node1, 'testnode2')
        dsd = fake_datasource.FakeDataSource('dsd')
        # faster time-out for testing
        dsd.LEADER_TIMEOUT = 2
        pe1 = agnostic.DseRuntime('pe1')
        pe2 = agnostic.DseRuntime('pe2')
        node1.register_service(pe1)
        node2.register_service(pe2)
        node1.register_service(dsd)
        assert dsd._running
        assert node1._running
        assert node2._running
        assert node1._control_bus._running

        # first exec request obeyed and leader set
        pe2.rpc('dsd', 'request_execute',
                {'action': 'fake_act', 'action_args': {'name': 'testnode2'},
                 'wait': True})
        helper.retry_check_function_return_value(
            lambda: len(dsd.exec_history), 1)
        self.assertEqual(dsd._leader_node_id, 'testnode2')

        # second exec request from leader obeyed and leader remains
        pe2.rpc('dsd', 'request_execute',
                {'action': 'fake_act', 'action_args': {'name': 'testnode2'},
                 'wait': True})
        helper.retry_check_function_return_value(
            lambda: len(dsd.exec_history), 2)
        self.assertEqual(dsd._leader_node_id, 'testnode2')

        # exec request from non-leader not obeyed
        pe1.rpc('dsd', 'request_execute',
                {'action': 'fake_act', 'action_args': {'name': 'testnode1'},
                 'wait': True})
        self.assertRaises(
            tenacity.RetryError,
            helper.retry_check_function_return_value,
            lambda: len(dsd.exec_history), 3)

        # leader vacated after heartbeat stops
        node2.stop()
        node2.wait()
        helper.retry_check_function_return_value(
            lambda: dsd._leader_node_id, None)

        # next exec request obeyed and new leader set
        pe1.rpc('dsd', 'request_execute',
                {'action': 'fake_act', 'action_args': {'name': 'testnode1'},
                 'wait': True})
        helper.retry_check_function_return_value(
            lambda: len(dsd.exec_history), 3)
        self.assertEqual(dsd._leader_node_id, 'testnode1')
        node1.stop()
        node2.stop()
