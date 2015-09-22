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
from congress.api import webservice
from congress.tests import base


class TestAPIUtils(base.TestCase):

    def setUp(self):
        super(TestAPIUtils, self).setUp()

    def test_create_table_dict(self):
        table_name = 'fake_table'
        schema = {'fake_table': ({'name': 'id', 'desc': None},
                                 {'name': 'name', 'desc': None})}
        expected = {'table_id': table_name,
                    'columns': [{'name': 'id', 'description': None},
                                {'name': 'name', 'description': None}]}
        result = api_utils.create_table_dict(table_name, schema)
        self.assertEqual(expected, result)

    def test_get_id_from_context_ds_id(self):
        context = {'ds_id': 'datasource id'}
        expected = ('datasource-mgr', 'datasource id')
        result = api_utils.get_id_from_context(context,
                                               'datasource-mgr',
                                               'policy-engine')
        self.assertEqual(expected, result)

    def test_get_id_from_context_policy_id(self):
        context = {'policy_id': 'policy id'}
        expected = ('policy-engine', 'policy id')
        result = api_utils.get_id_from_context(context,
                                               'datasource-mgr',
                                               'policy-engine')
        self.assertEqual(expected, result)

    def test_get_id_from_context_with_invalid_context(self):
        context = {'invalid_id': 'invalid id'}

        self.assertRaises(webservice.DataModelException,
                          api_utils.get_id_from_context,
                          context, 'datasource-mgr', 'policy-engine')
