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

from oslo_log import log as logging
from oslo_serialization import jsonutils as json

LOG = logging.getLogger(__name__)


class DataServiceInfo(object):
    """Metadata for DataService on the DSE.

    Attributes:
        service_id: The ID of the service.
        node_id: The ID of the node the service is running on.
        published_tables: List of table IDs published by this service.
        subscribed_tables: List of table IDs this service subscribes to.
        rpc_endpoints_info: List of RPC endpoints exposed by this service.
    """
    MARSHALL_ATTRS = set(['service_id', 'node_id', 'published_tables',
                          'subscribed_tables', 'rpc_endpoints_info'])

    def __init__(self, service_id=None, node_id=None, published_tables=None,
                 subscribed_tables=None, rpc_endpoints_info=None):
        self.service_id = service_id
        self.node_id = node_id
        self.published_tables = published_tables or []
        self.subscribed_tables = subscribed_tables or []
        self.rpc_endpoints_info = rpc_endpoints_info or []

    def __str__(self):
        return self.__class__.__name__ + "<%s>" % self.service_id

    def __repr__(self):
        return self.__class__.__name__ + "(%s)" % dict.__repr__(vars(self))

    @classmethod
    def from_json(cls, json_string):
        return json.loads(json_string, object_hook=cls.from_dict)

    @classmethod
    def from_dict(cls, raw_dict):
        provided_keys = set(raw_dict.keys())
        if provided_keys != cls.MARSHALL_ATTRS:
            missing = cls.MARSHALL_ATTRS - provided_keys
            malformed = provided_keys - cls.MARSHALL_ATTRS
            msg = "Cannot construct %s from input:" % cls.__name__
            if missing:
                msg += " Missing keys: %s" % list(missing)
            if malformed:
                msg += " Malformed keys: %s" % list(malformed)
            raise KeyError(msg)
        ret = DataServiceInfo()
        for n in cls.MARSHALL_ATTRS:
            setattr(ret, n, raw_dict[n])
        return ret

    def to_dict(self):
        return dict([(k, getattr(self, k)) for k in self.MARSHALL_ATTRS])

    def to_json(self):
        return json.dumps(self.to_dict())


class DataService(object):
    """A unit of data and business logic that interfaces with the DSE.

    A DataService may publish tables, subscribe to tables, and/or expose
    RPCs on the DSE.  DataService instances are bound to a DseNode which is
    used for all inter-service communication.

    Attributes:
        service_id: A unique ID of the service.
        _published_tables_with_subscriber: A set of tables published by self
            that has subscribers
    """

    # TODO(pballand): make default methods for pub/subscribed tables
    def __init__(self, service_id):
        self.service_id = service_id
        self.node = None
        self._rpc_endpoints = [DataServiceEndPoints(self)]
        self._running = False
        self._published_tables_with_subscriber = set()

    def add_rpc_endpoint(self, endpt):
        self._rpc_endpoints.append(endpt)

    def rpc_endpoints(self):
        """Return list of RPC endpoint objects to be exposed for this service.

        A DataService may include zero or more RPC endpoints to be exposed
        by the DseNode.  Each endpoint object must be compatible with the
        oslo.messaging RPC Server.
        """
        return self._rpc_endpoints

    @property
    def status(self):
        return "OK"

    @property
    def info(self):
        # TODO(pballand): populate rpc_endpoints_info from rpc_endpoints
        return DataServiceInfo(
            service_id=self.service_id,
            node_id=self.node.node_id if self.node else None,
            published_tables=None,
            subscribed_tables=None,
            rpc_endpoints_info=None,
            )

    def start(self):
        """Start the DataService.

        This method is called by a DseNode before any RPCs are invoked.
        """
        assert self.node is not None
        self._running = True

    def stop(self):
        """Stop the DataService.

        This method is called by a DseNode when the DataService instance is
        no longer needed.  No RPCs will invoked on stopped DataServices.
        """
        assert self.node is not None
        self._running = False

    def wait(self):
        """Wait for processing to complete.

        After a call to stop(), the DataService may have some outstanding work
        that has not yet completed.  The wait() method blocks until all
        DataService processing is complete.
        """
        assert self.node is not None
        pass

    def rpc(self, service, action, kwargs=None):
        if kwargs is None:
            kwargs = {}
        return self.node.invoke_service_rpc(service, action, **kwargs)

    # Will be removed once the reference of node exists in api
    def get_datasources(self, filter_secret=False):
        return self.node.get_datasources(filter_secret)

    # Will be removed once the reference of node exists in api
    def get_datasource(self, datasource_id):
        return self.node.get_datasource(datasource_id)

    # Will be removed once the reference of node exists in api
    def add_datasource(self, **kwargs):
        return self.node.add_datasource(**kwargs)

    # Will be removed once the reference of node exists in api
    def delete_datasource(self, datasource):
        return self.node.delete_datasource(datasource)

    def publish(self, table, data):
        self.node.publish_table(self.service_id, table, data)

    def subscribe(self, service, table):
        data = self.node.subscribe_table(self.service_id, service, table)
        self.receive_data(service, table, data)

    def unsubscribe(self, service, table):
        self.node.unsubscribe_table(self.service_id, service, table)

    def receive_data(self, publisher, table, data):
        """Method called when publication data arrives.

           Instances will override this method.
        """
        data = self.node.to_set_of_tuples(data)
        self.last_msg = {}
        self.last_msg['data'] = data
        self.last_msg['publisher'] = publisher
        self.last_msg['table'] = table

    def subscription_list(self):
        """Method that returns subscription list.

        It returns list of tuple that represents the service's subscription.
        The tuple forms following format:
        (service_id, table_name).
        """
        result = []
        subscription = self.node.get_subscription(self.service_id)
        for target, tables in subscription.items():
            result.extend([(target, t) for t in tables])
        return result

    def subscriber_list(self):
        """Method that returns subscribers list.

        This feature is duplicated in the distributed architecture. So the
        method is defined only for backward compatibility.
        """
        LOG.info('subscriber_list is duplicated in the new architecture.')
        return []

    def get_snapshot(self, table):
        """Method that returns the current data for the given table.

           Should be overridden.
        """
        raise NotImplementedError(
            "get_snapshot is not implemented in the '%s' class." %
            self.service_id)


class DataServiceEndPoints (object):
    def __init__(self, service):
        self.service = service

    def get_snapshot(self, context, table):
        """Function called on a node when an RPC request is sent."""
        try:
            return self.service.get_snapshot(table)
        except AttributeError:
            pass
