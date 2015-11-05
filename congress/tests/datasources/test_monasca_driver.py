# Copyright (c) 2015 Cisco, Inc. All rights reserved.
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
import mock
import sys

sys.modules['monascaclient.client'] = mock.Mock()
sys.modules['monascaclient'] = mock.Mock()

from congress.datasources import monasca_driver
from congress.tests import base
from congress.tests import helper


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
        args['client'] = mock.MagicMock()
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
        stats_list = list(self.driver.state[self.driver.STATISTICS])
        stats_data_list = list(self.driver.state[self.driver.DATA])
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
