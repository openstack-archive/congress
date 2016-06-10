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
import novaclient
import time

from oslo_config import cfg
cfg.CONF.distributed_architecture = True
from oslo_messaging import conffixture

from congress.datalog import compile
from congress.datasources.nova_driver import NovaDriver
from congress import exception as congressException
from congress.policy_engines.agnostic import Dse2Runtime
from congress.tests import base
from congress.tests.fake_datasource import FakeDataSource
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
        test1 = FakeDataSource('test1')
        test2 = FakeDataSource('test2')
        node.register_service(test1)
        node.register_service(test2)

        test1.subscribe('test2', 'p')
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        test2.publish('p', 42)
        helper.retry_check_function_return_value(
            lambda: test1.last_msg['data'], 42)
        self.assertFalse(hasattr(test2, "last_msg"))

    def test_intranode_pubsub2(self):
        # same as test_intranode_pubsub but with opposite ordering.
        # (Ordering does matter with internode_pubsub).
        node = helper.make_dsenode_new_partition('testnode')
        test1 = FakeDataSource('test1')
        test2 = FakeDataSource('test2')
        node.register_service(test1)
        node.register_service(test2)

        test2.subscribe('test1', 'p')
        helper.retry_check_function_return_value(
            lambda: hasattr(test2, 'last_msg'), True)
        test1.publish('p', 42)
        helper.retry_check_function_return_value(
            lambda: test2.last_msg['data'], 42)
        self.assertFalse(hasattr(test1, "last_msg"))

    def test_intranode_partial_unsub(self):
        node = helper.make_dsenode_new_partition('testnode')
        test1 = FakeDataSource('test1')
        test2 = FakeDataSource('test2')
        node.register_service(test1)
        node.register_service(test2)

        test1.subscribe('test2', 'p')
        test1.subscribe('test2', 'q')
        test1.unsubscribe('test2', 'q')  # unsub from q should not affect p
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        test2.publish('p', 42)
        helper.retry_check_function_return_value(
            lambda: test1.last_msg['data'], 42)
        self.assertFalse(hasattr(test2, "last_msg"))

    def test_internode_pubsub(self):
        node1 = helper.make_dsenode_new_partition('testnode1')
        test1 = FakeDataSource('test1')
        node1.register_service(test1)
        node2 = helper.make_dsenode_same_partition(node1, 'testnode2')
        test2 = FakeDataSource('test2')
        node2.register_service(test2)

        test1.subscribe('test2', 'p')
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        test2.publish('p', 42)
        helper.retry_check_function_return_value(
            lambda: test1.last_msg['data'], 42)
        self.assertFalse(hasattr(test2, "last_msg"))

    def test_internode_partial_unsub(self):
        node1 = helper.make_dsenode_new_partition('testnode1')
        node2 = helper.make_dsenode_same_partition(node1, 'testnode2')
        test1 = FakeDataSource('test1')
        test2 = FakeDataSource('test2')
        node1.register_service(test1)
        node2.register_service(test2)

        test1.subscribe('test2', 'p')
        test1.subscribe('test2', 'q')
        test1.unsubscribe('test2', 'q')  # unsub from q should not affect p
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        test2.publish('p', 42)
        helper.retry_check_function_return_value(
            lambda: test1.last_msg['data'], 42)
        self.assertFalse(hasattr(test2, "last_msg"))

    def test_multiservice_pubsub(self):
        node1 = helper.make_dsenode_new_partition('testnode1')
        test1 = FakeDataSource('test1')
        test2 = FakeDataSource('test2')
        node1.register_service(test1)
        node1.register_service(test2)
        node2 = helper.make_dsenode_same_partition(node1, 'testnode2')
        test3 = FakeDataSource('test3')
        node2.register_service(test3)

        test1.subscribe('test3', 'p')
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        test3.publish('p', 42)
        helper.retry_check_function_return_value(
            lambda: test1.last_msg['data'], 42)
        self.assertFalse(hasattr(test2, "last_msg"))
        self.assertFalse(hasattr(test3, "last_msg"))

    def test_subscribe_snapshot(self):
        node = helper.make_dsenode_new_partition('testnode')
        test1 = FakeDataSource('test1')
        test2 = FakeDataSource('test2')
        node.register_service(test1)
        node.register_service(test2)

        test1.subscribe('test2', 'fake_table')
        helper.retry_check_function_return_value(
            lambda: hasattr(test1, 'last_msg'), True)
        self.assertEqual(test1.last_msg['data'], test2.state['fake_table'])

    def test_datasource_sub(self):
        node = helper.make_dsenode_new_partition('testnode')
        nova_client = mock.MagicMock()
        with mock.patch.object(novaclient.client.Client, '__init__',
                               return_value=nova_client):
            nova = NovaDriver(
                name='nova', args=helper.datasource_openstack_args())
            test = FakeDataSource('test')
            node.register_service(nova)
            node.register_service(test)

            nova.subscribe('test', 'p')
            helper.retry_check_function_return_value(
                lambda: hasattr(nova, 'last_msg'), True)
            test.publish('p', 42)
            helper.retry_check_function_return_value(
                lambda: nova.last_msg['data'], 42)
            self.assertFalse(hasattr(test, "last_msg"))

    def test_datasource_unsub(self):
        node = helper.make_dsenode_new_partition('testnode')
        nova_client = mock.MagicMock()
        with mock.patch.object(novaclient.client.Client, '__init__',
                               return_value=nova_client):
            nova = NovaDriver(
                name='nova', args=helper.datasource_openstack_args())
            test = FakeDataSource('test')
            node.register_service(nova)
            node.register_service(test)

            nova.subscribe('test', 'p')
            helper.retry_check_function_return_value(
                lambda: hasattr(nova, 'last_msg'), True)
            test.publish('p', 42)
            helper.retry_check_function_return_value(
                lambda: nova.last_msg['data'], 42)
            self.assertFalse(hasattr(test, "last_msg"))
            nova.unsubscribe('test', 'p')
            test.publish('p', 43)
            # hard to test that the message is never delivered
            time.sleep(0.2)
            self.assertEqual(nova.last_msg['data'], 42)

    def test_datasource_pub(self):
        node = helper.make_dsenode_new_partition('testnode')
        nova_client = mock.MagicMock()
        with mock.patch.object(novaclient.client.Client, '__init__',
                               return_value=nova_client):
            nova = NovaDriver(
                name='nova', args=helper.datasource_openstack_args())
            test = FakeDataSource('test')
            node.register_service(nova)
            node.register_service(test)

            test.subscribe('nova', 'p')
            helper.retry_check_function_return_value(
                lambda: hasattr(test, 'last_msg'), True)
            nova.publish('p', 42)
            helper.retry_check_function_return_value(
                lambda: test.last_msg['data'], 42)
            self.assertFalse(hasattr(nova, "last_msg"))

    def test_datasource_poll(self):
        node = helper.make_dsenode_new_partition('testnode')
        node.always_snapshot = True  # Note(ekcs): this test expects snapshot
        pub = FakeDataSource('pub')
        sub = FakeDataSource('sub')
        node.register_service(pub)
        node.register_service(sub)

        sub.subscribe('pub', 'fake_table')
        pub.state = {'fake_table': set([(1, 2)])}
        pub.poll()
        helper.retry_check_function_return_value(
            lambda: sub.last_msg['data'], set(pub.state['fake_table']))
        self.assertFalse(hasattr(pub, "last_msg"))

    def test_policy_data(self):
        """Test policy correctly processes initial data snapshot."""
        node = helper.make_dsenode_new_partition('testnode')
        node.always_snapshot = False
        data = FakeDataSource('data')
        engine = Dse2Runtime('engine')
        node.register_service(data)
        node.register_service(engine)

        engine.create_policy('policy1')
        engine.create_policy('data')
        self.insert_rule(engine, 'p(x) :- data:fake_table(x)', 'policy1')
        data.state = {'fake_table': set([(1,), (2,)])}
        data.poll()
        helper.retry_check_db_equal(
            engine, 'p(x)', 'p(1) p(2)', target='policy1')
        self.assertFalse(hasattr(engine, "last_msg"))

    def test_policy_data_update(self):
        """Test policy correctly processes initial data snapshot and update."""
        node = helper.make_dsenode_new_partition('testnode')
        node.always_snapshot = False
        data = FakeDataSource('data')
        engine = Dse2Runtime('engine')
        node.register_service(data)
        node.register_service(engine)

        engine.create_policy('policy1')
        engine.create_policy('data')
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

    def test_policy_data_late_sub(self):
        """Test policy correctly processes data on late subscribe."""
        node = helper.make_dsenode_new_partition('testnode')
        node.always_snapshot = False
        data = FakeDataSource('data')
        engine = Dse2Runtime('engine')
        node.register_service(data)
        node.register_service(engine)

        engine.create_policy('policy1')
        engine.create_policy('data')
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

    def insert_rule(self, engine, statement, target=None):
        statement = compile.parse1(statement)
        if target is None:
            e = compile.Event(statement)
        else:
            e = compile.Event(statement, target=target)
        engine.process_policy_update([e])

    def test_unregister(self):
        node = helper.make_dsenode_new_partition('testnode')
        test1 = FakeDataSource('test1')
        node.register_service(test1)
        obj = node.invoke_service_rpc(
            'test1', 'get_status', source_id=None, params=None)
        self.assertIsNotNone(obj)
        node.unregister_service('test1')
        helper.retry_til_exception(
            congressException.NotFound,
            lambda: node.invoke_service_rpc(
                'test1', 'get_status', source_id=None, params=None))

    def _create_node_with_services(self, nodes, services, num, partition_id):
        nid = 'cbd_node%s' % num
        nodes.append(helper.make_dsenode_same_partition(partition_id, nid))
        ns = []
        for s in range(num):
            # intentionally starting different number services
            ns.append(FakeDataSource('cbd-%d_svc-%d' % (num, s)))
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

    def test_policy_table_publish(self):
        """Policy table result publish

        Test basic DSE functionality with policy engine and table result
        publish.
        """
        node = helper.make_dsenode_new_partition('testnode')
        data = FakeDataSource('data')
        policy = Dse2Runtime('policy')
        policy2 = Dse2Runtime('policy2')
        node.register_service(data)
        node.register_service(policy)
        node.register_service(policy2)

        policy.create_policy('data')
        policy.create_policy('classification')
        policy.set_schema('data', compile.Schema({'q': (1,)}))
        policy.insert('p(x):-data:q(x),gt(x,2)', target='classification')

        policy.insert('q(3)', target='data')
        # TODO(ekcs): test that no publish triggered (because no subscribers)

        policy2.create_policy('policy')
        policy2.subscribe('policy', 'classification:p')
        helper.retry_check_function_return_value(
            lambda: 'classification:p' in
            policy._published_tables_with_subscriber, True)
        self.assertEqual(list(policy.policySubData.keys()),
                         [('p', 'classification', None)])

        helper.retry_check_db_equal(
            policy2, 'policy:classification:p(x)',
            'policy:classification:p(3)')

        policy.insert('q(4)', target='data')
        helper.retry_check_db_equal(
            policy2, 'policy:classification:p(x)',
            ('policy:classification:p(3)'
             ' policy:classification:p(4)'))

        # test that no change to p means no publish triggered
        policy.insert('q(2)', target='data')
        # TODO(ekcs): test no publish triggered

        policy.delete('q(4)', target='data')
        helper.retry_check_db_equal(
            policy2, 'policy:classification:p(x)',
            'policy:classification:p(3)')

        policy2.unsubscribe('policy', 'classification:p')
        # trigger removed
        helper.retry_check_function_return_value(
            lambda: len(policy._published_tables_with_subscriber) == 0, True)
        self.assertEqual(list(policy.policySubData.keys()), [])

        policy.insert('q(4)', target='data')
        # TODO(ekcs): test that no publish triggered (because no subscribers)
