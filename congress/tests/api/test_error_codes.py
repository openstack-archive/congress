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
            "fake-error": (
                0000,
                'This is a fake error code.'
            )
        }
        expected_ret = (
            0000,
            'This is a fake error code.'
        )

        ret = error_codes.get(name)
        self.assertEqual(expected_ret, ret)

    def test_get_unknown__error_code(self):
        name = 'unknown'
        error_codes.errors = {
            "fake-error": (
                0000,
                'This is a fake error code.'
            )
        }
        expected_ret = (
            1000,
            'Unknown error'
        )

        ret = error_codes.get(name)
        self.assertEqual(expected_ret, ret)
