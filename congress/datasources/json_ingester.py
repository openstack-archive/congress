# Copyright (c) 2018 VMware, Inc. All rights reserved.
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
        self.config = config
        self._create_schema_and_tables()
        self.poll_time = self.config.get('poll', 60)
        self.api_endpoint = self.config['api_endpoint']
        self.initialize_session()
        self.initialize_update_methods()
        self._init_end_start_poll()

    def publish(self, table, data, use_snapshot=False):
        LOG.debug('JSON Ingester "%s" publishing table "%s"', self.name, table)
        LOG.trace('publish(self=%s, table=%s, data=%s, use_snapshot=%s',
                  self, table, data, use_snapshot)

        # FIXME: change to differential update
        self._insert_to_table(self.name, table, data)

    def _create_schema_and_tables(self):
        params = _get_config()

        create_schema_statement = """CREATE SCHEMA IF NOT EXISTS {};"""
        create_table_statement = \
            """CREATE TABLE IF NOT EXISTS {}.{}(d jsonb);"""
        conn = None
        try:
            # connect to the PostgreSQL database
            conn = psycopg2.connect(**params)
            # create a new cursor
            cur = conn.cursor()
            # create schema
            cur.execute(
                sql.SQL(create_schema_statement).format(
                    sql.Identifier(self.name)))
            for table_name in self.config['tables']:
                # create table
                cur.execute(sql.SQL(create_table_statement).format(
                    sql.Identifier(self.name), sql.Identifier(table_name)))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError):
            if table_name:
                LOG.exception("Error creating table %s in schema %s",
                              table_name, self.name)
            else:
                LOG.exception("Error creating schema %s", self.name)
        finally:
            if conn is not None:
                conn.close()

    @staticmethod
    def _insert_to_table(schema_name, table_name, data):
        params = _get_config()

        insert_statement = """INSERT INTO {}.{}
                 VALUES(%s);"""
        delete_statement = """DELETE FROM {}.{};"""
        conn = None
        try:
            # connect to the PostgreSQL database
            conn = psycopg2.connect(**params)
            cur = conn.cursor()
            # delete existing data from table
            cur.execute(sql.SQL(delete_statement).format(
                sql.Identifier(schema_name), sql.Identifier(table_name)))
            # insert new data into table
            for d in data:
                cur.execute(sql.SQL(insert_statement).format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name)),
                    (json.dumps(d),))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError):
            LOG.exception("Error writing to DB")
        finally:
            if conn is not None:
                conn.close()

    def add_update_method(self, method, table_name):
        if table_name in self.update_methods:
            raise exception.Conflict('A method has already registered for '
                                     'the table %s.' %
                                     table_name)
        self.update_methods[table_name] = method

    def initialize_session(self):
        self.session = datasource_utils.get_keystone_session(
            self.config['authentication'])

    def initialize_update_methods(self):
        for table_name in self.config['tables']:
            table_info = self.config['tables'][table_name]

            # Note: using default parameters to get early-binding of variables
            # in closure
            def update_method(table_name=table_name, table_info=table_info):
                full_path = self.api_endpoint.rstrip('/') + '/' + table_info[
                    'api_path'].lstrip('/')
                result = self.session.get(full_path).json()
                # FIXME: generalize to other verbs?

                jsonpath_expr = parser.parse(table_info['jsonpath'])
                ingest_data = [match.value for match in
                               jsonpath_expr.find(result)]
                self.state[table_name] = ingest_data

            self.add_update_method(update_method, table_name)

    def update_from_datasource(self):
        for table in self.config['tables']:
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
                # Note(thread-safety): blocking call
                self.publish(
                    tablename, self.state[tablename], use_snapshot=False)
        except Exception as e:
            self.last_error = e
            LOG.exception("Datasource driver raised exception")

        self.last_updated_time = datetime.datetime.now()
        self.number_of_updates += 1
        LOG.info("%s:: finished polling", self.name)
