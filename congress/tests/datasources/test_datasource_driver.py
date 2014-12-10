#!/usr/bin/env python
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

# FIXME(arosen): we should just import off of datasource_driver below
# rather than also importing DataSourceDriver directly.
from congress.datasources.datasource_driver import DataSourceDriver
from congress import exception
from congress.tests import base
from congress.tests.datasources.util import ResponseObj
from congress.tests import helper

import hashlib
import json


class TestDatasourceDriver(base.TestCase):

    def setUp(self):
        super(TestDatasourceDriver, self).setUp()
        self.val_trans = {'translation-type': 'VALUE'}

    def compute_hash(self, obj):
        s = json.dumps(sorted(obj), sort_keys=True)
        h = hashlib.md5(s).hexdigest()
        return h

    def test_in_list_results_hdict_hdict(self):
        ports_fixed_ips_translator = {
            'translation-type': 'HDICT',
            'table-name': 'fixed-ips',
            'parent-key': 'id',
            'selector-type': 'DICT_SELECTOR',
            'in-list': True,
            'field-translators':
                ({'fieldname': 'ip_address', 'translator': self.val_trans},
                 {'fieldname': 'subnet_id', 'translator': self.val_trans})}

        ports_translator = {
            'translation-type': 'HDICT',
            'table-name': 'ports',
            'selector-type': 'DICT_SELECTOR',
            'field-translators':
                ({'fieldname': 'id', 'translator': self.val_trans},
                 {'fieldname': 'fixed_ips',
                  'translator': ports_fixed_ips_translator})}

        driver = DataSourceDriver('', '', None, None, None)
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

        driver = DataSourceDriver('', '', None, None, None)
        driver.register_translator(level1_translator)
        data = [
            {'id': 11, 'level2':
                {'thing': 'blah!', 'level3': [{'level3_thing': '12345'}]}}]

        row_data = driver.convert_objs(data, level1_translator)
        expected = [('level3', (11, '12345')),
                    ('level2', (11, 'blah!')),
                    ('level1', (11,))]
        self.assertEqual(row_data, expected)

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
        driver = DataSourceDriver('', '', None, None, None)
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
        driver = DataSourceDriver('', '', None, None, None)
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
        driver = DataSourceDriver('', '', None, None, None)
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

        driver = DataSourceDriver('', '', None, None, None)
        self.assertRaises(exception.DuplicateTableName,
                          driver.register_translator,
                          translator)

    def test_invalid_translation_type(self):
        translator = {'translation-type': 'YOYO',
                      'table-name': 'table1'}
        driver = DataSourceDriver('', '', None, None, None)
        self.assertRaises(exception.InvalidTranslationType,
                          driver.register_translator,
                          translator)

    def test_no_key_col_in_vdict(self):
        translator = {'translation-type': 'VDICT',
                      'table-name': 'table1',
                      'val-col': 'id-col'}
        driver = DataSourceDriver('', '', None, None, None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_no_val_col_in_vdict(self):
        translator = {'translation-type': 'VDICT',
                      'table-name': 'table1',
                      'key-col': 'id-col'}
        driver = DataSourceDriver('', '', None, None, None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_no_val_col_in_list(self):
        translator = {'translation-type': 'LIST',
                      'table-name': 'table1'}
        driver = DataSourceDriver('', '', None, None, None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_no_parent_key_id_col(self):
        translator = {'translation-type': 'LIST',
                      'table-name': 'table1',
                      'id-col': 'id-col',
                      'parent-key': 'parent_key_column'}

        # Test LIST
        driver = DataSourceDriver('', '', None, None, None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)
        # Test HDICT
        translator['translation-type'] = 'VDICT'
        driver = DataSourceDriver('', '', None, None, None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)
        # Test HDICT
        translator['translation-type'] = 'HDICT'
        driver = DataSourceDriver('', '', None, None, None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_check_no_extra_params(self):
        translator = {'translation-type': 'LIST',
                      'table-name': 'table1',
                      'id-col': 'id-col',
                      'invalid_column': 'blah'}

        driver = DataSourceDriver('', '', None, None, None)
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

        driver = DataSourceDriver('', '', None, None, None)
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

        driver = DataSourceDriver('', '', None, None, None)
        self.assertRaises(exception.InvalidParamException,
                          driver.register_translator,
                          translator)

    def test_convert_vdict_with_id(self):
        # Test a single VDICT with an id column.
        resp = {'a': 'FOO', 'b': 123}
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
                      'translator': self.val_trans}
        rows, k = DataSourceDriver.convert_obj(resp, translator)

        k1 = self.compute_hash((('a', 'FOO'), ('b', 123)))

        self.assertEqual(2, len(rows))
        self.assertEqual(k1, k)
        self.assertTrue(('testtable', (k, 'a', 'FOO')) in rows)
        self.assertTrue(('testtable', (k, 'b', 123)) in rows)

    def test_convert_vdict_without_id(self):
        # Test a single VDICT without an id column.
        resp = {'a': 'FOO', 'b': 123}
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'key-col': 'key', 'val-col': 'value',
                      'translator': self.val_trans}
        rows, k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(2, len(rows))
        self.assertEqual(None, k)
        self.assertTrue(('testtable', ('a', 'FOO')) in rows)
        self.assertTrue(('testtable', ('b', 123)) in rows)

    def test_convert_vdict_list(self):
        # Test a VDICT that contains lists.
        resp = {'foo': (1, 2, 3), 'bar': ('a', 'b')}
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
                      'translator': {'translation-type': 'LIST',
                                     'table-name': 'subtable',
                                     'id-col': 'id_col', 'val-col': 'val_col',
                                     'translator': self.val_trans}}
        rows, actual_k = DataSourceDriver.convert_obj(resp, translator)

        k1 = self.compute_hash((1, 2, 3))
        k2 = self.compute_hash(('a', 'b'))
        k = self.compute_hash((('foo', k1), ('bar', k2)))

        self.assertEqual(7, len(rows))
        self.assertEqual(k, actual_k)

        self.assertTrue(('subtable', (k1, 1)) in rows)
        self.assertTrue(('subtable', (k1, 2)) in rows)
        self.assertTrue(('subtable', (k1, 3)) in rows)
        self.assertTrue(('subtable', (k2, 'a')) in rows)
        self.assertTrue(('subtable', (k2, 'b')) in rows)
        self.assertTrue(('testtable', (k, 'foo', k1)) in rows)
        self.assertTrue(('testtable', (k, 'bar', k2)) in rows)

    def test_convert_vdict_is_none(self):
        # Test a single VDICT with an id column.
        resp = None
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
                      'translator': self.val_trans}
        rows, k = DataSourceDriver.convert_obj(resp, translator)
        self.assertTrue(rows is None)

    def test_convert_list_with_id(self):
        # Test a single LIST with an id_column
        resp = (1, 'a', 'b', True)
        translator = {'translation-type': 'LIST', 'table-name': 'testtable',
                      'id-col': 'id_col', 'val-col': 'value',
                      'translator': self.val_trans}
        rows, k = DataSourceDriver.convert_obj(resp, translator)

        k1 = self.compute_hash((1, 'a', 'b', 'True'))

        self.assertEqual(4, len(rows))
        self.assertEqual(k1, k)
        self.assertTrue(('testtable', (k, 1)) in rows)
        self.assertTrue(('testtable', (k, 'a')) in rows)
        self.assertTrue(('testtable', (k, 'b')) in rows)
        self.assertTrue(('testtable', (k, 'True')) in rows)

    def test_convert_list_without_id(self):
        # Test a single LIST without an id_column
        resp = (1, 'a', 'b', True)
        translator = {'translation-type': 'LIST', 'table-name': 'testtable',
                      'val-col': 'value', 'translator': self.val_trans}
        rows, k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(4, len(rows))
        self.assertEqual(None, k)
        self.assertTrue(('testtable', (1,)) in rows)
        self.assertTrue(('testtable', ('a',)) in rows)
        self.assertTrue(('testtable', ('b',)) in rows)
        self.assertTrue(('testtable', ('True',)) in rows)

    def test_convert_list_with_sublist(self):
        # Test a single LIST with an id_column
        resp = ((1, 2, 3), ('a', 'b', 'c'), (True, False))
        translator = {'translation-type': 'LIST', 'table-name': 'testtable',
                      'id-col': 'id_col', 'val-col': 'value',
                      'translator': {'translation-type': 'LIST',
                                     'table-name': 'subtable',
                                     'id-col': 'id_col', 'val-col': 'val_col',
                                     'translator': self.val_trans}}
        rows, actual_k = DataSourceDriver.convert_obj(resp, translator)

        k1 = self.compute_hash((1, 2, 3))
        k2 = self.compute_hash(('a', 'b', 'c'))
        k3 = self.compute_hash(('True', 'False'))
        k = self.compute_hash((k1, k2, k3))

        self.assertEqual(11, len(rows))
        self.assertEqual(k, actual_k)
        self.assertTrue(('subtable', (k1, 1)) in rows)
        self.assertTrue(('subtable', (k1, 2)) in rows)
        self.assertTrue(('subtable', (k1, 3)) in rows)
        self.assertTrue(('subtable', (k2, 'a')) in rows)
        self.assertTrue(('subtable', (k2, 'b')) in rows)
        self.assertTrue(('subtable', (k2, 'c')) in rows)
        self.assertTrue(('subtable', (k3, 'True')) in rows)
        self.assertTrue(('subtable', (k3, 'False')) in rows)
        self.assertTrue(('testtable', (k, k1)) in rows)
        self.assertTrue(('testtable', (k, k2)) in rows)
        self.assertTrue(('testtable', (k, k3)) in rows)

    def test_convert_recursive_hdict_single_fields(self):
        # Test simple fields inside of an HDICT
        resp = ResponseObj({'testfield1': 'FOO',
                            'testfield2': 123})
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                          {'fieldname': 'testfield1', 'col': 'col1',
                           'translator': self.val_trans},
                          {'fieldname': 'testfield2', 'col': 'col2',
                           'translator': self.val_trans})}
        rows, k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(1, len(rows))
        self.assertEqual(None, k)
        self.assertEqual([('testtable', ('FOO', 123))], rows)

    def test_convert_recursive_hdict_single_fields_empty_fields(self):
        # Test simple fields inside of an HDICT where the translator
        # interprests a non-present field as None.
        resp = ResponseObj({'testfield1': 'FOO'})
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                          {'fieldname': 'testfield1', 'col': 'col1',
                           'translator': self.val_trans},
                          {'fieldname': 'testfield2', 'col': 'col2',
                           'translator': self.val_trans})}
        rows, k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(1, len(rows))
        self.assertEqual(None, k)
        self.assertEqual([('testtable', ('FOO', 'None'))], rows)

    def test_convert_recursive_hdict_single_fields_default_col(self):
        # Test simple fields inside of an HDICT using the default col name.

        resp = ResponseObj({'testfield1': 'FOO'})
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                          {'fieldname': 'testfield1',
                           'translator': self.val_trans},)}
        rows, k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(1, len(rows))
        self.assertEqual(None, k)
        self.assertEqual([('testtable', ('FOO',))], rows)

    def test_convert_recursive_hdict_extract_subfields(self):
        # Test simple fields inside of an HDICT
        # Also tests with and without extract-fn.
        field = ResponseObj({'b': 123})
        resp = ResponseObj({'testfield1': {'a': 'FOO'},
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
        rows, k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(1, len(rows))
        self.assertEqual(self.compute_hash(('FOO', 123, 456)), k)
        self.assertEqual([('testtable', (k, 'FOO', 123, 456))], rows)

    def test_convert_recursive_hdict_sublists(self):
        # Test sublists inside of an HDICT
        resp = ResponseObj({'testfield1': ('FOO', 'BAR'),
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
        rows, k = DataSourceDriver.convert_obj(resp, translator)

        k1 = self.compute_hash(('FOO', 'BAR'))
        k2 = self.compute_hash((1, 2, 3))

        self.assertEqual(None, k)
        self.assertEqual(6, len(rows))
        self.assertTrue(('subtable1', (k1, 'FOO')) in rows)
        self.assertTrue(('subtable1', (k1, 'BAR')) in rows)
        self.assertTrue(('subtable2', (k2, 1)) in rows)
        self.assertTrue(('subtable2', (k2, 2)) in rows)
        self.assertTrue(('subtable2', (k2, 3)) in rows)
        self.assertTrue(('testtable', (k1, k2)) in rows)

    def test_convert_recursive_hdict_vdict(self):
        # Test translator of an VDICT inside of an HDICT
        resp = ResponseObj({'testfield1': {'a': 123, 'b': 456},
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
        rows, k = DataSourceDriver.convert_obj(resp, translator)

        k1 = self.compute_hash((('a', 123), ('b', 456)))
        k2 = self.compute_hash((('c', 'abc'), ('d', 'def')))

        self.assertEqual(None, k)
        self.assertEqual(5, len(rows))
        self.assertTrue(('subtable1', (k1, 'a', 123)) in rows)
        self.assertTrue(('subtable1', (k1, 'b', 456)) in rows)
        self.assertTrue(('subtable2', (k2, 'c', 'abc')) in rows)
        self.assertTrue(('subtable2', (k2, 'd', 'def')) in rows)
        self.assertTrue(('testtable', (k1, k2)) in rows)

    def test_convert_recursive_hdict_hdict(self):
        # Test translator of an HDICT inside of an HDICT.
        resp = ResponseObj({'testfield1': {'a': 123, 'b': 456},
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

        rows, k = DataSourceDriver.convert_obj(resp, translator)

        k1 = self.compute_hash((123, 456))
        k2 = self.compute_hash(('abc', 'def'))

        self.assertEqual(None, k)
        self.assertEqual(3, len(rows))
        self.assertTrue(('subtable1', (k1, 123, 456)) in rows)
        self.assertTrue(('subtable2', (k2, 'abc', 'def')) in rows)
        self.assertTrue(('testtable', (k1, k2)) in rows)

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

        rows, k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(2, len(rows))
        self.assertEqual(None, k)

        self.assertTrue(('subtable', (100, 123)) in rows)
        self.assertTrue(('testtable', (100,)) in rows)

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

        rows, actual_k = DataSourceDriver.convert_obj(resp, translator)

        k = self.compute_hash((100,))
        self.assertEqual(2, len(rows))
        self.assertEqual(k, actual_k)

        self.assertTrue(('subtable', (100, 123)) in rows)
        self.assertTrue(('testtable', (k, 100,)) in rows)

    def test_convert_hdict_vdict_parent_key_without_id(self):
        # Test a HDICT that contains lists using a parent_key.
        resp = ResponseObj({'foreign-key': 100, 'foo': {'f1': 123, 'f2': 456}})
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

        rows, k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(3, len(rows))
        self.assertEqual(None, k)

        self.assertTrue(('subtable', (100, 'f1', 123)) in rows)
        self.assertTrue(('subtable', (100, 'f2', 456)) in rows)
        self.assertTrue(('testtable', (100,)) in rows)

    def test_convert_hdict_vdict_parent_key_with_id(self):
        # Test a HDICT that contains lists using a parent_key.
        resp = ResponseObj({'foreign-key': 100, 'foo': {'f1': 123, 'f2': 456}})
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

        rows, k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(3, len(rows))
        self.assertEqual(self.compute_hash((100,)), k)

        self.assertTrue(('subtable', (100, 'f1', 123)) in rows)
        self.assertTrue(('subtable', (100, 'f2', 456)) in rows)
        self.assertTrue(('testtable', (k, 100)) in rows)

    def test_convert_hdict_list_parent_key_without_id(self):
        # Test a HDICT that contains lists using a parent_key.
        resp = ResponseObj({'foreign-key': 100, 'foo': (1, 2)})
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

        rows, k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(3, len(rows))
        self.assertEqual(None, k)

        self.assertTrue(('subtable', (100, 1)) in rows)
        self.assertTrue(('subtable', (100, 2)) in rows)
        self.assertTrue(('testtable', (100,)) in rows)

    def test_convert_hdict_list_parent_key_with_id(self):
        # Test a HDICT that contains lists using a parent_key.
        resp = ResponseObj({'foreign-key': 100, 'foo': (1, 2)})
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

        rows, k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(3, len(rows))
        self.assertEqual(self.compute_hash((100,)), k)

        self.assertTrue(('subtable', (100, 1)) in rows)
        self.assertTrue(('subtable', (100, 2)) in rows)
        self.assertTrue(('testtable', (k, 100)) in rows)

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
        rows, actual_k = DataSourceDriver.convert_obj(resp, translator)

        self.assertEqual(7, len(rows))
        self.assertEqual(None, actual_k)

        self.assertTrue(('subtable', ('foo', 1)) in rows)
        self.assertTrue(('subtable', ('foo', 2)) in rows)
        self.assertTrue(('subtable', ('foo', 3)) in rows)
        self.assertTrue(('subtable', ('bar', 'a')) in rows)
        self.assertTrue(('subtable', ('bar', 'b')) in rows)
        self.assertTrue(('testtable', ('foo',)) in rows)
        self.assertTrue(('testtable', ('bar',)) in rows)

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
        rows, actual_k = DataSourceDriver.convert_obj(resp, translator)

        k = self.compute_hash((('foo',), ('bar',)))

        self.assertEqual(7, len(rows))
        self.assertEqual(k, actual_k)

        self.assertTrue(('subtable', ('foo', 1)) in rows)
        self.assertTrue(('subtable', ('foo', 2)) in rows)
        self.assertTrue(('subtable', ('foo', 3)) in rows)
        self.assertTrue(('subtable', ('bar', 'a')) in rows)
        self.assertTrue(('subtable', ('bar', 'b')) in rows)
        self.assertTrue(('testtable', (k, 'foo')) in rows)
        self.assertTrue(('testtable', (k, 'bar')) in rows)

    def test_convert_bad_params(self):
        def verify_invalid_params(translator, err_msg):
            driver = DataSourceDriver('', '', None, None,
                                      args=helper.datasource_openstack_args())
            try:
                driver.register_translator(translator)
            except exception.InvalidParamException as e:
                self.assertTrue(err_msg in str(e))
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
        class TestDriver(DataSourceDriver):
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
                                         'translator': self.val_trans},
                                        {'fieldname': 'b',
                                         'col': 'b1',
                                         'translator': self.val_trans})}},
                    {'fieldname': 'testfield2',
                     'translator': {'translation-type': 'HDICT',
                                    'table-name': 'subtable2',
                                    'id-col': 'id2',
                                    'field-translators': (
                                        {'fieldname': 'c',
                                         'col': 'c1',
                                         'translator': self.val_trans},
                                        {'fieldname': 'd',
                                         'col': 'd1',
                                         'translator': self.val_trans})}},
                    {'fieldname': 'ztestfield3', 'col': 'zparent_col3',
                     'translator': self.val_trans},
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

            def __init__(self):
                super(TestDriver, self).__init__('', '', None, None, None)
                self.register_translator(self.translator)

        schema = TestDriver().get_schema()
        self.assertEqual(7, len(schema))
        self.assertTrue(schema['subtable1'] == ('id1', 'a1', 'b1'))
        self.assertTrue(schema['subtable2'] == ('id2', 'c1', 'd1'))
        self.assertTrue(schema['subtable3'] == ('id3', 'key3', 'value3'))
        self.assertTrue(schema['subtable4'] == ('id4', 'value4'))
        self.assertTrue(schema['subtable5'] == ('key5', 'value5'))
        self.assertTrue(schema['subtable6'] == ('value6',))
        self.assertTrue(schema['testtable'] == ('parent_col1', 'testfield2',
                                                'zparent_col3', 'parent_col4',
                                                'parent_col5', 'parent_col6',
                                                'parent_col7', 'parent_col8'))

    def test_get_schema_with_table_reuse(self):
        class TestDriver(DataSourceDriver):
            translator = {'translation-type': 'LIST',
                          'table-name': 'testtable',
                          'id-col': 'id_col', 'val-col': 'value',
                          'translator': {'translation-type': 'LIST',
                                         'table-name': 'testtable',
                                         'id-col': 'id', 'val-col': 'val',
                                         'translator': self.val_trans}}

            def __init__(self):
                super(TestDriver, self).__init__('', '', None, None, None)
                self.register_translator(self.translator)

        try:
            TestDriver().get_schema()
        except exception.DuplicateTableName, e:
            self.assertTrue('table (testtable) used twice' in str(e))
        else:
            self.fail("Expected InvalidParamException but got none")

    def test_get_schema_with_hdict_parent(self):
        class TestDriver(DataSourceDriver):
            subtranslator = {'translation-type': 'LIST',
                             'table-name': 'subtable',
                             'parent-key': 'id', 'val-col': 'val',
                             'translator': self.val_trans}

            translator = {'translation-type': 'HDICT',
                          'table-name': 'testtable',
                          'id-col': 'id_col',
                          'selector-type': 'DICT_SELECTOR',
                          'field-translators': ({'fieldname': 'unique_key',
                                                 'translator': self.val_trans},
                                                {'fieldname': 'sublist',
                                                 'translator': subtranslator})}

            def __init__(self):
                super(TestDriver, self).__init__('', '', None, None, None)
                self.register_translator(self.translator)

        schema = TestDriver().get_schema()

        self.assertEqual(2, len(schema))
        self.assertTrue(schema['testtable'] == ('id_col', 'unique_key'))
        self.assertTrue(schema['subtable'] == ('parent_key', 'val'))

    def test_get_schema_with_vdict_parent(self):
        class TestDriver(DataSourceDriver):
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

            def __init__(self):
                super(TestDriver, self).__init__('', '', None, None, None)
                self.register_translator(self.translator)

        schema = TestDriver().get_schema()

        self.assertEqual(2, len(schema))
        self.assertTrue(schema['testtable'] == ('id_col', 'key'))
        self.assertTrue(schema['subtable'] == ('parent_key', 'val'))
