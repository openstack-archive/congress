# Copyright (c) 2016 VMware, Inc. All rights reserved.
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

import eventlet
import mock

from oslo_config import cfg
from oslo_messaging import conffixture

from congress import exception

from congress.dse2 import data_service
from congress.dse2 import datasource_manager as ds_manager
from congress.dse2 import dse_node
from congress.tests.api import base as api_base
from congress.tests import base
from congress.tests import helper


# Leave this in place for manual testing.
# For manual testing, support using rabbit driver instead of fake
USE_RABBIT = False
# if len(sys.argv) > 1:
#     driver_flg = sys.argv[1].lower()
#     if driver_flg == '--rabbit':
#         USE_RABBIT = True
#     elif driver_flg != '--fake':
#         print("Usage: %s [--fake | --rabbit]" % sys.argv[0])
#         sys.exit(1)
#     sys.argv[1:] = sys.argv[2:]


class _PingRpcEndpoint(object):
    def __init__(self, node_id):
        self.node_id = node_id
        self.ping_receive_count = 0
        self.ping_received_from = []

    def ping(self, client_ctxt, **args):
        return args

    def ping_test(self, client_ctxt, **args):
        self.ping_receive_count += 1
        self.ping_received_from.append(client_ctxt)
        return args


class _PingRpcService(data_service.DataService):
    def __init__(self, service_id, node_id):
        self.endpoints = [_PingRpcEndpoint(node_id)]
        super(_PingRpcService, self).__init__(service_id)

    def rpc_endpoints(self):
        return self.endpoints


