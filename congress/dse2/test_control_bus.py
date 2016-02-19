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
import sys

from oslo_config import cfg
from oslo_messaging import conffixture

from congress.dse2.data_service import DataService
from congress.dse2.dse_node import DseNode
from congress.tests import base


# For manual testing, support using rabbit driver instead of fake
USE_RABBIT = False
if len(sys.argv) > 1:
    driver_flg = sys.argv[1].lower()
    if driver_flg == '--rabbit':
        USE_RABBIT = True
    elif driver_flg != '--fake':
        print("Usage: %s [--fake | --rabbit]" % sys.argv[0])
        sys.exit(1)
    sys.argv[1:] = sys.argv[2:]


class TestControlBus(base.TestCase):

    def setUp(self):
        super(TestControlBus, self).setUp()

        if USE_RABBIT:
            self.messaging_config = cfg.CONF
        else:
            mc_fixture = conffixture.ConfFixture(cfg.CONF)
            mc_fixture.conf.transport_url = 'kombu+memory://'
            self.messaging_config = mc_fixture.conf
        self.messaging_config.rpc_response_timeout = 1

    def tearDown(self):
        super(TestControlBus, self).tearDown()

    def test_control_bus_discovery(self):
        nodes = []
        services = []

        def _create_node_with_services(num):
            nid = 'cbd_node%s' % num
            nodes.append(DseNode(self.messaging_config, nid, []))
            ns = []
            for s in range(num):
                # intentionally starting different number services
                ns.append(DataService('cbd-%d_svc-%d' % (num, s)))
                nodes[-1].register_service(ns[-1])
            services.append(ns)
            return nodes[-1]

        for i in range(3):
            n = _create_node_with_services(i)
            n.start()

        eventlet.sleep(.1)  # Allow for heartbeat propagation

        def _validate_peer_view(node):
            status = node.dse_status()
            expected_peers = set([n.node_id for n in nodes
                                  if n.node_id != node.node_id])
            peers = set(status['peers'].keys())
            self.assertEqual(peers, expected_peers,
                             '%s has incorrect peers list' % node.node_id)
            for n in nodes:
                if n.node_id == node.node_id:
                    continue
                expected_services = [s.service_id for s in n._services]
                services = [s['service_id']
                            for s in status['peers'][n.node_id]['services']]
                self.assertEqual(set(expected_services), set(services),
                                 '%s has incorrect service list'
                                 % node.node_id)

        for n in nodes:
            _validate_peer_view(n)

        # Late arriving node
        n = _create_node_with_services(3)
        n.start()
        eventlet.sleep(.1)  # Allow for heartbeat propagation
        for n in nodes:
            _validate_peer_view(n)


# TODO(pballand): replace with congress unit test framework when convenient
if __name__ == '__main__':
    import unittest
    unittest.main(verbosity=2)
