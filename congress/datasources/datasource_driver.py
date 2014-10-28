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

from congress.dse import deepsix
from congress.policy import compile
from congress.policy import runtime
from congress.utils import value_to_congress

import datetime
import hashlib
import json
import traceback


class InvalidParamException(Exception):
    pass


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
       'id-col': 'id_col',
       'selection-type': 'DOT_SELECTOR',
       'field-translators': ({'fieldname': 'field1', 'col': 'col1',
                              'translator': {'translation-type': 'VALUE'}},
                             {'fieldname': 'field2', 'col': 'col2',
                              'translator': {'translation-type': 'VALUE'})}

      The HDICT translator reads in a python dict and translates each key in
      the dict into a column of the output table.  The fields in the table
      will be in the same order as the fields in the HDICT translator.  Use
      selection-type to specify whether to access the fields using dot
      notation such as 'obj.field1' or using a dict selector such as
      obj['field1'].  SELECTOR must be either 'DOT_SELECTOR' or
      'DICT_SELECTOR'.  If the translator contains a field, but the object
      does not contain that field, the translator will populate the column
      with 'None'.  If 'id-col' is not specified, the translator will omit the
      id column.

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
       'selection-type': 'DOT_SELECTOR',
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
       'id-col': 'id_col',
       'key-col': 'key_col',
       'val-col': 'value_col',
       'translator': TRANSLATOR}

      The VDICT translator reads in a python dict, and turns each key-value
      pair into a row of the output table.  The output table will have 2 or 3
      columns, depending on whether the 'id-col' is present.  If 'id-col' is
      present, the columns will be (id_col, key_col, value_col), otherwise
      (key_col, value_col).  Recursion works as it does with HDICT.

    LIST parameters with example values:
      {'translation-type': 'LIST',
       'table-name': 'table1',
       'id-col': 'id_col',
       'val-col': 'value_col',
       'translator': {'translation-type': 'VALUE'}}

      The LIST translator is like the VDICT translator, except that it reads a
      python list from the object, and produces 1 or 2 columns depending on
      whether 'id-col' is present.  It always produces a column for id-col.
      The content of id-col is either a value (if the translator is a VALUE)
      or a hash of a recursive value as in HDICT.

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
    ID_COL = 'id-col'
    SELECTOR_TYPE = 'selector-type'
    FIELD_TRANSLATORS = 'field-translators'
    FIELDNAME = 'fieldname'
    TRANSLATOR = 'translator'
    COL = 'col'
    KEY_COL = 'key-col'
    VAL_COL = 'val-col'
    EXTRACT_FN = 'extract-fn'

    # valid params
    HDICT_PARAMS = (TRANSLATION_TYPE, TABLE_NAME, ID_COL, SELECTOR_TYPE,
                    FIELD_TRANSLATORS)
    FIELD_TRANSLATOR_PARAMS = (FIELDNAME, COL, TRANSLATOR)
    VDICT_PARAMS = (TRANSLATION_TYPE, TABLE_NAME, ID_COL, KEY_COL, VAL_COL,
                    TRANSLATOR)
    LIST_PARAMS = (TRANSLATION_TYPE, TABLE_NAME, ID_COL, VAL_COL, TRANSLATOR)
    VALUE_PARAMS = (TRANSLATION_TYPE, EXTRACT_FN)
    TRANSLATION_TYPE_PARAMS = (TRANSLATION_TYPE,)

    def __init__(self, name, keys, inbox, datapath, args):
        if args is None:
            args = dict()
        if 'poll_time' in args:
            self.poll_time = int(args['poll_time'])
        else:
            self.poll_time = 10
        # default to open-stack credentials, since that's the common case
        self.creds = self.get_credentials(name, args)
        self.last_poll_time = None
        self.last_error = None
        self.number_of_updates = 0

        # a dictionary from tablename to the SET of tuples, both currently
        #  and in the past.
        self.prior_state = dict()
        self.state = dict()

        # Make sure all data structures above are set up *before* calling
        #   this because it will publish info to the bus.
        super(DataSourceDriver, self).__init__(name, keys, inbox, datapath)

    @classmethod
    def get_translators(self):
        """Returns a set of translators that describes how to translate from
        the datasource's data structures to the Congress tables.
        """
        raise NotImplementedError

    @classmethod
    def get_schema(cls):
        """Returns a dictionary mapping tablenames to the list of
        column names for that table.  Both tablenames and columnnames
        are strings.
        """
        def _get_schema(translator, schema):
            cls.check_translation_type(translator.keys())
            translation_type = translator[cls.TRANSLATION_TYPE]
            if translation_type == cls.HDICT:
                # A missing parameter will raise a KeyError
                tablename = translator[cls.TABLE_NAME]
                id_col = translator.get(cls.ID_COL, None)
                field_translators = translator[cls.FIELD_TRANSLATORS]

                columns = []
                if id_col is not None:
                    columns.append(id_col)
                for field_translator in field_translators:
                    col = field_translator.get(cls.COL,
                                               field_translator[cls.FIELDNAME])
                    subtranslator = field_translator[cls.TRANSLATOR]
                    columns.append(col)
                    _get_schema(subtranslator, schema)

                if tablename in schema:
                    raise InvalidParamException("table %s already in schema" %
                                                tablename)
                schema[tablename] = tuple(columns)
            elif translation_type == cls.VDICT:
                tablename = translator[cls.TABLE_NAME]
                id_col = translator.get(cls.ID_COL, None)
                key_col = translator[cls.KEY_COL]
                value_col = translator[cls.VAL_COL]
                trans = translator[cls.TRANSLATOR]

                _get_schema(trans, schema)
                if tablename in schema:
                    raise InvalidParamException("table %s already in schema" %
                                                tablename)
                if id_col is None:
                    schema[tablename] = (key_col, value_col)
                else:
                    schema[tablename] = (id_col, key_col, value_col)
            elif translation_type == cls.LIST:
                tablename = translator[cls.TABLE_NAME]
                id_col = translator.get(cls.ID_COL, None)
                value_col = translator[cls.VAL_COL]
                trans = translator[cls.TRANSLATOR]

                _get_schema(trans, schema)
                if tablename in schema:
                    raise InvalidParamException("table %s already in schema" %
                                                tablename)
                if id_col is None:
                    schema[tablename] = (value_col,)
                else:
                    schema[tablename] = (id_col, value_col)
            elif translation_type == cls.VALUE:
                pass
            else:
                raise AssertionError('Unexpected translator type %s' %
                                     translation_type)
            return schema

        all_schemas = {}
        for trans in cls.get_translators():
            _get_schema(trans, all_schemas)
        return all_schemas

    @classmethod
    def get_column_map(cls, tablename):
        """Given a tablename, returns a dictionary mapping the columnnames
        of that table to the integer position of that column.  Returns None
        if tablename is not in the schema.
        """
        schema = cls.get_schema()
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
    def convert_obj(cls, obj, translator, seen_tables=None):
        """Takes an object and a translation descriptor.  Returns two items:
        (1) a list of tuples where the first element is the name of a table,
        and the second element is a tuple to be inserted into the table, and
        (2) a hash that takes into account all the content of the list of
        tuples.  The hash can be used as a unique key to identify the content
        in obj.
        """

        def get_value(o, field, selector):
            if selector == cls.DOT_SELECTOR:
                if hasattr(o, field):
                    return getattr(o, field)
                return None
            elif selector == cls.DICT_SELECTOR:
                if field in o:
                    return o[field]
                return None
            else:
                raise AssertionError("Unexpected selector type: %s" %
                                     (str(selector),))

        def compute_hash(obj):
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

        def extract_value(obj, extract_fn):
            # Reads a VALUE object and returns (result_rows, h)
            if extract_fn is None:
                extract_fn = lambda x: x
            return value_to_congress(extract_fn(obj))

        if obj is None:
            return None, None

        if seen_tables is None:
            seen_tables = []

        cls.check_translation_type(translator.keys())
        translation_type = translator[cls.TRANSLATION_TYPE]
        if translation_type == cls.HDICT:
            cls.check_params(translator.keys(), cls.HDICT_PARAMS)

            table = translator[cls.TABLE_NAME]
            id_col = translator.get(cls.ID_COL, None)
            selector = translator[cls.SELECTOR_TYPE]
            field_translators = translator[cls.FIELD_TRANSLATORS]

            if table in seen_tables:
                raise InvalidParamException('table (%s) used twice' % table)

            new_results = []  # New tuples from this HDICT and sub containers.
            hdict_row = {}  # The content of the HDICT's new row.

            for field_translator in field_translators:
                cls.check_params(field_translator.keys(),
                                 cls.FIELD_TRANSLATOR_PARAMS)
                field = field_translator[cls.FIELDNAME]
                subtranslator = field_translator[cls.TRANSLATOR]

                cls.check_translation_type(subtranslator.keys())
                if subtranslator[cls.TRANSLATION_TYPE] == cls.VALUE:
                    cls.check_params(subtranslator.keys(), cls.VALUE_PARAMS)
                    extract_fn = subtranslator.get(cls.EXTRACT_FN, None)
                    v = extract_value(get_value(obj, field, selector),
                                      extract_fn)
                    hdict_row[field] = v
                else:
                    assert subtranslator[cls.TRANSLATION_TYPE] in (cls.HDICT,
                                                                   cls.VDICT,
                                                                   cls.LIST)
                    v = get_value(obj, field, selector)
                    tuples, row_hash = cls.convert_obj(v, subtranslator,
                                                       seen_tables + [table])
                    if tuples:
                        new_results.extend(tuples)
                    hdict_row[field] = row_hash

            new_row = [
                value_to_congress(hdict_row[subtranslator[cls.FIELDNAME]])
                for subtranslator in field_translators]

            h = compute_hash(new_row)
            if id_col is None:
                new_row = tuple(new_row)
            else:
                # Insert a hash as the first column of the row.
                new_row = (h,) + tuple(new_row)
            new_results.append((table, new_row))
            return new_results, h

        elif translation_type == cls.VDICT:
            cls.check_params(translator.keys(), cls.VDICT_PARAMS)
            table = translator[cls.TABLE_NAME]
            id_col = translator.get(cls.ID_COL, None)
            trans = translator[cls.TRANSLATOR]

            if table in seen_tables:
                raise InvalidParamException('table (%s) used twice' % table)

            cls.check_translation_type(trans.keys())
            if trans[cls.TRANSLATION_TYPE] == cls.VALUE:
                cls.check_params(trans.keys(), cls.VALUE_PARAMS)
                extract_fn = trans.get(cls.EXTRACT_FN, None)
                converted_items = tuple([(value_to_congress(k),
                                          extract_value(v, extract_fn))
                                         for k, v in obj.items()])
                h = compute_hash(converted_items)
                if id_col is None:
                    new_tuples = [(table, i) for i in converted_items]
                else:
                    new_tuples = [(table, (h,) + i) for i in converted_items]
                return new_tuples, h

            else:
                assert translator[cls.TRANSLATION_TYPE] in (cls.HDICT,
                                                            cls.VDICT,
                                                            cls.LIST)
                new_tuples = []
                key_hash_pairs = []
                for k, v in obj.items():
                    tuples, row_hash = cls.convert_obj(v, trans,
                                                       seen_tables + [table])
                    if tuples:
                        new_tuples.extend(tuples)
                    key_hash_pairs.append((k, row_hash))
                h = compute_hash(key_hash_pairs)

                for row_key, row_hash in key_hash_pairs:
                    if id_col is None:
                        new_tuples.append((table, (row_key, row_hash)))
                    else:
                        new_tuples.append((table, (h, row_key, row_hash)))
                return new_tuples, h

        elif translation_type == cls.LIST:
            cls.check_params(translator.keys(), cls.LIST_PARAMS)
            table = translator[cls.TABLE_NAME]
            id_col = translator.get(cls.ID_COL, None)
            trans = translator[cls.TRANSLATOR]

            if table in seen_tables:
                raise InvalidParamException('table (%s) used twice' % table)

            cls.check_translation_type(trans.keys())
            if trans[cls.TRANSLATION_TYPE] == cls.VALUE:
                cls.check_params(trans.keys(), cls.VALUE_PARAMS)
                extract_fn = trans.get(cls.EXTRACT_FN, None)
                converted_values = tuple([extract_value(o, extract_fn)
                                          for o in obj])
                h = compute_hash(converted_values)
                if id_col is None:
                    new_tuples = [(table, (v,)) for v in converted_values]
                else:
                    new_tuples = [(table, (h, v)) for v in converted_values]
                return new_tuples, h

            else:
                assert translator[cls.TRANSLATION_TYPE] in (cls.HDICT,
                                                            cls.VDICT,
                                                            cls.LIST)
                new_tuples = []
                row_hashes = []
                for o in obj:
                    tuples, row_hash = cls.convert_obj(o, trans,
                                                       seen_tables + [table])
                    if tuples:
                        new_tuples.extend(tuples)
                    row_hashes.append(row_hash)
                h = compute_hash(row_hashes)

                for row_hash in row_hashes:
                    if id_col is None:
                        new_tuples.append((table, (row_hash,)))
                    else:
                        new_tuples.append((table, (h, row_hash)))
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
            rows, h = DataSourceDriver.convert_obj(o, translator)
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
            raise InvalidParamException(err)

    @classmethod
    def check_translation_type(cls, params):
        if cls.TRANSLATION_TYPE not in params:
            raise InvalidParamException("Param (%s) must be in translator" %
                                        cls.TRANSLATION_TYPE)

    def poll(self):
        """Function called periodically to grab new information, compute
        deltas, and publish those deltas.
        """
        self.log_info("polling")
        self.prior_state = dict(self.state)  # copying self.state
        self.last_error = None  # non-None only when last poll errored
        try:
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
            self.log("Caught exception:")
            self.log(traceback.format_exc())

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
        self.log("prepush_processor: dataindex <{}> data: {}".format(
            str(dataindex), str(data)))
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
        self.log("to_add: " + str(to_add))
        self.log("to_del: " + str(to_del))
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
        self.log("prepush_processor for <{}> returning with {} items".format(
            dataindex, text))
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

    def get_credentials(self, name, config_args):
        # TODO(thinrichs): Create OpenStack mixin that implements
        #   OpenStack-specific credential gathering, etc.
        d = {}
        missing = []
        for field in ['username', 'password', 'auth_url', 'tenant_name']:
            if field in config_args:
                d[field] = config_args[field]
            else:
                missing.append(field)
        if missing:
            raise DataSourceConfigException(
                "Service {} is missing configuration data for {}".format(
                    name, missing))
        return d

    def empty_credentials(self):
        return {'username': '',
                'password': '',
                'auth_url': '',
                'tenant_name': ''}


class DataSourceConfigException(Exception):
    pass
