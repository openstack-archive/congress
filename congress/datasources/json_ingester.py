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

import datetime
import json
import sys

from jsonpath_rw import parser
from oslo_config import cfg
from oslo_log import log as logging
import psycopg2
from psycopg2 import sql

from congress.api import base as api_base
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils
from congress import exception


LOG = logging.getLogger(__name__)


def _get_config():
    return {'host': cfg.CONF.json_ingester.postgres_host,
            'database': cfg.CONF.json_ingester.postgres_database,
            'user': cfg.CONF.json_ingester.postgres_user,
            'password': cfg.CONF.json_ingester.postgres_password}


class PollingJsonIngester(datasource_driver.PollingDataSourceDriver):
    def __init__(self, name, config):
        # use prefix to avoid service_id clash with regular data sources
        super(PollingJsonIngester, self).__init__(
            api_base.JSON_DS_SERVICE_PREFIX + name)
        self.name = name  # set name back to one without prefix for use here
        self._config = config
        self._create_schema_and_tables()
        self.poll_time = self._config.get('poll', 60)
        self._setup_table_key_sets()
        self._api_endpoint = self._config['api_endpoint']
        self._initialize_session()
        self._initialize_update_methods()
        self._init_end_start_poll()

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

        self._update_table(table, new_data=data,
                           old_data=self.prior_state.get(table, set([])),
                           use_snapshot=use_snapshot)

    def _create_schema_and_tables(self):
        params = _get_config()

        create_schema_statement = """CREATE SCHEMA IF NOT EXISTS {};"""
        create_table_statement = """
            CREATE TABLE IF NOT EXISTS {}.{}
            (d jsonb, _key bigint, primary key (_key));"""
        # Note: because postgres cannot directly use the jsonb column d as key,
        #       the _key column is added as key in order to support performant
        #       delete of specific rows in delta update to the db table

        create_index_statement = \
            """CREATE INDEX on {}.{} USING GIN (d);"""
        conn = None
        try:
            conn = psycopg2.connect(**params)
            cur = conn.cursor()
            # create schema
            cur.execute(
                sql.SQL(create_schema_statement).format(
                    sql.Identifier(self.name)))
            for table_name in self._config['tables']:
                # create table
                cur.execute(sql.SQL(create_table_statement).format(
                    sql.Identifier(self.name), sql.Identifier(table_name)))
                cur.execute(sql.SQL(create_index_statement).format(
                    sql.Identifier(self.name), sql.Identifier(table_name)))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError):
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

        # return immediately if no change to update
        if new_data == old_data:
            return

        params = _get_config()

        insert_statement = """INSERT INTO {}.{}
                 VALUES(%s, %s);"""
        delete_all_statement = """DELETE FROM {}.{};"""
        delete_tuple_statement = """
            DELETE FROM {}.{} WHERE _key == %s;"""
        conn = None
        try:
            conn = psycopg2.connect(**params)
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
                        sql.Identifier(table_name),
                        (self.key_sets[table_name].remove_and_get_key(d),)))
            # insert new data into table
            for d in to_insert:
                cur.execute(sql.SQL(insert_statement).format(
                    sql.Identifier(self.name),
                    sql.Identifier(table_name)),
                    (d, self.key_sets[table_name].add_and_get_key(d)))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError):
            LOG.exception("Error writing to DB")
            # makes the next update use snapshot
            self._clear_table_state(table_name)
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
        self._session = datasource_utils.get_keystone_session(
            self._config['authentication'])

    def _initialize_update_methods(self):
        for table_name in self._config['tables']:
            table_info = self._config['tables'][table_name]

            # Note: using default parameters to get early-binding of variables
            # in closure
            def update_method(table_name=table_name, table_info=table_info):
                full_path = self._api_endpoint.rstrip('/') + '/' + table_info[
                    'api_path'].lstrip('/')
                result = self._session.get(full_path).json()
                # FIXME: generalize to other verbs?

                jsonpath_expr = parser.parse(table_info['jsonpath'])
                ingest_data = [match.value for match in
                               jsonpath_expr.find(result)]
                self.state[table_name] = set(
                    [json.dumps(item, sort_keys=True) for item in ingest_data])

            self.add_update_method(update_method, table_name)

    def update_from_datasource(self):
        for table in self._config['tables']:
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
            for tablename in self.state:
                use_snapshot = tablename not in self.prior_state
                # Note(thread-safety): blocking call[
                self.publish(tablename, self.state[tablename],
                             use_snapshot=use_snapshot)
        except Exception as e:
            self.last_error = e
            LOG.exception("Datasource driver raised exception")

        self.last_updated_time = datetime.datetime.now()
        self.number_of_updates += 1
        LOG.info("%s:: finished polling", self.name)

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
