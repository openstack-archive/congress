# Copyright (c) 2015 Cisco, 2018 NEC, Inc.
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

from datetime import datetime
from datetime import timedelta

import eventlet
from futurist import periodics
from monascaclient import client as monasca_client
from oslo_concurrency import lockutils
from oslo_log import log as logging

from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils

LOG = logging.getLogger(__name__)

DATA = "statistics.data"
DIMENSIONS = "dimensions"
METRICS = "metrics"
NOTIFICATIONS = "alarm_notification"
STATISTICS = "statistics"
value_trans = {'translation-type': 'VALUE'}


# TODO(thinrichs): figure out how to move even more of this boilerplate
#   into DataSourceDriver.  E.g. change all the classes to Driver instead of
#   NeutronDriver, CeilometerDriver, etc. and move the d6instantiate function
#   to DataSourceDriver.
class MonascaDriver(datasource_driver.PollingDataSourceDriver,
                    datasource_driver.ExecutionDriver):

    # TODO(fabiog): add events and logs when fully supported in Monasca
    # EVENTS = "events"
    # LOGS = "logs"

    metric_translator = {
        'translation-type': 'HDICT',
        'table-name': METRICS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'dimensions',
              'translator': {'translation-type': 'VDICT',
                             'table-name': DIMENSIONS,
                             'id-col': 'id',
                             'key-col': 'key', 'val-col': 'value',
                             'translator': value_trans}})
    }

    statistics_translator = {
        'translation-type': 'HDICT',
        'table-name': STATISTICS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'statistics',
              'translator': {'translation-type': 'LIST',
                             'table-name': DATA,
                             'id-col': 'name',
                             'val-col': 'value_col',
                             'translator': value_trans}})
    }

    TRANSLATORS = [metric_translator, statistics_translator]

    def __init__(self,  name='', args=None):
        super(MonascaDriver, self).__init__(name, args=args)
        datasource_driver.ExecutionDriver.__init__(self)
        if not args.get('project_name'):
            args['project_name'] = args['tenant_name']

        # set default polling time to 1hr
        self.poll_time = int(args.get('poll_time', 3600))

        session = ds_utils.get_keystone_session(args)

        # if the endpoint not defined retrieved it from keystone catalog
        if 'endpoint' not in args:
            args['endpoint'] = session.get_endpoint(service_type='monitoring',
                                                    interface='publicURL')

        self.monasca = monasca_client.Client('2_0', session=session,
                                             endpoint=args['endpoint'])
        self.add_executable_client_methods(self.monasca, 'monascaclient.')
        self.initialize_update_methods()
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'monasca'
        result['description'] = ('Datasource driver that interfaces with '
                                 'monasca.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['config']['lazy_tables'] = constants.OPTIONAL
        result['secret'] = ['password']
        return result

    def initialize_update_methods(self):
        metrics_method = lambda: self._translate_metric(
            self.monasca.metrics.list())
        self.add_update_method(metrics_method, self.metric_translator)

        statistics_method = self.update_statistics
        self.add_update_method(statistics_method, self.statistics_translator)

    def update_statistics(self):
        today = datetime.utcnow()
        yesterday = timedelta(hours=24)
        start_from = datetime.isoformat(today-yesterday)

        for metric in self.monasca.metrics.list_names():
            LOG.debug("Monasca statistics for metric %s", metric['name'])
            _query_args = dict(
                start_time=start_from,
                name=metric['name'],
                statistics='avg',
                period=int(self.poll_time),
                merge_metrics='true')
            statistics = self.monasca.metrics.list_statistics(
                **_query_args)
            self._translate_statistics(statistics)

    @ds_utils.update_state_on_changed(METRICS)
    def _translate_metric(self, obj):
        """Translate the metrics represented by OBJ into tables."""
        LOG.debug("METRIC: %s", str(obj))

        row_data = MonascaDriver.convert_objs(obj,
                                              self.metric_translator)
        return row_data

    @ds_utils.update_state_on_changed(STATISTICS)
    def _translate_statistics(self, obj):
        """Translate the metrics represented by OBJ into tables."""

        LOG.debug("STATISTICS: %s", str(obj))

        row_data = MonascaDriver.convert_objs(obj,
                                              self.statistics_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.monasca, action, action_args)


class MonascaWebhookDriver(datasource_driver.PushedDataSourceDriver):

    METRICS = 'alarms.' + METRICS
    DIMENSIONS = METRICS + '.' + DIMENSIONS

    metric_translator = {
        'translation-type': 'HDICT',
        'table-name': METRICS,
        'parent-key': 'alarm_id',
        'parent-col-name': 'alarm_id',
        'parent-key-desc': 'ALARM id',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'dimensions',
              'translator': {'translation-type': 'VDICT',
                             'table-name': DIMENSIONS,
                             'id-col': 'id',
                             'key-col': 'key', 'val-col': 'value',
                             'translator': value_trans}})
    }

    alarm_notification_translator = {
        'translation-type': 'HDICT',
        'table-name': NOTIFICATIONS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'alarm_id', 'translator': value_trans},
             {'fieldname': 'alarm_definition_id', 'translator': value_trans},
             {'fieldname': 'alarm_name', 'translator': value_trans},
             {'fieldname': 'alarm_description', 'translator': value_trans},
             {'fieldname': 'alarm_timestamp', 'translator': value_trans},
             {'fieldname': 'state', 'translator': value_trans},
             {'fieldname': 'old_state', 'translator': value_trans},
             {'fieldname': 'message', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'metrics', 'translator': metric_translator},)
    }
    TRANSLATORS = [alarm_notification_translator]

    def __init__(self, name='', args=None):
        LOG.warning(
            'The Monasca webhook driver is classified as having unstable '
            'schema. The schema may change in future releases in '
            'backwards-incompatible ways.')
        super(MonascaWebhookDriver, self).__init__(name, args=args)
        if args is None:
            args = {}
        # set default time to 10 days before deleting an active alarm
        self.hours_to_keep_alarm = int(args.get('hours_to_keep_alarm', 240))
        self.set_up_periodic_tasks()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'monasca_webhook'
        result['description'] = ('Datasource driver that accepts Monasca '
                                 'webhook alarm notifications.')
        result['config'] = {'persist_data': constants.OPTIONAL,
                            'hours_to_keep_alarm': constants.OPTIONAL}
        return result

    def _delete_rows(self, tablename, column_number, value):
        to_remove = [row for row in self.state[tablename]
                     if row[column_number] == value]
        for row in to_remove:
            self.state[tablename].discard(row)

    def _webhook_handler(self, alarm):
        tablenames = [NOTIFICATIONS, self.METRICS, self.DIMENSIONS]

        # remove already existing same alarm row from alarm_notification
        alarm_id = alarm['alarm_id']
        column_index_number_of_alarm_id = 0
        self._delete_rows(NOTIFICATIONS, column_index_number_of_alarm_id,
                          alarm_id)

        # remove already existing same metric from metrics
        self._delete_rows(self.METRICS, column_index_number_of_alarm_id,
                          alarm_id)

        translator = self.alarm_notification_translator
        row_data = MonascaWebhookDriver.convert_objs([alarm], translator)

        # add alarm to table
        for table, row in row_data:
            if table in tablenames:
                self.state[table].add(row)
        for table in tablenames:
            LOG.debug('publish a new state %s in %s',
                      self.state[table], table)
            self.publish(table, self.state[table])
        return tablenames

    def set_up_periodic_tasks(self):
        @lockutils.synchronized('congress_monasca_webhook_ds_data')
        @periodics.periodic(spacing=max(self.hours_to_keep_alarm * 3600/10, 1))
        def delete_old_alarms():
            tablename = NOTIFICATIONS
            col_index_of_timestamp = 4
            # find for removal all alarms at least self.hours_to_keep_alarm old
            to_remove = [
                row for row in self.state[tablename]
                if (datetime.utcnow() -
                    datetime.utcfromtimestamp(row[col_index_of_timestamp])
                    >= timedelta(hours=self.hours_to_keep_alarm))]
            for row in to_remove:
                self.state[tablename].discard(row)
                # deletes corresponding metrics table rows
                col_index_of_alarm_id = 0
                alarm_id = row[col_index_of_alarm_id]
                self._delete_rows(self.METRICS, col_index_of_alarm_id,
                                  alarm_id)

        periodic_task_callables = [
            (delete_old_alarms, None, {}),
            (delete_old_alarms, None, {})]
        self.periodic_tasks = periodics.PeriodicWorker(periodic_task_callables)
        self.periodic_tasks_thread = eventlet.spawn_n(
            self.periodic_tasks.start)

    def __del__(self):
        if self.periodic_tasks:
            self.periodic_tasks.stop()
            self.periodic_tasks.wait()
            self.periodic_tasks = None
        if self.periodic_tasks_thread:
            eventlet.greenthread.kill(self.periodic_tasks_thread)
            self.periodic_tasks_thread = None
