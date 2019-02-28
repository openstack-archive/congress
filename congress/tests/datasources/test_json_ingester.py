# Copyright (c) 2019 VMware Inc All rights reserved.
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

import mock
import uuid

from congress.datasources import datasource_driver
from congress.datasources import json_ingester
from congress.tests import base


class TestPollingJsonIngester(base.TestCase):

    @mock.patch('congress.datasources.datasource_utils.get_keystone_session')
    @mock.patch.object(
        datasource_driver.PollingDataSourceDriver, '_init_end_start_poll')
    @mock.patch.object(
        json_ingester.PollingJsonIngester, '_create_schema_and_tables')
    def setUp(self, _create_schema_and_tables, _init_end_start_poll,
              get_keystone_session):
        super(TestPollingJsonIngester, self).setUp()

        test_config = {
            "api_endpoint": "http://127.0.0.1/compute/v2.1/",
            "tables": {
                "flavors": {
                    "api_verb": "get",
                    "api_path": "flavors/detail",
                    "jsonpath": "$.flavors[:]"
                },
                "servers": {
                    "api_verb": "get",
                    "api_path": "servers/detail",
                    "jsonpath": "$.servers[:]"
                }
            },
            "authentication": {
                "username": "admin",
                "type": "keystone",
                "project_name": "admin",
                "password": "password",
                "auth_url": "http://127.0.0.1/identity"
            },
            "poll": 1,
            "name": "nova"
        }

        self.test_driver = json_ingester.PollingJsonIngester(
            test_config['name'], test_config)

    @mock.patch.object(json_ingester.PollingJsonIngester, '_update_table')
    def test_poll(self, _update_table):
        mock_api_result = {
            "servers": [
                {"server": 1},
                {"server": 2},
                {"server": 3}
            ],
            "flavors": [],
            "servers_links": [
                {
                    "href": "blah",
                    "rel": "next"
                }
            ]
        }
        servers_api_result_str_set = set(
            ['{"server": 1}', '{"server": 2}', '{"server": 3}'])
        self.test_driver._session.get.return_value.json.return_value = \
            mock_api_result

        # test initial poll
        self.test_driver.poll()
        self.assertEqual(_update_table.call_count, 2)
        _update_table.assert_any_call(
            'servers',
            new_data=servers_api_result_str_set,
            old_data=set([]), use_snapshot=True)
        _update_table.assert_any_call(
            'flavors', new_data=set([]), old_data=set([]), use_snapshot=True)

        _update_table.reset_mock()

        # test subsequent poll
        self.test_driver.poll()
        self.assertEqual(_update_table.call_count, 2)
        _update_table.assert_any_call(
            'servers',
            new_data=servers_api_result_str_set,
            old_data=servers_api_result_str_set, use_snapshot=False)
        _update_table.assert_any_call(
            'flavors', new_data=set([]), old_data=set([]), use_snapshot=False)


class TestKeyMap(base.TestCase):

    def setUp(self):
        super(TestKeyMap, self).setUp()
        self.key_map = json_ingester.KeyMap()

    def test_init(self):
        self.assertEqual(len(self.key_map), 0, 'key set not empty upon init')

    def test_add_then_remove(self):
        datum = str(uuid.uuid4())
        key_on_add = self.key_map.add_and_get_key(datum)
        self.assertEqual(len(self.key_map), 1)
        key_on_remove = self.key_map.remove_and_get_key(datum)
        self.assertEqual(len(self.key_map), 0)
        self.assertEqual(key_on_add, key_on_remove)

    def test_increment(self):
        datum1 = str(uuid.uuid4())
        datum2 = datum1 + 'diff'

        key1 = self.key_map.add_and_get_key(datum1)
        key2 = self.key_map.add_and_get_key(datum2)
        self.assertEqual(len(self.key_map), 2)
        self.assertEqual(key2, key1 + 1)

    def test_reclaim(self):
        datum1 = str(uuid.uuid4())
        datum2 = datum1 + 'diff'
        datum3 = datum1 + 'diffdiff'

        key1 = self.key_map.add_and_get_key(datum1)
        self.key_map.add_and_get_key(datum2)
        self.key_map.remove_and_get_key(datum1)
        key3 = self.key_map.add_and_get_key(datum3)
        self.assertEqual(key1, key3)

    def test_repeat_add(self):
        datum = str(uuid.uuid4())
        key1 = self.key_map.add_and_get_key(datum)
        key2 = self.key_map.add_and_get_key(datum)
        self.assertEqual(len(self.key_map), 1)
        self.assertEqual(key1, key2)

    def test_remove_nonexistent(self):
        self.assertRaises(KeyError, self.key_map.remove_and_get_key, 'datum')