class TestDseNode(base.SqlTestCase):

    def setUp(self):
        super(TestDseNode, self).setUp()

        if USE_RABBIT:
            self.messaging_config = cfg.CONF
        else:
            mc_fixture = conffixture.ConfFixture(cfg.CONF)
            mc_fixture.conf.transport_url = 'kombu+memory://'
            self.messaging_config = mc_fixture.conf
        self.messaging_config.rpc_response_timeout = 1

    def test_start_stop(self):
        # create node and register services
        node = helper.make_dsenode_new_partition('test_node',
                                                 self.messaging_config, [])
        services = []
        for i in range(2):
            service = data_service.DataService('test-service-%s' % i)
            node.register_service(service)
            services.append(service)
        for s in node.get_services(True):
            self.assertTrue(s._running,
                            "Service '%s' started" % str(s))
        self.assertEqual(set(services), set(node.get_services()),
                         "All services accounted for on node.")
        self.assertTrue(node._rpc_server._started,
                        "RPC server is started")
        self.assertTrue(node._control_bus._running,
                        "Control Bus is started")

        # stop node
        node.stop()
        node.wait()
        self.assertFalse(node._running,
                         "Node is stopped after node start")
        for idx, s in enumerate(node.get_services(True)):
            self.assertFalse(s._running,
                             "Service '%s' stopped after node stop" % str(s))
        # TODO(pballand): fix bug
        # self.assertFalse(node._rpc_server._started,
        #                  "RPC server is stopped after node stop")
        self.assertFalse(node._control_bus._running,
                         "Control Bus is stopped after node stop")

        # restart node
        node.start()
        for s in node.get_services(True):
            self.assertTrue(s._running,
                            "Service '%s' started" % str(s))
        self.assertEqual(set(services), set(node.get_services()),
                         "All services accounted for on node.")
        self.assertTrue(node._rpc_server._started,
                        "RPC server is started")
        self.assertTrue(node._control_bus._running,
                        "Control Bus is started")

    def test_context(self):
        # Context must not only rely on node_id to prohibit multiple instances
        # of a node_id on the DSE
        part = helper.get_new_partition()
        n1 = helper.make_dsenode_same_partition(part, 'node_id',
                                                self.messaging_config, [])
        n2 = helper.make_dsenode_same_partition(part, 'node_id',
                                                self.messaging_config, [])
        self.assertEqual(n1._message_context, n1._message_context,
                         "Comparison of context from the same node is equal")
        self.assertNotEqual(n1._message_context, n2._message_context,
                            "Comparison of context from the different nodes "
                            "is not equal")

    # FIXME(dsetest): resolve instability and re-enable
    def _test_node_rpc(self):
        """Validate calling RPCs on DseNode"""
        part = helper.get_new_partition()
        nodes = []
        endpoints = []
        for i in range(3):
            nid = 'rpcnode%s' % i
            endpoints.append(_PingRpcEndpoint(nid))
            nodes.append(
                helper.make_dsenode_same_partition(
                    part, nid, self.messaging_config, [endpoints[-1]]))

        # Send from each node to each other node
        for i, source in enumerate(nodes):
            # intentionally including self in RPC target
            for j, target in enumerate(nodes):
                scount = endpoints[j].ping_receive_count
                args = {'arg1': 1, 'arg2': 'a'}
                ret = source.invoke_node_rpc(target.node_id, 'ping_test', args)
                self.assertEqual(ret, args, "Ping echoed arguments")
                ecount = endpoints[j].ping_receive_count
                self.assertEqual(ecount - scount, 1,
                                 "Node %s received ping (%s was sending)"
                                 % (nodes[j].node_id, nodes[i].node_id))
                self.assertEqual(
                    endpoints[j].ping_received_from[-1]['node_id'],
                    nodes[i].node_id,
                    "Last ping received on %s was from %s" % (
                        nodes[j].node_id, nodes[i].node_id))

    # FIXME(dsetest): resolve instability and re-enable
    def _test_node_broadcast_rpc(self):
        """Validate calling RPCs on DseNode"""
        part = helper.get_new_partition()
        nodes = []
        endpoints = []
        for i in range(3):
            nid = 'rpcnode%s' % i
            endpoints.append(_PingRpcEndpoint(nid))
            nodes.append(
                helper.make_dsenode_same_partition(
                    part, nid, self.messaging_config, [endpoints[-1]]))

        # Send from each node to all other nodes
        for i, source in enumerate(nodes):
            scounts = []
            for j, target in enumerate(nodes):
                scounts.append(endpoints[j].ping_receive_count)
            source.broadcast_node_rpc('ping_test', {'arg1': 1, 'arg2': 'a'})
            eventlet.sleep(0.5)  # wait for async delivery
            for j, target in enumerate(nodes):
                ecount = endpoints[j].ping_receive_count
                self.assertEqual(ecount - scounts[j], 1,
                                 "Node %s received ping (%s was sending)"
                                 % (nodes[j].node_id, source.node_id))
                self.assertEqual(
                    endpoints[j].ping_received_from[-1]['node_id'],
                    source.node_id,
                    "Last ping received on %s was from %s" % (
                        nodes[j].node_id, source.node_id))

    # FIXME(dsetest): resolve instability and re-enable
    def _test_service_rpc(self):
        part = helper.get_new_partition()
        nodes = []
        services = []
        for i in range(3):
            nid = 'svc_rpc_node%s' % i
            node = helper.make_dsenode_same_partition(
                part, nid, self.messaging_config)
            service = _PingRpcService('srpc_node_svc%s' % i, nid)
            node.register_service(service)
            nodes.append(node)
            services.append(service)

        # Send from each node to each other node
        for i, source in enumerate(nodes):
            # intentionally including self in RPC target
            for j, service in enumerate(services):
                ep = nodes[j]._services[-1].endpoints[0]
                scount = ep.ping_receive_count
                args = {'arg1': 1, 'arg2': 'a'}
                ret = source.invoke_service_rpc(
                    service.service_id, 'ping_test', args)
                self.assertEqual(ret, args, "Ping echoed arguments")
                ecount = ep.ping_receive_count
                self.assertEqual(ecount - scount, 1,
                                 "Node %s received ping (%s was sending)"
                                 % (nodes[j].node_id, nodes[i].node_id))
                self.assertEqual(
                    ep.ping_received_from[-1]['node_id'],
                    nodes[i].node_id,
                    "Last ping received on %s was from %s" % (
                        nodes[j].node_id, nodes[i].node_id))

    # FIXME(dsetest): resolve instability and re-enable
    def _test_broadcast_service_rpc(self):
        part = helper.get_new_partition()
        nodes = []
        services = []
        for i in range(3):
            nid = 'svc_rpc_node%s' % i
            node = helper.make_dsenode_same_partition(
                part, nid, self.messaging_config)
            service = _PingRpcService('tbsr_svc', nid)
            node.register_service(service)
            nodes.append(node)
            services.append(service)

        # Send from each node to all services
        for i, source in enumerate(nodes):
            scounts = []
            for j, target in enumerate(nodes):
                ep = nodes[j]._services[-1].endpoints[0]
                scounts.append(ep.ping_receive_count)
            source.broadcast_service_rpc(
                'tbsr_svc', 'ping_test', {'arg1': 1, 'arg2': 'a'})
            eventlet.sleep(0.5)  # wait for async delivery
            for j, target in enumerate(nodes):
                ep = nodes[j]._services[-1].endpoints[0]
                ecount = ep.ping_receive_count
                self.assertEqual(ecount - scounts[j], 1,
                                 "Node %s received ping (%s was sending)"
                                 % (nodes[j].node_id, source.node_id))
                self.assertEqual(
                    ep.ping_received_from[-1]['node_id'],
                    source.node_id,
                    "Last ping received on %s was from %s" % (
                        nodes[j].node_id, source.node_id))

    def test_get_global_service_names(self):
        node = helper.make_dsenode_new_partition('test_node',
                                                 self.messaging_config, [])
        test1 = _PingRpcService('test1', 'test1')
        test2 = _PingRpcService('test2', 'test2')
        node.register_service(test1)
        node.register_service(test2)
        actual = set(node.get_global_service_names())
        self.assertEqual(actual, set(['test1', 'test2']))

    def test_unregister_service(self):
        node = helper.make_dsenode_new_partition('test_node',
                                                 self.messaging_config, [])
        test1 = _PingRpcService('test1', 'test1')
        uuid1 = '1c5d6da0-64ae-11e6-8852-000c29242e6f'
        test1.ds_id = uuid1
        test2 = _PingRpcService('test2', 'test2')
        uuid2 = 'd36d3781-e9e4-4278-bbf4-9f5fef7c5101'
        test2.ds_id = uuid2
        node.register_service(test1)
        node.register_service(test2)
        actual = set(node.get_global_service_names())
        self.assertEqual(actual, set(['test1', 'test2']))

        # unregister by service_id
        node.unregister_service(service_id='test1')
        actual = set(node.get_global_service_names())
        self.assertEqual(actual, set(['test2']))

        # unregister by uuid
        node.unregister_service(uuid_=uuid2)
        actual = set(node.get_global_service_names())
        self.assertEqual(actual, set())

    def _get_datasource_request(self):
        # leave ID out--generated during creation
        return {'name': 'datasource1',
                'driver': 'fake_datasource',
                'description': 'hello world!',
                'enabled': True,
                'type': None,
                'config': {'auth_url': 'foo',
                           'username': 'armax',
                           'password': '<hidden>',
                           'tenant_name': 'armax'}}

    @mock.patch.object(dse_node.DseNode, 'validate_create_datasource')
    @mock.patch.object(dse_node.DseNode, 'get_driver_info')
    def test_missing_driver_datasources(self, mock_driver_info, mock_validate):
        services = api_base.setup_config(api=False, policy=False)
        node = services['node']
        ds_manager = services['ds_manager']
        ds = self._get_datasource_request()
        mock_driver_info.return_value = {'secret': []}
        ds_manager.add_datasource(ds)
        mock_driver_info.side_effect = [exception.DriverNotFound]
        node.delete_missing_driver_datasources()
        self.assertRaises(exception.DatasourceNotFound,
                          node.get_datasource, 'datasource1')


