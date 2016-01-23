# Copyright (c) 2015 OpenStack Foundation
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

from congress.api import error_codes
from congress.tests import base


class TestErrorCodes(base.TestCase):

    def setUp(self):
        super(TestErrorCodes, self).setUp()
        self.original_errors = error_codes.errors

    def tearDown(self):
        super(TestErrorCodes, self).tearDown()
        error_codes.errors = self.original_errors

    def test_get_error_code(self):
        name = 'fake-error'
        error_codes.errors = {
            "fake-error": (0000, 'This is a fake error code.', 400)
        }
        expected_num = 0000
        expected_desc = 'This is a fake error code.'
        expected_http = 400
        expected_ret = (expected_num, expected_desc)

        ret = error_codes.get(name)
        self.assertEqual(expected_ret, ret)

        num = error_codes.get_num(name)
        self.assertEqual(expected_num, num)

        desc = error_codes.get_desc(name)
        self.assertEqual(expected_desc, desc)

        http = error_codes.get_http(name)
        self.assertEqual(expected_http, http)

    def test_get_unknown__error_code(self):
        name = 'fake_error_code'
        error_codes.errors = {
            error_codes.UNKNOWN: (0000, 'Unknown error', 400),
            'fake-error': (1000, 'Fake error', 404)
        }
        expected_num = 0000
        expected_desc = 'Unknown error'
        expected_http = 400
        expected_ret = (expected_num, expected_desc)

        ret = error_codes.get(name)
        self.assertEqual(expected_ret, ret)

        num = error_codes.get_num(name)
        self.assertEqual(expected_num, num)

        desc = error_codes.get_desc(name)
        self.assertEqual(expected_desc, desc)

        http = error_codes.get_http(name)
        self.assertEqual(expected_http, http)
