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
        self.d6cage = args['d6cage']
        self.rootdir = args['rootdir']

    def receive_msg(self, msg):
        self.log("received msg " + str(msg))
        self.msg = msg

    def receive_data(self, msg):
        """Event handler for when a dataservice publishes data.
        That data can either be the full table (as a list of tuples)
        or a delta (a list of Events).
        """
        self.log("received data msg " + str(msg))
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
        self.log("received full data msg for {}: ".format(
            msg.header['dataindex'], runtime.iterstr(msg.body.data)))
        literals = []
        dataindex = msg.header['dataindex']
        tablename = msg.replyTo + ":" + dataindex
        for row in msg.body.data:
            assert isinstance(row, tuple), \
                "receive_data_full received non-tuple: " + str(row)
            # prefix tablename with data source
            literals.append(compile.Literal.create_from_table_tuple(
                tablename, row))
        (permitted, changes) = self.initialize([tablename], literals)
        if not permitted:
            raise runtime.CongressRuntime(
                "Update not permitted." + '\n'.join(str(x) for x in changes))
        else:
            self.log("full data msg for {} caused {} changes: {}".format(
                tablename, len(changes), runtime.iterstr(changes)))

    def receive_data_update(self, msg):
        """Handler for when dataservice publishes a delta."""
        self.log("received update data msg for {}: ".format(
            msg.header['dataindex'], runtime.iterstr(msg.body.data)))
        events = msg.body.data
        for event in events:
            assert compile.is_atom(event.formula), \
                "receive_data_update received non-atom: " + str(event.formula)
            # prefix tablename with data source
            event.formula.table = msg.replyTo + ":" + event.formula.table
        (permitted, changes) = self.update(events)
        if not permitted:
            raise runtime.CongressRuntime(
                "Update not permitted." + '\n'.join(str(x) for x in changes))
        else:
            dataindex = msg.header['dataindex']
            tablename = msg.replyTo + ":" + dataindex
            self.log("update data msg for {} caused {} changes: {}".format(
                tablename, len(changes), runtime.iterstr(changes)))
            if tablename in self.theory['classification'].tablenames():
                rows = self.theory['classification'].content([tablename])
                self.log("current table: " + runtime.iterstr(rows))

    def receive_policy_update(self, msg):
        self.log("received policy-update msg {}".format(
            runtime.iterstr(msg.body.data)))
        # update the policy and subscriptions to data tables.
        self.process_policy_update(msg.body.data)

    def process_policy_update(self, events):
        oldtables = self.tablenames()
        result = self.update(events)
        newtables = self.tablenames()
        self.update_table_subscriptions(oldtables, newtables)
        return result

    def initialize_table_subscriptions(self):
        """Once policies have all been loaded, this function subscribes to
        all the necessary tables.  See UPDATE_TABLE_SUBSCRIPTIONS as well.
        """
        self.update_table_subscriptions(set(), self.tablenames())

    def update_table_subscriptions(self, oldtables, newtables):
        """Change the subscriptions from OLDTABLES to NEWTABLES, ensuring
        to load all the appropriate services.
        """
        add = newtables - oldtables
        rem = oldtables - newtables
        self.log("Tables:: Old: {}, new: {}, add: {}, rem: {}".format(
            oldtables, newtables, add, rem))
        # subscribe to the new tables (loading services as required)
        for table in add:
            if not self.reserved_tablename(table):
                (service, tablename) = parse_tablename(table)
                if service is not None:
                    self.log("Subscribing to new (service, table): "
                             "({}, {})".format(service, tablename))
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
                self.log("Unsubscribing to new (service, table): "
                         "({}, {})".format(service, tablename))
                self.unsubscribe(service, tablename)

    # since both deepSix and Runtime define log (and differently),
    #   need to switch between them explicitly
    def log(self, *args):
        if len(args) == 1:
            deepsix.deepSix.log(self, *args)
        else:
            runtime.Runtime.log(self, *args)
