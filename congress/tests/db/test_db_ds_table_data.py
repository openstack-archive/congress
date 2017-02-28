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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from oslo_utils import uuidutils

from congress.db import db_ds_table_data
from congress.tests import base


class TestDbDsTableData(base.SqlTestCase):

    def test_store_ds_table_data(self):
        ds_id = uuidutils.generate_uuid()

        # store new data
        source = db_ds_table_data.store_ds_table_data(
            ds_id=ds_id,
            tablename='table1',
            tabledata=set([('a', 0)]))
        self.assertEqual(ds_id, source.ds_id)
        self.assertEqual('table1', source.tablename)
        self.assertEqual('[["a", 0]]', source.tabledata)

        # update exsting data
        db_ds_table_data.store_ds_table_data(
            ds_id=ds_id,
            tablename='table1',
            tabledata=set([('a', 0), ('new', 1)]))
        data = db_ds_table_data.get_ds_table_data(ds_id, 'table1')
        self.assertEqual(set([('a', 0), ('new', 1)]), data)

    def test_delete_ds_table_data(self):
        ds_id = uuidutils.generate_uuid()
        db_ds_table_data.store_ds_table_data(
            ds_id=ds_id,
            tablename='table1',
            tabledata=set([('a', 0), ('b', 1)]))
        db_ds_table_data.store_ds_table_data(
            ds_id=ds_id,
            tablename='table2',
            tabledata=set([('a', 0), ('b', 2)]))
        self.assertTrue(db_ds_table_data.delete_ds_table_data(ds_id, 'table1'))
        self.assertIsNone(db_ds_table_data.get_ds_table_data(ds_id, 'table1'))
        self.assertEqual(set([('a', 0), ('b', 2)]),
                         db_ds_table_data.get_ds_table_data(ds_id, 'table2'))

    def test_delete_ds_table_data_by_ds(self):
        ds_id = uuidutils.generate_uuid()
        ds2_id = uuidutils.generate_uuid()
        db_ds_table_data.store_ds_table_data(
            ds_id=ds_id,
            tablename='table1',
            tabledata=set([('a', 0), ('b', 1)]))
        db_ds_table_data.store_ds_table_data(
            ds_id=ds_id,
            tablename='table2',
            tabledata=set([('a', 0), ('b', 2)]))
        db_ds_table_data.store_ds_table_data(
            ds_id=ds2_id,
            tablename='table3',
            tabledata=set([('a', 0), ('b', 3)]))
        self.assertTrue(db_ds_table_data.delete_ds_table_data(ds_id))
        self.assertIsNone(db_ds_table_data.get_ds_table_data(ds_id, 'table1'))
        self.assertIsNone(db_ds_table_data.get_ds_table_data(ds_id, 'table2'))
        self.assertEqual(set([('a', 0), ('b', 3)]),
                         db_ds_table_data.get_ds_table_data(ds2_id, 'table3'))

    def test_delete_non_existing_ds_table_data(self):
        self.assertFalse(db_ds_table_data.delete_ds_table_data('none', 'none'))

    def test_get_ds_table_data(self):
        ds_id = uuidutils.generate_uuid()
        ds2_id = uuidutils.generate_uuid()
        db_ds_table_data.store_ds_table_data(
            ds_id=ds_id,
            tablename='table1',
            tabledata=set([('a', 0), ('b', 1)]))
        db_ds_table_data.store_ds_table_data(
            ds_id=ds_id,
            tablename='table2',
            tabledata=set([('a', 0), ('b', 2)]))
        db_ds_table_data.store_ds_table_data(
            ds_id=ds2_id,
            tablename='table3',
            tabledata=set([('a', 0), ('b', 3)]))
        data = db_ds_table_data.get_ds_table_data(ds_id, 'table1')
        self.assertEqual(set([('a', 0), ('b', 1)]), data)

        data = db_ds_table_data.get_ds_table_data(ds_id)
        self.assertEqual(2, len(data))
        self.assertIn(
            {'tablename': 'table1',
             'tabledata': set([('a', 0), ('b', 1)])},
            data)
        self.assertIn(
            {'tablename': 'table2',
             'tabledata': set([('a', 0), ('b', 2)])},
            data)
