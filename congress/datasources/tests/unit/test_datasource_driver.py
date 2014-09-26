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

from congress.datasources.datasource_driver import DataSourceDriver
from congress.datasources.datasource_driver import InvalidParamException
from congress.datasources.tests.unit.util import ResponseObj
from congress.tests import base

import hashlib
import json


class TestDatasourceDriver(base.TestCase):

    def setUp(self):
        super(TestDatasourceDriver, self).setUp()
        self.value_trans = {'translation-type': 'VALUE'}

    def compute_hash(self, obj):
        s = json.dumps(sorted(obj), sort_keys=True)
        h = hashlib.md5(s).hexdigest()
        return h

    def test_convert_vdict_with_id(self):
        # Test a single VDICT with an id column.
        resp = {'a': 'FOO', 'b': 123}
        translator = {'translation-type': 'VDICT', 'table-name': 'testtable',
                      'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
                      'translator': self.value_trans}
        rows, k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

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
                      'translator': self.value_trans}
        rows, k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

        k1 = self.compute_hash((('a', 'FOO'), ('b', 123)))

        self.assertEqual(2, len(rows))
        self.assertEqual(k1, k)
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
                                     'translator': self.value_trans}}
        rows, actual_k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

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

    def test_convert_list_with_id(self):
        # Test a single LIST with an id_column
        resp = (1, 'a', 'b', True)
        translator = {'translation-type': 'LIST', 'table-name': 'testtable',
                      'id-col': 'id_col', 'val-col': 'value',
                      'translator': self.value_trans}
        rows, k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

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
                      'val-col': 'value', 'translator': self.value_trans}
        rows, k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

        k1 = self.compute_hash((1, 'a', 'b', 'True'))

        self.assertEqual(4, len(rows))
        self.assertEqual(k1, k)
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
                                     'translator': self.value_trans}}
        rows, actual_k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

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
                 'translator': self.value_trans},
                {'fieldname': 'testfield2', 'col': 'col2',
                 'translator': self.value_trans})}
        rows, k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

        self.assertEqual(1, len(rows))
        self.assertEqual(self.compute_hash(('FOO', 123)), k)
        self.assertEqual([('testtable', ('FOO', 123))], rows)

    def test_convert_recursive_hdict_single_fields_empty_fields(self):
        # Test simple fields inside of an HDICT where the translator
        # interprests a non-present field as None.
        resp = ResponseObj({'testfield1': 'FOO'})
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                {'fieldname': 'testfield1', 'col': 'col1',
                 'translator': self.value_trans},
                {'fieldname': 'testfield2', 'col': 'col2',
                 'translator': self.value_trans})}
        rows, k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

        self.assertEqual(1, len(rows))
        self.assertEqual(self.compute_hash(('FOO', 'None')), k)
        self.assertEqual([('testtable', ('FOO', 'None'))], rows)

    def test_convert_recursive_hdict_single_fields_default_col(self):
        # Test simple fields inside of an HDICT using the default col name.

        resp = ResponseObj({'testfield1': 'FOO'})
        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                {'fieldname': 'testfield1', 'translator': self.value_trans},)}
        rows, k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

        self.assertEqual(1, len(rows))
        self.assertEqual(self.compute_hash(('FOO',)), k)
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
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

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
                                'translator': self.value_trans}},
                {'fieldname': 'testfield2', 'col': 'col2',
                 'translator': {'translation-type': 'LIST',
                                'table-name': 'subtable2',
                                'id-col': 'id', 'val-col': 'value',
                                'translator': self.value_trans}})}
        rows, k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

        k1 = self.compute_hash(('FOO', 'BAR'))
        k2 = self.compute_hash((1, 2, 3))
        k3 = self.compute_hash((k1, k2))

        self.assertEqual(k3, k)
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
                                'translator': self.value_trans}},
                {'fieldname': 'testfield2', 'col': 'col2',
                 'translator': {'translation-type': 'VDICT',
                                'table-name': 'subtable2',
                                'id-col': 'id', 'key-col': 'key',
                                'val-col': 'value',
                                'translator': self.value_trans}})}
        rows, k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

        k1 = self.compute_hash((('a', 123), ('b', 456)))
        k2 = self.compute_hash((('c', 'abc'), ('d', 'def')))
        k3 = self.compute_hash((k1, k2))

        self.assertEqual(k3, k)
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
                 'translator': self.value_trans},
                {'fieldname': 'b',
                 'col': 'b1',
                 'translator': self.value_trans})}

        subtranslator_2 = {'translation-type': 'HDICT',
                           'table-name': 'subtable2',
                           'selector-type': 'DICT_SELECTOR',
                           'id-col': 'id',
                           'field-translators': (
                {'fieldname': 'c',
                 'col': 'c1',
                 'translator': self.value_trans},
                {'fieldname': 'd',
                 'col': 'd1',
                 'translator': self.value_trans})}

        translator = {'translation-type': 'HDICT', 'table-name': 'testtable',
                      'selector-type': 'DOT_SELECTOR',
                      'field-translators': (
                {'fieldname': 'testfield1', 'col': 'col1',
                 'translator': subtranslator_1},
                {'fieldname': 'testfield2', 'col': 'col2',
                 'translator': subtranslator_2})}

        rows, k = DataSourceDriver.convert_obj(resp, translator)
        print "Rows: %s" % ('\n'.join([str(x) for x in rows]))

        k1 = self.compute_hash((123, 456))
        k2 = self.compute_hash(('abc', 'def'))
        k3 = self.compute_hash((k1, k2))

        self.assertEqual(k3, k)
        self.assertEqual(3, len(rows))
        self.assertTrue(('subtable1', (k1, 123, 456)) in rows)
        self.assertTrue(('subtable2', (k2, 'abc', 'def')) in rows)
        self.assertTrue(('testtable', (k1, k2)) in rows)

    def test_convert_bad_params(self):
        def verify_invalid_params(translator, err_msg):
            try:
                rows, k = DataSourceDriver.convert_obj(None, translator)
            except InvalidParamException, e:
                self.assertTrue(err_msg in str(e))
            else:
                self.fail("Expected InvalidParamException but got none")

        # Test an invalid translation-type.
        verify_invalid_params(
            {'translation-typeXX': 'VDICT', 'table-name': 'testtable',
             'id-col': 'id_col', 'key-col': 'key', 'val-col': 'value',
             'translator': self.value_trans},
            'Param (translation-type) must be in translator')

        # Test invalid HDICT params
        verify_invalid_params(
            {'translation-type': 'HDICT', 'table-nameXX': 'testtable',
             'id-col': 'id_col', 'selector-type': 'DOT_SELECTOR',
             'field-translators': ({'fieldname': 'abc',
                                   'translator': self.value_trans},)},
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
             'translator': self.value_trans},
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
             'translator': self.value_trans},
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

    def test_convert_with_table_reuse(self):
        # Test a LIST containing a LIST with the same table name.
        resp = ((1, 2), (3, 4))
        translator = {'translation-type': 'LIST', 'table-name': 'testtable',
                      'id-col': 'id_col', 'val-col': 'value',
                      'translator': {'translation-type': 'LIST',
                                     'table-name': 'testtable',
                                     'id-col': 'id', 'val-col': 'val',
                                     'translator': self.value_trans}}
        try:
            rows, k = DataSourceDriver.convert_obj(resp, translator)
        except InvalidParamException, e:
            self.assertTrue('table (testtable) used twice' in str(e))
        else:
            self.fail("Expected error on table reuse, but got none")

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
                                 'translator': self.value_trans},
                                {'fieldname': 'b',
                                 'col': 'b1',
                                 'translator': self.value_trans})}},
                    {'fieldname': 'testfield2',
                     'translator': {'translation-type': 'HDICT',
                                    'table-name': 'subtable2',
                                    'id-col': 'id2',
                                    'field-translators': (
                                {'fieldname': 'c',
                                 'col': 'c1',
                                 'translator': self.value_trans},
                                {'fieldname': 'd',
                                 'col': 'd1',
                                 'translator': self.value_trans})}},
                    {'fieldname': 'ztestfield3', 'col': 'zparent_col3',
                     'translator': self.value_trans},
                    {'fieldname': 'testfield4', 'col': 'parent_col4',
                     'translator': {'translation-type': 'VALUE',
                                    'extract_fn': lambda x: x.id}},
                    {'fieldname': 'testfield5', 'col': 'parent_col5',
                     'translator': {'translation-type': 'VDICT',
                                    'table-name': 'subtable3', 'id-col': 'id3',
                                    'key-col': 'key3', 'val-col': 'value3',
                                    'translator': self.value_trans}},
                    {'fieldname': 'testfield6', 'col': 'parent_col6',
                     'translator': {'translation-type': 'LIST',
                                    'table-name': 'subtable4', 'id-col': 'id4',
                                    'val-col': 'value4',
                                    'translator': self.value_trans}},
                    {'fieldname': 'testfield7', 'col': 'parent_col7',
                     'translator': {'translation-type': 'VDICT',
                                    'table-name': 'subtable5',
                                    'key-col': 'key5', 'val-col': 'value5',
                                    'translator': self.value_trans}},
                    {'fieldname': 'testfield8', 'col': 'parent_col8',
                     'translator': {'translation-type': 'LIST',
                                    'table-name': 'subtable6',
                                    'val-col': 'value6',
                                    'translator': self.value_trans}})}

            def __init__(self):
                pass

            @classmethod
            def get_translators(cls):
                return (cls.translator,)

        schema = TestDriver.get_schema()
        print "SCHEMA: %s" % str([str((k, schema[k]))
                                  for k in sorted(schema.keys())])
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
                                         'translator': self.value_trans}}

            def __init__(self):
                pass

            @classmethod
            def get_translators(cls):
                return (cls.translator,)

        try:
            schema = TestDriver.get_schema()
            print "SCHEMA: " + str(schema)
        except InvalidParamException, e:
            self.assertTrue('table testtable already in schema' in str(e))
        else:
            self.fail("Expected InvalidParamException but got none")
