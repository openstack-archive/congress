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
import copy
import six  # thirdparty import first because needed in import of Queue/queue
import time
if six.PY2:
    import Queue as queue_package
else:
    import queue as queue_package

from oslo_config import cfg
from oslo_log import log as logging
from oslo_serialization import jsonutils as json

from congress import exception

LOG = logging.getLogger(__name__)


class DataServiceInfo(object):
    """Metadata for DataService on the DSE.

    Attributes:
    - service_id: The ID of the service.
    - node_id: The ID of the node the service is running on.
    - published_tables: List of table IDs published by this service.
    - subscribed_tables: List of table IDs this service subscribes to.
    - rpc_endpoints_info: List of RPC endpoints exposed by this service.
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

    - service_id: A unique ID of the service.
    - _published_tables_with_subscriber: A set of tables published by self
      that has subscribers
    """

    # TODO(pballand): make default methods for pub/subscribed tables
    def __init__(self, service_id):
        # Note(ekcs): temporary setting to disable use of diffs and sequencing
        #   to avoid muddying the process of a first dse2 system test.
        self.service_id = service_id
        self.node = None
        self._rpc_server = None
        self._target = None
        self._rpc_endpoints = [DataServiceEndPoints(self)]
        self._running = False
        self._published_tables_with_subscriber = set()

        # data structures for sequenced data updates for reliable pub-sub
        # msg queues for msgs to be processed
        # each queue is a priority queue prioritizing lowest seqnum
        self.msg_queues = {}  # {publisher -> {table -> msg queue}}
        # oldest queued msg receipt time
        self.oldest_queue_times = {}  # {publisher -> {table -> receipt time}}
        # last received & processed seqnum
        self.receiver_seqnums = {}  # {publisher -> {table -> seqnum}}
        # last sent seqnum
        self.sender_seqnums = {}  # {table -> seqnum}
        # last published data
        self._last_published_data = {}  # {table -> data}

        # custom functions to execute on each heartbeat
        # must be 0-ary function
        # {id -> function}
        self.heartbeat_callbacks = {}

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
            subscribed_tables=self._published_tables_with_subscriber,
            rpc_endpoints_info=None,
            )

    def start(self):
        """Start the DataService.

        This method is called by a DseNode before any RPCs are invoked.
        """
        assert self.node is not None
        if not self._running:
            self._rpc_server.start()
            self._running = True

    def stop(self):
        """Stop the DataService.

        This method is called by a DseNode when the DataService instance is
        no longer needed.  No RPCs will invoked on stopped DataServices.
        """
        assert self.node is not None
        self._rpc_server.stop()
        self._running = False

    # Note(thread-safety): blocking function
    def wait(self):
        """Wait for processing to complete.

        After a call to stop(), the DataService may have some outstanding work
        that has not yet completed.  The wait() method blocks until all
        DataService processing is complete.
        """
        assert self.node is not None
        self._rpc_server.wait()

    # Note(thread-safety): blocking function
    def rpc(self, service, action, kwargs=None, timeout=None, local=False,
            retry=None):
        return self.node.invoke_service_rpc(
            service, action, kwargs, timeout=timeout, local=local, retry=retry)

    # Will be removed once the reference of node exists in api
    # Note(thread-safety): blocking function
    def get_datasources(self, filter_secret=False):
        return self.node.get_datasources(filter_secret)

    def is_valid_service(self, service_id):
        return self.node.is_valid_service(service_id)

    # Will be removed once the reference of node exists in api
    # Note(thread-safety): blocking function
    def get_datasource(self, datasource_id):
        return self.node.get_datasource(datasource_id)

    # Will be removed once the reference of node exists in api
    # Note(thread-safety): blocking function
    def get_drivers_info(self, *args):
        return self.node.get_drivers_info(*args)

    # Will be removed once the reference of node exists in api
    # Note(thread-safety): blocking function
    def get_driver_info(self, *args):
        return self.node.get_driver_info(*args)

    # Will be removed once the reference of node exists in api
    # Note(thread-safety): blocking function
    def get_driver_schema(self, *args):
        return self.node.get_driver_schema(*args)

    # Will be removed once the reference of node exists in api
    # Note(thread-safety): blocking function
    def make_datasource_dict(self, *args, **kwargs):
        return self.node.make_datasource_dict(*args, **kwargs)

    # Note(thread-safety): blocking function
    def publish(self, table, data, use_snapshot=False):
        LOG.debug('Publishing table %s', table)
        LOG.trace('Parameters: table: %s, data: %s, use_snapshot: %s',
                  table, data, use_snapshot)
        LOG.trace('Last published data %s', self._last_published_data)
        data = set(data)  # make a copy to avoid co-reference

        def get_differential_and_set_last_published_data():
            if table in self._last_published_data:
                LOG.trace('Diff against last published data %s',
                          self._last_published_data[table])
                to_add = list(data - self._last_published_data[table])
                to_del = list(self._last_published_data[table] - data)
                self._last_published_data[table] = data
            else:
                to_add = list(data)
                to_del = []
                self._last_published_data[table] = data
            return [to_add, to_del]

        def increment_get_seqnum():
            if table not in self.sender_seqnums:
                self.sender_seqnums[table] = 0
            else:
                self.sender_seqnums[table] = self.sender_seqnums[table] + 1
            return self.sender_seqnums[table]

        if not use_snapshot:
            data = get_differential_and_set_last_published_data()
            LOG.debug('Differential data to publish %s', data)
            if len(data[0]) == 0 and len(data[1]) == 0:
                return

        seqnum = increment_get_seqnum()
        self.node.publish_table_sequenced(
            self.service_id, table, data, use_snapshot, seqnum)

    # Note(thread-safety): blocking function
    def subscribe(self, service, table):
        try:
            # Note(thread-safety): blocking call
            (seqnum, data) = self.node.subscribe_table(
                self.service_id, service, table)
            self.receive_data_sequenced(
                service, table, data, seqnum, is_snapshot=True)
        except exception.NotFound:
            LOG.info("Service '%s' unresponsive. '%s:%s' subscribed but data "
                     "not yet initialized.", service, service, table)

    def unsubscribe(self, service, table):
        # Note(thread-safety): it is important to make sure there are no
        #             blocking calls in modifying the msg_queues and related
        #             data structures.
        #             Otherwise, concurrency bugs will likely occur when the
        #             periodic task _check_resub_all interrupts and modifies
        #             the same data structures.
        self.node.unsubscribe_table(self.service_id, service, table)
        self._clear_msg_queue(service, table)
        self._clear_receiver_seqnum(service, table)

    def _clear_msg_queue(self, publisher, table):
        # Note(thread-safety): it is important to make sure there are no
        #             blocking calls in modifying the msg_queues and related
        #             data structures.
        #             Otherwise, concurrency bugs will likely occur when the
        #             periodic task _check_resub_all interrupts and modifies
        #             the same data structures.
        if publisher in self.msg_queues:
            if table in self.msg_queues[publisher]:
                del self.msg_queues[publisher][table]
                del self.oldest_queue_times[publisher][table]

    def _clear_receiver_seqnum(self, publisher, table):
        # Note(thread-safety): it is important to make sure there are no
        #             blocking calls in modifying the msg_queues and related
        #             data structures.
        #             Otherwise, concurrency bugs will likely occur when the
        #             periodic task _check_resub_all interrupts and modifies
        #             the same data structures.
        if publisher in self.receiver_seqnums:
            if table in self.receiver_seqnums[publisher]:
                del self.receiver_seqnums[publisher][table]

    def receive_data_sequenced(
            self, publisher, table, data, seqnum, is_snapshot=False,
            receipt_time=None):
        """Method called when sequenced publication data arrives."""
        # Note(thread-safety): it is important to make sure there are no
        #             blocking calls in modifying the msg_queues and related
        #             data structures.
        #             Otherwise, concurrency bugs will likely occur when the
        #             periodic task _check_resub_all interrupts and modifies
        #             the same data structures.
        # TODO(ekcs): allow opting out of sequenced processing (per table)
        def set_seqnum():
            if publisher not in self.receiver_seqnums:
                self.receiver_seqnums[publisher] = {}
            self.receiver_seqnums[publisher][table] = seqnum

        def clear_msg_queue():
            self._clear_msg_queue(publisher, table)

        def add_to_msg_queue():
            if publisher not in self.msg_queues:
                self.msg_queues[publisher] = {}
                self.oldest_queue_times[publisher] = {}
            if table not in self.msg_queues[publisher]:
                self.msg_queues[publisher][table] = \
                    queue_package.PriorityQueue()
                # set oldest queue time on first msg only, others are newer
                self.oldest_queue_times[publisher][table] = receipt_time
            self.msg_queues[publisher][table].put_nowait(
                (seqnum, is_snapshot, data, receipt_time))
            assert self.msg_queues[publisher][table].qsize() > 0

        def process_queued_msg():
            def update_oldest_time():
                '''Set oldest time to the receipt time of oldest item in queue.

                Called after removing the previous oldest item from a queue.
                If queue is empty, corresponding oldest time is set to None.
                '''
                try:
                    # remove and then add back to priority queue to get the
                    # receipt time of the next oldest message
                    # (peek not available in python standard library queues)
                    s, i, d, t = self.msg_queues[publisher][table].get_nowait()
                    self.msg_queues[publisher][table].put_nowait((s, i, d, t))
                    self.oldest_queue_times[publisher][table] = t
                except queue_package.Empty:
                    # set oldest time to None if queue empty
                    self.oldest_queue_times[publisher][table] = None

            try:
                s, i, d, t = self.msg_queues[publisher][table].get_nowait()
                update_oldest_time()
                self.receive_data_sequenced(publisher, table, d, s, i, t)
            except queue_package.Empty:
                pass
            except KeyError:
                pass

        if receipt_time is None:
            receipt_time = time.time()

        # if no seqnum process immediately
        if seqnum is None:
            self.receive_data(publisher, table, data, is_snapshot)

        # if first data update received on this table
        elif (publisher not in self.receiver_seqnums or
                table not in self.receiver_seqnums[publisher]):
            if is_snapshot:
                # set sequence number and process data
                set_seqnum()
                self.receive_data(publisher, table, data, is_snapshot)
                process_queued_msg()
            else:
                # queue
                add_to_msg_queue()

        # if re-initialization
        elif seqnum == 0:  # initial snapshot or reset
            # set sequence number and process data
            set_seqnum()
            clear_msg_queue()
            self.receive_data(publisher, table, data, is_snapshot)

        else:
            # if seqnum is old, ignore
            if seqnum <= self.receiver_seqnums[publisher][table]:
                process_queued_msg()

            # if seqnum next, process all in sequence
            elif seqnum == self.receiver_seqnums[publisher][table] + 1:
                set_seqnum()
                self.receive_data(publisher, table, data, is_snapshot)
                process_queued_msg()

            # if seqnum future, queue for future
            elif seqnum > self.receiver_seqnums[publisher][table] + 1:
                add_to_msg_queue()

    def receive_data(self, publisher, table, data, is_snapshot=True):
        """Method called when publication data arrives.

           Instances will override this method.
        """
        if is_snapshot:
            data = self.node.to_set_of_tuples(data)
        else:
            data = (self.node.to_set_of_tuples(data[0]),
                    self.node.to_set_of_tuples(data[1]))

        self.last_msg = {}
        self.last_msg['data'] = data
        self.last_msg['publisher'] = publisher
        self.last_msg['table'] = table

        if not hasattr(self, 'receive_data_history'):
            self.receive_data_history = []
        self.receive_data_history.append(self.last_msg)

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

        It returns list of services subscribed to this service data.
        """
        return self.node.get_subscribers(self.service_id)

    def get_last_published_data_with_seqnum(self, table):
        """Method that returns the current seqnum & data for given table."""
        if table not in self.sender_seqnums:
            self.sender_seqnums[table] = 0
            self._last_published_data[table] = set(self.get_snapshot(table))
            # make a copy to avoid co-reference
        return (self.sender_seqnums[table],
                list(self._last_published_data[table]))

    def get_snapshot(self, table):
        """Method that returns the current data for the given table.

           Should be overridden.
        """
        raise NotImplementedError(
            "get_snapshot is not implemented in the '%s' class." %
            self.service_id)

    def check_resub_all(self):
        '''Check all subscriptions for long missing update and resubscribe.'''
        def check_resub(publisher, table):
            if (publisher in self.oldest_queue_times and
                table in self.oldest_queue_times[publisher] and
                self.oldest_queue_times[publisher][table] is not None and
                (time.time() - self.oldest_queue_times[publisher][table]
                 > cfg.CONF.dse.time_to_resub)):
                self.unsubscribe(publisher, table)
                self.subscribe(publisher, table)
                return True
            else:
                return False

        copy_oldest_queue_times = copy.copy(self.oldest_queue_times)
        for publisher in copy_oldest_queue_times:
            copy_oldest_queue_times_publisher = copy.copy(
                copy_oldest_queue_times[publisher])
            for table in copy_oldest_queue_times_publisher:
                check_resub(publisher, table)


class DataServiceEndPoints (object):
    def __init__(self, service):
        self.service = service

    def get_snapshot(self, context, table):
        """Function called on a node when an RPC request is sent."""
        try:
            return self.service.get_snapshot(table)
        except AttributeError:
            pass

    def get_last_published_data_with_seqnum(self, context, table):
        """Function called on a node when an RPC request is sent."""
        try:
            return self.service.get_last_published_data_with_seqnum(table)
        except AttributeError:
            pass

    def ping(self, client_ctxt, **args):
        """Echo args"""
        return args
