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

import mock

from congress.datasources.json_ingester import exec_api
from congress.tests import base


def mock_spawn_execute(func, *args, **kwargs):
    return func(*args, **kwargs)


class TestExecApiManager(base.TestCase):

    @mock.patch('congress.datasources.datasource_utils.get_keystone_session')
    def setUp(self, get_keystone_session):
        super(TestExecApiManager, self).setUp()

        get_keystone_session.side_effect = [
            mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock(), mock.Mock()]

        self.test_configs = [
            {
                "api_endpoint": "test1/url",
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
                        "auth_url": "http://127.0.0.1/identity"}
                },
                "poll_interval": 1,
                "name": "test1"
            },
            {
                "allow_exec_api": True,
                "api_endpoint": "test2/url",
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
                        "auth_url": "http://127.0.0.1/identity"}
                },
                "poll_interval": 1,
                "name": "test2"
            },
            {
                "allow_exec_api": True,
                "api_endpoint": "test3/url",
                "authentication": {
                    "type": "keystone",
                    "config": {
                        "username": "admin",
                        "project_name": "admin",
                        "password": "password",
                        "auth_url": "http://127.0.0.1/identity"}
                },
                "name": "test3"
            }
        ]

        self.test_exec_mgr = exec_api.ExecApiManager(self.test_configs)

    def test_init(self):
        # 'test1' ignored because no "allow_exec_api": True
        self.assertEqual(set(self.test_exec_mgr._exec_api_sessions.keys()),
                         set(['test2', 'test3']))
        self.assertEqual(set(self.test_exec_mgr._exec_api_endpoints.keys()),
                         set(['test2', 'test3']))

    def test_evaluate_and_execute_actions(self):
        test_rows1 = set([1, 2, 3])
        test_rows2 = set([2, 3, 4])

        self.test_exec_mgr._read_all_execute_tables = mock.Mock(
            spec_set=[], return_value=test_rows1)
        self.test_exec_mgr._execute_exec_api_rows = mock.Mock(spec_set=[])

        self.assertEqual(self.test_exec_mgr._last_exec_api_state, set([]))
        self.test_exec_mgr.evaluate_and_execute_actions()

        self.assertEqual(self.test_exec_mgr._last_exec_api_state, test_rows1)
        self.test_exec_mgr._read_all_execute_tables.assert_called_once()
        self.test_exec_mgr._execute_exec_api_rows.assert_called_once_with(
            test_rows1)

        self.test_exec_mgr._read_all_execute_tables = mock.Mock(
            spec_set=[], return_value=test_rows2)
        self.test_exec_mgr._execute_exec_api_rows = mock.Mock(spec_set=[])

        self.test_exec_mgr.evaluate_and_execute_actions()
        self.assertEqual(self.test_exec_mgr._last_exec_api_state, test_rows2)
        self.test_exec_mgr._read_all_execute_tables.assert_called_once()
        self.test_exec_mgr._execute_exec_api_rows.assert_called_once_with(
            test_rows2 - test_rows1)

    @mock.patch('eventlet.spawn_n', side_effect=mock_spawn_execute)
    def test_execute_exec_api_rows(self, mock_spawn):
        test_row1 = ('test1', 'path1', 'method1', '["body1"]', '["params1"]',
                     '["headers1"]')
        test_row2a = ('test2', 'path2a', 'method2a', '["body2a"]',
                      '["params2a"]', '["headers2a"]')
        test_row2b = ('test2', 'path2b', 'method2b', '["body2b"]',
                      '["params2b"]', '["headers2b"]')
        test_row3 = ('test3', 'path3', 'method3', '["body3"]', '["params3"]',
                     '["headers3"]')

        self.test_exec_mgr._execute_exec_api_rows(
            [test_row1, test_row2a, test_row3, test_row2b])
        self.assertEqual(
            self.test_exec_mgr._exec_api_sessions['test2'].request.call_count,
            2)
        self.test_exec_mgr._exec_api_sessions[
            'test2'].request.assert_any_call(
            endpoint_override='test2/url', url='path2a', method='METHOD2A',
            json=[u'body2a'], params=[u'params2a'], headers=[u'headers2a'],
            connect_retries=10, status_code_retries=10)
        self.test_exec_mgr._exec_api_sessions[
            'test2'].request.assert_any_call(
            endpoint_override='test2/url', url='path2b', method='METHOD2B',
            json=[u'body2b'], params=[u'params2b'], headers=[u'headers2b'],
            connect_retries=10, status_code_retries=10)
        self.test_exec_mgr._exec_api_sessions[
            'test3'].request.assert_called_once_with(
            endpoint_override='test3/url', url='path3', method='METHOD3',
            json=[u'body3'], params=[u'params3'], headers=[u'headers3'],
            connect_retries=10, status_code_retries=10)
