#! /usr/bin/python
#
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
import dse.deepsix as deepsix
import logging
import policy.compile as compile
import policy.runtime as runtime
import sys


def d6service(name, keys, inbox, datapath, args):
    return DseRuntime(name, keys, inbox=inbox, dataPath=datapath, **args)


def parse_tablename(tablename):
    pieces = tablename.split(':')
    return pieces[0], ':'.join(pieces[1:])


class DseRuntime (runtime.Runtime, deepsix.deepSix):
    def __init__(self, name, keys, inbox=None, dataPath=None):
        runtime.Runtime.__init__(self)
        deepsix.deepSix.__init__(self, name, keys, inbox=inbox,
                                 dataPath=dataPath)
        self.msg = None
        self.d6cage = None

    def receive_msg(self, msg):
        logging.info("DseRuntime: received msg " + str(msg))
        self.msg = msg

    def receive_data_update(self, msg):
        logging.info("DseRuntime: received data msg " +
                     runtime.iterstr(msg.body.data))
        events = msg.body.data
        for event in events:
            assert compile.is_atom(event.formula), \
                "receive_data_update received non-atom: " + str(event.formula)
            # prefix tablename with data source
            event.formula.table = msg.replyTo + ":" + event.formula.table
        self.update(events)

    def receive_policy_update(self, msg):
        logging.info("DseRuntime: received policy-update msg {}".format(
            runtime.iterstr(msg.body.data)))
        # update the policy and subscriptions to data tables.
        oldtables = self.tablenames()
        self.update(msg.body.data)
        newtables = self.tablenames()
        self.update_table_subscriptions(oldtables, newtables)

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
        logging.debug("Tables:: Old: {}, new: {}, add: {}, rem: {}".format(
            oldtables, newtables, add, rem))
        # subscribe to the new tables (loading services as required)
        for table in add:
            (service, tablename) = parse_tablename(table)
            if service is not None:
                self.conditional_load_data_service(service)
                self.subscribe(service, tablename,
                               callback=self.receive_data_update)
        # unsubscribe from the old tables
        # TODO(thinrichs): figure out scheme for removing old services once
        #     their tables are no longer needed.  Leaving them around is
        #     basically a memory leak, but deleting them too soon
        #     might mean fat-fingering policy yields large performance hits
        #     (e.g. if we need to re-sync entirely).  Probably create a queue
        #     of these tables, keep them up to date, and gc them after
        #     some amount of time.
        for table in rem:
            (service, tablename) = self.parse_tablename(table)
            if service is not None:
                self.unsubscribe(service, tablename)

    def conditional_load_data_service(self, service_name):
        """Load the service called SERVICE_NAME, if it has not already
        been loaded.  Also loads module if that has not already been
        loaded.
        """
        # TODO(thinrichs): work in d6cage's ability to reload a module,
        #    so that driver updates can be handled without shutting
        #    everything down.  A separate API call?
        if self.d6cage is None:
            # policy engine is running without ability to create services
            return
        if service_name in self.d6cage.services:
            return
        # data_service("service1", "modulename")
        # module("modulename", "/path/to/code.py")
        query = ('ans(name, path) :- data_service("{}", name), '
                 ' module(name, path)').format(service_name)
        modules = self.select(query, self.SERVICE_THEORY)
        modules = compile.parse(modules)
        # TODO(thinrichs): figure out what to do if we can't load the right
        #   data service.  Reject the policy update?  Keep it but treat the
        #   table as empty -- dangerous b/c of negation.
        assert len(modules) == 1, "Should only have 1 module per data service"
        module = modules[0]  # instance of QUERY above
        module_name = module.head.arguments[0]
        module_path = module.head.arguments[1]
        if module_name not in sys.modules:
            self.d6cage.loadModule(module_name, module_path)
        self.d6cage.createservice(name=service_name, module=module_name)
