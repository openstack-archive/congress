# Copyright (c) 2015 NTT, OpenStack Foundation
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

from congress.api import api_utils
from congress.tests import base


class TestAPIUtils(base.TestCase):

    def setUp(self):
        super(TestAPIUtils, self).setUp()

    def test_create_table_dict(self):
        table_name = 'fake_table'
        schema = {'fake_table': ('id', 'name')}
        expected = {'table_id': table_name,
                    'columns': [{'name': 'id', 'description': 'None'},
                                {'name': 'name', 'description': 'None'}]}
        result = api_utils.create_table_dict(table_name, schema)
        self.assertEqual(expected, result)
