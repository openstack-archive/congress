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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import copy

import ceilometerclient.client as cc
from oslo_log import log as logging
import six

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """Create a dataservice instance.

    This method is called by d6cage to create a dataservice
    instance.  There are a couple of parameters we found useful
    to add to that call, so we included them here instead of
    modifying d6cage (and all the d6cage.createservice calls).
    """
    return CeilometerDriver(name, keys, inbox, datapath, args)


# TODO(thinrichs): figure out how to move even more of this boilerplate
#   into DataSourceDriver.  E.g. change all the classes to Driver instead of
#   NeutronDriver, CeilometerDriver, etc. and move the d6instantiate function
#   to DataSourceDriver.
class CeilometerDriver(datasource_driver.PollingDataSourceDriver,
                       datasource_driver.ExecutionDriver):
    METERS = "meters"
    ALARMS = "alarms"
    EVENTS = "events"
    EVENT_TRAITS = "events.traits"
    ALARM_THRESHOLD_RULE = "alarms.threshold_rule"
    STATISTICS = "statistics"

    value_trans = {'translation-type': 'VALUE'}

    meters_translator = {
        'translation-type': 'HDICT',
        'table-name': METERS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'meter_id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'type', 'translator': value_trans},
             {'fieldname': 'unit', 'translator': value_trans},
             {'fieldname': 'source', 'translator': value_trans},
             {'fieldname': 'resource_id', 'translator': value_trans},
             {'fieldname': 'user_id', 'translator': value_trans},
             {'fieldname': 'project_id', 'translator': value_trans})}

    alarms_translator = {
        'translation-type': 'HDICT',
        'table-name': ALARMS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'alarm_id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'state', 'translator': value_trans},
             {'fieldname': 'enabled', 'translator': value_trans},
             {'fieldname': 'threshold_rule', 'col': 'threshold_rule_id',
              'translator': {'translation-type': 'VDICT',
                             'table-name': ALARM_THRESHOLD_RULE,
                             'id-col': 'threshold_rule_id',
                             'key-col': 'key', 'val-col': 'value',
                             'translator': value_trans}},
             {'fieldname': 'type', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'time_constraints', 'translator': value_trans},
             {'fieldname': 'user_id', 'translator': value_trans},
             {'fieldname': 'project_id', 'translator': value_trans},
             {'fieldname': 'alarm_actions', 'translator': value_trans},
             {'fieldname': 'ok_actions', 'translator': value_trans},
             {'fieldname': 'insufficient_data_actions', 'translator':
             value_trans},
             {'fieldname': 'repeat_actions', 'translator': value_trans},
             {'fieldname': 'timestamp', 'translator': value_trans},
             {'fieldname': 'state_timestamp', 'translator': value_trans},
             )}

    events_translator = {
        'translation-type': 'HDICT',
        'table-name': EVENTS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'message_id', 'translator': value_trans},
             {'fieldname': 'event_type', 'translator': value_trans},
             {'fieldname': 'generated', 'translator': value_trans},
             {'fieldname': 'traits',
              'translator': {'translation-type': 'HDICT',
                             'table-name': EVENT_TRAITS,
                             'selector-type': 'DICT_SELECTOR',
                             'in-list': True,
                             'parent-key': 'message_id',
                             'parent-col-name': 'event_message_id',
                             'field-translators':
                                 ({'fieldname': 'name',
                                   'translator': value_trans},
                                  {'fieldname': 'type',
                                   'translator': value_trans},
                                  {'fieldname': 'value',
                                   'translator': value_trans}
                                  )}}
             )}

    def safe_id(x):
        if isinstance(x, six.string_types):
            return x
        try:
            return x['resource_id']
        except KeyError:
            return str(x)

    statistics_translator = {
        'translation-type': 'HDICT',
        'table-name': STATISTICS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'meter_name', 'translator': value_trans},
             {'fieldname': 'groupby', 'col': 'resource_id',
              'translator': {'translation-type': 'VALUE',
                             'extract-fn': safe_id}},
             {'fieldname': 'avg', 'translator': value_trans},
             {'fieldname': 'count', 'translator': value_trans},
             {'fieldname': 'duration', 'translator': value_trans},
             {'fieldname': 'duration_start', 'translator': value_trans},
             {'fieldname': 'duration_end', 'translator': value_trans},
             {'fieldname': 'max', 'translator': value_trans},
             {'fieldname': 'min', 'translator': value_trans},
             {'fieldname': 'period', 'translator': value_trans},
             {'fieldname': 'period_end', 'translator': value_trans},
             {'fieldname': 'period_start', 'translator': value_trans},
             {'fieldname': 'sum', 'translator': value_trans},
             {'fieldname': 'unit', 'translator': value_trans})}

    TRANSLATORS = [meters_translator, alarms_translator, events_translator,
                   statistics_translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(CeilometerDriver, self).__init__(name, keys, inbox,
                                               datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        session = ds_utils.get_keystone_session(args)
        self.ceilometer_client = cc.get_client(version='2', session=session)
        self.add_executable_client_methods(self.ceilometer_client,
                                           'ceilometerclient.v2.')
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'ceilometer'
        result['description'] = ('Datasource driver that interfaces with '
                                 'ceilometer.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

    def update_from_datasource(self):
        """Read Data from Ceilometer datasource.

        And to fill up the current state of the policy engine.
        """
        LOG.debug("Ceilometer grabbing meters")
        meters = self.ceilometer_client.meters.list()
        self._translate_meters(meters)
        LOG.debug("METERS: %s" % str(self.state[self.METERS]))

        # TODO(ramineni): Ceilometer alarms is moved to separate
        # project Aodh. It's not fully functional yet.
        # Enable it back when its fully functional.

        # LOG.debug("Ceilometer grabbing alarms")
        # alarms = self.ceilometer_client.alarms.list()
        # self._translate_alarms(alarms)
        # LOG.debug("ALARMS: %s" % str(self.state[self.ALARMS]))
        # LOG.debug("THRESHOLD: %s"
        #          % str(self.state[self.ALARM_THRESHOLD_RULE]))

        LOG.debug("Ceilometer grabbing events")
        events = self.ceilometer_client.events.list()
        self._translate_events(events)
        LOG.debug("EVENTS: %s" % str(self.state[self.EVENTS]))
        LOG.debug("TRAITS: %s" % str(self.state[self.EVENT_TRAITS]))

        LOG.debug("Ceilometer grabbing statistics")
        statistics = self._get_statistics(meters)
        self._translate_statistics(statistics)
        LOG.debug("STATISTICS: %s" % str(self.state[self.STATISTICS]))

    def _get_statistics(self, meters):
        statistics = []
        names = set()
        for m in meters:
            LOG.debug("Adding meter %s" % m.name)
            names.add(m.name)
        for meter_name in names:
            LOG.debug("Getting all Resource ID for meter: %s"
                      % meter_name)
            stat_list = self.ceilometer_client.statistics.list(
                meter_name, groupby=['resource_id'])
            LOG.debug("Statistics List: %s" % stat_list)
            if (stat_list):
                for temp in stat_list:
                    temp_dict = copy.copy(temp.to_dict())
                    temp_dict['meter_name'] = meter_name
                    statistics.append(temp_dict)
        return statistics

    @ds_utils.update_state_on_changed(METERS)
    def _translate_meters(self, obj):
        """Translate the meters represented by OBJ into tables."""
        meters = [o.to_dict() for o in obj]

        LOG.debug("METERS: %s" % str(meters))

        row_data = CeilometerDriver.convert_objs(meters,
                                                 self.meters_translator)
        return row_data

    @ds_utils.update_state_on_changed(ALARMS)
    def _translate_alarms(self, obj):
        """Translate the alarms represented by OBJ into tables."""
        alarms = [o.to_dict() for o in obj]
        LOG.debug("ALARMS: %s" % str(alarms))

        row_data = CeilometerDriver.convert_objs(alarms,
                                                 self.alarms_translator)
        return row_data

    @ds_utils.update_state_on_changed(EVENTS)
    def _translate_events(self, obj):
        """Translate the events represented by OBJ into tables."""
        events = [o.to_dict() for o in obj]
        LOG.debug("EVENTS: %s" % str(events))

        row_data = CeilometerDriver.convert_objs(events,
                                                 self.events_translator)
        return row_data

    @ds_utils.update_state_on_changed(STATISTICS)
    def _translate_statistics(self, obj):
        """Translate the statistics represented by OBJ into tables."""
        LOG.debug("STATISTICS: %s" % str(obj))

        row_data = CeilometerDriver.convert_objs(obj,
                                                 self.statistics_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.ceilometer_client, action, action_args)
