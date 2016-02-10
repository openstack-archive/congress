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

import uuid

import eventlet
eventlet.monkey_patch()

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging

from congress.dse2.control_bus import DseNodeControlBus

LOG = logging.getLogger()


_dse_opts = [
    cfg.StrOpt('node_id', help='Unique ID of this DseNode on the DSE')
]
cfg.CONF.register_opts(_dse_opts, group='dse')


class DseNode(object):
    """Addressable entity participating on the DSE message bus.

    The Data Services Engine (DSE) is comprised of one or more DseNode
    instances that each may run one or more DataService instances.  All
    communication between data services uses the DseNode interface.

    Attributes:
        node_id: The unique ID of this node on the DSE.
        messaging_config: Configuration options for the message bus.  See
                          oslo.messaging for more details.
        node_rpc_endpoints: List of object instances exposing a remotely
                            invokable interface.
    """
    RPC_VERSION = '1.0'
    CONTROL_TOPIC = 'congress-control'
    SERVICE_TOPIC_PREFIX = 'congress-service-'

    @classmethod
    def node_rpc_target(cls, namespace=None, server=None, fanout=False):
        return messaging.Target(topic=cls.CONTROL_TOPIC,
                                version=cls.RPC_VERSION,
                                namespace=namespace,
                                server=server,
                                fanout=fanout)

    @classmethod
    def service_rpc_target(cls, service_id, namespace=None, server=None,
                           fanout=False):
        return messaging.Target(topic=cls.SERVICE_TOPIC_PREFIX + service_id,
                                version=cls.RPC_VERSION,
                                namespace=namespace,
                                server=server,
                                fanout=fanout)

    def __init__(self, messaging_config, node_id, node_rpc_endpoints):
        self.messaging_config = messaging_config
        self.node_id = node_id
        self.node_rpc_endpoints = node_rpc_endpoints
        self.node_rpc_endpoints.append(DseNodeEndpoints(self))
        self._running = False
        self._services = []
        self.instance = uuid.uuid4()
        self.context = self._message_context()
        self.transport = messaging.get_transport(self.messaging_config)
        self._rpctarget = self.node_rpc_target(self.node_id, self.node_id)
        self._rpcserver = messaging.get_rpc_server(
            self.transport, self._rpctarget, self.node_rpc_endpoints,
            executor='eventlet')
        self._service_rpc_servers = {}  # {service_id => (rpcserver, target)}

        self._control_bus = DseNodeControlBus(self)
        self.register_service(self._control_bus)
        # keep track of which local services subscribed to which other services
        self.subscribers = {}

    def __repr__(self):
        return self.__class__.__name__ + "<%s>" % self.node_id

    def _message_context(self):
        return {'node_id': self.node_id, 'instance': str(self.instance)}

    def register_service(self, service, index=None):
        assert not self._running
        assert service.node is None
        service.node = self
        if index is not None:
            self._services.insert(index, service)
        else:
            self._services.append(service)

        target = self.service_rpc_target(service.service_id,
                                         server=self.node_id)
        srpc = messaging.get_rpc_server(
            self.transport, target, service.rpc_endpoints(),
            executor='eventlet')
        self._service_rpc_servers[service.service_id] = (srpc, target)

    def get_services(self, hidden=False):
        if hidden:
            return self._services
        return [s for s in self._services if s.service_id[0] != '_']

    def service_object(self, name):
        """Returns the service object of the given name.  None if not found."""
        for s in self._services:
            if s.service_id == name:
                return s

    def start(self):
        LOG.debug("<%s> DSE Node '%s' starting with %s sevices...",
                  self.node_id, self.node_id, len(self._services))

        # Start Node RPC server
        self._rpcserver.start()
        LOG.debug('<%s> Node RPC Server listening on %s',
                  self.node_id, self._rpctarget)

        # Start Service RPC server(s)
        for s in self._services:
            s.start()
            sspec = self._service_rpc_servers.get(s.service_id)
            assert sspec is not None
            srpc, target = sspec
            srpc.start()
            LOG.debug('<%s> Service %s RPC Server listening on %s',
                      self.node_id, s.service_id, target)

        self._running = True

    def stop(self):
        LOG.info("Stopping DSE node '%s'" % self.node_id)
        for srpc, target in self._service_rpc_servers.values():
            srpc.stop()
        for s in self._services:
            s.stop()
        self._rpcserver.stop()
        self._running = False

    def wait(self):
        for s in self._services:
            s.wait()
        self._rpcserver.wait()

    def dse_status(self):
        """Return latest observation of DSE status."""
        return self._control_bus.dse_status()

    def invoke_node_rpc(self, node_id, method, **kwargs):
        """Invoke RPC method on a DSE Node.

        Args:
            node_id: The ID of the node on which to invoke the call.
            method: The method name to call.
            kwargs: A dict of method arguments.

        Returns:
            The result of the method invocation.

        Raises: MessagingTimeout, RemoteError, MessageDeliveryFailure
        """
        target = self.node_rpc_target(server=node_id)
        LOG.trace("<%s> Invoking RPC '%s' on %s", self.node_id, method, target)
        client = messaging.RPCClient(self.transport, target)
        return client.call(self.context, method, **kwargs)

    def broadcast_node_rpc(self, method, **kwargs):
        """Invoke RPC method on all DSE Nodes.

        Args:
            method: The method name to call.
            kwargs: A dict of method arguments.

        Returns:
            None - Methods are invoked asynchronously and results are dropped.

        Raises: RemoteError, MessageDeliveryFailure
        """
        target = self.node_rpc_target(fanout=True)
        LOG.trace("<%s> Casting RPC '%s' on %s", self.node_id, method, target)
        client = messaging.RPCClient(self.transport, target)
        client.cast(self.context, method, **kwargs)

    def invoke_service_rpc(self, service_id, method, **kwargs):
        """Invoke RPC method on a DSE Service.

        Args:
            service_id: The ID of the data service on which to invoke the call.
            method: The method name to call.
            kwargs: A dict of method arguments.

        Returns:
            The result of the method invocation.

        Raises: MessagingTimeout, RemoteError, MessageDeliveryFailure
        """
        target = self.service_rpc_target(service_id)
        LOG.trace("<%s> Invoking RPC '%s' on %s", self.node_id, method, target)
        client = messaging.RPCClient(self.transport, target)
        result = client.call(self.context, method, **kwargs)
        LOG.trace("<%s> RPC call returned: %s", self.node_id, result)
        return result

    def broadcast_service_rpc(self, service_id, method, **kwargs):
        """Invoke RPC method on all insances of service_id.

        Args:
            service_id: The ID of the data service on which to invoke the call.
            method: The method name to call.
            kwargs: A dict of method arguments.

        Returns:
            None - Methods are invoked asynchronously and results are dropped.

        Raises: RemoteError, MessageDeliveryFailure
        """
        target = self.service_rpc_target(service_id, fanout=True)
        LOG.trace("<%s> Casting RPC '%s' on %s", self.node_id, method, target)
        client = messaging.RPCClient(self.transport, target)
        client.cast(self.context, method, **kwargs)

    def publish_table(self, publisher, table, data):
        """Invoke RPC method on all insances of service_id.

        Args:
            service_id: The ID of the data service on which to invoke the call.
            method: The method name to call.
            kwargs: A dict of method arguments.

        Returns:
            None - Methods are invoked asynchronously and results are dropped.

        Raises: RemoteError, MessageDeliveryFailure
        """
        LOG.trace("<%s> Publishing from '%s' table %s: %s",
                  self.node_id, publisher, table, data)
        self.broadcast_node_rpc("handle_publish", publisher=publisher,
                                table=table, data=data)

    def table_subscribers(self, target, table):
        """List all services on this node that subscribed to target/table."""
        return [s for s in self.subscribers
                if (target in self.subscribers[s] and
                    table in self.subscribers[s][target])]

    def subscribe_table(self, service, target, table):
        """Prepare local service to receives publications from target/table."""
        # data structure: {service -> {target -> set-of-tables}
        LOG.trace("subscribing %s to %s:%s", service, target, table)
        if service not in self.subscribers:
            self.subscribers[service] = {}
        if target not in self.subscribers[service]:
            self.subscribers[service][target] = set()
        self.subscribers[service][target].add(table)
        snapshot = self.invoke_service_rpc(
            target, "get_snapshot", table=table)
        # oslo returns [] instead of set(), so handle that case directly
        return self.to_set_of_tuples(snapshot)

    def get_subscription(self, service_id):
        return self.subscribers.get(service_id, {})

    def to_set_of_tuples(self, snapshot):
        try:
            return set([tuple(x) for x in snapshot])
        except TypeError:
            return snapshot

    def unsubscribe_table(self, service, target, table):
        """Remove subscription for local service to target/table."""
        if service not in self.subscribers:
            return False
        if target not in self.subscribers[service]:
            return False
        del self.subscribers[service][target]
        if len(self.subscribers[service]) == 0:
            del self.subscribers[service]


class DseNodeEndpoints (object):
    """Collection of RPC endpoints that the DseNode exposes on the bus.

       Must be a separate class since all public methods of a given
       class are assumed to be valid RPC endpoints.
    """

    def __init__(self, dsenode):
        self.node = dsenode

    def handle_publish(self, context, publisher, table, data):
        """Function called on the node when a publication is sent.

           Forwards the publication to all of the relevant services.
        """
        for s in self.node.table_subscribers(publisher, table):
            self.node.service_object(s).receive_data(
                publisher=publisher, table=table, data=data)
