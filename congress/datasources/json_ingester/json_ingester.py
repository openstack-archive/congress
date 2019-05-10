# Copyright (c) 2018, 2019 VMware, Inc. All rights reserved.
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

import datetime
import json
import sys

from jsonpath_rw import parser
from oslo_config import cfg
from oslo_log import log as logging
import psycopg2
import requests

from congress.api import base as api_base
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils
from congress.datasources.json_ingester import sql
from congress.dse2 import data_service
from congress import exception


LOG = logging.getLogger(__name__)


class JsonIngester(datasource_driver.PollingDataSourceDriver):

    def __init__(self, name, config, exec_manager):

        def validate_config(config):
            # FIXME: use json schema to validate config
            config_tables = config['tables']
            poll_tables = [table for table in config_tables
                           if 'poll' in config_tables[table]]
            if len(poll_tables) > 0:
                # FIXME: when polling table exists, require configs:
                # api_endpoint, authentication
                pass
            for table_name in config_tables:
                if ('poll' in config_tables[table_name]
                        and 'webhook' in config_tables[table_name]):
                    raise exception.BadConfig(
                        'Table ({}) cannot be configured for '
                        'both poll and webhook.'.format(table_name))

        # use prefix to avoid service_id clash with regular data sources
        super(JsonIngester, self).__init__(
            api_base.JSON_DS_SERVICE_PREFIX + name)
        self.exec_manager = exec_manager  # ref to global mgr for api exec
        self.type = 'json_ingester'
        self.name = name  # set name back to one without prefix for use here
        if 'tables' not in config:
            # config w/o table used to define exec_api endpoint
            # in this case, no need to create datasource service
            return

        validate_config(config)
        self._config = config
        self._create_schema_and_tables()
        self.poll_time = self._config.get('poll_interval', 60)
        self._setup_table_key_sets()
        self._api_endpoint = self._config.get('api_endpoint')
        self._initialize_session()
        self._initialize_update_methods()
        if len(self.update_methods) > 0:
            self._init_end_start_poll()
        else:
            self.initialized = True

        # For DSE2.  Must go after __init__
        if hasattr(self, 'add_rpc_endpoint'):
            self.add_rpc_endpoint(JsonIngesterEndpoints(self))

    def _setup_table_key_sets(self):
        # because postgres cannot directly use the jsonb column d as key,
        # the _key column is added as key in order to support performant
        # delete of specific rows in delta update to the db table
        # for each table, maintain in memory an association between the json
        # data and a unique key. The association is maintained using the
        # KeyMap class
        # Note: The key may change from session to session, which does not
        # cause a problem in this case because the db tables
        # (along with old keys) are cleared each time congress starts

        # { table_name -> KeyMap object}
        self.key_sets = {}

        for table_name in self._config['tables']:
            self.key_sets[table_name] = KeyMap()

    def _clear_table_state(self, table_name):
        del self.state[table_name]
        self.key_sets[table_name].clear()

    def publish(self, table, data, use_snapshot=False):
        LOG.debug('JSON Ingester "%s" publishing table "%s"', self.name, table)
        LOG.trace('publish(self=%s, table=%s, data=%s, use_snapshot=%s',
                  self, table, data, use_snapshot)

        return self._update_table(
            table, new_data=data,
            old_data=self.prior_state.get(table, set([])),
            use_snapshot=use_snapshot)

    def _create_schema_and_tables(self):
        create_schema_statement = """CREATE SCHEMA IF NOT EXISTS {};"""
        create_table_statement = """
            CREATE TABLE IF NOT EXISTS {}.{}
            (d jsonb, _key text, primary key (_key));"""
        # Note: because postgres cannot directly use the jsonb column d as key,
        #       the _key column is added as key in order to support performant
        #       delete of specific rows in delta update to the db table

        create_index_statement = """
            CREATE INDEX IF NOT EXISTS {index} on {schema}.{table}
            USING GIN (d);"""
        drop_index_statement = """
            DROP INDEX IF EXISTS {schema}.{index};"""
        conn = None
        try:
            conn = psycopg2.connect(cfg.CONF.json_ingester.db_connection)
            conn.set_session(
                isolation_level=psycopg2.extensions.
                ISOLATION_LEVEL_READ_COMMITTED,
                readonly=False, autocommit=False)
            cur = conn.cursor()
            # create schema
            cur.execute(
                sql.SQL(create_schema_statement).format(
                    sql.Identifier(self.name)))
            for table_name in self._config['tables']:
                # create table
                cur.execute(sql.SQL(create_table_statement).format(
                    sql.Identifier(self.name), sql.Identifier(table_name)))
                if self._config['tables'][table_name].get('gin_index', True):
                    cur.execute(sql.SQL(create_index_statement).format(
                        schema=sql.Identifier(self.name),
                        table=sql.Identifier(table_name),
                        index=sql.Identifier(
                            '__{}_d_gin_idx'.format(table_name))))
                else:
                    cur.execute(sql.SQL(drop_index_statement).format(
                        schema=sql.Identifier(self.name),
                        index=sql.Identifier(
                            '__{}_d_gin_idx'.format(table_name))))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.Error):
            if 'table_name' in locals():
                LOG.exception("Error creating table %s in schema %s",
                              table_name, self.name)
            else:
                LOG.exception("Error creating schema %s", self.name)
            raise
        finally:
            if conn is not None:
                conn.close()

    def _update_table(
            self, table_name, new_data, old_data, use_snapshot):

        # return False immediately if no change to update
        if new_data == old_data:
            return False

        insert_statement = """INSERT INTO {}.{}
                 VALUES(%s, %s);"""
        delete_all_statement = """DELETE FROM {}.{};"""
        delete_tuple_statement = """
            DELETE FROM {}.{} WHERE _key = %s;"""
        conn = None
        try:
            conn = psycopg2.connect(cfg.CONF.json_ingester.db_connection)
            conn.set_session(
                isolation_level=psycopg2.extensions.
                ISOLATION_LEVEL_READ_COMMITTED,
                readonly=False, autocommit=False)
            cur = conn.cursor()
            if use_snapshot:
                to_insert = new_data
                # delete all existing data from table
                cur.execute(sql.SQL(delete_all_statement).format(
                    sql.Identifier(self.name), sql.Identifier(table_name)))
                self.key_sets[table_name].clear()
            else:
                to_insert = new_data - old_data
                to_delete = old_data - new_data
                # delete the appropriate rows from table
                for d in to_delete:
                    cur.execute(sql.SQL(delete_tuple_statement).format(
                        sql.Identifier(self.name),
                        sql.Identifier(table_name)),
                        (str(self.key_sets[table_name].remove_and_get_key(d)),)
                    )
            # insert new data into table
            for d in to_insert:
                cur.execute(sql.SQL(insert_statement).format(
                    sql.Identifier(self.name),
                    sql.Identifier(table_name)),
                    (d, str(self.key_sets[table_name].add_and_get_key(d))))
            conn.commit()
            cur.close()
            return True  # return True indicating change made
        except (Exception, psycopg2.Error):
            LOG.exception("Error writing to DB")
            # makes the next update use snapshot
            self._clear_table_state(table_name)
            return False  # return False indicating no change made (rollback)
        finally:
            if conn is not None:
                conn.close()

    def add_update_method(self, method, table_name):
        if table_name in self.update_methods:
            raise exception.Conflict('A method has already registered for '
                                     'the table %s.' %
                                     table_name)
        self.update_methods[table_name] = method

    def _initialize_session(self):
        auth_config = self._config.get('authentication')
        if auth_config is None:
            self._session = requests.Session()
            self._session.headers.update(
                self._config.get('api_default_headers', {}))
        else:
            if auth_config['type'] == 'keystone':
                self._session = datasource_utils.get_keystone_session(
                    self._config['authentication']['config'],
                    headers=self._config.get('api_default_headers', {}))
            else:
                LOG.error('authentication type %s not supported.',
                          auth_config.get['type'])
                raise exception.BadConfig(
                    'authentication type {} not supported.'.format(
                        auth_config['type']))

    def _initialize_update_methods(self):
        for table_name in self._config['tables']:
            if 'poll' in self._config['tables'][table_name]:
                table_info = self._config['tables'][table_name]['poll']

                # Note: using default parameters to get early-binding of
                # variables in closure
                def update_method(
                        table_name=table_name, table_info=table_info):
                    try:
                        full_path = self._api_endpoint.rstrip(
                            '/') + '/' + table_info['api_path'].lstrip('/')
                        result = self._session.get(full_path).json()
                        # FIXME: generalize to other verbs?

                        jsonpath_expr = parser.parse(table_info['jsonpath'])
                        ingest_data = [match.value for match in
                                       jsonpath_expr.find(result)]
                        self.state[table_name] = set(
                            [json.dumps(item, sort_keys=True)
                             for item in ingest_data])
                    except BaseException:
                        LOG.exception('Exception occurred while updating '
                                      'table %s.%s from: URL %s',
                                      self.name, table_name,
                                      full_path)

                self.add_update_method(update_method, table_name)

    def update_from_datasource(self):
        for table in self.update_methods:
            LOG.debug('update table %s.' % table)
            self.update_methods[table]()

    # Note(thread-safety): blocking function
    def poll(self):
        """Periodically called to update new info.

        Function called periodically to grab new information, compute
        deltas, and publish those deltas.
        """
        LOG.info("%s:: polling", self.name)
        self.prior_state = dict(self.state)  # copying self.state
        self.last_error = None  # non-None only when last poll errored
        try:
            self.update_from_datasource()  # sets self.state
            # publish those tables with polling update methods
            overall_change_made = False
            for tablename in self.update_methods:
                use_snapshot = tablename not in self.prior_state
                # Note(thread-safety): blocking call[
                this_table_change_made = self.publish(
                    tablename, self.state.get(tablename, set([])),
                    use_snapshot=use_snapshot)
                overall_change_made = (overall_change_made
                                       or this_table_change_made)
            if overall_change_made:
                self.exec_manager.evaluate_and_execute_actions()
        except Exception as e:
            self.last_error = e
            LOG.exception("Datasource driver raised exception")

        self.last_updated_time = datetime.datetime.now()
        self.number_of_updates += 1
        LOG.info("%s:: finished polling", self.name)

    def json_ingester_webhook_handler(self, table_name, body):

        def get_exactly_one_jsonpath_match(
                jsonpath, jsondata, custom_error_msg):
            jsonpath_expr = parser.parse(jsonpath)
            matches = jsonpath_expr.find(jsondata)
            if len(matches) != 1:
                raise exception.BadRequest(
                    custom_error_msg.format(jsonpath, jsondata))
            return matches[0].value

        try:
            webhook_config = self._config['tables'][table_name]['webhook']
        except KeyError:
            raise exception.NotFound(
                'In JSON Ingester: "{}", the table "{}" either does not exist '
                'or is not configured for webhook.'.format(
                    self.name, table_name))

        json_record = get_exactly_one_jsonpath_match(
            webhook_config['record_jsonpath'], body,
            'In identifying JSON record from webhook body, the configured '
            'jsonpath expression "{}" fails to obtain exactly one match on '
            'webhook body "{}".')
        json_id = get_exactly_one_jsonpath_match(
            webhook_config['id_jsonpath'], json_record,
            'In identifying ID from JSON record, the configured jsonpath '
            'expression "{}" fails to obtain exactly one match on JSON record'
            ' "{}".')
        self._webhook_update_table(table_name, key=json_id, data=json_record)
        self.exec_manager.evaluate_and_execute_actions()

    def _webhook_update_table(self, table_name, key, data):
        key_string = json.dumps(key, sort_keys=True)
        PGSQL_MAX_INDEXABLE_SIZE = 2712
        if len(key_string) > PGSQL_MAX_INDEXABLE_SIZE:
            raise exception.BadRequest(
                'The supplied key ({}) exceeds the max indexable size ({}) in '
                'PostgreSQL.'.format(key_string, PGSQL_MAX_INDEXABLE_SIZE))

        insert_statement = """INSERT INTO {}.{}
                 VALUES(%s, %s);"""
        delete_tuple_statement = """
            DELETE FROM {}.{} WHERE _key = %s;"""
        conn = None
        try:
            conn = psycopg2.connect(cfg.CONF.json_ingester.db_connection)
            conn.set_session(
                isolation_level=psycopg2.extensions.
                ISOLATION_LEVEL_READ_COMMITTED,
                readonly=False, autocommit=False)
            cur = conn.cursor()
            # delete the appropriate row from table
            cur.execute(sql.SQL(delete_tuple_statement).format(
                sql.Identifier(self.name),
                sql.Identifier(table_name)),
                (key_string,))
            # insert new row into table
            cur.execute(sql.SQL(insert_statement).format(
                sql.Identifier(self.name),
                sql.Identifier(table_name)),
                (json.dumps(data), key_string))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.Error):
            LOG.exception("Error writing to DB")
        finally:
            if conn is not None:
                conn.close()

    def validate_lazy_tables(self):
        '''override non-applicable parent method as no-op'''
        pass

    def initialize_translators(self):
        '''override non-applicable parent method as no-op'''
        pass

    def get_snapshot(self, table_name):
        raise NotImplementedError(
            'This method should not be called in PollingJsonIngester.')

    def get_row_data(self, table_id, *args, **kwargs):
        raise NotImplementedError(
            'This method should not be called in PollingJsonIngester.')

    def register_translator(self, translator):
        raise NotImplementedError(
            'This method should not be called in PollingJsonIngester.')

    def get_translator(self, translator_name):
        raise NotImplementedError(
            'This method should not be called in PollingJsonIngester.')

    def get_translators(self):
        raise NotImplementedError(
            'This method should not be called in PollingJsonIngester.')


