# Copyright (c) 2014 VMware, Inc. All rights reserved.
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
from congress.dse import deepsix
from congress.openstack.common import log as logging
from congress.policy import compile
from congress.policy import runtime


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return DseRuntime(name, keys, inbox, datapath, args)


def parse_tablename(tablename):
    """Given tablename returns (service, name)."""
    pieces = tablename.split(':')
    if len(pieces) == 1:
        return (None, pieces[0])
    else:
        return (pieces[0], ':'.join(pieces[1:]))


class DseRuntime (runtime.Runtime, deepsix.deepSix):
    def __init__(self, name, keys, inbox, datapath, args):
        runtime.Runtime.__init__(self)
        deepsix.deepSix.__init__(self, name, keys, inbox=inbox,
                                 dataPath=datapath)
        self.msg = None
        self.last_policy_change = None
        self.d6cage = args['d6cage']
        self.rootdir = args['rootdir']

    def extend_schema(self, service_name, schema):
        newschema = {}
        for key, value in schema:
            newschema[service_name + ":" + key] = value
        super(DseRuntime, self).extend_schema(self, newschema)

    def receive_msg(self, msg):
        self.log("received msg %s", msg)
        self.msg = msg

    def receive_data(self, msg):
        """Event handler for when a dataservice publishes data.

        That data can either be the full table (as a list of tuples)
        or a delta (a list of Events).
        """
        self.log("received data msg %s", msg)
        # if empty data, assume it is an init msg, since noop otherwise
        if len(msg.body.data) == 0:
            self.receive_data_full(msg)
        else:
            # grab an item from any iterable
            dataelem = iter(msg.body.data).next()
            if isinstance(dataelem, runtime.Event):
                self.receive_data_update(msg)
            else:
                self.receive_data_full(msg)

    def receive_data_full(self, msg):
        """Handler for when dataservice publishes full table."""
        self.log("received full data msg for %s: %s",
                 msg.header['dataindex'], runtime.iterstr(msg.body.data))
        tablename = msg.header['dataindex']
        service = msg.replyTo

        # Use a generator to avoid instantiating all these Facts at once.
        literals = (compile.Fact(tablename, row) for row in msg.body.data)

        self.initialize_tables([tablename], literals, target=service)
        self.log("full data msg for %s", tablename)

    def receive_data_update(self, msg):
        """Handler for when dataservice publishes a delta."""
        self.log("received update data msg for %s: %s",
                 msg.header['dataindex'], runtime.iterstr(msg.body.data))
        events = msg.body.data
        for event in events:
            assert compile.is_atom(event.formula), (
                "receive_data_update received non-atom: " +
                str(event.formula))
            # prefix tablename with data source
            event.target = msg.replyTo
        (permitted, changes) = self.update(events)
        if not permitted:
            raise runtime.CongressRuntime(
                "Update not permitted." + '\n'.join(str(x) for x in changes))
        else:
            tablename = msg.header['dataindex']
            service = msg.replyTo
            self.log("update data msg for %s from %s caused %d "
                     "changes: %s", tablename, service, len(changes),
                     runtime.iterstr(changes))
            if tablename in self.theory[service].tablenames():
                rows = self.theory[service].content([tablename])
                self.log("current table: %s", runtime.iterstr(rows))

    def receive_policy_update(self, msg):
        self.log("received policy-update msg %s",
                 runtime.iterstr(msg.body.data))
        # update the policy and subscriptions to data tables.
        self.last_policy_change = self.process_policy_update(msg.body.data)

    def process_policy_update(self, events):
        self.log("process_policy_update %s" % events)
        oldtables = self.tablenames()
        result = self.update(events)
        newtables = self.tablenames()
        self.update_table_subscriptions(oldtables, newtables)
        return result

    def initialize_table_subscriptions(self):
        """Initialize table subscription.

        Once policies have all been loaded, this function subscribes to
        all the necessary tables.  See UPDATE_TABLE_SUBSCRIPTIONS as well.
        """
        self.update_table_subscriptions(set(), self.tablenames())

    def update_table_subscriptions(self, oldtables, newtables):
        """Update table subscription.

        Change the subscriptions from OLDTABLES to NEWTABLES, ensuring
        to load all the appropriate services.
        """
        add = newtables - oldtables
        rem = oldtables - newtables
        self.log("Tables:: Old: %s, new: %s, add: %s, rem: %s",
                 oldtables, newtables, add, rem)
        # subscribe to the new tables (loading services as required)
        for table in add:
            if not self.reserved_tablename(table):
                (service, tablename) = parse_tablename(table)
                if service is not None:
                    self.log("Subscribing to new (service, table): (%s, %s)",
                             service, tablename)
                    self.subscribe(service, tablename,
                                   callback=self.receive_data)

        # TODO(thinrichs): figure out scheme for removing old services once
        #     their tables are no longer needed.  Leaving them around is
        #     basically a memory leak, but deleting them too soon
        #     might mean fat-fingering policy yields large performance hits
        #     (e.g. if we need to re-sync entirely).  Probably create a queue
        #     of these tables, keep them up to date, and gc them after
        #     some amount of time.
        # unsubscribe from the old tables
        for table in rem:
            (service, tablename) = parse_tablename(table)
            if service is not None:
                self.log("Unsubscribing to new (service, table): (%s, %s)",
                         service, tablename)
                self.unsubscribe(service, tablename)
