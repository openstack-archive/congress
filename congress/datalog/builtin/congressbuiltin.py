#! /usr/bin/python
#
# Copyright (c) 2014 IBM, Corp. All rights reserved.
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
import datetime

import six
from six.moves import range

from dateutil import parser as datetime_parser


class DatetimeBuiltins(object):

    # casting operators (used internally)
    @classmethod
    def to_timedelta(cls, x):
        if isinstance(x, six.string_types):
            fields = x.split(":")
            num_fields = len(fields)
            args = {}
            keys = ['seconds', 'minutes', 'hours', 'days', 'weeks']
            for i in range(0, len(fields)):
                args[keys[i]] = int(fields[num_fields - 1 - i])
            return datetime.timedelta(**args)
        else:
            return datetime.timedelta(seconds=x)

    @classmethod
    def to_datetime(cls, x):
        return datetime_parser.parse(x, ignoretz=True)

    # current time
    @classmethod
    def now(cls):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # extraction and creation of datetimes
    @classmethod
    def unpack_time(cls, x):
        x = cls.to_datetime(x)
        return (x.hour, x.minute, x.second)

    @classmethod
    def unpack_date(cls, x):
        x = cls.to_datetime(x)
        return (x.year, x.month, x.day)

    @classmethod
    def unpack_datetime(cls, x):
        x = cls.to_datetime(x)
        return (x.year, x.month, x.day, x.hour, x.minute, x.second)

    @classmethod
    def pack_time(cls, hour, minute, second):
        return "{}:{}:{}".format(hour, minute, second)

    @classmethod
    def pack_date(cls, year, month, day):
        return "{}-{}-{}".format(year, month, day)

    @classmethod
    def pack_datetime(cls, year, month, day, hour, minute, second):
        return "{}-{}-{} {}:{}:{}".format(
            year, month, day, hour, minute, second)

    # extraction/creation convenience function
    @classmethod
    def extract_date(cls, x):
        return str(cls.to_datetime(x).date())

    @classmethod
    def extract_time(cls, x):
        return str(cls.to_datetime(x).time())

    # conversion to seconds
    @classmethod
    def datetime_to_seconds(cls, x):
        since1900 = cls.to_datetime(x) - datetime.datetime(year=1900,
                                                           month=1,
                                                           day=1)
        return int(since1900.total_seconds())

    # native operations on datetime
    @classmethod
    def datetime_plus(cls, x, y):
        return str(cls.to_datetime(x) + cls.to_timedelta(y))

    @classmethod
    def datetime_minus(cls, x, y):
        return str(cls.to_datetime(x) - cls.to_timedelta(y))

    @classmethod
    def datetime_lessthan(cls, x, y):
        return cls.to_datetime(x) < cls.to_datetime(y)

    @classmethod
    def datetime_lessthanequal(cls, x, y):
        return cls.to_datetime(x) <= cls.to_datetime(y)

    @classmethod
    def datetime_greaterthan(cls, x, y):
        return cls.to_datetime(x) > cls.to_datetime(y)

    @classmethod
    def datetime_greaterthanequal(cls, x, y):
        return cls.to_datetime(x) >= cls.to_datetime(y)

    @classmethod
    def datetime_equal(cls, x, y):
        return cls.to_datetime(x) == cls.to_datetime(y)


