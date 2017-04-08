# Copyright 2016 NEC Corporation. All rights reserved.
# All Rights Reserved.
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

from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions
from tempest import test

from congress_tempest_tests.tests.scenario import manager_congress


CONF = config.CONF


class TestAodhDriver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def skip_checks(cls):
        super(TestAodhDriver, cls).skip_checks()
        if not getattr(CONF.service_available, 'aodh_plugin', False):
            msg = ("%s skipped as aodh is not available" %
                   cls.__class__.__name__)
            raise cls.skipException(msg)

    def setUp(cls):
        super(TestAodhDriver, cls).setUp()
        cls.alarms_client = cls.admin_manager.alarms_client
        cls.datasource_id = manager_congress.get_datasource_id(
            cls.admin_manager.congress_client, 'aodh')

    @test.attr(type='smoke')
    def test_aodh_alarms_table(self):
        # Add test alarm
        rule = {'meter_name': 'cpu_util',
                'comparison_operator': 'gt',
                'threshold': 80.0,
                'period': 70}
        self.alarms_client.create_alarm(name='test-alarm',
                                        type='threshold',
                                        enabled=False,
                                        threshold_rule=rule)
        alarms_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'alarms')['columns'])
        alarms_id_col = next(i for i, c in enumerate(alarms_schema)
                             if c['name'] == 'alarm_id')

        def _check_data_table_aodh_alarms():
            # Fetch data from aodh each time, because this test may start
            # before aodh has all the users.
            alarms = self.alarms_client.list_alarms()
            alarm_map = {}
            for alarm in alarms:
                alarm_map[alarm['alarm_id']] = alarm

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'alarms'))
            rule_data = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'alarms.threshold_rule'))['results']

            for row in results['results']:
                try:
                    alarm_row = alarm_map[row['data'][alarms_id_col]]
                except KeyError:
                    return False
                for index in range(len(alarms_schema)):
                    if alarms_schema[index]['name'] == 'threshold_rule_id':
                        threshold_rule = alarm_row['threshold_rule']
                        data = [r['data'] for r in rule_data
                                if r['data'][0] == row['data'][index]]
                        for l in data:
                            if str(threshold_rule[l[1]]) != str(l[2]):
                                return False
                        continue

                    if (str(row['data'][index]) !=
                            str(alarm_row[alarms_schema[index]['name']])):
                        return False
            return True

        if not test_utils.call_until_true(func=_check_data_table_aodh_alarms,
                                          duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @test.attr(type='smoke')
    def test_update_no_error(self):
        if not test_utils.call_until_true(
                func=lambda: self.check_datasource_no_error('aodh'),
                duration=30, sleep_for=5):
            raise exceptions.TimeoutException('Datasource could not poll '
                                              'without error.')
