# Copyright (c) 2015 VMware, Inc. All rights reserved.
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

from congress.datalog.base import Tracer
from congress.datalog import compile
from congress.datalog.nonrecursive import MultiModuleNonrecursiveRuleTheory
from congress.exception import CongressException
from congress.openstack.common import log as logging
from congress.policy_engines.base_driver import PolicyEngineDriver

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return ComputePlacementEngine(name, keys, inbox, datapath, args)


# TODO(thinrichs): Figure out what to move to the base class
class ComputePlacementEngine(PolicyEngineDriver):
    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(ComputePlacementEngine, self).__init__(
            name, keys, inbox, datapath)
        self.policy = MultiModuleNonrecursiveRuleTheory(name=name)
        self.initialized = True

    def set_policy(self, policy):
        LOG.info("%s:: setting policy to %s", str(self.name), str(policy))
        # empty out current policy
        external = [compile.build_tablename(service, name)
                    for service, name in self._current_external_tables()]
        self.policy.empty(tablenames=external, invert=True)

        # insert new policy and subscribe to the tablenames referencing a
        #    datasource driver
        tablenames = set()
        for rule in self.parse(policy):
            tablenames |= rule.tablenames()
            self.policy.insert(rule)
        LOG.info("new policy: %s", self.policy.content_string())
        tablenames = [compile.parse_tablename(table) for table in tablenames]
        tablenames = [(service, name) for (service, name) in tablenames
                      if service is not None]
        self._set_subscriptions(tablenames)

    def insert(self, formula):
        return self.policy.insert(self.parse1(formula))

    def delete(self, formula):
        return self.policy.delete(self.parse1(formula))

    def select(self, query):
        ans = self.policy.select(self.parse1(query))
        return " ".join(str(x) for x in ans)

    def debug_mode(self):
        tracer = Tracer()
        tracer.trace('*')
        self.policy.set_tracer(tracer)

    def production_mode(self):
        tracer = Tracer()
        self.policy.set_tracer(tracer)

    def _current_external_tables(self):
        return [(value.key, value.dataindex)
                for value in self.subdata.values()]

    def _set_subscriptions(self, tablenames):
        subscriptions = set(self._current_external_tables())
        tablenames = set(tablenames)
        toadd = tablenames - subscriptions
        torem = subscriptions - tablenames
        for service, tablename in toadd:
            if service is not None:
                LOG.info("%s:: subscribing to (%s, %s)",
                         self.name, service, tablename)
                self.subscribe(service, tablename,
                               callback=self.receive_data)

        for service, tablename in torem:
            if service is not None:
                LOG.info("%s:: unsubscribing from (%s, %s)",
                         self.name, service, tablename)
                self.unsubscribe(service, tablename)
                relevant_tables = [compile.build_tablename(service, tablename)]
                self.policy.empty(relevant_tables)

    def receive_data(self, msg):
        """Event handler for when a dataservice publishes data.

        That data can either be the full table (as a list of tuples)
        or a delta (a list of Events).
        """
        LOG.info("%s:: received data msg %s", self.name, msg)
        # if empty data, assume it is an init msg, since noop otherwise
        if len(msg.body.data) == 0:
            self.receive_data_full(msg)
        else:
            # grab an item from any iterable
            dataelem = iter(msg.body.data).next()
            if isinstance(dataelem, compile.Event):
                self.receive_data_update(msg)
            else:
                self.receive_data_full(msg)

    def receive_data_full(self, msg):
        """Handler for when dataservice publishes full table."""
        LOG.info("%s:: received full data msg for %s: %s",
                 self.name, msg.header['dataindex'],
                 ";".join(str(x) for x in msg.body.data))
        tablename = compile.build_tablename(msg.replyTo,
                                            msg.header['dataindex'])

        # Use a generator to avoid instantiating all these Facts at once.
        #   Don't print out 'literals' since that will eat the generator
        literals = (compile.Fact(tablename, row) for row in msg.body.data)

        LOG.info("%s:: begin initialize_tables %s", self.name, tablename)
        self.policy.initialize_tables([tablename], literals)
        LOG.info("%s:: end initialize data msg for %s", self.name, tablename)
        select = [str(x) for x in self.select('p(x)')]
        LOG.info("%s:: select('p(x)'): %s ENDED", self.name, " ".join(select))

    def receive_data_update(self, msg):
        """Handler for when dataservice publishes a delta."""
        LOG.info("%s:: received update data msg for %s: %s",
                 self.name, msg.header['dataindex'],
                 ";".join(str(x) for x in msg.body.data))
        new_events = []
        for event in msg.body.data:
            assert compile.is_atom(event.formula), (
                "receive_data_update received non-atom: " +
                str(event.formula))
            # prefix tablename with data source
            actual_table = compile.build_tablename(msg.replyTo,
                                                   event.formula.table)
            values = [term.name for term in event.formula.arguments]
            newevent = compile.Event(compile.Fact(actual_table, values),
                                     insert=event.insert)
            new_events.append(newevent)
        (permitted, changes) = self.policy.update(new_events)
        if not permitted:
            raise CongressException(
                "Update not permitted." + '\n'.join(str(x) for x in changes))
        else:
            tablename = msg.header['dataindex']
            service = msg.replyTo
            LOG.debug("update data msg for %s from %s caused %d "
                      "changes: %s", tablename, service, len(changes),
                      ";".join(str(x) for x in changes))

    def parse(self, policy):
        return compile.parse(policy, use_modules=False)

    def parse1(self, policy):
        return compile.parse1(policy, use_modules=False)
