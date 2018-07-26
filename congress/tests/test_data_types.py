# Copyright (c) 2018 VMware
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import testtools

from congress import data_types


class TestDataTypes(testtools.TestCase):

    def test_nullable(self):
        for type_class in data_types.TYPES:
            self.assertIsNone(type_class.marshal(None))

    def test_Scalar(self):
        valid_values = [1, 1.0, 'str', u'str', True]
        invalid_values = [{}, []]
        for val in valid_values:
            self.assertEqual(val, data_types.Scalar.marshal(val))

        for val in invalid_values:
            self.assertRaises(ValueError, data_types.Scalar.marshal, val)

    def test_Str(self):
        valid_values = ['str', u'str', '1']
        invalid_values = [{}, [], True, 1]
        for val in valid_values:
            self.assertEqual(val, data_types.Str.marshal(val))

        for val in invalid_values:
            self.assertRaises(ValueError, data_types.Str.marshal, val)

    def test_Bool(self):
        valid_values = [True, False]
        invalid_values = [{}, [], 'True', 0, 1]
        for val in valid_values:
            self.assertEqual(val, data_types.Bool.marshal(val))

        for val in invalid_values:
            self.assertRaises(ValueError, data_types.Bool.marshal, val)

    def test_Int(self):
        valid_values = [1, 1.0, -1, True, False]
        invalid_values = [{}, [], 1.1, '1']
        for val in valid_values:
            self.assertEqual(val, data_types.Int.marshal(val))

        for val in invalid_values:
            self.assertRaises(ValueError, data_types.Int.marshal, val)

    def test_Float(self):
        valid_values = [1, 1.0, -1, True, False]
        invalid_values = [{}, [], '1']
        for val in valid_values:
            self.assertEqual(val, data_types.Int.marshal(val))

        for val in invalid_values:
            self.assertRaises(ValueError, data_types.Int.marshal, val)

    def test_UUID(self):
        valid_values = ['026f66d3-d6f1-44d1-8451-0a95ee984ffa',
                        '026f66d3d6f144d184510a95ee984ffa',
                        '-0-2-6f66d3d6f144d184510a95ee984ffa']
        invalid_values = [{}, [], '1', True, 1,
                          'z26f66d3d6f144d184510a95ee984ffa']
        for val in valid_values:
            self.assertEqual(val, data_types.UUID.marshal(val))

        for val in invalid_values:
            self.assertRaises(ValueError, data_types.UUID.marshal, val)

    def test_IPAddress(self):
        valid_values = [('10.0.0.1', '10.0.0.1'),
                        ('::ffff:0a00:0001', '10.0.0.1'),
                        ('0000:0000:0000:0000:0000:ffff:0a00:0001',
                         '10.0.0.1'),
                        ('2001:db8::ff00:42:8329', '2001:db8::ff00:42:8329'),
                        ('2001:0db8:0000:0000:0000:ff00:0042:8329',
                         '2001:db8::ff00:42:8329')]
        invalid_values = [{}, [], '1', True, 1,
                          '256.0.0.1']
        for val in valid_values:
            self.assertEqual(val[1], data_types.IPAddress.marshal(val[0]))

        for val in invalid_values:
            self.assertRaises(ValueError, data_types.IPAddress.marshal, val)

    def test_IPNetwork(self):
        valid_values = [('10.0.0.0/16', '10.0.0.0/16'),
                        ('2001:db00::0/24', '2001:db00::/24'),
                        ('::ffff:0a00:0000/128', '::ffff:a00:0/128')]
        invalid_values = [{}, [], '1', True, 1,
                          '10.0.0.0/4'
                          '10.0.0.1/16']
        for val in valid_values:
            self.assertEqual(val[1], data_types.IPNetwork.marshal(val[0]))

        for val in invalid_values:
            self.assertRaises(ValueError, data_types.IPNetwork.marshal, val)

    def test_enum_types(self):
        Test1 = data_types.create_congress_enum_type(
            'Test', [1, 2], data_types.Int)
        self.assertEqual(1, Test1.marshal(1))
        self.assertIsNone(Test1.marshal(None))
        self.assertRaises(ValueError, Test1.marshal, 0)

        Test2 = data_types.create_congress_enum_type(
            'Test', [1, 2], data_types.Int, catch_all_default_value=0)
        self.assertEqual(1, Test2.marshal(1))
        self.assertEqual(0, Test2.marshal(-1))
        self.assertEqual(0, Test2.marshal('blah'))
