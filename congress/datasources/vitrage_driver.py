# Copyright (c) 2018 VMware Inc All rights reserved.
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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from datetime import datetime
from datetime import timedelta

import eventlet
from futurist import periodics
from oslo_concurrency import lockutils
from oslo_log import log as logging

from congress.datasources import constants
from congress.datasources import datasource_driver

LOG = logging.getLogger(__name__)

TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class VitrageDriver(datasource_driver.PushedDataSourceDriver):
    '''Datasource driver that accepts Vitrage webhook alarm notification.'''

    value_trans = {'translation-type': 'VALUE'}

    def flatten_and_timestamp_alarm_webhook(webhook_alarms_objects):
        flattened = []
        key_to_sub_dict = 'resource'
        for alarm in webhook_alarms_objects:
            sub_dict = alarm.pop(key_to_sub_dict)
            for k, v in sub_dict.items():
                # add prefix to key and move to top level dict
                alarm[key_to_sub_dict + '_' + k] = v
            alarm['receive_timestamp'] = datetime.utcnow().strftime(
                TIMESTAMP_FORMAT)
            flattened.append(alarm)
        return flattened

    webhook_alarm_translator = {
        'translation-type': 'HDICT',
        'table-name': 'alarms',
        'selector-type': 'DICT_SELECTOR',
        'objects-extract-fn': flatten_and_timestamp_alarm_webhook,
        'field-translators':
            ({'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'state', 'translator': value_trans},
             {'fieldname': 'vitrage_type', 'col': 'type',
              'translator': value_trans},
             {'fieldname': 'vitrage_operational_severity',
              'col': 'operational_severity',
              'translator': value_trans},
             {'fieldname': 'vitrage_id', 'translator': value_trans},
             {'fieldname': 'update_timestamp', 'translator': value_trans},
             {'fieldname': 'receive_timestamp', 'translator': value_trans},
             {'fieldname': 'resource_name', 'translator': value_trans},
             {'fieldname': 'resource_id', 'translator': value_trans},
             {'fieldname': 'resource_vitrage_id', 'translator': value_trans},
             {'fieldname': 'resource_project_id', 'translator': value_trans},
             {'fieldname': 'resource_vitrage_operational_state',
              'col': 'resource_operational_state',
              'translator': value_trans},
             {'fieldname': 'resource_vitrage_type',
              'col': 'resource_type', 'translator': value_trans},
             )}

    TRANSLATORS = [webhook_alarm_translator]

    def __init__(self, name='', args=None):
        LOG.warning(
            'The Vitrage driver is classified as having unstable schema. '
            'The schema may change in future releases in '
            'backwards-incompatible ways.')
        super(VitrageDriver, self).__init__(name, args=args)
        if args is None:
            args = {}
        # set default time to 10 days before deleting an active alarm
        self.hours_to_keep_alarm = int(args.get('hours_to_keep_alarm', 240))
        self.set_up_periodic_tasks()

    @lockutils.synchronized('congress_vitrage_ds_data')
    def _webhook_handler(self, payload):
        tablename = 'alarms'

        # remove previous alarms of same ID from table
        row_id = payload['payload']['vitrage_id']
        column_index_number_of_row_id = 4
        to_remove = [row for row in self.state[tablename]
                     if row[column_index_number_of_row_id] == row_id]
        for row in to_remove:
            self.state[tablename].discard(row)

        # add new alarm to table
        translator = self.webhook_alarm_translator
        row_data = VitrageDriver.convert_objs(
            [payload['payload']], translator)
        for table, row in row_data:
            if table == tablename:
                self.state[tablename].add(row)

        LOG.debug('publish a new state %s in %s',
                  self.state[tablename], tablename)
        # Note (thread-safety): blocking call
        self.publish(tablename, self.state[tablename])
        return [tablename]

    def set_up_periodic_tasks(self):
        @lockutils.synchronized('congress_vitrage_ds_data')
        @periodics.periodic(spacing=max(self.hours_to_keep_alarm * 3600/10, 1))
        def delete_old_alarms():
            tablename = 'alarms'
            col_index_of_timestamp = 5
            # find for removal all alarms at least self.hours_to_keep_alarm old
            to_remove = [
                row for row in self.state[tablename]
                if (datetime.utcnow() -
                    datetime.strptime(row[col_index_of_timestamp],
                                      TIMESTAMP_FORMAT)
                    >= timedelta(hours=self.hours_to_keep_alarm))]
            for row in to_remove:
                self.state[tablename].discard(row)

        periodic_task_callables = [
            (delete_old_alarms, None, {}),
            (delete_old_alarms, None, {})]
        self.periodic_tasks = periodics.PeriodicWorker(periodic_task_callables)
        self.periodic_tasks_thread = eventlet.spawn_n(
            self.periodic_tasks.start)

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'vitrage'
        result['description'] = ('Datasource driver that accepts Vitrage '
                                 'webhook alarm notifications.')
        result['config'] = {'persist_data': constants.OPTIONAL,
                            'hours_to_keep_alarm': constants.OPTIONAL}
        return result

    def __del__(self):
        if self.periodic_tasks:
            self.periodic_tasks.stop()
            self.periodic_tasks.wait()
            self.periodic_tasks = None
        if self.periodic_tasks_thread:
            eventlet.greenthread.kill(self.periodic_tasks_thread)
            self.periodic_tasks_thread = None
