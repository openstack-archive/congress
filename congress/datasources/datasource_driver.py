#!/usr/bin/env python
# Copyright (c) 2013,2014 VMware, Inc. All rights reserved.
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
# TODO(thinrichs): not all datasources poll, though for now that's the only
# option.  Create PollingDataSourceDriver subclass to handle the polling
# logic.

import time

from congress.dse import deepsix
from congress import exception
from congress.openstack.common import log as logging
from congress.policy import compile
from congress.policy import runtime
from congress.utils import value_to_congress

import datetime
import hashlib
import json

LOG = logging.getLogger(__name__)


class DataSourceDriver(deepsix.deepSix):
    """A super-class for datasource drivers.  This class implements a polling
    mechanism for polling a datasource.

    This class also implements a translation mechanism that accepts data from
    the datasource in the form of Python lists, dicts, and individual values,
    and puts that data into Congress data tables.  The translation mechanism
    takes a declarative description of the Python object's structure, for
    example, whether an object is a list or dict, if a list contains another
    list, which dict keys to extract, and the tables and columns in which to
    put the extracted data.

    The DataSourceDriver uses a predefined scheme for translating datasource
    objects into Congress tables.  For example, the driver converts a list
    containing individual values into a single table, where each row contains
    an entry from the list, but the declarative description enables us to
    control the table names and column names used for the resulting table
    schema.

    The declarative description consists of four different types of
    translator: HDICT, VDICT, LIST, and VALUE.  A translator itself is a
    python dict containing several parameters.  The translation-type parameter
    describes which of the four types the translator is; the remainder of the
    parameters describe things like the table, column names, and
    sub-translators.

    HDICT parameters with example values:
      {'translation-type': 'HDICT',
       'table-name': 'example_table',
       'parent-key': 'parent_key_column',
       'id-col': 'id_col',
       'selector-type': 'DOT_SELECTOR',
       'field-translators': ({'fieldname': 'field1', 'col': 'col1',
                              'translator': {'translation-type': 'VALUE'}},
                             {'fieldname': 'field2', 'col': 'col2',
                              'translator': {'translation-type': 'VALUE'})}

      The HDICT translator reads in a python dict and translates each key in
      the dict into a column of the output table.  The fields in the table
      will be in the same order as the fields in the HDICT translator.  Use
      selector-type to specify whether to access the fields using dot
      notation such as 'obj.field1' or using a dict selector such as
      obj['field1'].  SELECTOR must be either 'DOT_SELECTOR' or
      'DICT_SELECTOR'.  If the translator contains a field, but the object
      does not contain that field, the translator will populate the column
      with 'None'.

      If 'parent-key' is specified, the translator prepends a value from the
      parent translator as the first column of this table.  For example, if
      the parent table already has a unique key named 'id', then setting
      'parent-key': 'id' will populate each row in the child table with the
      unique foreign key from the parent.  Also, if the subtranslator
      specifies a 'parent-key', the parent table will not have a column for
      that subtranslator.  For example, if the subtranslator for 'field1'
      specifies a 'parent-key', the parent table will not have a column for
      field1; instead, the parent table's parent_key_column will be the
      foreign key into the subtable.

      Instead, if 'id-col' is specified, the translator will prepend a unique
      id column to each row where the id's value is the hash of the remaining
      columns for that row.  Using both parent-key and id-col at the same time
      is redudant, so DataSourceDriver will reject that configuration.

      The example translator expects an object such as:
        {'field1': 123, 'field2': 456}
      and populates a table 'example_table' with row (id, 123, 456) where id
      is equal to the hash of (123, 456).

      Recursion: If a field-translator is a translator other than VALUE, then
      that field-translator will cause the creation of a second table.  The
      field-translator will populate the second table, and each row in the
      primary table will (in the column for that field) contain a hash of the
      second table's entries derived from the the primary table's row.  For
      example, if the translator is:

      {'translation-type': 'HDICT',
       'table-name': 'example_table',
       'selector-type': 'DOT_SELECTOR',
       'field-translators': ({'fieldname': 'field1', 'col': 'col1',
                              'translator': {
           'translation-type': 'LIST',
           'table-name': 'subtable',
           'val-col': 'c',
           'translator': {'translation-type': 'VALUE'}},})}

      The object {'field1': [1, 2, 3]} will translate to one tuple in
      example_table and three tuples in subtable:
        example_table: (h(1, 2, 3))
        subtable: (h(1, 2, 3), 1)
                  (h(1, 2, 3), 2)
                  (h(1, 2, 3), 3)

    VDICT parameters with example values:
      {'translation-type': 'VDICT',
       'table-name': 'table',
       'parent-key': 'parent_key_column',
       'id-col': 'id_col',
       'key-col': 'key_col',
       'val-col': 'value_col',
       'translator': TRANSLATOR}

      The VDICT translator reads in a python dict, and turns each key-value
      pair into a row of the output table.  The output table will have 2 or 3
      columns, depending on whether the 'id-col' or 'parent-key' is present.
      Recursion works as it does with HDICT.

      VDICT treats a subtranslator with a 'parent-key' the same way that a
      HDICT does.  The subtranslator prepends the parent's key value to each
      row of the subtable, i.e. (parent_key_column, key_col, value_col).
      Instead if 'id-col' is present, the columns will be (id_col, key_col,
      value_col), otherwise (key_col, value_col).  However, if the VDICT's
      subtranslator specifies the parent-key, the parent-key must be the
      VDICT's 'val-col' column due to an implementation choice (the id column
      is not available until after the subtranslator runs).

    LIST parameters with example values:
      {'translation-type': 'LIST',
       'table-name': 'table1',
       'parent-key': 'parent_key_column',
       'id-col': 'id_col',
       'val-col': 'value_col',
       'translator': {'translation-type': 'VALUE'}}

      The LIST translator is like the VDICT translator, except that it reads a
      python list from the object, and produces 1 or 2 columns depending on
      whether 'id-col' is present.  It always produces a column for id-col.
      The content of id-col is either a value (if the translator is a VALUE)
      or a hash of a recursive value as in HDICT.

      A LIST may specify a parent-key when the LIST is a subtranslator, but
      the subtranslator of a LIST may not specify a 'parent-key' because the
      LIST's table will then have no columns.

   VALUE parameters with example values:
     {'translation-type': 'VALUE',
      'extract-fn': lambda x: x.['foo']}

      The VALUE translator reads a single value like and int or a string from
      the object.  The translator uses the extract-fn to extract a value from
      the object.  If 'extract-fn' is not defined, then the default extract
      function is the identity function.  The resulting value will be either a
      number such as 123 or a string.  It will translate a boolean value to
      the string 'True' or 'False'.
    """

    HDICT = 'HDICT'
    VDICT = 'VDICT'
    LIST = 'LIST'
    VALUE = 'VALUE'

    DICT_SELECTOR = 'DICT_SELECTOR'
    DOT_SELECTOR = 'DOT_SELECTOR'

    # Translator params:
    TRANSLATION_TYPE = 'translation-type'
    TABLE_NAME = 'table-name'
    PARENT_KEY = 'parent-key'
    ID_COL = 'id-col'
    SELECTOR_TYPE = 'selector-type'
    FIELD_TRANSLATORS = 'field-translators'
    FIELDNAME = 'fieldname'
    TRANSLATOR = 'translator'
    COL = 'col'
    KEY_COL = 'key-col'
    VAL_COL = 'val-col'
    EXTRACT_FN = 'extract-fn'

    # Name of the column name when using a parent key.
    PARENT_KEY_COL_NAME = 'parent_key'

    # valid params
    HDICT_PARAMS = (TRANSLATION_TYPE, TABLE_NAME, PARENT_KEY, ID_COL,
                    SELECTOR_TYPE, FIELD_TRANSLATORS)
    FIELD_TRANSLATOR_PARAMS = (FIELDNAME, COL, TRANSLATOR)
    VDICT_PARAMS = (TRANSLATION_TYPE, TABLE_NAME, PARENT_KEY, ID_COL, KEY_COL,
                    VAL_COL, TRANSLATOR)
    LIST_PARAMS = (TRANSLATION_TYPE, TABLE_NAME, PARENT_KEY, ID_COL, VAL_COL,
                   TRANSLATOR)
    VALUE_PARAMS = (TRANSLATION_TYPE, EXTRACT_FN)
    TRANSLATION_TYPE_PARAMS = (TRANSLATION_TYPE,)
    VALID_TRANSLATION_TYPES = (HDICT, VDICT, LIST, VALUE)

    def __init__(self, name, keys, inbox, datapath, args):
        self.initialized = False
        if args is None:
            args = dict()
        if 'poll_time' in args:
            self.poll_time = int(args['poll_time'])
        else:
            self.poll_time = 10
        # default to open-stack credentials, since that's the common case
        self.last_poll_time = None
        self.last_error = None
        self.number_of_updates = 0

        # a dictionary from tablename to the SET of tuples, both currently
        #  and in the past.
        self.prior_state = dict()
        self.state = dict()

        # set of translators that are registered with datasource.
        self._translators = []

        # Make sure all data structures above are set up *before* calling
        #   this because it will publish info to the bus.
        super(DataSourceDriver, self).__init__(name, keys, inbox, datapath)

    def _get_translator_params(self, translator_type):
        if translator_type is self.HDICT:
            return self.HDICT_PARAMS
        elif translator_type is self.VDICT:
            return self.VDICT_PARAMS
        elif translator_type is self.LIST:
            return self.LIST_PARAMS
        elif translator_type is self.VALUE:
            return self.VALUE_PARAMS
        else:
            raise TypeError("Invalid translator_type")

    def _validate_non_value_type_properties(self, translator):
        """HDICT, VDICT, and LIST types all share some common properties."""
        parent_key = translator.get(self.PARENT_KEY)
        id_col = translator.get(self.ID_COL)

        # Specifying both parent-key and id_col in a translator is not valid,
        # one should use one or the other but not both.
        if parent_key and id_col:
            raise exception.InvalidParamException(
                'Specify at most one of %s or %s' %
                (self.PARENT_KEY, self.ID_COL))

    def _validate_hdict_type(self, translator):
        # validate field-translators
        field_translators = translator[self.FIELD_TRANSLATORS]
        for field_translator in field_translators:
            self.check_params(field_translator.keys(),
                              self.FIELD_TRANSLATOR_PARAMS)
            subtranslator = field_translator[self.TRANSLATOR]
            self._validate_translator(subtranslator)

    def _validate_list_type(self, translator):
        if self.VAL_COL not in translator:
            raise exception.InvalidParamException(
                "Param (%s) must be in translator" % self.VAL_COL)

        subtranslator = translator[self.TRANSLATOR]
        self._validate_translator(subtranslator)

    def _validate_vdict_type(self, translator):
        if self.KEY_COL not in translator:
            raise exception.InvalidParamException(
                "Param (%s) must be in translator" % self.KEY_COL)
        if self.VAL_COL not in translator:
            raise exception.InvalidParamException(
                "Param (%s) must be in translator" % self.VAL_COL)

        subtranslator = translator[self.TRANSLATOR]
        self._validate_translator(subtranslator)

    def _validate_by_translation_type(self, translator):
        translation_type = translator[self.TRANSLATION_TYPE]

        # validate that only valid params are present
        self.check_params(translator.keys(),
                          self._get_translator_params(translation_type))

        if translation_type is not self.VALUE:
            self._validate_non_value_type_properties(translator)
            table_name = translator[self.TABLE_NAME]
            if table_name in self.state:
                raise exception.DuplicateTableName(
                    'table (%s) used twice' % table_name)
            self.state[table_name] = set()
        if translation_type is self.HDICT:
            self._validate_hdict_type(translator)
        elif translation_type in self.LIST:
            self._validate_list_type(translator)
        elif translation_type is self.VDICT:
            self._validate_vdict_type(translator)

    def _validate_translator(self, translator):
        translation_type = translator.get(self.TRANSLATION_TYPE)

        if self.TRANSLATION_TYPE not in translator:
            raise exception.InvalidParamException(
                "Param (%s) must be in translator" % self.TRANSLATION_TYPE)

        # check that translation_type is valid
        if translation_type not in self.VALID_TRANSLATION_TYPES:
            msg = ("Translation Type %s not a valid transltion-type %s" % (
                   translation_type, self.VALID_TRANSLATION_TYPES))
            raise exception.InvalidTranslationType(msg)
        self._validate_by_translation_type(translator)

    def register_translator(self, translator):
        """Registers translator with congress and validates its schema."""
        self._validate_translator(translator)
        self._translators.append(translator)

    def get_translators(self):
        """Returns a list of translators that describes how to translate from
        the datasource's data structures to the Congress tables.
        """
        return self._translators

    def get_schema(self):
        """Returns a dictionary mapping tablenames to the list of
        column names for that table.  Both tablenames and columnnames
        are strings.
        """
        def _get_schema(translator, schema):
            self.check_translation_type(translator.keys())
            translation_type = translator[self.TRANSLATION_TYPE]
            if translation_type == self.HDICT:
                # A missing parameter will raise a KeyError
                tablename = translator[self.TABLE_NAME]
                parent_key = translator.get(self.PARENT_KEY, None)
                id_col = translator.get(self.ID_COL, None)
                field_translators = translator[self.FIELD_TRANSLATORS]

                columns = []
                if id_col is not None:
                    columns.append(id_col)
                elif parent_key is not None:
                    columns.append(self.PARENT_KEY_COL_NAME)

                for field_translator in field_translators:
                    col = field_translator.get(
                        self.COL, field_translator[self.FIELDNAME])
                    subtranslator = field_translator[self.TRANSLATOR]
                    if self.PARENT_KEY not in subtranslator:
                        columns.append(col)
                    _get_schema(subtranslator, schema)

                if tablename in schema:
                    raise exception.InvalidParamException(
                        "table %s already in schema" % tablename)
                schema[tablename] = tuple(columns)
            elif translation_type == self.VDICT:
                tablename = translator[self.TABLE_NAME]
                parent_key = translator.get(self.PARENT_KEY, None)
                id_col = translator.get(self.ID_COL, None)
                key_col = translator[self.KEY_COL]
                value_col = translator[self.VAL_COL]
                subtrans = translator[self.TRANSLATOR]

                _get_schema(subtrans, schema)
                if tablename in schema:
                    raise exception.InvalidParamException(
                        "table %s already in schema" % tablename)
                # Construct the schema for this table.
                new_schema = (key_col,)
                if id_col:
                    new_schema = (id_col,) + new_schema
                elif parent_key:
                    new_schema = (self.PARENT_KEY_COL_NAME,) + new_schema
                if self.PARENT_KEY not in subtrans:
                    new_schema = new_schema + (value_col,)

                schema[tablename] = new_schema

            elif translation_type == self.LIST:
                tablename = translator[self.TABLE_NAME]
                parent_key = translator.get(self.PARENT_KEY, None)
                id_col = translator.get(self.ID_COL, None)
                value_col = translator[self.VAL_COL]
                trans = translator[self.TRANSLATOR]

                _get_schema(trans, schema)
                if tablename in schema:
                    raise exception.InvalidParamException(
                        "table %s already in schema" % tablename)
                if id_col:
                    schema[tablename] = (id_col, value_col)
                elif parent_key:
                    schema[tablename] = (self.PARENT_KEY_COL_NAME, value_col)
                else:
                    schema[tablename] = (value_col,)

            elif translation_type == self.VALUE:
                pass
            else:
                raise AssertionError('Unexpected translator type %s' %
                                     translation_type)
            return schema

        all_schemas = {}
        for trans in self.get_translators():
            _get_schema(trans, all_schemas)
        return all_schemas

    def get_column_map(self, tablename):
        """Given a tablename, returns a dictionary mapping the columnnames
        of that table to the integer position of that column.  Returns None
        if tablename is not in the schema.
        """
        schema = self.get_schema()
        if tablename not in schema:
            return
        return {name: index for index, name in enumerate(schema[tablename])}

    def get_last_updated_time(self):
        return self.last_poll_time

    def get_status(self):
        d = {}
        d['last_updated'] = str(self.last_poll_time)
        d['last_error'] = str(self.last_error)
        d['number_of_updates'] = str(self.number_of_updates)
        d['initialized'] = str(self.initialized)
        d['subscriptions'] = [(value.key, value.dataindex)
                              for value in self.subdata.values()]
        d['subscribers'] = [(name, pubdata.dataindex)
                            for pubdata in self.pubdata.values()
                            for name in pubdata.subscribers]

        # d['inbox_size'] = str(len(self.inbox))
        return d

    def state_set_diff(self, state1, state2, table=None):
        """Given 2 tuplesets STATE1 and STATE2, return the set difference
        STATE1-STATE2.  Each tupleset is represented as a dictionary
        from tablename to set of tuples.  Return value is a tupleset,
        also represented as a dictionary from tablename to set of tuples.
        """
        if table is None:
            diff = {}
            for tablename in state1:
                if tablename not in state2:
                    # make sure to copy the set (the set-diff below does too)
                    diff[tablename] = set(state1[tablename])
                else:
                    diff[tablename] = state1[tablename] - state2[tablename]
            return diff
        else:
            if table not in state1:
                return set()
            if table not in state2:
                # make copy
                return set(state1[table])
            else:
                return state1[table] - state2[table]

    @classmethod
    def need_column_for_subtable_id(cls, subtranslator):
        if cls.ID_COL in subtranslator:
            return True
        return False

    @classmethod
    def _get_value(cls, o, field, selector):
        if selector == cls.DOT_SELECTOR:
            if hasattr(o, field):
                return getattr(o, field)
            return
        elif selector == cls.DICT_SELECTOR:
            if field in o:
                return o[field]
            return
        else:
            raise AssertionError("Unexpected selector type: %s" %
                                 (str(selector),))

    @classmethod
    def _compute_hash(cls, obj):
        # This might turn out to be expensive.

        # The datasource can contain a list which has an order, but
        # Congress uses unordered sets internally for its tables which
        # throw away a list's order.  Since Congress throws away the
        # order, this hash function needs to reimpose an order (by
        # sorting) to ensure that two invocations of the hash function
        # will always return the same result.
        s = json.dumps(sorted(obj), sort_keys=True)
        h = hashlib.md5(s).hexdigest()
        return h

    @classmethod
    def _extract_value(cls, obj, extract_fn):
        # Reads a VALUE object and returns (result_rows, h)
        if extract_fn is None:
            extract_fn = lambda x: x
        return value_to_congress(extract_fn(obj))

    @classmethod
    def convert_obj(cls, obj, translator, parent_row_dict=None):
        """Takes an object and a translation descriptor.  Returns two items:
        (1) a list of tuples where the first element is the name of a table,
        and the second element is a tuple to be inserted into the table, and

        (2) if the translator specified an id-col, then return the id's value
        here.  The id is a hash that takes into account all the content of the
        list of tuples.  The hash can be used as a unique key to identify the
        content in obj.  Otherwise, return None here.
        """

        if obj is None:
            return None, None

        translation_type = translator[cls.TRANSLATION_TYPE]
        if translation_type == cls.HDICT:
            table = translator[cls.TABLE_NAME]
            parent_key = translator.get(cls.PARENT_KEY, None)
            id_col = translator.get(cls.ID_COL, None)
            selector = translator[cls.SELECTOR_TYPE]
            field_translators = translator[cls.FIELD_TRANSLATORS]

            new_results = []  # New tuples from this HDICT and sub containers.
            hdict_row = {}  # The content of the HDICT's new row.

            def compare_subtranslator(x, y):
                if cls.PARENT_KEY not in x[cls.TRANSLATOR] \
                        and cls.PARENT_KEY in y[cls.TRANSLATOR]:
                    return -1
                elif cls.PARENT_KEY in x[cls.TRANSLATOR] \
                        and cls.PARENT_KEY not in y[cls.TRANSLATOR]:
                    return 1
                else:
                    return cmp(x, y)

            # Sort with fields lacking parent-key coming first so that the
            # subtranslators that need a parent field will be able to get them
            # from hdict_row.
            sorted_translators = sorted(field_translators,
                                        cmp=compare_subtranslator)

            for field_translator in sorted_translators:
                field = field_translator[cls.FIELDNAME]
                col_name = field_translator.get(cls.COL, field)
                subtranslator = field_translator[cls.TRANSLATOR]

                if subtranslator[cls.TRANSLATION_TYPE] == cls.VALUE:
                    extract_fn = subtranslator.get(cls.EXTRACT_FN, None)
                    v = cls._extract_value(
                        cls._get_value(obj, field, selector), extract_fn)
                    hdict_row[col_name] = v
                else:
                    assert subtranslator[cls.TRANSLATION_TYPE] in (cls.HDICT,
                                                                   cls.VDICT,
                                                                   cls.LIST)
                    tuples = []
                    row_hash = None
                    v = cls._get_value(obj, field, selector)
                    if v is None:
                        if cls.ID_COL in subtranslator:
                            row_hash = cls._compute_hash([])
                    else:
                        tuples, row_hash = cls.convert_obj(v, subtranslator,
                                                           hdict_row)
                    new_results.extend(tuples)
                    if cls.need_column_for_subtable_id(subtranslator):
                        hdict_row[col_name] = row_hash

            new_row = []
            for fieldtranslator in field_translators:
                col = fieldtranslator.get(cls.COL,
                                          fieldtranslator[cls.FIELDNAME])
                if col in hdict_row:
                    new_row.append(value_to_congress(hdict_row[col]))

            if id_col:
                h = cls._compute_hash(new_row)
                new_row = (h,) + tuple(new_row)
            elif parent_key:
                h = None
                new_row = (parent_row_dict[parent_key],) + tuple(new_row)
            else:
                h = None
                new_row = tuple(new_row)
            new_results.append((table, new_row))
            return new_results, h

        elif translation_type == cls.VDICT:
            table = translator[cls.TABLE_NAME]
            parent_key = translator.get(cls.PARENT_KEY, None)
            id_col = translator.get(cls.ID_COL, None)
            key_col = translator[cls.KEY_COL]
            subtrans = translator[cls.TRANSLATOR]

            if subtrans[cls.TRANSLATION_TYPE] == cls.VALUE:
                extract_fn = subtrans.get(cls.EXTRACT_FN, None)
                converted_items = tuple([(value_to_congress(k),
                                          cls._extract_value(v, extract_fn))
                                         for k, v in obj.items()])
                if id_col:
                    h = cls._compute_hash(converted_items)
                    new_tuples = [(table, (h,) + i) for i in converted_items]
                elif parent_key:
                    h = None
                    parent_key_value = parent_row_dict[parent_key]
                    new_tuples = [(table, (parent_key_value,) + i)
                                  for i in converted_items]
                else:
                    h = None
                    new_tuples = [(table, i) for i in converted_items]
                return new_tuples, h

            else:
                assert translator[cls.TRANSLATION_TYPE] in (cls.HDICT,
                                                            cls.VDICT,
                                                            cls.LIST)
                new_tuples = []
                vdict_rows = []

                for k, v in obj.items():
                    if v is None:
                        tuples = []
                        row_hash = []
                        if cls.ID_COL in subtrans:
                            row_hash = cls._compute_hash([])
                    else:
                        tuples, row_hash = cls.convert_obj(v, subtrans,
                                                           {key_col: k})
                    if tuples:
                        new_tuples.extend(tuples)
                    vdict_row = (k,)
                    if cls.need_column_for_subtable_id(subtrans):
                        vdict_row = vdict_row + (row_hash,)
                    vdict_rows.append(vdict_row)

                h = None
                if id_col:
                    h = cls._compute_hash(vdict_rows)
                for vdict_row in vdict_rows:
                    if id_col:
                        new_tuples.append((table, (h,) + vdict_row))
                    elif parent_key:
                        k = parent_row_dict[parent_key]
                        new_tuples.append((table, (k,) + vdict_row))
                    else:
                        new_tuples.append((table, vdict_row))

                return new_tuples, h

        elif translation_type == cls.LIST:
            table = translator[cls.TABLE_NAME]
            parent_key = translator.get(cls.PARENT_KEY, None)
            id_col = translator.get(cls.ID_COL, None)
            subtrans = translator[cls.TRANSLATOR]

            if subtrans[cls.TRANSLATION_TYPE] == cls.VALUE:
                extract_fn = subtrans.get(cls.EXTRACT_FN, None)
                converted_values = tuple([cls._extract_value(o, extract_fn)
                                          for o in obj])
                if id_col:
                    h = cls._compute_hash(converted_values)
                    new_tuples = [(table, (h, v)) for v in converted_values]
                elif parent_key:
                    h = None
                    parent_key_value = parent_row_dict[parent_key]
                    new_tuples = [(table, (parent_key_value, v))
                                  for v in converted_values]
                else:
                    h = None
                    new_tuples = [(table, (v,)) for v in converted_values]
                return new_tuples, h

            else:
                assert translator[cls.TRANSLATION_TYPE] in (cls.HDICT,
                                                            cls.VDICT,
                                                            cls.LIST)
                new_tuples = []
                row_hashes = []
                for o in obj:
                    if o is None:
                        tuples = []
                        row_hash = []
                        if cls.ID_COL in subtrans:
                            row_hash = cls._compute_hash([])
                    else:
                        tuples, row_hash = cls.convert_obj(o, subtrans)
                    assert row_hash, "LIST's subtranslator must have row_hash"
                    assert cls.need_column_for_subtable_id(subtrans), \
                        "LIST's subtranslator should have id"

                    if tuples:
                        new_tuples.extend(tuples)
                    row_hashes.append(row_hash)

                if id_col:
                    h = cls._compute_hash(row_hashes)
                else:
                    h = None

                for row_hash in row_hashes:
                    if id_col:
                        new_tuples.append((table, (h, row_hash)))
                    elif parent_key:
                        new_tuples.append((table, (parent_row_dict[parent_key],
                                                   row_hash)))
                    else:
                        new_tuples.append((table, (row_hash,)))
                return new_tuples, h
        else:
            raise AssertionError("unexpected translator type %s" %
                                 translation_type)

    @classmethod
    def convert_objs(cls, obj_list, translator):
        """Takes a list of objects, and translates them using the translator.
        Returns a list of tuples, where each tuple is a pair containing a
        table name, and a tuple to be inserted into the table.
        """
        results = []
        for o in obj_list:
            rows, _ = DataSourceDriver.convert_obj(o, translator)
            results.extend(rows)
        return results

    @classmethod
    def convert_responses(cls, obj_list, conversion):
        results = []
        for o in obj_list:
            rows, h = DataSourceDriver.convert_response(o, conversion)
            results.extend(rows)
        return results

    @classmethod
    def check_params(cls, params, valid_params):
        diff = sorted(set(params).difference(valid_params))
        if diff:
            err = ("Params (%s) are invalid.  Valid params: %s" %
                   (', '.join(diff), str(valid_params)))
            raise exception.InvalidParamException(err)

    @classmethod
    def check_translation_type(cls, params):
        if cls.TRANSLATION_TYPE not in params:
            raise exception.InvalidParamException(
                "Param (%s) must be in translator" % cls.TRANSLATION_TYPE)

    def poll(self):
        """Function called periodically to grab new information, compute
        deltas, and publish those deltas.
        """
        self.log_info("polling")
        self.prior_state = dict(self.state)  # copying self.state
        self.last_error = None  # non-None only when last poll errored
        try:
            # Avoid race condition where poll() is called before object
            #   has finished initializing.  Every instance of this class
            #   must set self.initialized to True at the very end of
            #   __init__()
            # TODO(thinrichs): figure out how to remove this
            while not self.initialized:
                self.log("Not yet initialized: waiting to poll.")
                time.sleep(1)
            self.update_from_datasource()  # sets self.state
            tablenames = set(self.state.keys()) | set(self.prior_state.keys())
            for tablename in tablenames:
                # publishing full table and using prepush_processing to send
                #   only deltas.  Useful so that if policy engine subscribes
                #   late (or dies and comes back up), DSE can automatically
                #   send the full table.
                if tablename in self.state:
                    self.publish(tablename, self.state[tablename])
                else:
                    self.publish(tablename, set())
        except Exception as e:
            self.last_error = e
            LOG.exception("Datasource driver raised exception")

        self.last_poll_time = datetime.datetime.now()
        self.number_of_updates += 1
        self.log_info("finished polling")

    def prepush_processor(self, data, dataindex, type=None):
        """Takes as input the DATA that the receiver needs and returns
        the payload for the message.  If this is a regular publication
        message, make the payload just the delta; otherwise, make the
        payload the entire table.
        """
        # This routine basically ignores DATA and sends a delta
        #  of the self.prior_state and self.state, for the DATAINDEX
        #  part of the state.
        self.log("prepush_processor: dataindex <%s> data: %s", dataindex, data)
        # if not a regular publication, just return the original data
        if type != 'pub':
            self.log("prepush_processor: returned original data")
            if type == 'sub':
                # Always want to send initialization of []
                if data is None:
                    return []
                else:
                    return data
            return data
        # grab deltas
        to_add = self.state_set_diff(self.state, self.prior_state, dataindex)
        to_del = self.state_set_diff(self.prior_state, self.state, dataindex)
        self.log("to_add: %s", to_add)
        self.log("to_del: %s", to_del)
        # create Events
        result = []
        for row in to_add:
            formula = compile.Literal.create_from_table_tuple(dataindex, row)
            event = runtime.Event(formula=formula, insert=True)
            result.append(event)
        for row in to_del:
            formula = compile.Literal.create_from_table_tuple(dataindex, row)
            event = runtime.Event(formula=formula, insert=False)
            result.append(event)
        if len(result) == 0:
            # Policy engine expects an empty update to be an init msg
            #  So if delta is empty, return None, which signals
            #  the message should not be sent.
            result = None
            text = "None"
        else:
            text = runtime.iterstr(result)
        self.log("prepush_processor for <%s> returning with %s items",
            dataindex, text)
        return result

    def d6run(self):
        # This method is run by DSE, so don't sleep here--it'll delay message
        #   handling for this deepsix instance.
        if self.poll_time:  # setting to 0/False/None means auto-polling is off
            if self.last_poll_time is None:
                self.poll()
            else:
                now = datetime.datetime.now()
                diff = now - self.last_poll_time
                seconds = diff.seconds + diff.days * 24 * 3600
                if seconds > self.poll_time:
                    self.poll()

    def empty_credentials(self):
        return {'username': '',
                'password': '',
                'auth_url': '',
                'tenant_name': ''}
