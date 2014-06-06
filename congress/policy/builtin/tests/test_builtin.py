#! /usr/bin/python
#
# Copyright (c) 2014 IBM, Inc. All rights reserved.
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

from policy.builtin.congressbuiltin import append_map as addmap
from policy.builtin.congressbuiltin \
    import CongressBuiltinCategoryMap as builtins
from policy.builtin.congressbuiltin import CongressBuiltinPred
from policy.builtin.congressbuiltin import start_builtin_map as initbuiltin
import unittest


append_builtin = {'arithmetic': [{'func': 'div(x,y)',
                                  'num_inputs': 2,
                                  'code': 'lambda x,y: x / y'}]}


class BuiltinTests(unittest.TestCase):

    def setUp(self):
        self.cbcmap = builtins(initbuiltin)
        self.predl = self.cbcmap.return_builtin_pred('lt')

    def test_add_and_delete_map(self):
        cbcmap_before = self.cbcmap
        self.cbcmap.add_map(append_builtin)
        self.cbcmap.delete_map(append_builtin)
        self.assertTrue(self.cbcmap.mapequal(cbcmap_before))

    def test_add_map_only(self):
        self.cbcmap.add_map(append_builtin)
        predl = self.cbcmap.return_builtin_pred('div')
        self.assertNotEqual(predl, None)
        self.cbcmap.add_map(addmap)
        predl = self.cbcmap.return_builtin_pred('max')
        self.assertNotEqual(predl, None)

    def test_add_and_delete_builtin(self):
        cbcmap_before = self.cbcmap
        self.cbcmap.add_map(append_builtin)
        self.cbcmap.delete_builtin('arithmetic', 'div', 2)
        self.assertTrue(self.cbcmap.mapequal(cbcmap_before))

    def test_string_pred_string(self):
        predstring = self.predl.pred_to_string()
        self.assertNotEqual(predstring, 'ltc(x,y')

    def test_add_and_delete_to_category(self):
        cbcmap_before = self.cbcmap
        arglist = ['x', 'y', 'z']
        pred = CongressBuiltinPred('testfunc', arglist, 1, 'lambda x: not x')
        self.cbcmap.insert_to_category('arithmetic', pred)
        self.cbcmap.delete_from_category('arithmetic', pred)
        self.assertTrue(self.cbcmap.mapequal(cbcmap_before))

    def test_all_checks(self):
        predtotest = self.cbcmap.return_builtin_pred('lt')
        self.assertTrue(self.cbcmap.check_if_builtin(predtotest))

    def test_eval_builtin(self):
        predl = self.cbcmap.return_builtin_pred('plus')
        result = self.cbcmap.eval_builtin(predl.code, [1, 2])
        self.assertEqual(result, 3)
        predl = self.cbcmap.return_builtin_pred('gt')
        result = self.cbcmap.eval_builtin(predl.code, [1, 2])
        self.assertEqual(result, False)

if __name__ == '__main__':
    unittest.main()
