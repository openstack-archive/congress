# Copyright (c) 2014 VMware, Inc. All rights reserved.
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

import copy
import hashlib
import json

import eventlet
import mock
from oslo_utils import uuidutils

from congress import data_types
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils
from congress.db import db_ds_table_data
from congress import exception
from congress.tests import base
from congress.tests.datasources import util
from congress.tests import fake_datasource
from congress.tests import helper


class TestDatasourceDriver(base.TestCase):

    def setUp(self):
        super(TestDatasourceDriver, self).setUp()
        self.val_trans = {'translation-type': 'VALUE'}

    def compute_hash(self, obj):
        s = json.dumps(sorted(obj, key=(lambda x: str(type(x)) + repr(x))),
                       sort_keys=True)
        h = hashlib.md5(s.encode('ascii')).hexdigest()
        return h

    def test_translator_key_elements(self):
        """Test for keys of all translator."""
        expected_params = {
            'hdict': ('translation-type', 'table-name', 'parent-key',
                      'id-col', 'selector-type', 'field-translators',
                      'in-list', 'parent-col-name', 'objects-extract-fn',
                      'parent-key-desc'),
            'vdict': ('translation-type', 'table-name', 'parent-key',
                      'id-col', 'key-col', 'val-col', 'translator',
                      'parent-col-name', 'objects-extract-fn'),
            'list': ('translation-type', 'table-name', 'parent-key',
                     'id-col', 'val-col', 'translator', 'parent-col-name',
                     'objects-extract-fn', 'parent-key-desc', 'val-col-desc'),
            }

        actual_params = {
            'hdict': datasource_driver.DataSourceDriver.HDICT_PARAMS,
            'vdict': datasource_driver.DataSourceDriver.VDICT_PARAMS,
            'list': datasource_driver.DataSourceDriver.LIST_PARAMS,
            }

        for key, params in actual_params.items():
            expected = expected_params[key]
            self.assertEqual(params, expected)

    def test_in_list_results_hdict_hdict(self):
        class Type1(object):
            @classmethod
            def marshal(cls, value):
                return value

        class Type2(object):
            @classmethod
            def marshal(cls, value):
                return value

        ports_fixed_ips_translator = {
            'translation-type': 'HDICT',
            'table-name': 'fixed-ips',
            'parent-key': 'id',
            'selector-type': 'DICT_SELECTOR',
            'in-list': True,
            'field-translators':
                ({'fieldname': 'ip_address',
                  'translator': datasource_utils.typed_value_trans(Type2)},
                 {'fieldname': 'subnet_id', 'translator': self.val_trans})}

        ports_translator = {
            'translation-type': 'HDICT',
            'table-name': 'ports',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'id',
                  'translator': datasource_utils.typed_value_trans(Type2)},
                 {'fieldname': 'fixed_ips',
                  'translator': ports_fixed_ips_translator})}

        driver = datasource_driver.DataSourceDriver('', None)
        driver.register_translator(ports_translator)
        ports = [{'id': '12345',
                  'fixed_ips': [{'ip_address': '1.1.1.1', 'subnet_id': 'aa'},
                                {'ip_address': '2.2.2.2', 'subnet_id': 'bb'}]}]
        row_data = driver.convert_objs(ports, ports_translator)
        expected = [('fixed-ips', ('12345', '1.1.1.1', 'aa')),
                    ('fixed-ips', ('12345', '2.2.2.2', 'bb')),
                    ('ports', ('12345',))]
        self.assertEqual(row_data, expected)

    def test_getting_parent_key_from_nested_tables(self):
        level3_translator = {
            'translation-type': 'HDICT',
            'table-name': 'level3',
            'parent-key': 'parent_key',
            'selector-type': 'DICT_SELECTOR',
            'in-list': True,
            'field-translators':
                ({'fieldname': 'level3_thing', 'translator': self.val_trans},)}

        level2_translator = {
            'translation-type': 'HDICT',
            'table-name': 'level2',
            'parent-key': 'id',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'thing', 'translator': self.val_trans},
                 {'fieldname': 'level3',
                  'translator': level3_translator})}

        level1_translator = {
            'translation-type': 'HDICT',
            'table-name': 'level1',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'id', 'translator': self.val_trans},
                 {'fieldname': 'level2',
                  'translator': level2_translator})}

        driver = datasource_driver.DataSourceDriver('', None)
        driver.register_translator(level1_translator)
        data = [
            {'id': 11, 'level2':
                {'thing': 'blah!', 'level3': [{'level3_thing': '12345'}]}}]

        row_data = driver.convert_objs(data, level1_translator)
        expected = [('level3', (11, '12345')),
                    ('level2', (11, 'blah!')),
                    ('level1', (11,))]
        self.assertEqual(row_data, expected)

    def test_parent_col_name_in_hdict(self):
        level2_translator = {
            'translation-type': 'HDICT',
            'table-name': 'level2',
            'parent-key': 'id',
            'parent-col-name': 'level1_id',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'thing', 'translator': self.val_trans},)}

        level1_translator = {
            'translation-type': 'HDICT',
            'table-name': 'level1',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'id', 'translator': self.val_trans},
                 {'fieldname': 'level2',
                  'translator': level2_translator})}

        @mock.patch('congress.datasources.datasource_driver.DataSourceDriver.'
                    'TRANSLATORS',
                    [level1_translator])
        def do_test():
            driver = datasource_driver.DataSourceDriver('', None)
            # test schema
            schema = driver.get_schema()
            expected = {'level1': ({'name': 'id', 'desc': None},),
                        'level2': ({'name': 'level1_id', 'desc': None},
                                   {'name': 'thing', 'desc': None})}
            self.assertEqual(schema, expected)

            # test data
            data = [{'id': 11, 'level2': {'thing': 'blah!'}}]
            row_data = driver.convert_objs(data, level1_translator)
            expected = [('level2', (11, 'blah!')), ('level1', (11,))]
            self.assertEqual(row_data, expected)

        do_test()

    def test_parent_col_name_in_vdict(self):
        level2_translator = {
            'translation-type': 'VDICT',
            'table-name': 'level2',
            'parent-key': 'id',
            'key-col': 'id',
            'val-col': 'value',
            'parent-col-name': 'level1_id',
            'translator': self.val_trans}

        level1_translator = {
            'translation-type': 'HDICT',
            'table-name': 'level1',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'id', 'translator': self.val_trans},
                 {'fieldname': 'level2',
                  'translator': level2_translator})}

        @mock.patch('congress.datasources.datasource_driver.DataSourceDriver.'
                    'TRANSLATORS',
                    [level1_translator])
        def do_test():
            driver = datasource_driver.DataSourceDriver('', None)
            # test schema
            schema = driver.get_schema()
            expected = {'level1': ({'name': 'id', 'desc': None},),
                        'level2': ('level1_id', 'id', 'value')}
            self.assertEqual(expected, schema)

            # test data
            data = [{'id': 11, 'level2': {'thing': 'blah!'}}]
            row_data = driver.convert_objs(data, level1_translator)
            expected = [('level2', (11, 'thing', 'blah!')), ('level1', (11,))]
            self.assertEqual(row_data, expected)

        do_test()

    def test_parent_col_name_in_list(self):
        level2_translator = {
            'translation-type': 'LIST',
            'table-name': 'level2',
            'parent-key': 'id',
            'parent-key-desc': 'level1_parent-desc',
            'parent-col-name': 'level1_id',
            'val-col': 'level_1_data',
            'val-col-desc': 'level_1_desc',
            'translator': self.val_trans}

        level1_translator = {
            'translation-type': 'HDICT',
            'table-name': 'level1',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'id', 'translator': self.val_trans},
                 {'fieldname': 'level2',
                  'translator': level2_translator})}

        @mock.patch('congress.datasources.datasource_driver.DataSourceDriver.'
                    'TRANSLATORS',
                    [level1_translator])
        def do_test():
            driver = datasource_driver.DataSourceDriver('', None)
            # test schema
            schema = driver.get_schema()
            expected = {'level1': ({'name': 'id', 'desc': None},),
                        'level2': ({'name': 'level1_id',
                                    'desc': 'level1_parent-desc'},
                                   {'name': 'level_1_data',
                                    'desc': 'level_1_desc'})}
            self.assertEqual(expected, schema)

            # test data
            data = [{'id': 11, 'level2': ['thing']}]
            row_data = driver.convert_objs(data, level1_translator)
            expected = [('level2', (11, 'thing')), ('level1', (11,))]
            self.assertEqual(row_data, expected)

        do_test()

    def test_check_for_duplicate_table_names_hdict_list(self):
        translator = {
            'translation-type': 'HDICT',
            'table-name': 'table1',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'tags',
                  'translator': {'translation-type': 'LIST',
                                 'table-name': 'table1',
                                 'val-col': 'tag',
                                 'translator': self.val_trans}},)}
        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.DuplicateTableName,
                          driver.register_translator,
                          translator)

    def test_check_for_duplicate_table_names_nested_list_list(self):
        # Test a LIST containing a LIST with the same table name.
        translator = {'translation-type': 'LIST', 'table-name': 'testtable',
                      'id-col': 'id_col', 'val-col': 'value',
                      'translator': {'translation-type': 'LIST',
                                     'table-name': 'testtable',
                                     'id-col': 'id', 'val-col': 'val',
                                     'translator': self.val_trans}}
        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.DuplicateTableName,
                          driver.register_translator, translator)

    def test_check_for_duplicate_table_names_in_different_translator(self):
        translator = {
            'translation-type': 'HDICT',
            'table-name': 'table1',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'tags',
                  'translator': {'translation-type': 'LIST',
                                 'table-name': 'table2',
                                 'val-col': 'tag',
                                 'translator': self.val_trans}},)}
        driver = datasource_driver.DataSourceDriver('', None)
        driver.register_translator(translator)
        self.assertRaises(exception.DuplicateTableName,
                          driver.register_translator,
                          translator)

    def test_check_for_duplicate_table_names_hdict_hdict(self):
        translator = {
            'translation-type': 'HDICT',
            'table-name': 'table1',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'tags',
                  'translator': {'translation-type': 'HDICT',
                                 'table-name': 'table1',
                                 'selector-type': 'DICT_SELECTOR',
                                 'field-translators':
                                     ({'fieldname': 'x',
                                       'translator': self.val_trans},)}},)}

        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.DuplicateTableName,
                          driver.register_translator,
                          translator)

    def test_invalid_translation_type(self):
        translator = {'translation-type': 'YOYO',
                      'table-name': 'table1'}
        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.InvalidTranslationType,
                          driver.register_translator,
                          translator)

        translator = {'translation-type': 'LIS',
                      'table-name': 'table1'}
        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.InvalidTranslationType,
                          driver.register_translator,
                          translator)

    def test_no_key_col_in_vdict(self):
        translator = {'translation-type': 'VDICT',
                      'table-name': 'table1',
                      'val-col': 'id-col'}
        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_no_val_col_in_vdict(self):
        translator = {'translation-type': 'VDICT',
                      'table-name': 'table1',
                      'key-col': 'id-col'}
        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_no_val_col_in_list(self):
        translator = {'translation-type': 'LIST',
                      'table-name': 'table1'}
        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_no_parent_key_id_col(self):
        translator = {'translation-type': 'LIST',
                      'table-name': 'table1',
                      'id-col': 'id-col',
                      'parent-key': 'parent_key_column'}

        # Test LIST
        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)
        # Test HDICT
        translator['translation-type'] = 'VDICT'
        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)
        # Test HDICT
        translator['translation-type'] = 'HDICT'
        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_check_no_extra_params(self):
        translator = {'translation-type': 'LIST',
                      'table-name': 'table1',
                      'id-col': 'id-col',
                      'invalid_column': 'blah'}

        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_check_no_extra_params_nested_hdict(self):
        translator = {
            'translation-type': 'HDICT',
            'table-name': 'table1',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'tags',
                  'translator': {'translation-type': 'HDICT',
                                 'table-name': 'table2',
                                 'selector-type': 'DICT_SELECTOR',
                                 'invalid_column': 'yaya',
                                 'field-translators':
                                     ({'fieldname': 'x',
                                       'translator': self.val_trans},)}},)}

        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_check_no_extra_params_nested_list_hdict(self):
        translator = {
            'translation-type': 'LIST',
            'table-name': 'table1',
            'val-col': 'fixed_ips',
            'translator': {
                'table-name': 'table2',
                'invalid-column': 'hello_there!',
                'translation-type': 'HDICT',
                'selector-type': 'DICT_SELECTOR',
                'field-translators':
                    ({'fieldname': 'ip_address',
                      'translator': self.val_trans},)}}

        driver = datasource_driver.DataSourceDriver('', None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_convert_vdict_with_id(self):
        # Test a single VDICT with an id column.
        resp = {'a': 'FOO', 'b': 123}
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
                      'translator': self.val_trans}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        k1 = self.compute_hash((('a', 'FOO'), ('b', 123)))

        self.assertEqual(2, len(rows))
        self.assertEqual(k1, k)
        self.assertIn(('testtable', (k, 'a', 'FOO')), rows)
        self.assertIn(('testtable', (k, 'b', 123)), rows)

    def test_convert_vdict_without_id(self):
        # Test a single VDICT without an id column.
        resp = {'a': 'FOO', 'b': 123}
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'key-col': 'key', 'val-col': 'value',
                      'translator': self.val_trans}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        self.assertEqual(2, len(rows))
        self.assertIsNone(k)
        self.assertIn(('testtable', ('a', 'FOO')), rows)
        self.assertIn(('testtable', ('b', 123)), rows)

    def test_convert_vdict_with_id_function(self):
        # Test a single VDICT with an id column that is a function.
        resp = {'a': 'FOO', 'b': 123}
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'id-col': lambda obj: 'id:' + obj['a'],
                      'key-col': 'key', 'val-col': 'value',
                      'translator': self.val_trans}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        k1 = 'id:FOO'

        self.assertEqual(2, len(rows))
        self.assertEqual(k1, k)
        self.assertIn(('testtable', (k, 'a', 'FOO')), rows)
        self.assertIn(('testtable', (k, 'b', 123)), rows)

    def test_convert_vdict_list(self):
        # Test a VDICT that contains lists.
        resp = {'foo': (1, 2, 3), 'bar': ('a', 'b')}
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
                      'translator': {'translation-type': 'LIST',
                                     'table-name': 'subtable',
                                     'id-col': 'id_col', 'val-col': 'val_col',
                                     'translator': self.val_trans}}
        rows, actual_k = datasource_driver.DataSourceDriver.convert_obj(
            resp, translator)

        k1 = self.compute_hash((1, 2, 3))
        k2 = self.compute_hash(('a', 'b'))
        k = self.compute_hash((('foo', k1), ('bar', k2)))

        self.assertEqual(7, len(rows))
        self.assertEqual(k, actual_k)

        self.assertIn(('subtable', (k1, 1)), rows)
        self.assertIn(('subtable', (k1, 2)), rows)
        self.assertIn(('subtable', (k1, 3)), rows)
        self.assertIn(('subtable', (k2, 'a')), rows)
        self.assertIn(('subtable', (k2, 'b')), rows)
        self.assertIn(('testtable', (k, 'foo', k1)), rows)
        self.assertIn(('testtable', (k, 'bar', k2)), rows)

    def test_convert_vdict_is_none(self):
        # Test a single VDICT with an id column.
        resp = None
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
                      'translator': self.val_trans}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)
        self.assertIsNone(rows)

    def test_convert_list_with_id(self):
        # Test a single LIST with an id_column
        resp = (1, 'a', 'b', True)
        translator = {'translation-type': 'LIST', 'table-name': 'testtable',
                      'id-col': 'id_col', 'val-col': 'value',
                      'translator': self.val_trans}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        k1 = self.compute_hash((1, 'a', 'b', True))

        self.assertEqual(4, len(rows))
        self.assertEqual(k1, k)
        self.assertIn(('testtable', (k, 1)), rows)
        self.assertIn(('testtable', (k, 'a')), rows)
        self.assertIn(('testtable', (k, 'b')), rows)
        self.assertIn(('testtable', (k, True)), rows)

    def test_convert_list_with_id_function(self):
        # Test a single LIST with an id function
        resp = (1, 'a', 'b', True)
        translator = {'translation-type': 'LIST', 'table-name': 'testtable',
                      'id-col': lambda obj: obj[0], 'val-col': 'value',
                      'translator': self.val_trans}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        k1 = 1

        self.assertEqual(4, len(rows))
        self.assertEqual(k1, k)
        self.assertIn(('testtable', (k, 1)), rows)
        self.assertIn(('testtable', (k, 'a')), rows)
        self.assertIn(('testtable', (k, 'b')), rows)
        self.assertIn(('testtable', (k, True)), rows)

    def test_convert_list_without_id(self):
        # Test a single LIST without an id_column
        resp = (1, 'a', 'b', True)
        translator = {'translation-type': 'LIST', 'table-name': 'testtable',
                      'val-col': 'value', 'translator': self.val_trans}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        self.assertEqual(4, len(rows))
        self.assertIsNone(k)
        self.assertIn(('testtable', (1,)), rows)
        self.assertIn(('testtable', ('a',)), rows)
        self.assertIn(('testtable', ('b',)), rows)
        self.assertIn(('testtable', (True,)), rows)

    def test_convert_list_with_sublist(self):
        # Test a single LIST with an id_column
        resp = ((1, 2, 3), ('a', 'b', 'c'), (True, False))
        translator = {'translation-type': 'LIST', 'table-name': 'testtable',
                      'id-col': 'id_col', 'val-col': 'value',
                      'translator': {'translation-type': 'LIST',
                                     'table-name': 'subtable',
                                     'id-col': 'id_col', 'val-col': 'val_col',
                                     'translator': self.val_trans}}
        rows, actual_k = datasource_driver.DataSourceDriver.convert_obj(
            resp, translator)

        k1 = self.compute_hash((1, 2, 3))
        k2 = self.compute_hash(('a', 'b', 'c'))
        k3 = self.compute_hash((True, False))
        k = self.compute_hash((k1, k2, k3))

        self.assertEqual(11, len(rows))
        self.assertEqual(k, actual_k)
        self.assertIn(('subtable', (k1, 1)), rows)
        self.assertIn(('subtable', (k1, 2)), rows)
        self.assertIn(('subtable', (k1, 3)), rows)
        self.assertIn(('subtable', (k2, 'a')), rows)
        self.assertIn(('subtable', (k2, 'b')), rows)
        self.assertIn(('subtable', (k2, 'c')), rows)
        self.assertIn(('subtable', (k3, True)), rows)
        self.assertIn(('subtable', (k3, False)), rows)
        self.assertIn(('testtable', (k, k1)), rows)
        self.assertIn(('testtable', (k, k2)), rows)
        self.assertIn(('testtable', (k, k3)), rows)

    def test_convert_recursive_hdict_single_fields(self):
        # Test simple fields inside of an HDICT
        resp = util.ResponseObj({'testfield1': 'FOO',
                                 'testfield2': 123})
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                          {'fieldname': 'testfield1', 'col': 'col1',
                           'translator': self.val_trans},
                          {'fieldname': 'testfield2', 'col': 'col2',
                           'translator': self.val_trans})}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        self.assertEqual(1, len(rows))
        self.assertIsNone(k)
        self.assertEqual([('testtable', ('FOO', 123))], rows)

    def test_convert_recursive_hdict_single_fields_empty_fields(self):
        # Test simple fields inside of an HDICT where the translator
        # interprests a non-present field as None.
        resp = util.ResponseObj({'testfield1': 'FOO'})
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                          {'fieldname': 'testfield1', 'col': 'col1',
                           'translator': self.val_trans},
                          {'fieldname': 'testfield2', 'col': 'col2',
                           'translator': self.val_trans})}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        self.assertEqual(1, len(rows))
        self.assertIsNone(k)
        self.assertEqual([('testtable', ('FOO', None))], rows)

    def test_convert_recursive_hdict_single_fields_default_col(self):
        # Test simple fields inside of an HDICT using the default col name.

        resp = util.ResponseObj({'testfield1': 'FOO'})
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                          {'fieldname': 'testfield1',
                           'translator': self.val_trans},)}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        self.assertEqual(1, len(rows))
        self.assertIsNone(k)
        self.assertEqual([('testtable', ('FOO',))], rows)

    def test_convert_recursive_hdict_extract_subfields(self):
        # Test simple fields inside of an HDICT
        # Also tests with and without extract-fn.
        field = util.ResponseObj({'b': 123})
        resp = util.ResponseObj({'testfield1': {'a': 'FOO'},
                                 'testfield2': field,
                                 'testfield3': 456})
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'id-col': 'id_col', 'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                          {'fieldname': 'testfield1', 'col': 'col1',
                           'translator': {'translation-type': 'VALUE',
                                          'extract-fn': lambda x: x['a']}},
                          {'fieldname': 'testfield2', 'col': 'col2',
                           'translator': {'translation-type': 'VALUE',
                                          'extract-fn': lambda x: x.b}},
                          {'fieldname': 'testfield3', 'col': 'col3',
                           'translator': {'translation-type': 'VALUE'}})}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        self.assertEqual(1, len(rows))
        self.assertEqual(self.compute_hash(('FOO', 123, 456)), k)
        self.assertEqual([('testtable', (k, 'FOO', 123, 456))], rows)

    def test_convert_recursive_hdict_sublists(self):
        # Test sublists inside of an HDICT
        resp = util.ResponseObj({'testfield1': ('FOO', 'BAR'),
                                 'testfield2': (1, 2, 3)})
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                          {'fieldname': 'testfield1', 'col': 'col1',
                           'translator': {'translation-type': 'LIST',
                                          'table-name': 'subtable1',
                                          'id-col': 'id', 'val-col': 'value',
                                          'translator': self.val_trans}},
                          {'fieldname': 'testfield2', 'col': 'col2',
                           'translator': {'translation-type': 'LIST',
                                          'table-name': 'subtable2',
                                          'id-col': 'id', 'val-col': 'value',
                                          'translator': self.val_trans}})}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        k1 = self.compute_hash(('FOO', 'BAR'))
        k2 = self.compute_hash((1, 2, 3))

        self.assertIsNone(k)
        self.assertEqual(6, len(rows))
        self.assertIn(('subtable1', (k1, 'FOO')), rows)
        self.assertIn(('subtable1', (k1, 'BAR')), rows)
        self.assertIn(('subtable2', (k2, 1)), rows)
        self.assertIn(('subtable2', (k2, 2)), rows)
        self.assertIn(('subtable2', (k2, 3)), rows)
        self.assertIn(('testtable', (k1, k2)), rows)

    def test_convert_recursive_hdict_vdict(self):
        # Test translator of an VDICT inside of an HDICT
        resp = util.ResponseObj({'testfield1': {'a': 123, 'b': 456},
                                 'testfield2': {'c': 'abc', 'd': 'def'}})
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                          {'fieldname': 'testfield1', 'col': 'col1',
                           'translator': {'translation-type': 'VDICT',
                                          'table-name': 'subtable1',
                                          'id-col': 'id', 'key-col': 'key',
                                          'val-col': 'value',
                                          'translator': self.val_trans}},
                          {'fieldname': 'testfield2', 'col': 'col2',
                           'translator': {'translation-type': 'VDICT',
                                          'table-name': 'subtable2',
                                          'id-col': 'id', 'key-col': 'key',
                                          'val-col': 'value',
                                          'translator': self.val_trans}})}
        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        k1 = self.compute_hash((('a', 123), ('b', 456)))
        k2 = self.compute_hash((('c', 'abc'), ('d', 'def')))

        self.assertIsNone(k)
        self.assertEqual(5, len(rows))
        self.assertIn(('subtable1', (k1, 'a', 123)), rows)
        self.assertIn(('subtable1', (k1, 'b', 456)), rows)
        self.assertIn(('subtable2', (k2, 'c', 'abc')), rows)
        self.assertIn(('subtable2', (k2, 'd', 'def')), rows)
        self.assertIn(('testtable', (k1, k2)), rows)

    def test_convert_recursive_hdict_hdict(self):
        # Test translator of an HDICT inside of an HDICT.
        resp = util.ResponseObj({'testfield1': {'a': 123, 'b': 456},
                                 'testfield2': {'c': 'abc', 'd': 'def'}})

        subtranslator_1 = {'translation-type': 'HDICT',
                           'table-name': 'subtable1',
                           'selector-type': 'DICT_SELECTOR',
                           'id-col': 'id',
                           'field-translators': (
                               {'fieldname': 'a',
                                'col': 'a1',
                                'translator': self.val_trans},
                               {'fieldname': 'b',
                                'col': 'b1',
                                'translator': self.val_trans})}

        subtranslator_2 = {'translation-type': 'HDICT',
                           'table-name': 'subtable2',
                           'selector-type': 'DICT_SELECTOR',
                           'id-col': 'id',
                           'field-translators': (
                               {'fieldname': 'c',
                                'col': 'c1',
                                'translator': self.val_trans},
                               {'fieldname': 'd',
                                'col': 'd1',
                                'translator': self.val_trans})}

        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                          {'fieldname': 'testfield1', 'col': 'col1',
                           'translator': subtranslator_1},
                          {'fieldname': 'testfield2', 'col': 'col2',
                           'translator': subtranslator_2})}

        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        k1 = self.compute_hash((123, 456))
        k2 = self.compute_hash(('abc', 'def'))

        self.assertIsNone(k)
        self.assertEqual(3, len(rows))
        self.assertIn(('subtable1', (k1, 123, 456)), rows)
        self.assertIn(('subtable2', (k2, 'abc', 'def')), rows)
        self.assertIn(('testtable', (k1, k2)), rows)

    def test_convert_hdict_hdict_parent_key_without_id(self):
        # Test a HDICT that contains lists using a parent_key.
        resp = {'foreign-key': 100, 'foo': {'f1': 123}}
        subtranslator = {'translation-type': 'HDICT',
                         'table-name': 'subtable',
                         'parent-key': 'foreign-key',
                         'selector-type': 'DICT_SELECTOR',
                         'field-translators': ({'fieldname': 'f1',
                                                'translator': self.val_trans},
                                               )}
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DICT_SELECTOR',
                      'field-translators': ({'fieldname': 'foreign-key',
                                             'translator': self.val_trans},
                                            {'fieldname': 'foo',
                                             'translator': subtranslator})}

        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        self.assertEqual(2, len(rows))
        self.assertIsNone(k)

        self.assertIn(('subtable', (100, 123)), rows)
        self.assertIn(('testtable', (100,)), rows)

    def test_convert_hdict_hdict_parent_key_with_id(self):
        # Test a HDICT that contains lists using a parent_key.
        resp = {'foreign-key': 100, 'foo': {'f1': 123}}
        subtranslator = {'translation-type': 'HDICT',
                         'table-name': 'subtable',
                         'parent-key': 'foreign-key',
                         'selector-type': 'DICT_SELECTOR',
                         'field-translators': ({'fieldname': 'f1',
                                                'translator': self.val_trans},
                                               )}
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DICT_SELECTOR', 'id-col': 'id',
                      'field-translators': ({'fieldname': 'foreign-key',
                                             'translator': self.val_trans},
                                            {'fieldname': 'foo',
                                             'translator': subtranslator})}

        rows, actual_k = datasource_driver.DataSourceDriver.convert_obj(
            resp, translator)

        k = self.compute_hash((100,))
        self.assertEqual(2, len(rows))
        self.assertEqual(k, actual_k)

        self.assertIn(('subtable', (100, 123)), rows)
        self.assertIn(('testtable', (k, 100,)), rows)

    def test_convert_hdict_vdict_parent_key_without_id(self):
        # Test a HDICT that contains lists using a parent_key.
        resp = util.ResponseObj({'foreign-key': 100,
                                 'foo': {'f1': 123, 'f2': 456}})
        subtranslator = {'translation-type': 'VDICT',
                         'table-name': 'subtable',
                         'parent-key': 'foreign-key',
                         'key-col': 'key_col',
                         'val-col': 'val_col',
                         'translator': self.val_trans}
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': ({'fieldname': 'foreign-key',
                                             'translator': self.val_trans},
                                            {'fieldname': 'foo',
                                             'translator': subtranslator})}

        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        self.assertEqual(3, len(rows))
        self.assertIsNone(k)

        self.assertIn(('subtable', (100, 'f1', 123)), rows)
        self.assertIn(('subtable', (100, 'f2', 456)), rows)
        self.assertIn(('testtable', (100,)), rows)

    def test_convert_hdict_vdict_parent_key_with_id(self):
        # Test a HDICT that contains lists using a parent_key.
        resp = util.ResponseObj({'foreign-key': 100,
                                 'foo': {'f1': 123, 'f2': 456}})
        list_translator = {'translation-type': 'VDICT',
                           'table-name': 'subtable',
                           'parent-key': 'foreign-key',
                           'key-col': 'key_col',
                           'val-col': 'val_col',
                           'translator': self.val_trans}
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'id-col': 'id', 'selector-type': 'DOT_SELECTOR',
                      'field-translators': ({'fieldname': 'foreign-key',
                                             'translator': self.val_trans},
                                            {'fieldname': 'foo',
                                             'translator': list_translator})}

        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        self.assertEqual(3, len(rows))
        self.assertEqual(self.compute_hash((100,)), k)

        self.assertIn(('subtable', (100, 'f1', 123)), rows)
        self.assertIn(('subtable', (100, 'f2', 456)), rows)
        self.assertIn(('testtable', (k, 100)), rows)

    def test_convert_hdict_list_parent_key_without_id(self):
        # Test a HDICT that contains lists using a parent_key.
        resp = util.ResponseObj({'foreign-key': 100, 'foo': (1, 2)})
        list_translator = {'translation-type': 'LIST',
                           'table-name': 'subtable',
                           'parent-key': 'foreign-key',
                           'val-col': 'val_col',
                           'translator': self.val_trans}
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': ({'fieldname': 'foreign-key',
                                             'translator': self.val_trans},
                                            {'fieldname': 'foo',
                                             'translator': list_translator})}

        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        self.assertEqual(3, len(rows))
        self.assertIsNone(k)

        self.assertIn(('subtable', (100, 1)), rows)
        self.assertIn(('subtable', (100, 2)), rows)
        self.assertIn(('testtable', (100,)), rows)

    def test_convert_hdict_list_parent_key_with_id(self):
        # Test a HDICT that contains lists using a parent_key.
        resp = util.ResponseObj({'foreign-key': 100, 'foo': (1, 2)})
        list_translator = {'translation-type': 'LIST',
                           'table-name': 'subtable',
                           'parent-key': 'foreign-key',
                           'val-col': 'val_col',
                           'translator': self.val_trans}
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'id-col': 'id', 'selector-type': 'DOT_SELECTOR',
                      'field-translators': ({'fieldname': 'foreign-key',
                                             'translator': self.val_trans},
                                            {'fieldname': 'foo',
                                             'translator': list_translator})}

        rows, k = datasource_driver.DataSourceDriver.convert_obj(resp,
                                                                 translator)

        self.assertEqual(3, len(rows))
        self.assertEqual(self.compute_hash((100,)), k)

        self.assertIn(('subtable', (100, 1)), rows)
        self.assertIn(('subtable', (100, 2)), rows)
        self.assertIn(('testtable', (k, 100)), rows)

    def test_convert_vdict_list_parent_key_without_id(self):
        # Test a VDICT that contains lists using a parent_key.
        resp = {'foo': (1, 2, 3), 'bar': ('a', 'b')}
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'key-col': 'key', 'val-col': 'value',
                      'translator': {'translation-type': 'LIST',
                                     'table-name': 'subtable',
                                     'parent-key': 'key',
                                     'val-col': 'val_col',
                                     'translator': self.val_trans}}
        rows, actual_k = datasource_driver.DataSourceDriver.convert_obj(
            resp, translator)

        self.assertEqual(7, len(rows))
        self.assertIsNone(actual_k)

        self.assertIn(('subtable', ('foo', 1)), rows)
        self.assertIn(('subtable', ('foo', 2)), rows)
        self.assertIn(('subtable', ('foo', 3)), rows)
        self.assertIn(('subtable', ('bar', 'a')), rows)
        self.assertIn(('subtable', ('bar', 'b')), rows)
        self.assertIn(('testtable', ('foo',)), rows)
        self.assertIn(('testtable', ('bar',)), rows)

    def test_convert_vdict_list_parent_key_with_id(self):
        # Test a VDICT that contains lists using a parent_key.
        resp = {'foo': (1, 2, 3), 'bar': ('a', 'b')}
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'id-col': 'id', 'key-col': 'key', 'val-col': 'value',
                      'translator': {'translation-type': 'LIST',
                                     'table-name': 'subtable',
                                     'parent-key': 'key',
                                     'val-col': 'val_col',
                                     'translator': self.val_trans}}
        rows, actual_k = datasource_driver.DataSourceDriver.convert_obj(
            resp, translator)

        k = self.compute_hash((('foo',), ('bar',)))

        self.assertEqual(7, len(rows))
        self.assertEqual(k, actual_k)

        self.assertIn(('subtable', ('foo', 1)), rows)
        self.assertIn(('subtable', ('foo', 2)), rows)
        self.assertIn(('subtable', ('foo', 3)), rows)
        self.assertIn(('subtable', ('bar', 'a')), rows)
        self.assertIn(('subtable', ('bar', 'b')), rows)
        self.assertIn(('testtable', (k, 'foo')), rows)
        self.assertIn(('testtable', (k, 'bar')), rows)

    def test_convert_bad_params(self):
        def verify_invalid_params(translator, err_msg):
            args = helper.datasource_openstack_args()
            driver = datasource_driver.DataSourceDriver('', args=args)
            try:
                driver.register_translator(translator)
            except exception.InvalidParamException as e:
                self.assertIn(err_msg, str(e))
            else:
                self.fail("Expected InvalidParamException but got none")

        # Test an invalid translation-type.
        verify_invalid_params(
            {'translation-typeXX': 'VDICT', 'table-name': 'testtable',
             'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
             'translator': self.val_trans},
            'Param (translation-type) must be in translator')

        # Test invalid HDICT params
        verify_invalid_params(
            {'translation-type': 'HDICT', 'table-nameXX': 'testtable',
             'id-col': 'id_col', 'selector-type': 'DOT_SELECTOR',
             'field-translators': ({'fieldname': 'abc',
                                   'translator': self.val_trans},)},
            'Params (table-nameXX) are invalid')

        # Test invalid HDICT field translator params
        verify_invalid_params(
            {'translation-type': 'HDICT', 'table-name': 'testtable',
             'id-col': 'id_col', 'selector-type': 'DOT_SELECTOR',
             'field-translators':
                 ({'fieldname': 'abc',
                   'translator': {'translation-typeXX': 'VALUE'}},)},
            'Param (translation-type) must be in translator')

        # Test invalid HDICT field translator params
        verify_invalid_params(
            {'translation-type': 'HDICT', 'table-name': 'testtable',
             'id-col': 'id_col', 'selector-type': 'DOT_SELECTOR',
             'field-translators':
                 ({'fieldname': 'abc',
                   'translator': {'translation-type': 'VALUE',
                                  'XX': 123}},)},
            'Params (XX) are invalid')

        # Test invalid VDICT params
        verify_invalid_params(
            {'translation-type': 'VDICT', 'table-nameXX': 'testtable',
             'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
             'translator': self.val_trans},
            'Params (table-nameXX) are invalid')

        # Test invalid VDICT sub translator params
        verify_invalid_params(
            {'translation-type': 'VDICT', 'table-name': 'testtable',
             'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
             'translator': {'translation-typeXX': 'VALUE'}},
            'Param (translation-type) must be in translator')

        # Test invalid VDICT sub translator params
        verify_invalid_params(
            {'translation-type': 'VDICT', 'table-nameXX': 'testtable',
             'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
             'translator': {'translation-type': 'VALUE', 'XX': 123}},
            'Params (table-nameXX) are invalid')

        # Test invalid LIST params
        verify_invalid_params(
            {'translation-type': 'LIST', 'table-nameXX': 'testtable',
             'id-col': 'id_col', 'val-col': 'value',
             'translator': self.val_trans},
            'Params (table-nameXX) are invalid')

        # Test invalid LIST sub translator params
        verify_invalid_params(
            {'translation-type': 'VDICT', 'table-name': 'testtable',
             'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
             'translator': {'translation-typeXX': 'VALUE'}},
            'Param (translation-type) must be in translator')

        # Test invalid LIST sub translator params
        verify_invalid_params(
            {'translation-type': 'VDICT', 'table-name': 'testtable',
             'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
             'translator': {'translation-type': 'VALUE', 'XX': 123}},
            'Params (XX) are invalid')

    def test_get_schema(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            translator = {
                'translation-type': 'HDICT',
                'table-name': 'testtable',
                'selector-type': 'DOT_SELECTOR',
                'field-translators': (
                    {'fieldname': 'testfield1',
                     'col': 'parent_col1',
                     'translator': {'translation-type': 'HDICT',
                                    'table-name': 'subtable1',
                                    'id-col': 'id1',
                                    'field-translators': (
                                        {'fieldname': 'a',
                                         'col': 'a1',
                                         'translator':
                                             datasource_utils.
                                             typed_value_trans(
                                                 data_types.Bool)},
                                        {'fieldname': 'b',
                                         'col': 'b1',
                                         'translator': self.val_trans})}},
                    {'fieldname': 'testfield2',
                     'translator': {'translation-type': 'HDICT',
                                    'table-name': 'subtable2',
                                    'parent-key': 'zparent_col3',
                                    'parent-col-name': 'id2',
                                    'field-translators': (
                                        {'fieldname': 'c',
                                         'col': 'c1',
                                         'translator': self.val_trans},
                                        {'fieldname': 'd',
                                         'col': 'd1',
                                         'translator': self.val_trans})}},
                    {'fieldname': 'ztestfield3', 'col': 'zparent_col3',
                     'translator': datasource_utils.typed_value_trans(
                         data_types.Str)},
                    {'fieldname': 'testfield4', 'col': 'parent_col4',
                     'translator': {'translation-type': 'VALUE',
                                    'extract-fn': lambda x: x.id}},
                    {'fieldname': 'testfield5', 'col': 'parent_col5',
                     'translator': {'translation-type': 'VDICT',
                                    'table-name': 'subtable3', 'id-col': 'id3',
                                    'key-col': 'key3', 'val-col': 'value3',
                                    'translator': self.val_trans}},
                    {'fieldname': 'testfield6', 'col': 'parent_col6',
                     'translator': {'translation-type': 'LIST',
                                    'table-name': 'subtable4', 'id-col': 'id4',
                                    'val-col': 'value4',
                                    'translator': self.val_trans}},
                    {'fieldname': 'testfield7', 'col': 'parent_col7',
                     'translator': {'translation-type': 'VDICT',
                                    'table-name': 'subtable5',
                                    'key-col': 'key5', 'val-col': 'value5',
                                    'translator': self.val_trans}},
                    {'fieldname': 'testfield8', 'col': 'parent_col8',
                     'translator': {'translation-type': 'LIST',
                                    'table-name': 'subtable6',
                                    'val-col': 'value6',
                                    'translator': self.val_trans}})}

            TRANSLATORS = [translator]

            def __init__(self):
                super(TestDriver, self).__init__('', None)

        schema = TestDriver().get_schema()
        self.assertEqual(7, len(schema))

        self.assertEqual(({'name': 'id1', 'desc': None},
                          {'name': 'a1', 'desc': None, 'type': 'Bool'},
                          {'name': 'b1', 'desc': None}), schema['subtable1'])
        self.assertEqual(({'name': 'id2', 'desc': None, 'type': 'Str'},
                          {'name': 'c1', 'desc': None},
                          {'name': 'd1', 'desc': None}), schema['subtable2'])
        self.assertEqual(('id3', 'key3', 'value3'), schema['subtable3'])
        self.assertEqual(
            ({'name': 'id4', 'desc': None},
             {'name': 'value4', 'desc': None}), schema['subtable4'])
        self.assertEqual(('key5', 'value5'), schema['subtable5'])
        self.assertEqual(({'name': 'value6',
                           'desc': None},), schema['subtable6'])
        self.assertEqual(
            ({'name': 'parent_col1', 'desc': None},
             {'name': 'zparent_col3', 'desc': None, 'type': 'Str'},
             {'name': 'parent_col4', 'desc': None},
             {'name': 'parent_col5', 'desc': None},
             {'name': 'parent_col6', 'desc': None},
             {'name': 'parent_col7', 'desc': None},
             {'name': 'parent_col8', 'desc': None}), schema['testtable'])

    def test_get_schema_with_table_reuse(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            translator = {'translation-type': 'LIST',
                          'table-name': 'testtable',
                          'id-col': 'id_col', 'val-col': 'value',
                          'translator': {'translation-type': 'LIST',
                                         'table-name': 'testtable',
                                         'id-col': 'id', 'val-col': 'val',
                                         'translator': self.val_trans}}

            TRANSLATORS = [translator]

            def __init__(self):
                super(TestDriver, self).__init__('', None)

        try:
            TestDriver().get_schema()
        except exception.DuplicateTableName as e:
            self.assertIn('table (testtable) used twice', str(e))
        else:
            self.fail("Expected InvalidParamException but got none")

    def test_get_schema_with_hdict_parent(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            subtranslator = {'translation-type': 'LIST',
                             'table-name': 'subtable',
                             'parent-key': 'id_col', 'val-col': 'val',
                             'translator': self.val_trans}

            translator = {'translation-type': 'HDICT',
                          'table-name': 'testtable',
                          'id-col': 'id_col',
                          'selector-type': 'DICT_SELECTOR',
                          'field-translators': ({'fieldname': 'unique_key',
                                                 'translator': self.val_trans},
                                                {'fieldname': 'sublist',
                                                 'translator': subtranslator})}

            TRANSLATORS = [translator]

            def __init__(self):
                super(TestDriver, self).__init__('', None)

        schema = TestDriver().get_schema()

        self.assertEqual(2, len(schema))
        self.assertEqual(
            ({'name': 'id_col', 'desc': None},
             {'name': 'unique_key', 'desc': None}), schema['testtable'])
        self.assertEqual(
            ({'name': 'parent_key', 'desc': None},
             {'name': 'val', 'desc': None}), schema['subtable'])

    def test_get_schema_with_hdict_parent_and_id_col_in_subtranslator(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            subtranslator = {'translation-type': 'LIST',
                             'table-name': 'subtable',
                             'id-col': 'id', 'val-col': 'val',
                             'translator': self.val_trans}

            translator = {'translation-type': 'HDICT',
                          'table-name': 'testtable',
                          'selector-type': 'DICT_SELECTOR',
                          'field-translators': ({'fieldname': 'unique_key',
                                                 'translator': self.val_trans},
                                                {'fieldname': 'sublist',
                                                 'translator': subtranslator})}

            TRANSLATORS = [translator]

            def __init__(self):
                super(TestDriver, self).__init__('', None)

        schema = TestDriver().get_schema()

        self.assertEqual(2, len(schema))
        self.assertEqual(
            ({'desc': None, 'name': 'unique_key'},
             {'desc': None, 'name': 'sublist'}), schema['testtable'])
        self.assertEqual(
            ({'desc': None, 'name': 'id'},
             {'desc': None, 'name': 'val'}), schema['subtable'])

    def test_get_schema_with_hdict_id_function(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            translator = {
                'translation-type': 'HDICT',
                'table-name': 'testtable',
                'id-col': lambda obj: obj,
                'selector-type': 'DICT_SELECTOR',
                'field-translators': ({'fieldname': 'field1',
                                       'desc': 'test-field-1',
                                       'translator': self.val_trans},
                                      {'fieldname': 'field2',
                                       'desc': 'test-field-2',
                                       'translator': self.val_trans})}

            TRANSLATORS = [translator]

            def __init__(self):
                super(TestDriver, self).__init__('', None)

        schema = TestDriver().get_schema()

        self.assertEqual(1, len(schema))
        self.assertEqual(
            ({'name': 'id-col', 'desc': None},
             {'name': 'field1', 'desc': 'test-field-1'},
             {'name': 'field2', 'desc': 'test-field-2'}), schema['testtable'])

    def test_get_schema_with_vdict_parent(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            subtranslator = {'translation-type': 'LIST',
                             'table-name': 'subtable',
                             'parent-key': 'id_col', 'val-col': 'val',
                             'translator': self.val_trans}

            translator = {'translation-type': 'VDICT',
                          'table-name': 'testtable',
                          'id-col': 'id_col',
                          'key-col': 'key',
                          'val-col': 'val',
                          'translator': subtranslator}

            TRANSLATORS = [translator]

            def __init__(self):
                super(TestDriver, self).__init__('', None)

        schema = TestDriver().get_schema()

        self.assertEqual(2, len(schema))
        self.assertEqual(('id_col', 'key'), schema['testtable'])
        self.assertEqual(
            ({'name': 'parent_key', 'desc': None},
             {'name': 'val', 'desc': None}), schema['subtable'])

    def test_get_tablename(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            translator1 = {
                'translation-type': 'HDICT',
                'table-name': 'table-name1',
                'selector-type': 'DICT_SELECTOR',
                'field-translators':
                    ({'fieldname': 'col1', 'translator': self.val_trans},
                     {'fieldname': 'col2', 'translator': self.val_trans})
                }
            TRANSLATORS = [translator1]

            def __init__(self):
                super(TestDriver, self).__init__('', None)

        expected_ret = 'table-name1'
        ret = TestDriver().get_tablename('table-name1')
        self.assertEqual(expected_ret, ret)

    def test_get_tablenames(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            translator1 = {
                'translation-type': 'HDICT',
                'table-name': 'table-name1',
                'selector-type': 'DICT_SELECTOR',
                'field-translators':
                    ({'fieldname': 'col1', 'translator': self.val_trans},
                     {'fieldname': 'col2', 'translator': self.val_trans})
                }
            translator2 = {
                'translation-type': 'HDICT',
                'table-name': 'table-name2',
                'selector-type': 'DICT_SELECTOR',
                'field-translators':
                    ({'fieldname': 'col1', 'translator': self.val_trans},
                     {'fieldname': 'col2', 'translator': self.val_trans})
                }

            TRANSLATORS = [translator1, translator2]

            def __init__(self):
                super(TestDriver, self).__init__('', None)

        expected_ret = ['table-name1', 'table-name2']
        ret = TestDriver().get_tablenames()
        self.assertEqual(set(expected_ret), set(ret))

    def test_get_row_data(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            def __init__(self):
                super(TestDriver, self).__init__('', None)

        test_driver = TestDriver()
        test_driver.state = {'fake_table': [('d1', 'd2'), ('d3', 'd4')]}
        result = test_driver.get_row_data('fake_table')
        expected = [{'data': ('d1', 'd2')},
                    {'data': ('d3', 'd4')}]
        self.assertItemsEqual(expected, result)

    def test_nested_get_tables(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            translator2 = {
                'translation-type': 'HDICT',
                'table-name': 'table-name2',
                'selector-type': 'DICT_SELECTOR',
                'field-translators':
                    ({'fieldname': 'col1', 'translator': self.val_trans},
                     {'fieldname': 'col2', 'translator': self.val_trans})
                }

            translator1 = {
                'translation-type': 'HDICT',
                'table-name': 'table-name1',
                'selector-type': 'DICT_SELECTOR',
                'field-translators':
                    ({'fieldname': 'col1', 'translator': self.val_trans},
                     {'fieldname': 'col2', 'translator': translator2})
                }

            TRANSLATORS = [translator1]

            def __init__(self):
                super(TestDriver, self).__init__('', None)

        expected_ret = ['table-name1', 'table-name2']
        ret = TestDriver().get_tablenames()
        self.assertEqual(set(expected_ret), set(ret))

    def test_update_state_on_changed(self):
        mocked_self = mock.MagicMock()
        mocked_self.raw_state = dict()
        resource = 'fake_resource'

        @datasource_utils.update_state_on_changed(resource)
        def _translate_raw_data(_self, raw_data):
            return mock.sentinel.translated_data

        result = _translate_raw_data(mocked_self, mock.sentinel.raw_data)

        self.assertEqual(mock.sentinel.translated_data, result)
        self.assertEqual(mock.sentinel.raw_data,
                         mocked_self.raw_state[resource])
        mocked_self._update_state.assert_called_once_with(
            resource, mock.sentinel.translated_data)

        # raw data is not changed, don't translate anything.
        result = _translate_raw_data(mocked_self, mock.sentinel.raw_data)

        self.assertEqual([], result)
        self.assertEqual(mock.sentinel.raw_data,
                         mocked_self.raw_state[resource])
        mocked_self._update_state.assert_called_once_with(
            resource, mock.sentinel.translated_data)

    def test_update_state_on_changed_with_changed_raw_data(self):
        mocked_self = mock.MagicMock()
        mocked_self.raw_state = dict()
        resource = 'fake_resource'
        mocked_self.raw_state[resource] = mock.sentinel.last_data

        @datasource_utils.update_state_on_changed(resource)
        def _translate_raw_data(_self, raw_data):
            return mock.sentinel.translated_data

        result = _translate_raw_data(mocked_self, mock.sentinel.new_data)

        self.assertEqual(mock.sentinel.translated_data, result)
        self.assertEqual(mock.sentinel.new_data,
                         mocked_self.raw_state[resource])
        mocked_self._update_state.assert_called_once_with(
            resource, mock.sentinel.translated_data)

    def test_update_state_on_changed_with_empty_raw_data(self):
        mocked_self = mock.MagicMock()
        mocked_self.raw_state = dict()
        resource = 'fake_resource'
        mocked_self.raw_state[resource] = mock.sentinel.last_data

        @datasource_utils.update_state_on_changed(resource)
        def _translate_raw_data(_self, raw_data):
            return []

        result = _translate_raw_data(mocked_self, [])

        self.assertEqual([], result)
        self.assertEqual([], mocked_self.raw_state[resource])
        mocked_self._update_state.assert_called_once_with(resource, [])

    # The test case should be removed, once oslo-incubator bug/1499369 is
    # resolved.
    def test_update_state_on_changed_with_wrong_eq(self):
        class EqObject(object):
            def __eq__(self, other):
                return True

        mocked_self = mock.MagicMock()
        mocked_self.raw_state = dict()
        resource = 'fake_resource'
        cached_data = EqObject()
        mocked_self.raw_state[resource] = [cached_data]

        @datasource_utils.update_state_on_changed(resource)
        def _translate_raw_data(_self, raw_data):
            return []

        new_data = EqObject()
        _translate_raw_data(mocked_self, [new_data])
        mocked_self._update_state.assert_called_once_with(resource, [])
        self.assertIs(new_data, mocked_self.raw_state[resource][0])

    def test_update_state(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            def __init__(self):
                super(TestDriver, self).__init__('', None)

        test_driver = TestDriver()
        test_driver.state = {'fake_table': set(), 'foo_table': set(),
                             'unchanged_table': {mock.sentinel.data}}
        test_driver._table_deps = {'fake_table': ['fake_table', 'foo_table'],
                                   'unchanged_table': ['unchanged_table']}

        row_data = [('fake_table', mock.sentinel.data1),
                    ('fake_table', mock.sentinel.data2),
                    ('foo_table', mock.sentinel.data3)]
        expected_state = {'fake_table': {mock.sentinel.data1,
                                         mock.sentinel.data2},
                          'foo_table': {mock.sentinel.data3},
                          'unchanged_table': {mock.sentinel.data}}

        test_driver._update_state('fake_table', row_data)

        self.assertEqual(expected_state, test_driver.state)

    def test_update_state_with_undefined_table(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            def __init__(self):
                super(TestDriver, self).__init__('', None)

        test_driver = TestDriver()
        test_driver.state = {'fake_table': set(), 'foo_table': set()}
        test_driver._table_deps = {'fake_table': ['fake_table', 'foo_table']}

        row_data = [('fake_table', mock.sentinel.data1),
                    ('foo_table', mock.sentinel.data2),
                    ('undefined_table', mock.sentinel.data3)]
        expected_state = {'fake_table': {mock.sentinel.data1},
                          'foo_table': {mock.sentinel.data2}}

        test_driver._update_state('fake_table', row_data)

        self.assertEqual(expected_state, test_driver.state)

    def test_update_state_with_none_row_data(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            def __init__(self):
                super(TestDriver, self).__init__('', None)

        test_driver = TestDriver()
        test_driver.state = {'fake_table': {mock.sentinel.data1},
                             'foo_table': {mock.sentinel.data2}}
        test_driver._table_deps = {'fake_table': ['fake_table', 'foo_table']}

        expected_state = {'fake_table': set(), 'foo_table': set()}
        test_driver._update_state('fake_table', [])

        self.assertEqual(expected_state, test_driver.state)

    def test_update_state_with_part_none_row_data(self):
        class TestDriver(datasource_driver.DataSourceDriver):
            def __init__(self):
                super(TestDriver, self).__init__('', None)

        test_driver = TestDriver()
        test_driver.state = {'fake_table': set(),
                             'foo_table': {mock.sentinel.data3}}
        test_driver._table_deps = {'fake_table': ['fake_table', 'foo_table']}

        row_data = [('fake_table', mock.sentinel.data1),
                    ('fake_table', mock.sentinel.data2)]
        expected_state = {'fake_table': {mock.sentinel.data1,
                                         mock.sentinel.data2},
                          'foo_table': set()}

        test_driver._update_state('fake_table', row_data)

        self.assertEqual(expected_state, test_driver.state)

    def test_build_table_deps(self):
        level10_translator = {
            'translation-type': 'HDICT',
            'table-name': 'level10',
            'parent-key': 'parent_key',
            'selector-type': 'DICT_SELECTOR',
            'in-list': True,
            'field-translators':
                ({'fieldname': 'level3_thing', 'translator': self.val_trans},)}

        level3_translator = {
            'translation-type': 'HDICT',
            'table-name': 'level3',
            'parent-key': 'parent_key',
            'selector-type': 'DICT_SELECTOR',
            'in-list': True,
            'field-translators':
                ({'fieldname': 'level3_thing', 'translator': self.val_trans},)}

        level2_translator = {
            'translation-type': 'HDICT',
            'table-name': 'level2',
            'parent-key': 'id',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'thing', 'translator': self.val_trans},
                 {'fieldname': 'level3',
                  'translator': level3_translator})}

        level1_translator = {
            'translation-type': 'HDICT',
            'table-name': 'level1',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'id', 'translator': self.val_trans},
                 {'fieldname': 'level2',
                  'translator': level2_translator})}

        driver = datasource_driver.DataSourceDriver('', None)
        driver.register_translator(level1_translator)
        driver.register_translator(level10_translator)
        expected_table_deps = {'level1': ['level1', 'level2', 'level3'],
                               'level10': ['level10']}
        self.assertEqual(expected_table_deps, driver._table_deps)

    @mock.patch.object(eventlet, 'spawn')
    def test_init_consistence_with_exception(self, mock_spawn):
        class TestDriver(datasource_driver.DataSourceDriver):
            def __init__(self):
                super(TestDriver, self).__init__('', None)
                self.do_something()
                self._init_end_start_poll()

            def do_something(self):
                pass

        with mock.patch.object(TestDriver, "do_something",
                               side_effect=Exception()):
            test_driver = None
            try:
                test_driver = TestDriver()
                self.fail("Exception should be raised")
            except Exception:
                self.assertEqual(0, mock_spawn.call_count)
                self.assertIsNone(test_driver)

    def test_objects_extract_func(self):
        def translate_json_str_to_list(objs):
            result = []
            data_list = objs['result']
            for k, v in data_list.items():
                dict_obj = json.loads(v)
                for key, value in dict_obj.items():
                    obj = {
                        'key': key,
                        'value': value
                        }
                    result.append(obj)

            return result

        test_translator = {
            'translation-type': 'HDICT',
            'table-name': 'test',
            'selector-type': 'DICT_SELECTOR',
            'objects-extract-fn': translate_json_str_to_list,
            'field-translators':
                ({'fieldname': 'key', 'translator': self.val_trans},
                 {'fieldname': 'value', 'translator': self.val_trans})
            }

        objs = {
            "result": {
                "data1": """{"key1": "value1", "key2": "value2"}""",
                }
            }

        expected_ret = [('test', ('key1', 'value1')),
                        ('test', ('key2', 'value2'))]

        driver = datasource_driver.DataSourceDriver('', None)
        driver.register_translator(test_translator)

        ret = driver.convert_objs(objs, test_translator)

        for row in ret:
            self.assertIn(row, expected_ret)
            expected_ret.remove(row)
        self.assertEqual([], expected_ret)

    def test_recursive_objects_extract_func(self):
        def translate_json_str_to_list(objs):
            result = []
            data_str = objs['data']
            dict_list = json.loads(data_str)
            for key, value in dict_list.items():
                obj = {
                    'key': key,
                    'value': value
                    }
                result.append(obj)
            return result

        test_child_translator = {
            'translation-type': 'HDICT',
            'table-name': 'test-child',
            'parent-key': 'id',
            'parent-col-name': 'result',
            'selector-type': 'DICT_SELECTOR',
            'in-list': True,
            'objects-extract-fn': translate_json_str_to_list,
            'field-translators':
                ({'fieldname': 'key', 'translator': self.val_trans},
                 {'fieldname': 'value', 'translator': self.val_trans})
            }

        test_parent_translator = {
            'translation-type': 'HDICT',
            'table-name': 'test-parent',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'id', 'translator': self.val_trans},
                 {'fieldname': 'result', 'translator': test_child_translator})
            }

        expected_ret = [('test-parent', ('id-1', )),
                        ('test-child', ('id-1', 'key1', 'value1')),
                        ('test-child', ('id-1', 'key2', 'value2'))]

        objs = [{
            "id": "id-1",
            "result": {
                "data": """{"key1": "value1", "key2": "value2"}""",
                }
            }]

        driver = datasource_driver.DataSourceDriver('', None)
        driver.register_translator(test_parent_translator)

        ret = driver.convert_objs(objs, test_parent_translator)

        for row in ret:
            self.assertIn(row, expected_ret)
            expected_ret.remove(row)
        self.assertEqual([], expected_ret)

# Old version
# class TestPollingDataSourceDriver(base.TestCase):
#     class TestDriver(datasource_driver.PollingDataSourceDriver):
#         def __init__(self):
#             super(TestPollingDataSourceDriver.TestDriver, self).__init__(
#                 '', '', None, None, None)
#             self._init_end_start_poll()

#     def setUp(self):
#         super(TestPollingDataSourceDriver, self).setUp()

#     @mock.patch.object(eventlet, 'spawn')
#     def test_init_consistence(self, mock_spawn):
#         test_driver = TestPollingDataSourceDriver.TestDriver()
#         mock_spawn.assert_called_once_with(test_driver.poll_loop,
#                                            test_driver.poll_time)
#         self.assertTrue(test_driver.initialized)
#         self.assertIsNotNone(test_driver.worker_greenthread)

#     @mock.patch.object(eventlet.greenthread, 'kill')
#     @mock.patch.object(eventlet, 'spawn')
#     def test_cleanup(self, mock_spawn, mock_kill):
#         dummy_thread = dict()
#         mock_spawn.return_value = dummy_thread

#         test_driver = TestPollingDataSourceDriver.TestDriver()

#         self.assertEqual(test_driver.worker_greenthread, dummy_thread)

#         test_driver.cleanup()

#         mock_kill.assert_called_once_with(dummy_thread)
#         self.assertIsNone(test_driver.worker_greenthread)


class TestPollingDataSourceDriver(base.TestCase):
    class TestDriver(datasource_driver.PollingDataSourceDriver):
        def __init__(self):
            super(TestPollingDataSourceDriver.TestDriver, self).__init__()
            self.node = 'node'
            self._rpc_server = mock.MagicMock()
            self._init_end_start_poll()

    def setUp(self):
        super(TestPollingDataSourceDriver, self).setUp()

    @mock.patch.object(eventlet, 'spawn')
    def test_init_consistence(self, mock_spawn):
        test_driver = TestPollingDataSourceDriver.TestDriver()
        mock_spawn.assert_not_called()
        self.assertIsNone(test_driver.worker_greenthread)
        test_driver.start()
        mock_spawn.assert_called_once_with(test_driver.poll_loop,
                                           test_driver.poll_time)
        self.assertTrue(test_driver.initialized)
        self.assertIsNotNone(test_driver.worker_greenthread)

    @mock.patch.object(eventlet.greenthread, 'kill')
    @mock.patch.object(eventlet, 'spawn')
    def test_cleanup(self, mock_spawn, mock_kill):
        dummy_thread = mock.MagicMock()
        mock_spawn.return_value = dummy_thread

        test_driver = TestPollingDataSourceDriver.TestDriver()
        test_driver.start()

        self.assertEqual(test_driver.worker_greenthread, dummy_thread)

        test_driver.stop()

        mock_kill.assert_called_once_with(dummy_thread)
        self.assertIsNone(test_driver.worker_greenthread)

    def test_evaluate_lazy_table(self):
        args = {'lazy_tables': ['fake_table']}
        test_driver = fake_datasource.FakeDataSource(args=args)

        self.assertNotIn('fake_table', test_driver._table_deps)
        test_driver.update_from_datasource()
        self.assertEqual(test_driver.update_number, 0)

        test_driver.get_snapshot('fake_table')

        self.assertIn('fake_table', test_driver._table_deps)
        test_driver.update_from_datasource()
        # update happens twice before the check. First one is in get_snapshot.
        self.assertEqual(test_driver.update_number, 2)

    def test_add_update_method(self):
        class TestDriver(datasource_driver.PollingDataSourceDriver):
            test_translator = {
                'table-name': 'test'
                }

            def __init__(self):
                super(TestDriver, self).__init__('', None)
                self.add_update_method(self.update_method,
                                       self.test_translator)

            def update_method(self):
                pass

        test_driver = TestDriver()
        self.assertEqual(test_driver.update_methods['test'],
                         test_driver.update_method)

    def test_add_duplicated_update_method(self):
        class TestDriver(datasource_driver.PollingDataSourceDriver):
            test_translator = {
                'table-name': 'test'
                }

            def __init__(self):
                super(TestDriver, self).__init__('', None)
                self.add_update_method(self.update_method,
                                       self.test_translator)

            def update_method(self):
                pass

        test_driver = TestDriver()
        self.assertRaises(exception.Conflict, test_driver.add_update_method,
                          test_driver.update_method,
                          test_driver.test_translator)


class TestPushedDriver(base.SqlTestCase):
    class TestDriver(datasource_driver.PushedDataSourceDriver):
        value_trans = {'translation-type': 'VALUE'}
        test_translator = {
            'translation-type': 'HDICT',
            'table-name': 'test_translator',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'id', 'translator': value_trans},
                 {'fieldname': 'name', 'translator': value_trans},
                 {'fieldname': 'status', 'translator': value_trans})
            }

        TRANSLATORS = [test_translator]

        def __init__(self, args=None):
            super(TestPushedDriver.TestDriver, self).__init__('test-pushed',
                                                              args)

    def setUp(self):
        super(TestPushedDriver, self).setUp()

    def test_init_push_driver(self):
        test_driver = TestPushedDriver.TestDriver()
        self.assertTrue(test_driver.initialized)

    @mock.patch.object(datasource_driver.DataSourceDriver, 'publish')
    def test_push_entire_data(self, mock_publish):
        test_driver = TestPushedDriver.TestDriver()
        obj = [
            {'id': 1, 'name': 'column1', 'status': 'up'},
            {'id': 2, 'name': 'column2', 'status': 'down'}
            ]
        test_driver.replace_entire_table_data('test_translator', obj)
        expected_state = set([
            (1, 'column1', 'up'),
            (2, 'column2', 'down')])

        mock_publish.assert_called_with('test_translator',
                                        test_driver.state['test_translator'])
        self.assertEqual(expected_state, test_driver.state['test_translator'])

    @mock.patch.object(datasource_driver.DataSourceDriver, 'publish')
    def test_persist_data(self, mock_publish):
        ds_id = uuidutils.generate_uuid()
        obj = [
            {'id': 1, 'name': 'column1', 'status': 'up'},
            {'id': 2, 'name': 'column2', 'status': 'down'}
            ]

        # test no persist if not enabled
        test_driver = TestPushedDriver.TestDriver(
            args={'ds_id': ds_id, 'persist_data': False})
        test_driver.replace_entire_table_data('test_translator', obj)
        expected_state = set([
            (1, 'column1', 'up'),
            (2, 'column2', 'down')])
        self.assertEqual(expected_state, test_driver.state['test_translator'])
        self.assertEqual(
            [], db_ds_table_data.get_ds_table_data(test_driver.ds_id))

        # test data persisted in DB
        test_driver = TestPushedDriver.TestDriver(
            args={'ds_id': ds_id, 'persist_data': True})
        test_driver.replace_entire_table_data('test_translator', obj)
        expected_state = set([
            (1, 'column1', 'up'),
            (2, 'column2', 'down')])
        self.assertEqual(expected_state, test_driver.state['test_translator'])
        self.assertEqual(
            [{'tablename': 'test_translator', 'tabledata': expected_state}],
            db_ds_table_data.get_ds_table_data(test_driver.ds_id))

        # test no restoring persisted data if not enabled
        del test_driver
        test_driver = TestPushedDriver.TestDriver(
            args={'ds_id': ds_id, 'persist_data': False})
        self.assertEqual(0, len(test_driver.state['test_translator']))
        self.assertEqual(set([]), test_driver.state['test_translator'])

        # test restoring persisted data
        del test_driver
        test_driver = TestPushedDriver.TestDriver(
            args={'ds_id': ds_id, 'persist_data': True})
        self.assertEqual(expected_state, test_driver.state['test_translator'])


class TestExecutionDriver(base.TestCase):
    class ExtendedExecutionDriver(datasource_driver.ExecutionDriver):
        """Subclass of test target.

        Execution Driver is an add-on class for datasource driver so
        it's assumed to have heartbeat_callbacks variable defined in
        DataService class.
        """
        def __init__(self):
            # A variable defined in datasource_driver
            self.name = 'TestExecutionDriver'
            self.heartbeat_callbacks = {}
            super(TestExecutionDriver.ExtendedExecutionDriver, self).__init__()
            self.method_structured_args = {
                'action_struct': {'named': frozenset(['arg2', 'arg3'])}}

    def setUp(self):
        super(TestExecutionDriver, self).setUp()
        self.exec_driver = TestExecutionDriver.ExtendedExecutionDriver()

    def test_get_method_nested(self):
        class server(object):
            def nested_method(self):
                return True

        class NovaClient(object):
            def __init__(self):
                self.servers = server()

            def top_method(self):
                return True

        nova_client = NovaClient()
        method = self.exec_driver._get_method(nova_client,
                                              "servers.nested_method")
        self.assertTrue(method())

    def test_get_method_top(self):
        class NovaClient(object):
            def top_method(self):
                return True

        nova_client = NovaClient()
        method = self.exec_driver._get_method(nova_client, "top_method")
        self.assertTrue(method())

    def test_execute_api(self):
        class NovaClient(object):
            def action(self, arg1, arg2, arg3):
                return "arg1=%s arg2=%s arg3=%s" % (arg1, arg2, arg3)

        nova_client = NovaClient()
        arg = {"positional": ["value1", "value2"], "named": {"arg3": "value3"}}
        # it will raise exception if the method _execute_api failed to location
        # the api
        self.exec_driver._execute_api(nova_client, "action", arg)

    def test_execute_api_structured_args(self):
        class NovaClient(object):
            def action_struct(self, arg1, arg2, arg3):
                return (arg1, arg2, arg3)

        nova_client = NovaClient()
        arg = {"positional": ["value1", '{"value2":2}'],
               "named": {"arg3": '{"value3":3}'}}
        # it will raise exception if the method _execute_api failed to location
        # the api
        self.assertEqual(
            ("value1", {"value2": 2}, {"value3": 3}),
            self.exec_driver._execute_api(nova_client, "action_struct", arg))

        arg = {"positional": ["value1", "}{invalid"],
               "named": {"arg3": '{"value3":3}'}}

        self.assertRaisesRegexp(
            exception.CongressException, '.*invalid format.*',
            self.exec_driver._execute_api, nova_client, "action_struct", arg)

    def test_get_actions_order_by_name(self):
        mock_methods = {'funcA': mock.MagicMock(),
                        'funcH': mock.MagicMock(),
                        'funcF': mock.MagicMock()}
        with mock.patch.dict(self.exec_driver.executable_methods,
                             mock_methods):
            action_list = self.exec_driver.get_actions().get('results')
            expected_list = copy.deepcopy(action_list)
            expected_list.sort(key=lambda item: item['name'])
            self.assertEqual(expected_list, action_list)

    def test_add_executable_client_methods(self):
        class FakeNovaClient(object):

            def _internal_action(self, arg1, arg2):
                """internal action with docs.

                :param arg1: internal test arg1
                :param arg2: internal test arg2
                """
                pass

            def action_no_doc(self, arg1, arg2):
                pass

            def action_doc(self, arg1, arg2):
                """action with docs.

                :param arg1: test arg1
                :param arg2: test arg2
                """
                pass

        expected_methods = {'action_doc': [[{'desc': 'arg1: test arg1',
                                             'name': 'arg1'},
                                            {'desc': 'arg2: test arg2',
                                             'name': 'arg2'}],
                                           'action with docs. '],
                            'action_no_doc': [[], '']}

        nova_client = FakeNovaClient()
        api_prefix = 'congress.tests.datasources.test_datasource_driver'
        self.exec_driver.add_executable_client_methods(nova_client, api_prefix)
        self.assertEqual(expected_methods, self.exec_driver.executable_methods)

    @mock.patch.object(eventlet, 'spawn')
    def test_request_execute_with_wait(self, mock_spawn):
        thread = mock.MagicMock()
        mock_spawn.return_value = thread

        context = {'node_id': 'fake_node'}
        action = 'test-action'
        action_args = ()

        test_driver = fake_datasource.FakeDataSource()
        test_driver.request_execute(context, action, action_args, True)
        mock_spawn.assert_called_once_with(test_driver.execute,
                                           action, action_args)
        thread.wait.assert_called_once()

    @mock.patch.object(eventlet, 'spawn')
    @mock.patch.object(eventlet.greenthread.GreenThread, 'wait')
    def test_request_execute_without_wait(self, mock_wait, mock_spawn):
        mock_wait.return_value = mock.MagicMock()
        mock_spawn.return_value = mock.MagicMock()

        context = {'node_id': 'fake_node'}
        action = 'test-action'
        action_args = []

        test_driver = fake_datasource.FakeDataSource()
        test_driver.request_execute(context, action, action_args, False)
        mock_spawn.assert_called_once_with(test_driver.execute,
                                           action, action_args)
        mock_wait.assert_not_called()
