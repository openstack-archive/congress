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

import json
import six

from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_messaging import exceptions as messaging_exceptions
from oslo_messaging.rpc import dispatcher
from oslo_utils import strutils
from oslo_utils import uuidutils
import pkg_resources
import stevedore

from congress.datalog import compile as datalog_compile
from congress.datasources import constants
from congress.db import datasources as datasources_db
from congress.dse2 import control_bus
from congress import exception


LOG = logging.getLogger(__name__)


class DseNode(object):
    """Addressable entity participating on the DSE message bus.

    The Data Services Engine (DSE) is comprised of one or more DseNode
    instances that each may run one or more DataService instances.  All
    communication between data services uses the DseNode interface.

    Attributes:

    - node_id: The unique ID of this node on the DSE.
    - messaging_config: Configuration options for the message bus.  See
      oslo.messaging for more details.
    - node_rpc_endpoints: List of object instances exposing a remotely
      invokable interface.
    """
    RPC_VERSION = '1.0'
    EXCHANGE = 'congress'
    CONTROL_TOPIC = 'congress-control'
    SERVICE_TOPIC_PREFIX = 'congress-service-'

    loaded_drivers = {}

    def node_rpc_target(self, namespace=None, server=None, fanout=False):
        return messaging.Target(exchange=self.EXCHANGE,
                                topic=self._add_partition(self.CONTROL_TOPIC),
                                version=self.RPC_VERSION,
                                namespace=namespace,
                                server=server,
                                fanout=fanout)

    def service_rpc_target(self, service_id, namespace=None, server=None,
                           fanout=False):
        topic = self._add_partition(self.SERVICE_TOPIC_PREFIX + service_id)
        return messaging.Target(exchange=self.EXCHANGE,
                                topic=topic,
                                version=self.RPC_VERSION,
                                namespace=namespace,
                                server=server,
                                fanout=fanout)

    def _add_partition(self, topic, partition_id=None):
        """Create a seed-specific version of an oslo-messaging topic."""
        partition_id = partition_id or self.partition_id
        if partition_id is None:
            return topic
        return topic + "-" + str(partition_id)

    def __init__(self, messaging_config, node_id, node_rpc_endpoints,
                 partition_id=None):
        self.messaging_config = messaging_config
        self.node_id = node_id
        self.node_rpc_endpoints = node_rpc_endpoints
        # unique identifier shared by all nodes that can communicate
        self.partition_id = partition_id or cfg.CONF.dse.bus_id or "bus"
        self.node_rpc_endpoints.append(DseNodeEndpoints(self))
        self._running = False
        self._services = []
        # uuid to help recognize node_id clash
        self.instance = uuidutils.generate_uuid()
        # TODO(dse2): add detection and logging/rectifying for node_id clash?
        access_policy = dispatcher.DefaultRPCAccessPolicy
        self.context = self._message_context()
        self.transport = messaging.get_rpc_transport(
            self.messaging_config,
            allowed_remote_exmods=[exception.__name__, dispatcher.__name__,
                                   db_exc.__name__, ])
        self._rpctarget = self.node_rpc_target(self.node_id, self.node_id)
        self._rpc_server = messaging.get_rpc_server(
            self.transport, self._rpctarget, self.node_rpc_endpoints,
            executor='eventlet', access_policy=access_policy)

        # # keep track of what publisher/tables local services subscribe to
        # subscribers indexed by publisher and table:
        # {publisher_id ->
        #     {table_name -> set_of_subscriber_ids}}
        self.subscriptions = {}

        # Note(ekcs): A little strange that _control_bus starts before self?
        self._control_bus = control_bus.DseNodeControlBus(self)
        self.register_service(self._control_bus)
        self.periodic_tasks = None
        self.sync_thread = None
        self.start()

    def __del__(self):
        self.stop()
        self.wait()

    def __repr__(self):
        return self.__class__.__name__ + "<%s>" % self.node_id

    def _message_context(self):
        return {'node_id': self.node_id, 'instance': str(self.instance)}

    # Note(thread-safety): blocking function
    def register_service(self, service):
        assert service.node is None
        if self.service_object(service.service_id):
            msg = ('Service %s already exsists on the node %s'
                   % (service.service_id, self.node_id))
            raise exception.DataServiceError(msg)
        access_policy = dispatcher.DefaultRPCAccessPolicy
        service.node = self
        self._services.append(service)
        service._target = self.service_rpc_target(service.service_id,
                                                  server=self.node_id)
        service._rpc_server = messaging.get_rpc_server(
            self.transport, service._target, service.rpc_endpoints(),
            executor='eventlet', access_policy=access_policy)

        if self._running:
            service.start()

        LOG.debug('<%s> Service %s RPC Server listening on %s',
                  self.node_id, service.service_id, service._target)

    # Note(thread-safety): blocking function
    def unregister_service(self, service_id=None, uuid_=None):
        """Unregister service from DseNode matching on service_id or uuid\_

        Only one should be supplied. No-op if no matching service found.
        """
        LOG.debug("unregistering service %s on node %s", service_id,
                  self.node_id)
        service = self.service_object(service_id=service_id, uuid_=uuid_)
        if service is not None:
            self._services.remove(service)
            service.stop()
            # Note(thread-safety): blocking call
            service.wait()

    def get_services(self, hidden=False):
        """Return all local service objects."""
        if hidden:
            return self._services
        return [s for s in self._services if s.service_id[0] != '_']

    def get_global_service_names(self, hidden=False):
        """Return names of all services on all nodes."""
        services = self.get_services(hidden=hidden)
        local_services = [s.service_id for s in services]
        # Also, check services registered on other nodes
        peer_nodes = self.dse_status()['peers']
        peer_services = []
        for node in peer_nodes.values():
            peer_services.extend(
                [srv['service_id'] for srv in node['services']])
        return set(local_services + peer_services)

    def service_object(self, service_id=None, uuid_=None):
        """Return the service object requested.

        Search by service_id or uuid\_ (only one should be supplied).
        None if not found.
        """
        if service_id is not None:
            if uuid_ is not None:
                raise TypeError('service_object() cannot accept both args '
                                'service_id and uuid_')
            for s in self._services:
                if s.service_id == service_id:
                    return s
        elif uuid_ is not None:
            for s in self._services:
                if getattr(s, 'ds_id', None) == uuid_:
                    return s
        else:
            raise TypeError('service_object() requires service_id or '
                            'uuid_ argument, but neither is given.')
        return None

    def start(self):
        LOG.debug("<%s> DSE Node '%s' starting with %s sevices...",
                  self.node_id, self.node_id, len(self._services))

        # Start Node RPC server
        self._rpc_server.start()
        LOG.debug('<%s> Node RPC Server listening on %s',
                  self.node_id, self._rpctarget)

        # Start Service RPC server(s)
        for s in self._services:
            s.start()
            LOG.debug('<%s> Service %s RPC Server listening on %s',
                      self.node_id, s.service_id, s._target)

        self._running = True

    def stop(self):
        if self._running is False:
            return

        LOG.info("Stopping DSE node '%s'", self.node_id)
        for s in self._services:
            s.stop()
        self._rpc_server.stop()
        self._running = False

    # Note(thread-safety): blocking function
    def wait(self):
        for s in self._services:
            # Note(thread-safety): blocking call
            s.wait()
        # Note(thread-safety): blocking call
        self._rpc_server.wait()

    def dse_status(self):
        """Return latest observation of DSE status."""
        return self._control_bus.dse_status()

    def is_valid_service(self, service_id):
        return service_id in self.get_global_service_names(hidden=True)

    # Note(thread-safety): blocking function
    def invoke_node_rpc(self, node_id, method, kwargs=None, timeout=None):
        """Invoke RPC method on a DSE Node.

        :param: node_id: The ID of the node on which to invoke the call.
        :param: method: The method name to call.
        :param: kwargs: A dict of method arguments.

        :returns: The result of the method invocation.

        :raises: MessagingTimeout, RemoteError, MessageDeliveryFailure
        """
        if kwargs is None:
            kwargs = {}
        target = self.node_rpc_target(server=node_id)
        LOG.trace("<%s> Invoking RPC '%s' on %s", self.node_id, method, target)
        client = messaging.RPCClient(self.transport, target, timeout=timeout)
        return client.call(self.context, method, **kwargs)

    # Note(thread-safety): blocking function
    def broadcast_node_rpc(self, method, kwargs=None):
        """Invoke RPC method on all DSE Nodes.

        :param: method: The method name to call.
        :param: kwargs: A dict of method arguments.

        :returns: None
                  Methods are invoked asynchronously and results are dropped.

        :raises: RemoteError, MessageDeliveryFailure
        """
        if kwargs is None:
            kwargs = {}
        target = self.node_rpc_target(fanout=True)
        LOG.trace("<%s> Casting RPC '%s' on %s", self.node_id, method, target)
        client = messaging.RPCClient(self.transport, target)
        client.cast(self.context, method, **kwargs)

    # Note(thread-safety): blocking function
    def invoke_service_rpc(
            self, service_id, method, kwargs=None, timeout=None, local=False,
            retry=None):
        """Invoke RPC method on a DSE Service.

        :param: service_id: The ID of the data service on which to invoke the
            call.
        :param: method: The method name to call.
        :param: kwargs: A dict of method arguments.

        :returns: The result of the method invocation.

        :raises: MessagingTimeout, RemoteError, MessageDeliveryFailure,
                 NotFound
        """
        target = self.service_rpc_target(
            service_id, server=(self.node_id if local else None))
        LOG.trace("<%s> Preparing to invoking RPC '%s' on %s",
                  self.node_id, method, target)
        client = messaging.RPCClient(self.transport, target, timeout=timeout,
                                     retry=retry)
        if not self.is_valid_service(service_id):
            try:
                # First ping the destination to fail fast if unresponsive
                LOG.trace("<%s> Checking responsiveness before invoking RPC "
                          "'%s' on %s", self.node_id, method, target)
                client.prepare(timeout=cfg.CONF.dse.ping_timeout).call(
                    self.context, 'ping')
            except (messaging_exceptions.MessagingTimeout,
                    messaging_exceptions.MessageDeliveryFailure):
                msg = "service '%s' could not be found"
                raise exception.RpcTargetNotFound(msg % service_id)
        if kwargs is None:
            kwargs = {}
        try:
            LOG.trace(
                "<%s> Invoking RPC '%s' on %s", self.node_id, method, target)
            result = client.call(self.context, method, **kwargs)
        except dispatcher.NoSuchMethod:
            msg = "Method %s not supported for datasource %s"
            LOG.exception(msg, method, service_id)
            raise exception.BadRequest(msg % (method, service_id))
        except (messaging_exceptions.MessagingTimeout,
                messaging_exceptions.MessageDeliveryFailure):
            msg = "Request to service '%s' timed out"
            raise exception.Unavailable(msg % service_id)
        LOG.trace("<%s> RPC call returned: %s", self.node_id, result)
        return result

    # Note(thread-safety): blocking function
    def broadcast_service_rpc(self, service_id, method, kwargs=None):
        """Invoke RPC method on all instances of service_id.

        :param: service_id: The ID of the data service on which to invoke the
                call.
        :param: method: The method name to call.
        :param: kwargs: A dict of method arguments.

        :returns: None - Methods are invoked asynchronously and results are
                  dropped.

        :raises: RemoteError, MessageDeliveryFailure
        """
        if kwargs is None:
            kwargs = {}
        if not self.is_valid_service(service_id):
            msg = "service '%s' is not a registered service"
            raise exception.RpcTargetNotFound(msg % service_id)

        target = self.service_rpc_target(service_id, fanout=True)
        LOG.trace("<%s> Casting RPC '%s' on %s", self.node_id, method, target)
        client = messaging.RPCClient(self.transport, target)
        client.cast(self.context, method, **kwargs)

    # Note(ekcs): non-sequenced publish retained to simplify rollout of dse2
    #   to be replaced by handle_publish_sequenced
    # Note(thread-safety): blocking function
    def publish_table(self, publisher, table, data):
        """Invoke RPC method on all insances of service_id.

        :param: service_id: The ID of the data service on which to invoke the
            call.
        :param: method: The method name to call.
        :param: kwargs: A dict of method arguments.

        :returns: None
                  Methods are invoked asynchronously and results are dropped.

        :raises: RemoteError, MessageDeliveryFailure
        """
        LOG.trace("<%s> Publishing from '%s' table %s: %s",
                  self.node_id, publisher, table, data)
        self.broadcast_node_rpc(
            "handle_publish",
            {'publisher': publisher, 'table': table, 'data': data})

    # Note(thread-safety): blocking function
    def publish_table_sequenced(
            self, publisher, table, data, is_snapshot, seqnum):
        """Invoke RPC method on all insances of service_id.

        :param: service_id: The ID of the data service on which to invoke the
            call.
        :param: method: The method name to call.
        :param: kwargs: A dict of method arguments.

        :returns: None
                  Methods are invoked asynchronously and results are dropped.

        :raises: RemoteError, MessageDeliveryFailure
        """
        LOG.trace("<%s> Publishing from '%s' table %s: %s",
                  self.node_id, publisher, table, data)
        self.broadcast_node_rpc(
            "handle_publish_sequenced",
            {'publisher': publisher, 'table': table,
             'data': data, 'is_snapshot': is_snapshot, 'seqnum': seqnum})

    def table_subscribers(self, publisher, table):
        """List services on this node that subscribes to publisher/table."""
        return self.subscriptions.get(
            publisher, {}).get(table, [])

    # Note(thread-safety): blocking function
    def subscribe_table(self, subscriber, publisher, table):
        """Prepare local service to receives publications from target/table."""
        # data structure: {service -> {target -> set-of-tables}
        LOG.trace("subscribing %s to %s:%s", subscriber, publisher, table)
        if publisher not in self.subscriptions:
            self.subscriptions[publisher] = {}
        if table not in self.subscriptions[publisher]:
            self.subscriptions[publisher][table] = set()
        self.subscriptions[publisher][table].add(subscriber)

        # oslo returns [] instead of set(), so handle that case directly

        # Note(thread-safety): blocking call
        snapshot_seqnum = self.invoke_service_rpc(
            publisher, "get_last_published_data_with_seqnum",
            {'table': table})
        return snapshot_seqnum

    def get_subscription(self, service_id):
        """Return publisher/tables subscribed by service: service_id

        Return data structure:
        {publisher_id -> set of tables}
        """
        result = {}
        for publisher in self.subscriptions:
            for table in self.subscriptions[publisher]:
                if service_id in self.subscriptions[publisher][table]:
                    try:
                        result[publisher].add(table)
                    except KeyError:
                        result[publisher] = set([table])
        return result

    def get_subscribers(self, service_id):
        """List of services subscribed to this service."""

        result = set()
        tables = self.subscriptions.get(service_id, None)
        if not tables:
            # no subscribers
            return []

        for t in tables:
            result = result | self.subscriptions[service_id][t]

        return list(result)

    def to_set_of_tuples(self, snapshot):
        try:
            return set([tuple(x) for x in snapshot])
        except TypeError:
            return snapshot

    def unsubscribe_table(self, subscriber, publisher, table):
        """Remove subscription for local service to target/table."""
        if publisher not in self.subscriptions:
            return False
        if table not in self.subscriptions[publisher]:
            return False
        self.subscriptions[publisher][table].discard(subscriber)
        if len(self.subscriptions[publisher][table]) == 0:
            del self.subscriptions[publisher][table]
        if len(self.subscriptions[publisher]) == 0:
            del self.subscriptions[publisher]

    def _update_tables_with_subscriber(self):
        # not thread-safe: assumes each dseNode is single-threaded
        peers = self.dse_status()['peers']
        for s in self.get_services():
            sid = s.service_id
            # first, include subscriptions within the node, if any
            tables_with_subs = set(self.subscriptions.get(sid, {}))
            # then add subscriptions from other nodes
            for peer_id in peers:
                if sid in peers[peer_id]['subscribed_tables']:
                    tables_with_subs |= peers[
                        peer_id]['subscribed_tables'][sid]
            # call DataService hooks
            if hasattr(s, 'on_first_subs'):
                added = tables_with_subs - s._published_tables_with_subscriber
                if len(added) > 0:
                    s.on_first_subs(added)
            if hasattr(s, 'on_no_subs'):
                removed = \
                    s._published_tables_with_subscriber - tables_with_subs
                if len(removed) > 0:
                    s.on_no_subs(removed)
            s._published_tables_with_subscriber = tables_with_subs

    # Driver CRUD.  Maybe belongs in a subclass of DseNode?
    @classmethod
    def load_drivers(cls):
        """Loads all configured drivers"""
        result = {}
        mgr = stevedore.extension.ExtensionManager(
            namespace='congress.datasource.drivers',
            invoke_on_load=False)

        # Load third party drivers from config if any
        if cfg.CONF.custom_driver_endpoints:
            custom_extensions = cls.load_custom_drivers()
            if custom_extensions:
                mgr.extensions.extend(custom_extensions)

        for driver in mgr:
            if driver.name not in cfg.CONF.disabled_drivers:
                result[driver.name] = driver

        cls.loaded_drivers = result

    @classmethod
    def load_custom_drivers(cls):
        cdist = pkg_resources.get_distribution('openstack-congress')
        ext_list = []
        for driver in cfg.CONF.custom_driver_endpoints:
            try:
                ep = pkg_resources.EntryPoint.parse(driver, dist=cdist)
                ep_plugin = ep.load()
                ext = stevedore.extension.Extension(
                    name=ep.name, entry_point=ep, plugin=ep_plugin, obj=None)
                ext_list.append(ext)
            except Exception:
                LOG.exception("Failed to load driver endpoint %s", driver)
        return ext_list

    @classmethod
    def get_driver_info(cls, driver_name):
        driver = cls.loaded_drivers.get(driver_name)
        if not driver:
            raise exception.DriverNotFound(id=driver_name)
        return driver.plugin.get_datasource_info()

    @classmethod
    def get_drivers_info(cls):
        drivers = cls.loaded_drivers.values()
        return [d.plugin.get_datasource_info() for d in drivers]

    @classmethod
    def get_driver_schema(cls, drivername):
        driver = cls.loaded_drivers.get(drivername)
        return driver.plugin.get_schema()

    # Datasource CRUD.  Maybe belongs in a subclass of DseNode?
    # Note(thread-safety): blocking function
    def get_datasource(cls, id_):
        """Return the created datasource."""
        # Note(thread-safety): blocking call
        result = datasources_db.get_datasource(id_)
        if not result:
            raise exception.DatasourceNotFound(id=id_)
        return cls.make_datasource_dict(result)

    # Note(thread-safety): blocking function
    def get_datasources(self, filter_secret=False):
        """Return the created datasources as recorded in the DB.

        This returns what datasources the database contains, not the
        datasources that this server instance is running.
        """
        results = []
        for datasource in datasources_db.get_datasources():
            result = self.make_datasource_dict(datasource)
            if filter_secret:
                # driver_info knows which fields should be secret
                driver_info = self.get_driver_info(result['driver'])
                try:
                    for hide_field in driver_info['secret']:
                        result['config'][hide_field] = "<hidden>"
                except KeyError:
                    pass
            results.append(result)
        return results

    def delete_missing_driver_datasources(self):
        removed = 0
        for datasource in datasources_db.get_datasources():
            try:
                self.get_driver_info(datasource.driver)
            except exception.DriverNotFound:
                datasources_db.delete_datasource_with_data(datasource.id)
                removed = removed+1
                LOG.debug("Datasource driver '%s' not found, deleting the "
                          "datasource '%s' from DB ", datasource.driver,
                          datasource.name)

        LOG.info("Datsource cleanup completed, removed %d datasources",
                 removed)

    def make_datasource_dict(self, req, fields=None):
        result = {'id': req.get('id') or uuidutils.generate_uuid(),
                  'name': req.get('name'),
                  'driver': req.get('driver'),
                  'description': req.get('description'),
                  'type': None,
                  'enabled': req.get('enabled', True)}
        # NOTE(arosen): we store the config as a string in the db so
        # here we serialize it back when returning it.
        if isinstance(req.get('config'), six.string_types):
            result['config'] = json.loads(req['config'])
        else:
            result['config'] = req.get('config')

        return self._fields(result, fields)

    def _fields(self, resource, fields):
        if fields:
            return dict(((key, item) for key, item in resource.items()
                         if key in fields))
        return resource

    def validate_create_datasource(self, req):
        name = req['name']
        if not datalog_compile.string_is_servicename(name):
            raise exception.InvalidDatasourceName(value=name)
        driver = req['driver']
        config = req['config'] or {}

        try:
            loaded_driver = self.get_driver_info(driver)
        except exception.DriverNotFound:
            raise exception.InvalidDriver(driver=req)

        specified_options = set(config.keys())
        valid_options = set(loaded_driver['config'].keys())
        # Check that all the specified options passed in are
        # valid configuration options that the driver exposes.
        invalid_options = specified_options - valid_options
        if invalid_options:
            raise exception.InvalidDriverOption(
                invalid_options=invalid_options)

        # check that all the required options are passed in
        required_options = set(
            [k for k, v in loaded_driver['config'].items()
             if v == constants.REQUIRED])
        missing_options = required_options - specified_options

        if ('project_name' in missing_options and 'tenant_name' in
                specified_options):
            LOG.warning("tenant_name is deprecated, use project_name instead")
            missing_options.remove('project_name')

        if missing_options:
            missing_options = ', '.join(missing_options)
            raise exception.MissingRequiredConfigOptions(
                missing_options=missing_options)
        return loaded_driver

    # Note (thread-safety): blocking function
    def create_datasource_service(self, datasource):
        """Create a new DataService on this node.

        :param: datasource: datsource object.
        """
        # get the driver info for the datasource
        ds_dict = self.make_datasource_dict(datasource)
        if not ds_dict['enabled']:
            LOG.info("datasource %s not enabled, skip loading",
                     ds_dict['name'])
            return
        driver = self.loaded_drivers.get(ds_dict['driver'])
        if not driver:
            raise exception.DriverNotFound(id=ds_dict['driver'])

        if ds_dict['config'] is None:
            args = {'ds_id': ds_dict['id']}
        else:
            args = dict(ds_dict['config'], ds_id=ds_dict['id'])
        kwargs = {'name': ds_dict['name'], 'args': args}
        LOG.info("creating service %s with class %s and args %s",
                 ds_dict['name'], driver.plugin,
                 strutils.mask_password(kwargs, "****"))
        try:
            service = driver.plugin(**kwargs)
        except Exception:
            msg = ("Error loading instance of module '%s'")
            LOG.exception(msg, driver.plugin)
            raise exception.DataServiceError(msg % driver.plugin)
        return service


class DseNodeEndpoints (object):
    """Collection of RPC endpoints that the DseNode exposes on the bus.

       Must be a separate class since all public methods of a given
       class are assumed to be valid RPC endpoints.
    """

    def __init__(self, dsenode):
        self.node = dsenode

    # Note(ekcs): non-sequenced publish retained to simplify rollout of dse2
    #   to be replaced by handle_publish_sequenced
    def handle_publish(self, context, publisher, table, data):
        """Function called on the node when a publication is sent.

           Forwards the publication to all of the relevant services.
        """
        for s in self.node.table_subscribers(publisher, table):
            self.node.service_object(s).receive_data(
                publisher=publisher, table=table, data=data, is_snapshot=True)

    def handle_publish_sequenced(
            self, context, publisher, table, data, is_snapshot, seqnum):
        """Function called on the node when a publication is sent.

           Forwards the publication to all of the relevant services.
        """
        for s in self.node.table_subscribers(publisher, table):
            self.node.service_object(s).receive_data_sequenced(
                publisher=publisher, table=table, data=data, seqnum=seqnum,
                is_snapshot=is_snapshot)
