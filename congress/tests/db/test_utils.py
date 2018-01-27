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

import mock
from oslo_db import exception as db_exc
import testtools

from congress.db import utils as db_utils


class TestUtils(testtools.TestCase):

    def _get_fail_then_succeed_func(self, failure_exception):
        fail_then_succeed = mock.Mock(
            side_effect=[failure_exception, True])

        # set name as required by functools.wrap
        fail_then_succeed.__name__ = 'fail_then_suceed'
        return fail_then_succeed

    def test_no_retry_on_unknown_db_error(self):
        fail_then_succeed = db_utils.retry_on_db_error(
            self._get_fail_then_succeed_func(db_exc.DBError))
        self.assertRaises(db_exc.DBError, fail_then_succeed)

    def test_retry_on_db_deadlock_error(self):
        fail_then_succeed = db_utils.retry_on_db_error(
            self._get_fail_then_succeed_func(db_exc.DBDeadlock))
        self.assertTrue(fail_then_succeed())
