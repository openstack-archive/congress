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

start_builtin_map = {
    'comparison': [
        {'func': 'lt(x,y)', 'num_inputs': 2, 'code': 'lambda x,y: x < y'},
        {'func': 'equal(x,y)', 'num_inputs': 2, 'code': 'lambda x,y: x==y'},
        {'func': 'gt(x,y)', 'num_inputs': 2, 'code': 'lambda x,y:  x > y'}],
    'arithmetic': [
        {'func': 'plus(x,y,z)', 'num_inputs': 3, 'code': 'lambda x,y: x+y'},
        {'func': 'minus(x,y,z)', 'num_inputs': 3, 'code': 'lambda x,y: x - y'},
        {'func': 'mul(x,y,z)', 'num_inputs': 3, 'code': 'lambda x,y: x*y '}]
}

append_map = {
    'comparison': [
        {'func': 'max(x,y)', 'num_inputs': 2,
            'code': 'lambda x,y: x if x > y else y'}],
    'string': [
        {'func': 'concat(x,y)', 'num_inputs': 2, 'code': 'lambda x,y: x + y'}]
}

append_builtin = {'arithmetic': [{'func': 'div(x,y,z)',
                                  'num_inputs': 2,
                                  'code': 'lambda x,y: x/y'}]}


class CongressBuiltinPred(object):

    def __init__(self, name, arglist, num_inputs, code):
        self.predname = name
        self.predargs = arglist
        self.num_inputs = num_inputs
        bfunc = 'f = ' + code
        exec(bfunc)
        self.code = eval('f')

    def __str__(self):
        predall = str(self.predname) + " " + str(self.predargs)\
            + " " + str(self.num_inputs) + " " + str(self.code)
        return predall

    def string_to_pred(self, predstring):
        try:
            self.predname = predstring.split('(')[0]
            self.predargs = predstring.split('(')[1].split(')')[0].split(',')
        except Exception:
            print "Unexpected error in parsing predicate string"

    def pred_to_string(self):
        return self.predname + '(' + str(self.predargs) + ')'


# initial set of builtins need to decide if this is the best place for it

class CongressBuiltinCategoryMap(object):

    def __init__(self, start_builtin_map):
        self.categorydict = dict()
        self.preddict = dict()
        for key, value in start_builtin_map.items():
            self.categorydict[key] = []
            for predtriple in value:
                print predtriple
                pred = self.dict_predtriple_to_pred(predtriple)
                self.categorydict[key].append(pred)
                self.sync_with_predlist(pred.predname, pred, key, 'add')

    def mapequal(self, othercbc):
        if self.categorydict == othercbc.categorydict:
            return True
        else:
            return False

    def dict_predtriple_to_pred(self, predtriple):
        print predtriple
        ncode = predtriple['code']
        ninputs = predtriple['num_inputs']
        nfunc = predtriple['func']
        nfunc_pred = nfunc.split("(")[0]
        nfunc_arglist = nfunc.split("(")[1].split(")")[0].split(",")
        print ncode, ninputs, nfunc, nfunc_pred, nfunc_arglist
        pred = CongressBuiltinPred(nfunc_pred, nfunc_arglist, ninputs, ncode)
        return pred

    def add_map(self, newmap):
        for key, value in newmap.items():
            if key not in self.categorydict:
                self.categorydict[key] = []
                print key
                print 'category exists'
            for predtriple in value:
                pred = self.dict_predtriple_to_pred(predtriple)
                if not self.check_if_builtin(pred):
                    self.categorydict[key].append(pred)
                    self.sync_with_predlist(pred.predname, pred, key, 'add')
                else:
                    print "builtin exists"

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

    def check_if_builtin(self, predtotest):
        pname = predtotest.predname
        if pname in self.preddict:
            if self.preddict[pname][0].num_inputs == predtotest.num_inputs:
                return True
        return False

    def return_builtin_pred(self, predname):
        if predname in self.preddict:
            return self.preddict[predname][0]
        return None

    def list_available_builtins(self):
        for key, value in self.categorydict.items():
            predlist = self.categorydict[key]
            for pred in predlist:
                print pred
                print pred.pred_to_string()

    def eval_builtin(self, code, arglist):
        return code(*arglist)


def main():
    cbcmap = CongressBuiltinCategoryMap(start_builtin_map)
    cbcmap.list_available_builtins()
    cbcmap.add_map(append_map)
    predl = cbcmap.return_builtin_pred('lt')
    print predl
    print 'printing pred'
    predl.string_to_pred('ltc(x,y)')
    cbcmap.list_available_builtins()
    cbcmap.delete_builtin('arithmetic', 'max', 2)
    cbcmap.list_available_builtins()
    predl = cbcmap.return_builtin_pred('plus')
    result = cbcmap.eval_builtin(predl.code, [1, 2])
    print result
    print cbcmap

if __name__ == "__main__":
    main()
