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

import mock
from oslo_config import cfg

from congress.api import api_utils
from congress.api import schema_model
from congress.api import webservice
from congress.managers import datasource as datasource_manager
from congress.tests import base
from congress.tests import fake_datasource


class TestSchemaModel(base.TestCase):
    def setUp(self):
        super(TestSchemaModel, self).setUp()
        # Here we load the fake driver and test the schema functions with it.
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])
        ds_mgr = datasource_manager.DataSourceManager()
        self.schema_model = schema_model.SchemaModel("test_schema", {},
                                                     datasource_mgr=ds_mgr)

    def test_get_item_all_table(self):
        context = {'ds_id': 'fake_datasource'}
        schema = fake_datasource.FakeDataSource.get_schema()
        fake_tables = {'tables':
                       [api_utils.create_table_dict(
                        table_, schema) for table_ in schema]}
        with mock.patch.object(self.schema_model.datasource_mgr,
                               "get_datasource_schema",
                               return_value=schema):
            tables = self.schema_model.get_item(None, {}, context=context)
            self.assertEqual(fake_tables, tables)

    def test_get_item_table(self):
        context = {'ds_id': 'fake_datasource', 'table_id': 'fake_table'}
        fake_schema = fake_datasource.FakeDataSource.get_schema()
        fake_table = api_utils.create_table_dict(
            "fake_table", fake_schema)

        with mock.patch.object(self.schema_model.datasource_mgr,
                               "get_datasource_schema",
                               return_value=fake_schema):
            table = self.schema_model.get_item(None, {}, context=context)
            self.assertEqual(fake_table, table)

    def test_get_invalid_datasource(self):
        context = {'ds_id': 'invalid'}
        with mock.patch.object(
            self.schema_model.datasource_mgr,
            "get_datasource_schema",
            side_effect=datasource_manager.DatasourceNotFound('invalid')
        ):
            try:
                self.schema_model.get_item(None, {}, context=context)
            except webservice.DataModelException as e:
                self.assertEqual(404, e.error_code)
            else:
                raise Exception("Should not get here")

    def test_get_invalid_datasource_table(self):
        context = {'ds_id': 'fake_datasource', 'table_id': 'invalid_table'}
        fake_schema = fake_datasource.FakeDataSource.get_schema()
        with mock.patch.object(self.schema_model.datasource_mgr,
                               "get_datasource_schema",
                               return_value=fake_schema):
            try:
                self.schema_model.get_item(None, {}, context=context)
            except webservice.DataModelException as e:
                self.assertEqual(404, e.error_code)
            else:
                raise Exception("Should not get here")
