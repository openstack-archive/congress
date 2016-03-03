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

import functools
import json
import time

import eventlet
eventlet.monkey_patch()

from oslo_log import log as logging

from congress.dse2.data_service import DataService

LOG = logging.getLogger()


def drop_cast_echos(wrapped):
    @functools.wraps(wrapped)
    def wrapper(rpc_endpoint, message_context, *args, **kwargs):
        node = rpc_endpoint.dse_bus.node
        if message_context['node_id'] == node.node_id:
            LOG.trace("<%s> Ignoring my echo", node.node_id)
            return
        return wrapped(rpc_endpoint, message_context, *args, **kwargs)
    return wrapper


class HeartbeatEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return 0  # suppress sets
        # Let the base class default method handle all other cases
        return json.JSONEncoder.default(self, obj)


class _DseControlBusEndpoint(object):
    def __init__(self, dse_bus):
        self.dse_bus = dse_bus

    @drop_cast_echos
    def accept_heartbeat(self, client_ctxt, args):
        LOG.debug("<%s> Accepted heartbeat: context=%s, args='%s'",
                  self.dse_bus.node.node_id, client_ctxt, args)
        hb = json.loads(args)
        # convert dict to set
        for target in hb['subscribed_tables']:
            hb['subscribed_tables'][target] = set(
                hb['subscribed_tables'][target])
        peer_id = client_ctxt['node_id']
        new_status = {
            'node_id': peer_id,
            'instance': client_ctxt['instance'],
            'services': hb['services'],
            'subscribed_tables': hb['subscribed_tables']
        }

        old_status = self.dse_bus.peers.get(peer_id)
        if old_status:
            # TODO(pballand): validate instance, services
            LOG.trace("<%s> Refreshed peer '%s' with services %s",
                      self.dse_bus.node.node_id, peer_id,
                      [s['service_id'] for s in new_status['services']])
        else:
            LOG.info("<%s> New peer '%s' with services %s",
                     self.dse_bus.node.node_id, peer_id,
                     [s['service_id'] for s in new_status['services']])
        self.dse_bus.peers[peer_id] = new_status

        # TODO(pballand): handle time going backwards
        self.dse_bus.peers[peer_id]['last_hb_time'] = time.time()

    @drop_cast_echos
    def list_services(self, client_ctxt):
        LOG.debug("<%s> Peer '%s' requested updated service list",
                  self.dse_bus.node.node_id,  client_ctxt['node_id'])
        self.dse_bus._publish_heartbeat()


class DseNodeControlBus(DataService):
    """Maintain DSE connection for a DseNode.

    The DSE maintains a common directory of data services and their
    corresponding exported tables and RPCs.  This control bus maintains
    this view using oslo.messaging RPC primitives.
    """
    HEARTBEAT_INTERVAL = 1

    def __init__(self, node):
        self.node = node
        self.control_bus_ep = _DseControlBusEndpoint(self)
        self.peers = {}
        super(DseNodeControlBus, self).__init__('_control_bus')

    def rpc_endpoints(self):
        return [self.control_bus_ep]

    def _publish_heartbeat(self):
        args = json.dumps(
            {'services': [s.info.to_dict()
                          for s in self.node.get_services(True)],
             'subscribed_tables': self.node.subscriptions},
            cls=HeartbeatEncoder)
        self.node.broadcast_service_rpc(self.service_id, 'accept_heartbeat',
                                        args=args)

    def _heartbeat_loop(self):
        while self._running:
            self._publish_heartbeat()
            self.node._update_tables_with_subscriber()
            eventlet.sleep(self.HEARTBEAT_INTERVAL)

    def _refresh_peers(self):
        # Request immediate status refresh from peers
        LOG.debug("<%s> Requesting service list from all peers",
                  self.node.node_id)
        self.node.broadcast_service_rpc(self.service_id, 'list_services')

    def start(self):
        LOG.debug("<%s> Starting DSE control bus", self.node.node_id)
        super(DseNodeControlBus, self).start()

        # TODO(pballand): ensure I am not currently running
        #  Add an instance UUID to the node status, have timeout on nodes
        self._refresh_peers()

        # TODO(pballand): before enabling self, check if my node ID is
        # already present (no consensus service, so use timeout heuristic)
        eventlet.spawn(self._heartbeat_loop)

    def dse_status(self):
        """Return latest observation of DSE status."""
        # TODO(pballand): include node status [JOINING, JOINED]
        return {'peers': self.peers}
