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
from mock import MagicMock

from congress.datasources.ceilometer_driver import CeilometerDriver
from congress.tests import base
from congress.tests.datasources.util import ResponseObj
from congress.tests import helper


class TestCeilometerDriver(base.TestCase):

    def setUp(self):
        super(TestCeilometerDriver, self).setUp()
        self.ceilometer_client = MagicMock()

        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        self.driver = CeilometerDriver(name='testceilometer', args=args)

    def test_list_meters(self):
        meters_data = [
            ResponseObj({'name': 'network.incoming.bytes',
                         'type': 'cumulative',
                         'unit': 'B',
                         'resource_id': 'instance-00000001-tap437ce69c-e5',
                         'user_id': '2b01323fd71345bc8cdc5dbbd6d127ea',
                         'project_id': '0020df0171ec41b597cd8b3002e21bee',
                         'meter_id': 'aW5zdGFuY2UtMDAwMDAwMDEtYTI1N2JhMT',
                         'source': 'openstack'}),
            ResponseObj({'name': 'instance:m1.tiny',
                         'type': 'gauge',
                         'unit': 'instance',
                         'resource_id': 'a257ba13-0b36-4a86-ae89-f78dd28b8ae5',
                         'user_id': '2b01323fd71345bc8cdc5dbbd6d127ea',
                         'project_id': '0020df0171ec41b597cd8b3002e21bee',
                         'meter_id': 'YTI1N2JhMTMtMGIzNi00YTg2LWFlODktZjc4ZG',
                         'source': 'openstack'})]

        self.driver._translate_meters(meters_data)
        meter_list = self.driver.meters
        self.assertIsNotNone(meter_list)
        self.assertEqual(2, len(meter_list))

        # Verifying individual tuple data
        self.assertEqual(('aW5zdGFuY2UtMDAwMDAwMDEtYTI1N2JhMT',
                          'network.incoming.bytes',
                          'cumulative',
                          'B',
                          'openstack',
                          'instance-00000001-tap437ce69c-e5',
                          '2b01323fd71345bc8cdc5dbbd6d127ea',
                          '0020df0171ec41b597cd8b3002e21bee'),
                         meter_list[0])

        self.assertEqual(('YTI1N2JhMTMtMGIzNi00YTg2LWFlODktZjc4ZG',
                          'instance:m1.tiny',
                          'gauge',
                          'instance',
                          'openstack',
                          'a257ba13-0b36-4a86-ae89-f78dd28b8ae5',
                          '2b01323fd71345bc8cdc5dbbd6d127ea',
                          '0020df0171ec41b597cd8b3002e21bee'),
                         meter_list[1])

    def test_list_alarms(self):
        threshold_rule1 = {'key1': 'value1',
                           'key2': 'value2',
                           'key3': 'value3'}

        alarms_data = [
            ResponseObj({'alarm_id': 'd1b2b7a7-9512-4290-97ca-2580ed72c375',
                         'name': 'cpu_high',
                         'state': 'insufficient data',
                         'enabled': 'True',
                         'threshold_rule': threshold_rule1,
                         'type': 'threshold',
                         'description': 'instance running hot',
                         'time_constraints': '[]',
                         'user_id': '2b01323fd71345bc8cdc5dbbd6d127ea',
                         'project_id': '',
                         'alarm_actions': "[u'log://']",
                         'ok_actions': '[]',
                         'insufficient_data_actions': '[]',
                         'repeat_actions': 'False',
                         'timestamp': '2014-09-30T04:55:36.015925',
                         'state_timestamp': '2014-09-30T04:55:36.015925'}),
            ResponseObj({'alarm_id': '7ef99553-a73f-4b18-a617-997a479c48e9',
                         'name': 'cpu_high2',
                         'state': 'insufficient data',
                         'enabled': 'True',
                         'threshold_rule': threshold_rule1,
                         'type': 'threshold',
                         'description': 'instance running hot',
                         'time_constraints': '[]',
                         'user_id': '2b01323fd71345bc8cdc5dbbd6d127ea',
                         'project_id': '',
                         'alarm_actions': "[u'log://']",
                         'ok_actions': '[]',
                         'insufficient_data_actions': '[]',
                         'repeat_actions': 'False',
                         'timestamp': '2014-09-30T05:00:43.351041',
                         'state_timestamp': '2014-09-30T05:00:43.351041'})]

        self.driver._translate_alarms(alarms_data)
        alarm_list = self.driver.alarms
        self.assertIsNotNone(alarm_list)
        self.assertEqual(2, len(alarm_list))

        alarm_threshold_rule = self.driver.alarm_threshold_rule
        self.assertIsNotNone(alarm_threshold_rule)
        self.assertEqual(6, len(alarm_threshold_rule))

        thresh_rule_id1 = alarm_threshold_rule[0][0]
        thresh_rule_id2 = alarm_threshold_rule[3][0]

        # Verifying individual tuple data
        self.assertEqual(('d1b2b7a7-9512-4290-97ca-2580ed72c375',
                          'cpu_high', 'insufficient data', 'True',
                          thresh_rule_id1,
                          'threshold', 'instance running hot',
                          '[]', '2b01323fd71345bc8cdc5dbbd6d127ea',
                          '', "[u'log://']", '[]', '[]',
                          'False', '2014-09-30T04:55:36.015925',
                          '2014-09-30T04:55:36.015925'),
                         alarm_list[0])

        self.assertEqual(('7ef99553-a73f-4b18-a617-997a479c48e9',
                          'cpu_high2', 'insufficient data',
                          'True',
                          thresh_rule_id2,
                          'threshold', 'instance running hot',
                          '[]', '2b01323fd71345bc8cdc5dbbd6d127ea',
                          '', "[u'log://']", '[]', '[]', 'False',
                          '2014-09-30T05:00:43.351041',
                          '2014-09-30T05:00:43.351041'),
                         alarm_list[1])

    def test_list_events(self):
        trait = [{'name': 'payload',
                  'value': "{'t1': 'value1', 't2': 'value2', 't3': 'value3'}"}]
        events_data = [
            ResponseObj({'message_id': '6834861c-ccb3-4c6f-ac00-fe8fe1ad4ed4',
                         'event_type': 'image.create',
                         'generated': '2014-09-29T08:19:45.556301',
                         'traits': trait}),
            ResponseObj({'message_id': '3676d6d4-5c65-4442-9eda-b78d750ea91f',
                         'event_type': 'compute.instance.update',
                         'generated': '2014-09-30T04:54:45.395522',
                         'traits': trait})]

        self.driver._translate_events(events_data)
        event_list = self.driver.events
        self.assertIsNotNone(event_list)
        self.assertEqual(2, len(event_list))

        event_trait_list = self.driver.event_traits
        self.assertIsNotNone(event_trait_list)
        self.assertEqual(6, len(event_trait_list))

        event_trait1 = event_trait_list[0][0]
        event_trait2 = event_trait_list[3][0]

        # check an individual user entry
        self.assertEqual(('6834861c-ccb3-4c6f-ac00-fe8fe1ad4ed4',
                          'image.create',
                          '2014-09-29T08:19:45.556301',
                          event_trait1),
                         event_list[0])

        self.assertEqual(('3676d6d4-5c65-4442-9eda-b78d750ea91f',
                          'compute.instance.update',
                          '2014-09-30T04:54:45.395522',
                          event_trait2),
                         event_list[1])
