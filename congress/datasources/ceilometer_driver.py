#!/usr/bin/env python
# Copyright (c) 2014 Montavista Software, LLC.
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
import ceilometerclient.client as cc
import uuid

from congress.datasources.datasource_driver import DataSourceDriver
from congress.openstack.common import log as logging
from congress.utils import value_to_congress

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice
    instance.  There are a couple of parameters we found useful
    to add to that call, so we included them here instead of
    modifying d6cage (and all the d6cage.createservice calls).
    """
    return CeilometerDriver(name, keys, inbox, datapath, args)


# TODO(thinrichs): figure out how to move even more of this boilerplate
#   into DataSourceDriver.  E.g. change all the classes to Driver instead of
#   NeutronDriver, CeilometerDriver, etc. and move the d6instantiate function
#   to DataSourceDriver.
class CeilometerDriver(DataSourceDriver):
    METERS = "meters"
    ALARMS = "alarms"
    EVENTS = "events"
    EVENT_TRAITS = "events.traits"
    ALARM_THRESHOLD_RULE = "alarms.threshold_rule"

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        if args is None:
            args = self.empty_credentials()
        super(CeilometerDriver, self).__init__(name, keys, inbox,
                                               datapath, args)
        if 'client' in args:
            self.ceilometer_client = args['client']
        else:
            self.creds = self.get_ceilometer_credentials_v2(name, args)
            self.ceilometer_client = cc.get_client(**self.creds)

        self.raw_state = {}

    def update_from_datasource(self):
        self.state = {}
        self.meters = []
        self.alarms = []
        self.alarm_threshold_rule = []
        self.events = []
        self.event_traits = []

        meters = self.ceilometer_client.meters.list()
        if ('meters' not in self.raw_state or meters !=
            self.raw_state['meters']):
            self.raw_state['meters'] = meters
            self._translate_meters(meters)
        else:
            self.raw_state['meters'] = meters
            self._translate_meters(meters)

        alarms = self.ceilometer_client.alarms.list()
        if ('alarms' not in self.raw_state or alarms !=
            self.raw_state['alarms']):
            self.raw_state['alarms'] = alarms
            self._translate_alarms(alarms)
        else:
            self.alarms = self.state[self.ALARMS]
            self.alarm_threshold_rule = self.state[self.ALARM_THRESHOLD_RULE]

        events = self.ceilometer_client.events.list()
        if ('events' not in self.raw_state or events !=
            self.raw_state['events']):
            self.raw_state['events'] = events
            self._translate_events(events)
        else:
            self.events = self.state[self.EVENTS]
            self.event_traits = self.state[self.EVENT_TRAITS]

        LOG.debug("EVENTS obtained from ceilometer %s" % self.events)
        # set state
        # TODO(thinrichs): use self.state everywhere instead of self.meters...
        self.state[self.METERS] = set(self.meters)
        self.state[self.ALARMS] = set(self.alarms)
        self.state[self.ALARM_THRESHOLD_RULE] = set(self.alarm_threshold_rule)
        self.state[self.EVENTS] = set(self.events)
        self.state[self.EVENT_TRAITS] = set(self.event_traits)

    @classmethod
    def get_schema(cls):
        d = {}
        d[cls.METERS] = ("meter_id", "name", "type", "unit", "source",
                         "resource_id", "user_id", "project_id")
        d[cls.ALARMS] = ("alarm_id", "name", "state", "enabled",
                         "threshold_rule", "type", "description",
                         "time_constraints", "user_id", "project_id",
                         "alarm_actions", "ok_actions",
                         "insufficient_data_actions", "repeat_actions",
                         "timestamp", "state_timestamp")
        d[cls.EVENTS] = ("message_id", "event_type", "generated", "traits")
        return d

    def get_ceilometer_credentials_v2(self, name, args):
        creds = self.get_credentials(name, args)
        d = {}
        d['version'] = '2'
        d['username'] = creds['username']
        d['password'] = creds['password']
        d['auth_url'] = creds['auth_url']
        d['tenant_name'] = creds['tenant_name']
        return d

    @classmethod
    def meter_key_position_map(cls):
        d = {}
        d['meter_id'] = 0
        d['name'] = 1
        d['type'] = 2
        d['unit'] = 3
        d['source'] = 4
        d['resource_id'] = 5
        d['user_id'] = 6
        d['project_id'] = 7
        return d

    @classmethod
    def alarm_key_position_map(cls):
        d = {}
        d['alarm_id'] = 0
        d['name'] = 1
        d['state'] = 2
        d['enabled'] = 3
        d['threshold_rule'] = 4
        d['type'] = 5
        d['description'] = 6
        d['time_constraints'] = 7
        d['user_id'] = 8
        d['project_id'] = 9
        d['alarm_actions'] = 10
        d['ok_actions'] = 11
        d['insufficient_data_actions'] = 12
        d['repeat_actions'] = 13
        d['timestamp'] = 14
        d['state_timestamp'] = 15
        return d

    @classmethod
    def event_key_position_map(cls):
        d = {}
        d['message_id'] = 0
        d['event_type'] = 1
        d['generated'] = 2
        d['traits'] = 3
        return d

    def _translate_meters(self, obj):
        self.meters = []
        key_to_index = self.meter_key_position_map()
        max_meter_index = max(key_to_index.values()) + 1
        t_list = []
        for p in obj:
            if type(p) != type(dict()):
                p_dict = p.to_dict()
            else:
                p_dict = p
            row = ['None'] * max_meter_index
            for k, v in p_dict.items():
                row[key_to_index[k]] = value_to_congress(v)
            t_list.append(tuple(row))
        self.meters = t_list

    def _translate_alarms(self, obj):
        LOG.debug("Translating ALARM object %s" % obj)
        self.alarms = []
        self.alarm_threshold_rule = []
        key_to_index = self.alarm_key_position_map()
        max_alarm_index = max(key_to_index.values()) + 1
        t_list = []
        t_thres_list = []
        for k in obj:
            if type(k) != type(dict()):
                k_dict = k.to_dict()
            else:
                k_dict = k
            row = ['None'] * max_alarm_index
            for p, v in k_dict.items():
                if p == 'threshold_rule':
                    threshold_rule_id = str(uuid.uuid1())
                    for s, t in v.items():
                        if type(t) != type(list()) and type(t) != type(dict()):
                            # FIXME(madhumohan): Dirty workaround. A cleaner
                            # approach is required to handled None object in
                            # the data
                            if t is None:
                                t = 'None'
                            row_thres_tuple = (threshold_rule_id, s, t)
                            t_thres_list.append(row_thres_tuple)
                    row[key_to_index['threshold_rule']] = threshold_rule_id
                else:
                    if p in key_to_index:
                        row[key_to_index[p]] = value_to_congress(v)
                    else:
                        LOG.info("Ignoring unexpected dict key " + p)
            t_list.append(tuple(row))

        LOG.debug("Generated alarm list %s" % t_list)
        LOG.debug("Generated threshold rule list %s" % t_thres_list)

        self.alarms = t_list
        self.alarm_threshold_rule = t_thres_list

    def _translate_events(self, obj):
        LOG.debug("Translating EVENT object %s" % obj)
        self.events = []
        self.event_traits = []
        key_to_index = self.event_key_position_map()
        max_event_index = max(key_to_index.values()) + 1
        t_list = []
        t_trait_list = []
        # TODO(madhumohan): Need a modular implementation of the below loop for
        # better readability and maintainability. Also for flexible translation
        # all types of nested datastructure in the data.
        for k in obj:
            if type(k) != type(dict()):
                k_dict = k.to_dict()
            else:
                k_dict = k
            row = ['None'] * max_event_index
            for p, v in k_dict.items():
                if p == 'traits':
                    trait_id = str(uuid.uuid1())
                    for trait in k_dict[p]:
                        if trait['name'] == 'payload':
                            t_dict = eval(trait['value'])
                            for s, t in t_dict.items():
                    # FIXME(madhumohan): Dictionary items within the payload
                    # are handled as additional fields in the payload
                    # table. Need a better way to handle
                    # dictionaries or other structures within payload
                    # Nested dictionaries in the payload are skipped
                    # Lists within the dictionaries are also ignored
                                if type(t) == type(dict()):
                                    for n, m in t.items():
                                        if type(m) != type(dict()) and \
                                           type(m) != type(list()):
                            # FIXME(madhumohan): Dirty workaround. A cleaner
                            # approach is required to handled None object in
                            # the data
                                            if m is None:
                                                m = 'None'
                                            row_trait_tuple = \
                                                (trait_id, n, m)
                                            t_trait_list.append(
                                                row_trait_tuple)
                                else:
                                    if type(t) != type(list()):
                            # FIXME(madhumohan): Dirty workaround. A cleaner
                            # approach is required to handled None object in
                            # the data
                                        if t is None:
                                            t = 'None'
                                        row_trait_tuple = (trait_id, s, t)
                                        t_trait_list.append(row_trait_tuple)
                    row[key_to_index['traits']] = trait_id
                else:
                    if p in key_to_index:
                        row[key_to_index[p]] = value_to_congress(v)
                    else:
                        LOG.info("Ignoring unexpected dict key " + p)
            t_list.append(tuple(row))

        LOG.debug("Generated event list %s" % t_list)
        LOG.debug("Generated trait list %s" % t_trait_list)

        self.events = t_list
        self.event_traits = t_trait_list


def main():
    driver = CeilometerDriver()
    print "Last updated: %s" % driver.get_last_updated_time()

    print "Starting Ceilometer Sync Service"
    print "Tuple Names : " + str(driver.get_tuple_names())
    print ("Tuple Metadata - : " +
           str(CeilometerDriver.get_schema()))
    # sync with the ceilometer service
    driver.update_from_datasource()
    print "Meters: %s" % driver.get_all(driver.METERS)
    print "Alarms: %s" % driver.get_all(driver.ALARMS)
    print "Events: %s" % driver.get_all(driver.EVENTS)
    print "Last updated: %s" % driver.get_last_updated_time()
    print "Sync completed"

    print "-----------------------------------------"


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        raise
