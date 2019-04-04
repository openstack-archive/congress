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

import json

import eventlet
from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_log import log as logging
import psycopg2
import requests

from congress.datasources import datasource_utils
from congress.datasources.json_ingester import sql
from congress import exception


LOG = logging.getLogger(__name__)


class ExecApiManager(object):
    def __init__(self, configs):
        super(ExecApiManager, self).__init__()
        self._exec_api_sessions = {}
        self._exec_api_endpoints = {}
        # state tracking the most recent state consisting of the union
        # of all the rows from all the _exec_api tables
        # used to determine which rows are new
        self._last_exec_api_state = set([])

        for config in configs:
            # FIXME(json_ingester): validate config
            if config.get('allow_exec_api', False) is True:
                auth_config = config.get('authentication')
                if auth_config is None:
                    session = requests.Session()
                    session.headers.update(
                        config.get('api_default_headers', {}))
                else:
                    if auth_config['type'] == 'keystone':
                        session = datasource_utils.get_keystone_session(
                            config['authentication']['config'],
                            headers=config.get('api_default_headers', {}))
                    else:
                        LOG.error('authentication type %s not supported.',
                                  auth_config.get['type'])
                        raise exception.BadConfig(
                            'authentication type {} not '
                            'supported.'.auth_config['type'])

                name = config['name']
                self._exec_api_endpoints[name] = config['api_endpoint']
                self._exec_api_sessions[name] = session

    @lockutils.synchronized('congress_json_ingester_exec_api')
    def evaluate_and_execute_actions(self):
        # FIXME(json_ingester): retry
        new_exec_api_state = self._read_all_execute_tables()

        new_exec_api_rows = new_exec_api_state - self._last_exec_api_state
        LOG.debug('New exec_api rows %s', new_exec_api_rows)
        self._execute_exec_api_rows(new_exec_api_rows)
        self._last_exec_api_state = new_exec_api_state

    def _execute_exec_api_rows(self, rows):
        def exec_api(session, kwargs):
            LOG.info("Making API request %s.", kwargs)
            try:
                session.request(**kwargs)
            except Exception:
                LOG.exception('Exception in making API request %s.', kwargs)

        for row in rows:
            (endpoint, path, method, body, parameters, headers) = row
            if endpoint in self._exec_api_endpoints:
                kwargs = {
                    'endpoint_override': self._exec_api_endpoints[endpoint],
                    'url': path,
                    'method': method.upper(),
                    'connect_retries': 10,
                    'status_code_retries': 10}
                body = json.loads(body)
                if body is not None:
                    kwargs['json'] = body
                parameters = json.loads(parameters)
                if parameters is not None:
                    kwargs['params'] = parameters
                headers = json.loads(headers)
                if headers is not None:
                    kwargs['headers'] = headers

                if cfg.CONF.enable_execute_action:
                    eventlet.spawn_n(
                        exec_api, self._exec_api_sessions[endpoint], kwargs)
                else:
                    LOG.info("Simulating API request %s", kwargs)
            else:
                LOG.warning(
                    'No configured API endpoint with name %s. '
                    'Skipping the API request: '
                    '(endpoint, path, method, body, parameters, headers) '
                    '= %s.', endpoint, row)
        eventlet.sleep(0)  # defer to greenthreads running api requests

    @staticmethod
    def _read_all_execute_tables():
        def json_rows_to_str_rows(json_rows):
            # FIXME(json_ingester): validate; log and drop invalid rows
            return [(endpoint, path, method, json.dumps(body, sort_keys=True),
                     json.dumps(parameters, sort_keys=True),
                     json.dumps(headers, sort_keys=True)) for
                    (endpoint, path, method, body, parameters, headers)
                    in json_rows]

        FIND_ALL_EXEC_VIEWS = """
            SELECT table_schema, table_name FROM information_schema.tables
            WHERE table_schema NOT LIKE 'pg\_%'
            AND table_schema <> 'information_schema'
            AND table_name LIKE '\_exec_api';"""
        READ_EXEC_VIEW = """
            SELECT endpoint, path, method, body, parameters, headers
            FROM {}.{};"""
        conn = None
        try:
            conn = psycopg2.connect(cfg.CONF.json_ingester.db_connection)
            # repeatable read to make sure all the _exec_api rows from all
            # schemas are obtained at the same snapshot
            conn.set_session(
                isolation_level=psycopg2.extensions.
                ISOLATION_LEVEL_REPEATABLE_READ,
                readonly=True, autocommit=False)
            cur = conn.cursor()
            # find all _exec_api tables
            cur.execute(sql.SQL(FIND_ALL_EXEC_VIEWS))
            all_exec_api_tables = cur.fetchall()

            # read each _exec_api_table
            all_exec_api_rows = set([])
            for (table_schema, table_name) in all_exec_api_tables:
                try:
                    cur.execute(sql.SQL(READ_EXEC_VIEW).format(
                        sql.Identifier(table_schema),
                        sql.Identifier(table_name)))
                    all_rows = cur.fetchall()
                    all_exec_api_rows.update(
                        json_rows_to_str_rows(all_rows))
                except psycopg2.ProgrammingError:
                    LOG.warning('The "%s" table in the "%s" schema does not '
                                'have the right columns for API execution. '
                                'Its content is ignored for the purpose of '
                                'API execution. Please check and correct the '
                                'view definition.',
                                table_name, table_schema)
            conn.commit()
            cur.close()
            return all_exec_api_rows
        except (Exception, psycopg2.Error):
            LOG.exception("Error reading from DB")
            raise
        finally:
            if conn is not None:
                conn.close()