# the registry for builtins
_builtin_map = {
    'comparison': [
        {'func': 'lt(x,y)', 'num_inputs': 2, 'code': lambda x, y: x < y},
        {'func': 'lteq(x,y)', 'num_inputs': 2, 'code': lambda x, y: x <= y},
        {'func': 'equal(x,y)', 'num_inputs': 2, 'code': lambda x, y: x == y},
        {'func': 'gt(x,y)', 'num_inputs': 2, 'code': lambda x, y: x > y},
        {'func': 'gteq(x,y)', 'num_inputs': 2, 'code': lambda x, y: x >= y},
        {'func': 'max(x,y,z)', 'num_inputs': 2,
         'code': lambda x, y: max(x, y)}],
    'arithmetic': [
        {'func': 'plus(x,y,z)', 'num_inputs': 2, 'code': lambda x, y: x + y},
        {'func': 'minus(x,y,z)', 'num_inputs': 2, 'code': lambda x, y: x - y},
        {'func': 'mul(x,y,z)', 'num_inputs': 2, 'code': lambda x, y: x * y},
        {'func': 'div(x,y,z)', 'num_inputs': 2, 'code': lambda x, y:
            ((x // y) if (type(x) == int and type(y) == int) else (x / y))},
        {'func': 'float(x,y)', 'num_inputs': 1, 'code': lambda x: float(x)},
        {'func': 'int(x,y)', 'num_inputs': 1, 'code': lambda x: int(x)}],
    'string': [
        {'func': 'concat(x,y,z)', 'num_inputs': 2, 'code': lambda x, y: x + y},
        {'func': 'len(x, y)', 'num_inputs': 1, 'code': lambda x: len(x)}],
    'datetime': [
        {'func': 'now(x)', 'num_inputs': 0,
         'code': DatetimeBuiltins.now},
        {'func': 'unpack_date(x, year, month, day)', 'num_inputs': 1,
         'code': DatetimeBuiltins.unpack_date},
        {'func': 'unpack_time(x, hours, minutes, seconds)', 'num_inputs': 1,
         'code': DatetimeBuiltins.unpack_time},
        {'func': 'unpack_datetime(x, y, m, d, h, i, s)', 'num_inputs': 1,
         'code': DatetimeBuiltins.unpack_datetime},
        {'func': 'pack_time(hours, minutes, seconds, result)', 'num_inputs': 3,
         'code': DatetimeBuiltins.pack_time},
        {'func': 'pack_date(year, month, day, result)', 'num_inputs': 3,
         'code': DatetimeBuiltins.pack_date},
        {'func': 'pack_datetime(y, m, d, h, i, s, result)', 'num_inputs': 6,
         'code': DatetimeBuiltins.pack_datetime},
        {'func': 'extract_date(x, y)', 'num_inputs': 1,
         'code': DatetimeBuiltins.extract_date},
        {'func': 'extract_time(x, y)', 'num_inputs': 1,
         'code': DatetimeBuiltins.extract_time},
        {'func': 'datetime_to_seconds(x, y)', 'num_inputs': 1,
         'code': DatetimeBuiltins.datetime_to_seconds},
        {'func': 'datetime_plus(x,y,z)', 'num_inputs': 2,
         'code': DatetimeBuiltins.datetime_plus},
        {'func': 'datetime_minus(x,y,z)', 'num_inputs': 2,
         'code': DatetimeBuiltins.datetime_minus},
        {'func': 'datetime_lt(x,y)', 'num_inputs': 2,
         'code': DatetimeBuiltins.datetime_lessthan},
        {'func': 'datetime_lteq(x,y)', 'num_inputs': 2,
         'code': DatetimeBuiltins.datetime_lessthanequal},
        {'func': 'datetime_gt(x,y)', 'num_inputs': 2,
         'code': DatetimeBuiltins.datetime_greaterthan},
        {'func': 'datetime_gteq(x,y)', 'num_inputs': 2,
         'code': DatetimeBuiltins.datetime_greaterthanequal},
        {'func': 'datetime_equal(x,y)', 'num_inputs': 2,
         'code': DatetimeBuiltins.datetime_equal}]}


class CongressBuiltinPred(object):

    def __init__(self, name, arglist, num_inputs, code):
        self.predname = name
        self.predargs = arglist
        self.num_inputs = num_inputs
        self.code = code
        self.num_outputs = len(arglist) - num_inputs

    def string_to_pred(self, predstring):
        try:
            self.predname = predstring.split('(')[0]
            self.predargs = predstring.split('(')[1].split(')')[0].split(',')
        except Exception:
            print("Unexpected error in parsing predicate string")

    def __str__(self):
        return self.predname + '(' + ",".join(self.predargs) + ')'


class CongressBuiltinCategoryMap(object):

    def __init__(self, start_builtin_map):
        self.categorydict = dict()
        self.preddict = dict()
        for key, value in start_builtin_map.items():
            self.categorydict[key] = []
            for predtriple in value:
                pred = self.dict_predtriple_to_pred(predtriple)
                self.categorydict[key].append(pred)
                self.sync_with_predlist(pred.predname, pred, key, 'add')

    def mapequal(self, othercbc):
        if self.categorydict == othercbc.categorydict:
            return True
        else:
            return False

    def dict_predtriple_to_pred(self, predtriple):
        ncode = predtriple['code']
        ninputs = predtriple['num_inputs']
        nfunc = predtriple['func']
        nfunc_pred = nfunc.split("(")[0]
        nfunc_arglist = nfunc.split("(")[1].split(")")[0].split(",")
        pred = CongressBuiltinPred(nfunc_pred, nfunc_arglist, ninputs, ncode)
        return pred

    def add_map(self, newmap):
        for key, value in newmap.items():
            if key not in self.categorydict:
                self.categorydict[key] = []
            for predtriple in value:
                pred = self.dict_predtriple_to_pred(predtriple)
                if not self.builtin_is_registered(pred):
                    self.categorydict[key].append(pred)
                    self.sync_with_predlist(pred.predname, pred, key, 'add')

    def delete_map(self, newmap):
        for key, value in newmap.items():
            for predtriple in value:
                predtotest = self.dict_predtriple_to_pred(predtriple)
                for pred in self.categorydict[key]:
                    if pred.predname == predtotest.predname:
                        if pred.num_inputs == predtotest.num_inputs:
                            self.categorydict[key].remove(pred)
                            self.sync_with_predlist(pred.predname,
                                                    pred, key, 'del')
                if self.categorydict[key] == []:
                    del self.categorydict[key]

    def sync_with_predlist(self, predname, pred, category, operation):
        if operation == 'add':
            self.preddict[predname] = [pred, category]
        if operation == 'del':
            if predname in self.preddict:
                del self.preddict[predname]

    def delete_builtin(self, category, name, inputs):
        if category not in self.categorydict:
            self.categorydict[category] = []
        for pred in self.categorydict[category]:
            if pred.num_inputs == inputs and pred.predname == name:
                self.categorydict[category].remove(pred)
                self.sync_with_predlist(name, pred, category, 'del')

    def get_category_name(self, predname, predinputs):
        if predname in self.preddict:
            if self.preddict[predname][0].num_inputs == predinputs:
                return self.preddict[predname][1]
        return None

    def exists_category(self, category):
        return category in self.categorydict

    def insert_category(self, category):
        self.categorydict[category] = []

    def delete_category(self, category):
        if category in self.categorydict:
            categorypreds = self.categorydict[category]
            for pred in categorypreds:
                self.sync_with_predlist(pred.predname, pred, category, 'del')
            del self.categorydict[category]

    def insert_to_category(self, category, pred):
        if category in self.categorydict:
            self.categorydict[category].append(pred)
            self.sync_with_predlist(pred.predname, pred, category, 'add')
        else:
            assert("Category does not exist")

    def delete_from_category(self, category, pred):
        if category in self.categorydict:
            self.categorydict[category].remove(pred)
            self.sync_with_predlist(pred.predname, pred, category, 'del')
        else:
            assert("Category does not exist")

    def delete_all_in_category(self, category):
        if category in self.categorydict:
            categorypreds = self.categorydict[category]
            for pred in categorypreds:
                self.sync_with_predlist(pred.predname, pred, category, 'del')
            self.categorydict[category] = []
        else:
            assert("Category does not exist")

    def builtin_is_registered(self, predtotest):
        """Given a CongressBuiltinPred, check if it has been registered."""
        pname = predtotest.predname
        if pname in self.preddict:
            if self.preddict[pname][0].num_inputs == predtotest.num_inputs:
                return True
        return False

    def is_builtin(self, table, arity=None):
        """Given a Tablename and arity, check if it is a builtin."""
        if table.table in self.preddict:
            if not arity:
                return True
            if len(self.preddict[table.table][0].predargs) == arity:
                return True
        return False

    def builtin(self, table):
        """Return a CongressBuiltinPred for given Tablename or None."""
        if not isinstance(table, six.string_types):
            table = table.table
        if table in self.preddict:
            return self.preddict[table][0]
        return None

    def list_available_builtins(self):
        """Print out the list of builtins, by category."""
        for key, value in self.categorydict.items():
            predlist = self.categorydict[key]
            for pred in predlist:
                print(str(pred))


# a Singleton that serves as the entry point for builtin functionality
builtin_registry = CongressBuiltinCategoryMap(_builtin_map)
