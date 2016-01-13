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
    """

    # TODO(pballand): make default methods for pub/subscribed tables
    def __init__(self, service_id):
        self.service_id = service_id
        self.node = None

        self._running = False

    def rpc_endpoints(self):
        """Return list of RPC endpoint objects to be exposed for this service.

        A DataService may include zero or more RPC endpoints to be exposed
        by the DseNode.  Each endpoint object must be compatible with the
        oslo.messaging RPC Server.
        """
        return []

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
