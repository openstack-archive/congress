# Copyright (c) 2019 VMware, Inc. All rights reserved.
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

import uuid

import mock

from congress.datasources import datasource_driver
from congress.datasources.json_ingester import json_ingester
from congress import exception
from congress.tests import base


class TestJsonIngester(base.TestCase):

    @mock.patch('congress.datasources.datasource_utils.get_keystone_session')
    @mock.patch.object(
        datasource_driver.PollingDataSourceDriver, '_init_end_start_poll')
    @mock.patch.object(
        json_ingester.JsonIngester, '_create_schema_and_tables')
    def setUp(self, _create_schema_and_tables, _init_end_start_poll,
              get_keystone_session):
        super(TestJsonIngester, self).setUp()

        self.test_config = {
            "api_endpoint": "http://127.0.0.1/compute/v2.1/",
            "tables": {
                "flavors": {
                    "poll": {
                        "api_method": "get",
                        "api_path": "flavors/detail",
                        "jsonpath": "$.flavors[:]"
                    }
                },
                "servers": {
                    "poll": {
                        "api_method": "get",
                        "api_path": "servers/detail",
                        "jsonpath": "$.servers[:]"
                    }
                },
                "alarms": {
                    "webhook": {
                        "record_jsonpath": "$.payload",
                        "id_jsonpath": "$.id"
                    }
                }
            },
            "authentication": {
                "type": "keystone",
                "config": {
                    "username": "admin",
                    "project_name": "admin",
                    "password": "password",
                    "auth_url": "http://127.0.0.1/identity"
                }
            },
            "poll_interval": 1,
            "name": "nova"
        }

        from congress.datasources.json_ingester import exec_api
        # exec_manager = exec_api.ExecApiManager([])
        exec_manager_mock = mock.Mock(spec=exec_api.ExecApiManager)
        self.test_driver = json_ingester.JsonIngester(
            self.test_config['name'], self.test_config, exec_manager_mock)

    def test_invalid_config_poll_plus_webhook(self):
        invalid_config = self.test_config
        invalid_config['tables']['servers']['webhook'] = {
            "record_jsonpath": "$.payload",
            "id_jsonpath": "$.id"}
        self.assertRaises(
            exception.BadConfig, json_ingester.JsonIngester,
            invalid_config['name'], invalid_config, None)

    @mock.patch.object(json_ingester.JsonIngester, '_update_table')
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

    @mock.patch.object(json_ingester.JsonIngester, '_webhook_update_table')
    def test_json_ingester_webhook_handler(self, _webhook_update_table):
        test_body = {"payload": {"id": 42, "other": "stuff"}}
        self.test_driver.json_ingester_webhook_handler('alarms', test_body)
        _webhook_update_table.assert_called_once_with(
            'alarms', key=42, data=test_body['payload'])
        (self.test_driver.exec_manager.
         evaluate_and_execute_actions.assert_called_once())

    @mock.patch.object(json_ingester.JsonIngester, '_webhook_update_table')
    def test_json_ingester_webhook_handler_non_primitive_key(
            self, _webhook_update_table):
        test_key = {1: [2, 3], "2": "4"}
        test_body = {"payload": {"id": test_key, "other": "stuff"}}
        self.test_driver.json_ingester_webhook_handler('alarms', test_body)
        _webhook_update_table.assert_called_once_with(
            'alarms', key=test_key, data=test_body['payload'])
        (self.test_driver.exec_manager.
         evaluate_and_execute_actions.assert_called_once())

    @mock.patch.object(json_ingester.JsonIngester, '_webhook_update_table')
    def test_json_ingester_webhook_handler_missing_payload(
            self, _webhook_update_table):
        test_body = {"not_payload": {"id": 42, "other": "stuff"}}
        self.assertRaises(
            exception.BadRequest,
            self.test_driver.json_ingester_webhook_handler,
            'alarms', test_body)

    @mock.patch.object(json_ingester.JsonIngester, '_webhook_update_table')
    def test_json_ingester_webhook_handler_missing_id(
            self, _webhook_update_table):
        test_body = {"payload": {"not_id": 42, "other": "stuff"}}
        self.assertRaises(
            exception.BadRequest,
            self.test_driver.json_ingester_webhook_handler,
            'alarms', test_body)

    def test_json_ingester_webhook_key_too_long(self):
        test_body = {"payload": {"id": "X"*2713, "other": "stuff"}}
        self.assertRaises(
            exception.BadRequest,
            self.test_driver.json_ingester_webhook_handler,
            'alarms', test_body)

    def test_json_ingester_webhook_nonexistent_table(self):
        test_body = {"payload": {"id": 42, "other": "stuff"}}
        self.assertRaises(
            exception.NotFound,
            self.test_driver.json_ingester_webhook_handler,
            'no_such_table', test_body)

    def test_json_ingester_webhook_non_webhook_table(self):
        test_body = {"payload": {"id": 42, "other": "stuff"}}
        self.assertRaises(
            exception.NotFound,
            self.test_driver.json_ingester_webhook_handler,
            'servers', test_body)


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
