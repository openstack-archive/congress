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

import dse.deepsix
import logging
import policy.compile
import policy.runtime
import time


class DataSourceDriver(dse.deepsix.deepSix):
    def __init__(self, name, keys, inbox=None, datapath=None,
                 poll_time=None, **creds):
        if poll_time is None:
            poll_time = 10
        super(DataSourceDriver, self).__init__(name, keys, inbox, datapath)
        self.creds = creds
        # a dictionary from tablename to the SET of tuples
        self.state = dict()
        self.poll_time = poll_time

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

    def state_set_diff(self, state1, state2):
        """Given 2 tuplesets STATE1 and STATE2, return the set difference
        STATE1-STATE2.  Each tupleset is represented as a dictionary
        from tablename to set of tuples.  Return value is a tupleset,
        also represented as a dictionary from tablename to set of tuples.
        """
        diff = {}
        for tablename in state1:
            if tablename not in state2:
                # make sure to copy the set (the set-diff below does too)
                diff[tablename] = set(state1[tablename])
            else:
                diff[tablename] = state1[tablename] - state2[tablename]
        return diff

    def get_updates(self):
        """Pulls the latest data and computes deltas from previous data.
        Returns (newtuples, oldtuples).
        """
        # save current data
        oldstate = self.state
        # grab new data, making sure to reset it beforehand
        self.state = {}
        self.update_from_datasource()
        logging.debug("New state: " + str(self.state.keys()))
        logging.debug("Old state: " + str(oldstate.keys()))
        # compute deltas
        to_add = self.state_set_diff(self.state, oldstate)
        to_del = self.state_set_diff(oldstate, self.state)
        # return results
        return (to_add, to_del)

    def poll(self):
        """Function called periodically to grab new information, compute
        deltas, and publish those deltas.
        """
        logging.debug("Service {} is polling".format(self.name))
        # grab deltas
        to_add, to_del = self.get_updates()
        logging.debug("to_add: " + str(to_add))
        logging.debug("to_del: " + str(to_del))
        # grab all tables in the delta
        all_tables = set(to_add.keys()) | set(to_del.keys())
        logging.debug("all_tables: " + str(all_tables))
        # convert deltas into events and publish on the bus
        for tablename in all_tables:
            events = []
            logging.debug("tablename: " + str(tablename))
            if tablename in to_add:
                new = [policy.runtime.Event(
                    formula=policy.compile.Literal.create_from_table_tuple(
                        tablename, x),
                    insert=True)
                    for x in to_add[tablename]]
                # logging.debug("adding tuples for {}: {}".format(
                #     tablename, len(new)))
                events.extend(new)
            if tablename in to_del:
                new = [policy.runtime.Event(
                    formula=policy.compile.Literal.create_from_table_tuple(
                        tablename, x),
                    insert=False)
                    for x in to_del[tablename]]
                # logging.debug("deleting tuples for {}: {}".format(
                #     tablename, len(new)))
                events.extend(new)
            if len(events) > 0:
                self.publish(tablename, events)
        time.sleep(self.poll_time)
        logging.debug("Service {} finished polling".format(self.name))

    def d6run(self):
        if self.poll_time:  # setting to 0/False/None means auto-polling is off
            self.poll()
