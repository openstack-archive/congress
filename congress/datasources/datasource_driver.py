#!/usr/bin/env python
# Copyright (c) 2013 VMware, Inc. All rights reserved.
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
from congress.policy import compile
from congress.policy import runtime


class DataSourceDriver(deepsix.deepSix):
    def __init__(self, name, keys, inbox=None, datapath=None,
                 poll_time=None, **creds):
        if poll_time is None:
            poll_time = 10
        # a dictionary from tablename to the SET of tuples, both currently
        #  and in the past.
        self.prior_state = dict()
        self.state = dict()
        self.poll_time = poll_time
        self.creds = creds
        # Make sure all data structures above are set up *before* calling
        #   this because it will publish info to the bus.
        super(DataSourceDriver, self).__init__(name, keys, inbox, datapath)

    def get_all(self, type):
        raise NotImplementedError()

    def get_last_updated_time(self):
        raise NotImplementedError()

    def boolean_to_congress(self, value):
        return self.value_to_congress(value)

    def value_to_congress(self, value):
        if isinstance(value, basestring):
            return value
        if value in (True, False):
            return str(value)
        if (isinstance(value, int) or
            isinstance(value, long) or
            isinstance(value, float)):
            return value
        return str(value)

    def state_set_diff(self, state1, state2, table=None):
        """Given 2 tuplesets STATE1 and STATE2, return the set difference
        STATE1-STATE2.  Each tupleset is represented as a dictionary
        from tablename to set of tuples.  Return value is a tupleset,
        also represented as a dictionary from tablename to set of tuples.
        """
        if table is None:
            diff = {}
            for tablename in state1:
                if tablename not in state2:
                    # make sure to copy the set (the set-diff below does too)
                    diff[tablename] = set(state1[tablename])
                else:
                    diff[tablename] = state1[tablename] - state2[tablename]
            return diff
        else:
            if table not in state1:
                return set()
            if table not in state2:
                # make copy
                return set(state1[table])
            else:
                return state1[table] - state2[table]

    def poll(self):
        """Function called periodically to grab new information, compute
        deltas, and publish those deltas.
        """
        self.log("polling".format(self.name))
        self.prior_state = self.state
        self.state = {}
        self.update_from_datasource()  # sets self.state
        tablenames = set(self.state.keys()) | set(self.prior_state.keys())
        for tablename in tablenames:
            # publishing full table and using prepush_processing to send
            #   only deltas.  Useful so that if policy engine subscribes
            #   late (or dies and comes back up), DSE can automatically
            #   send the full table.
            if tablename in self.state:
                self.publish(tablename, self.state[tablename])
            else:
                self.publish(tablename, set())
        self.log("finished polling".format(self.name))

    def prepush_processor(self, data, dataindex, type=None):
        """Takes as input the DATA that the receiver needs and returns
        the payload for the message.  If this is a regular publication
        message, make the payload just the delta; otherwise, make the
        payload the entire table.
        """
        # This routine basically ignores DATA and sends a delta
        #  of the self.prior_state and self.state, for the DATAINDEX
        #  part of the state.
        self.log("prepush_processor: dataindex <{}> data: {}".format(
            str(dataindex), str(data)))
        # if not a regular publication, just return the original data
        if type != 'pub':
            self.log("prepush_processor: returned original data")
            if type == 'sub':
                # Always want to send initialization of []
                if data is None:
                    return []
                else:
                    return data
            return data
        # grab deltas
        to_add = self.state_set_diff(self.state, self.prior_state, dataindex)
        to_del = self.state_set_diff(self.prior_state, self.state, dataindex)
        self.log("to_add: " + str(to_add))
        self.log("to_del: " + str(to_del))
        # create Events
        to_add = [runtime.Event(
                  formula=compile.Literal.create_from_table_tuple(
                      dataindex, x), insert=True)
                  for x in to_add]
        to_del = [runtime.Event(
                  formula=compile.Literal.create_from_table_tuple(
                      dataindex, x), insert=False)
                  for x in to_del]
        result = to_add + to_del
        if len(result) == 0:
            # Policy engine expects an empty update to be an init msg
            #  So if delta is empty, return None, which signals
            #  the message should not be sent.
            result = None
            text = "None"
        else:
            text = runtime.iterstr(result)
        self.log("prepush_processor for <{}> returning: {}".format(self.name,
                 dataindex, text))
        return result

    def d6run(self):
        if self.poll_time:  # setting to 0/False/None means auto-polling is off
            self.poll()
