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

from oslo_config import cfg
cfg.CONF.distributed_architecture = True

from congress.api import api_utils
from congress.api import schema_model
from congress.api import webservice
from congress.tests import base
from congress.tests2.api import base as api_base


class TestSchemaModel(base.TestCase):
    def setUp(self):
        super(TestSchemaModel, self).setUp()
        self.schema_model = schema_model.SchemaModel("test_schema", {})
        self.config = api_base.setup_config([self.schema_model])
        self.data = self.config['data']

    def test_get_item_all_table(self):
        context = {'ds_id': self.data.service_id}
        schema = self.data.get_schema()
        fake_tables = {'tables':
                       [api_utils.create_table_dict(
                        table_, schema) for table_ in schema]}
        tables = self.schema_model.get_item(None, {}, context=context)
        self.assertEqual(fake_tables, tables)

    def test_get_item_table(self):
        context = {'ds_id': self.data.service_id, 'table_id': 'fake_table'}
        fake_schema = self.data.get_schema()
        fake_table = api_utils.create_table_dict(
            "fake_table", fake_schema)
        table = self.schema_model.get_item(None, {}, context=context)
        self.assertEqual(fake_table, table)

    def test_get_invalid_datasource_table(self):
        context = {'ds_id': self.data.service_id, 'table_id': 'invalid_table'}
        try:
            self.schema_model.get_item(None, {}, context=context)
        except webservice.DataModelException as e:
            self.assertEqual(404, e.error_code)
        else:
            raise Exception("Should not get here")

    def test_get_invalid_datasource(self):
        context = {'ds_id': 'invalid'}
        try:
            self.schema_model.get_item(None, {}, context=context)
        except webservice.DataModelException as e:
            self.assertEqual(404, e.error_code)
        else:
            raise Exception("Should not get here")