class TestDSManagerService(base.TestCase):

    def setUp(self):
        super(TestDSManagerService, self).setUp()

    def test_ds_manager_endpoints_add_ds(self):
        ds_manager_service = ds_manager.DSManagerService('test_mgr')
        node_mock = mock.MagicMock()
        ds_manager_service.add_datasource = mock.MagicMock()
        ds_manager_service.add_datasource.return_value = 'add_datasource'
        ds_manager_service.node = node_mock
        endpoints = ds_manager.DSManagerEndpoints(ds_manager_service)

        expect_ret = 'add_datasource'
        self.assertEqual(expect_ret, endpoints.add_datasource('context', {}))

        ds_manager_service.add_datasource.assert_called_with({})

    def test_ds_manager_endpoints_delete_ds(self):
        ds_manager_service = ds_manager.DSManagerService('test_mgr')
        node_mock = mock.MagicMock()
        ds_manager_service.delete_datasource = mock.MagicMock()
        ds_manager_service.delete_datasource.return_value = 'delete_datasource'
        ds_manager_service.node = node_mock
        endpoints = ds_manager.DSManagerEndpoints(ds_manager_service)

        expect_ret = 'delete_datasource'
        self.assertEqual(expect_ret,
                         endpoints.delete_datasource('context', 'ds-id'))

        ds_manager_service.delete_datasource.assert_called_with('ds-id')


# Leave this to make manual testing with RabbitMQ easy
# if __name__ == '__main__':
#     import unittest
#     unittest.main(verbosity=2)