class JsonIngesterEndpoints(data_service.DataServiceEndPoints):
    def __init__(self, service):
        super(JsonIngesterEndpoints, self).__init__(service)

    # Note (thread-safety): blocking function
    def json_ingester_webhook_handler(self, context, table_name, body):
        # Note (thread-safety): blocking call
        return self.service.json_ingester_webhook_handler(table_name, body)


class KeyMap(object):
    '''Map associating a unique integer key with each hashable object'''

    _PY_MIN_INT = -sys.maxsize - 1  # minimum primitive integer supported
    _PGSQL_MIN_BIGINT = -2**63  # minimum BIGINT supported in postgreSQL
    # reference: https://www.postgresql.org/docs/9.4/datatype-numeric.html

    def __init__(self):
        self._key_mapping = {}
        self._reclaimed_free_keys = set([])
        self._next_incremental_key = max(
            self._PY_MIN_INT, self._PGSQL_MIN_BIGINT)  # start from least

    def add_and_get_key(self, datum):
        '''Add a datum and return associated key'''
        if datum in self._key_mapping:
            return self._key_mapping[datum]
        else:
            try:
                next_key = self._reclaimed_free_keys.pop()
            except KeyError:
                next_key = self._next_incremental_key
                self._next_incremental_key += 1
            self._key_mapping[datum] = next_key
            return next_key

    def remove_and_get_key(self, datum):
        '''Remove a datum and return associated key'''
        key = self._key_mapping.pop(datum)
        self._reclaimed_free_keys.add(key)
        return key

    def clear(self):
        '''Remove all data and keys'''
        self.__init__()

    def __len__(self):
        return len(self._key_mapping)
