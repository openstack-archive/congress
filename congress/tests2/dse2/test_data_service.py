# Copyright (c) 2016 VMware, Inc. All rights reserved.
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

import json
import mock
import time

from congress.dse2.data_service import DataService
from congress.dse2.data_service import DataServiceInfo
from congress.tests import base


class TestDataServiceInfo(base.TestCase):
    TESTDATA = {'service_id': 'test-service-id', 'node_id': 'test-node-id',
                'published_tables': ['t1', 't2'],
                'subscribed_tables': ['s1', 's2', 's3'],
                'rpc_endpoints_info': ['call1', 'call2']}

    def test_from_json(self):
        s = DataServiceInfo.from_json(json.dumps(self.TESTDATA))
        for a in DataServiceInfo.MARSHALL_ATTRS:
            self.assertEqual(getattr(s, a), self.TESTDATA[a],
                             "Attr '%s' set properly in from_dict" % a)
        self.assertRaises(KeyError, DataServiceInfo.from_json,
                          '{"bad_attr": 123}')

    def test_to_json(self):
        s = DataServiceInfo(**self.TESTDATA)
        self.assertEqual(json.loads(s.to_json()), self.TESTDATA,
                         'JSON representation matches constructed data')
        s.last_hb_time = time.time()
        self.assertEqual(json.loads(s.to_json()), self.TESTDATA,
                         'JSON representation ignores last_hb_time')

    def test_from_dict(self):
        s = DataServiceInfo.from_dict(self.TESTDATA)
        for a in DataServiceInfo.MARSHALL_ATTRS:
            self.assertEqual(getattr(s, a), self.TESTDATA[a],
                             "Attr '%s' set properly in from_dict" % a)
        self.assertRaises(KeyError, DataServiceInfo.from_dict,
                          {'bad_attr': 123})

    def test_to_dict(self):
        s = DataServiceInfo(**self.TESTDATA)
        self.assertEqual(s.to_dict(), self.TESTDATA,
                         'dict representation matches constructed data')
        s.last_hb_time = time.time()
        self.assertEqual(s.to_dict(), self.TESTDATA,
                         'dict representation ignores last_hb_time')


class TestDataService(base.TestCase):

    def test_info(self):
        ds = DataService("svc1")
        node = mock.MagicMock()
        node.node_id = 'testnode'
        ds.node = node
        info = ds.info
        self.assertEqual(info.service_id, 'svc1')
        self.assertEqual(info.node_id, 'testnode')
        self.assertEqual(info.published_tables, [])
        self.assertEqual(info.subscribed_tables, [])
        self.assertEqual(info.rpc_endpoints_info, [])

    def test_start_stop(self):
        ds = DataService("svc1")
        ds.node = mock.MagicMock()
        ds._rpc_server = mock.MagicMock()
        self.assertEqual(ds._running, False,
                         "Newly created service is marked as not running")
        ds.start()
        self.assertEqual(ds._running, True,
                         "Started service is marked as running")
        ds.stop()
        self.assertEqual(ds._running, False,
                         "Stopped service is marked as not running")


# TODO(pballand): replace with congress unit test framework when convenient
if __name__ == '__main__':
    import unittest
    unittest.main(verbosity=2)
