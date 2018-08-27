# Copyright (c) 2018 NEC, Inc. All rights reserved.
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

import copy
import mock
import sys
import time

sys.modules['monascaclient.client'] = mock.Mock()
sys.modules['monascaclient'] = mock.Mock()

from congress.datasources import monasca_driver
from congress.tests import base
from congress.tests import helper


METRICS = "alarms.metrics"
DIMENSIONS = METRICS + ".dimensions"
NOTIFICATIONS = "alarm_notification"


class TestMonascaDriver(base.TestCase):

    def setUp(self):
        super(TestMonascaDriver, self).setUp()
        self.keystone_client_p = mock.patch(
            "keystoneclient.v3.client.Client")
        self.keystone_client_p.start()
        self.monasca_client_p = mock.patch("monascaclient.client.Client")
        self.monasca_client_p.start()

        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        args['endpoint'] = 'http://localhost:8070/v2.0'
        self.driver = monasca_driver.MonascaDriver(args=args)

        self.mock_metrics = {"links": [{
            "rel": "self",
            "href": "http://192.168.10.4:8070/v2.0/metrics"}],
            "elements": [{
                "id": "0",
                "name": "mem.used_buffers",
                "dimensions": {
                    "component": "monasca-persister",
                    "service": "monitoring",
                    "hostname": "ceilosca",
                    "url": "http://localhost:8091/metrics"}
            }]}

        self.mock_statistics = {"links": [{
            "rel": "self",
            "href": "http://192.168.10.4:8070/v2.0/metrics/statistics"}],
            "elements": [{
                "id": "2015-11-30T18:00:00Z",
                "name": "mem.used_buffers",
                "dimensions": {},
                "columns": ["timestamp", "avg"],
                "statistics": [
                    ["2015-11-24T00:00:00Z", 56],
                    ["2015-11-24T06:00:00Z", 46],
                    ["2015-11-24T12:00:00Z", 70],
                    ["2015-11-24T18:00:00Z", 60]]
            }]}

    def test_statistics_update_from_datasource(self):
        self.driver._translate_statistics(self.mock_statistics['elements'])
        stats_list = list(self.driver.state[monasca_driver.STATISTICS])
        stats_data_list = list(self.driver.state[monasca_driver.DATA])
        self.assertIsNotNone(stats_list)
        self.assertIsNotNone(stats_data_list)

        expected_stats = [
            ('mem.used_buffers', 'd1fea02438d17fb7446255573bf54d45')]
        self.assertEqual(expected_stats, stats_list)

        expected_stats_data = [
            ('d1fea02438d17fb7446255573bf54d45',
             "['2015-11-24T00:00:00Z', 56]"),
            ('d1fea02438d17fb7446255573bf54d45',
             "['2015-11-24T12:00:00Z', 70]"),
            ('d1fea02438d17fb7446255573bf54d45',
             "['2015-11-24T18:00:00Z', 60]"),
            ('d1fea02438d17fb7446255573bf54d45',
             "['2015-11-24T06:00:00Z', 46]")]
        self.assertEqual(sorted(expected_stats_data), sorted(stats_data_list))

    def test_metrics_update_from_datasource(self):
        with mock.patch.object(self.driver.monasca.metrics, "list") as metrics:
            metrics.return_value = self.mock_metrics['elements']
            self.driver.update_from_datasource()

        expected = {
            'dimensions': set([
                ('e138b5d90a4265c7525f480dd988210b',
                    'component', 'monasca-persister'),
                ('e138b5d90a4265c7525f480dd988210b',
                    'service', 'monitoring'),
                ('e138b5d90a4265c7525f480dd988210b',
                    'hostname', 'ceilosca'),
                ('e138b5d90a4265c7525f480dd988210b',
                    'url', 'http://localhost:8091/metrics')]),
            'metrics': set([
                ('0', 'mem.used_buffers',
                    'e138b5d90a4265c7525f480dd988210b')]),
            'statistics': set([]),
            'statistics.data': set([])
            }
        self.assertEqual(expected, self.driver.state)

    def test_execute(self):
        class MonascaClient(object):
            def __init__(self):
                self.testkey = None

            def getStatistics(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        monasca_client = MonascaClient()
        self.driver.monasca = monasca_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('getStatistics', api_args)

        self.assertEqual(expected_ans, monasca_client.testkey)


class TestMonascaWebhookDriver(base.TestCase):

    def setUp(self):
        super(TestMonascaWebhookDriver, self).setUp()
        self.monasca = monasca_driver.MonascaWebhookDriver('test-monasca')

    @mock.patch.object(monasca_driver.MonascaWebhookDriver, 'publish')
    def test_monasca_webhook_alarm(self, mocked_publish):
        test_alarm = {
            'metrics': [
                {u'dimensions': {u'hostname': u'openstack-13.local.lan',
                                 u'service': u'monitoring'},
                 u'id': None,
                 u'name': u'load.avg_1_min'}],
            'alarm_id': u'3beb4934-053d-4f8f-9704-273bffc2441b',
            'state': u'ALARM',
            'alarm_timestamp': 1531821822,
            'tenant_id': u'3661888238874df098988deab07c599d',
            'old_state': u'UNDETERMINED',
            'alarm_description': u'',
            'message': u'Thresholds were exceeded for the sub-alarms',
            'alarm_definition_id': u'8e5d033f-28cc-459f-91d4-813307e4ca8a',
            'alarm_name': u'alarmPerHost23'}
        self.monasca._webhook_handler(test_alarm)

        expected_alarm_notification = set(
            [(u'3beb4934-053d-4f8f-9704-273bffc2441b',
              u'8e5d033f-28cc-459f-91d4-813307e4ca8a',
              u'alarmPerHost23',
              u'',
              1531821822,
              u'ALARM',
              u'UNDETERMINED',
              u'Thresholds were exceeded for the sub-alarms',
              u'3661888238874df098988deab07c599d')])
        self.assertEqual(self.monasca.state[NOTIFICATIONS],
                         expected_alarm_notification)

        dimension_id = (copy.deepcopy(self.monasca.state[METRICS])).pop()[3]
        expected_metrics = set([(u'3beb4934-053d-4f8f-9704-273bffc2441b',
                                 None,
                                 u'load.avg_1_min',
                                 dimension_id)])
        self.assertEqual(self.monasca.state[METRICS], expected_metrics)

        expected_dimensions = set(
            [(dimension_id, 'hostname', 'openstack-13.local.lan'),
             (dimension_id, 'service', 'monitoring')])
        self.assertEqual(self.monasca.state[DIMENSIONS],
                         expected_dimensions)

        # generate another webhook notification with same alarm_id to check
        # if it gets updated
        test_alarm['metrics'][0]['name'] = 'modified_name'
        test_alarm['state'] = 'OK'
        test_alarm['old_state'] = 'ALARM'
        self.monasca._webhook_handler(test_alarm)
        expected_alarm_notification = set(
            [(u'3beb4934-053d-4f8f-9704-273bffc2441b',
              u'8e5d033f-28cc-459f-91d4-813307e4ca8a',
              u'alarmPerHost23',
              u'',
              1531821822,
              u'OK',
              u'ALARM',
              u'Thresholds were exceeded for the sub-alarms',
              u'3661888238874df098988deab07c599d')])
        self.assertEqual(self.monasca.state[NOTIFICATIONS],
                         expected_alarm_notification)
        # to check that same alarm is updated rather than creating a new one
        self.assertEqual(len(self.monasca.state[NOTIFICATIONS]), 1)

        expected_metrics = set([(u'3beb4934-053d-4f8f-9704-273bffc2441b',
                                 None,
                                 u'modified_name',
                                 dimension_id)])
        self.assertEqual(self.monasca.state[METRICS], expected_metrics)
        # to check that same alarm metric is updated rather than creating new
        self.assertEqual(len(self.monasca.state[METRICS]), 1)

    @mock.patch.object(monasca_driver.MonascaWebhookDriver, 'publish')
    def test_webhook_alarm_cleanup(self, mocked_publish):
        self.monasca = monasca_driver.MonascaWebhookDriver(
            'test-monasca',
            args={'hours_to_keep_alarm': 1 / 3600})  # set to 1 sec for test

        test_alarm = {
            'metrics': [
                {u'dimensions': {u'hostname': u'openstack-13.local.lan',
                                 u'service': u'monitoring'},
                 u'id': None,
                 u'name': u'load.avg_1_min'}],
            'alarm_id': u'3beb4934-053d-4f8f-9704-273bffc2441b',
            'state': u'ALARM',
            'alarm_timestamp': 1531821822,
            'tenant_id': u'3661888238874df098988deab07c599d',
            'old_state': u'UNDETERMINED',
            'alarm_description': u'',
            'message': u'Thresholds were exceeded for the sub-alarms',
            'alarm_definition_id': u'8e5d033f-28cc-459f-91d4-813307e4ca8a',
            'alarm_name': u'alarmPerHost23'}

        self.monasca._webhook_handler(test_alarm)

        self.assertEqual(1, len(self.monasca.state[NOTIFICATIONS]))
        self.assertEqual(1, len(self.monasca.state[METRICS]))
        time.sleep(3)
        self.assertEqual(0, len(self.monasca.state[NOTIFICATIONS]))
        self.assertEqual(0, len(self.monasca.state[METRICS]))
