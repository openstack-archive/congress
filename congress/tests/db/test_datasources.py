# Copyright (c) 2015 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from oslo_utils import uuidutils

from congress.db import datasources
from congress.tests import base


class TestDbDatasource(base.SqlTestCase):

    def test_add_datasource(self):
        id_ = uuidutils.generate_uuid()
        source = datasources.add_datasource(
            id_=id_,
            name="hiya",
            driver="foo",
            config='{user: foo}',
            description="hello",
            enabled=True)
        self.assertEqual(id_, source.id)
        self.assertEqual("hiya", source.name)
        self.assertEqual("foo", source.driver)
        self.assertEqual("hello", source.description)
        self.assertEqual('"{user: foo}"', source.config)
        self.assertEqual(True, source.enabled)

    def test_delete_datasource(self):
        id_ = uuidutils.generate_uuid()
        datasources.add_datasource(
            id_=id_,
            name="hiya",
            driver="foo",
            config='{user: foo}',
            description="hello",
            enabled=True)
        self.assertTrue(datasources.delete_datasource(id_))

    def test_delete_non_existing_datasource(self):
        self.assertFalse(datasources.delete_datasource('no_id'))

    def test_get_datasource_by_name(self):
        id_ = uuidutils.generate_uuid()
        datasources.add_datasource(
            id_=id_,
            name="hiya",
            driver="foo",
            config='{user: foo}',
            description="hello",
            enabled=True)
        source = datasources.get_datasource_by_name('hiya')
        self.assertEqual(id_, source.id)
        self.assertEqual("hiya", source.name)
        self.assertEqual("foo", source.driver)
        self.assertEqual("hello", source.description)
        self.assertEqual('"{user: foo}"', source.config)
        self.assertEqual(True, source.enabled)

    def test_get_datasource_by_id(self):
        id_ = uuidutils.generate_uuid()
        datasources.add_datasource(
            id_=id_,
            name="hiya",
            driver="foo",
            config='{user: foo}',
            description="hello",
            enabled=True)
        source = datasources.get_datasource(id_)
        self.assertEqual(id_, source.id)
        self.assertEqual("hiya", source.name)
        self.assertEqual("foo", source.driver)
        self.assertEqual("hello", source.description)
        self.assertEqual('"{user: foo}"', source.config)
        self.assertEqual(True, source.enabled)

    def test_get_datasource(self):
        id_ = uuidutils.generate_uuid()
        datasources.add_datasource(
            id_=id_,
            name="hiya",
            driver="foo",
            config='{user: foo}',
            description="hello",
            enabled=True)
        sources = datasources.get_datasources()
        self.assertEqual(id_, sources[0].id)
        self.assertEqual("hiya", sources[0].name)
        self.assertEqual("foo", sources[0].driver)
        self.assertEqual("hello", sources[0].description)
        self.assertEqual('"{user: foo}"', sources[0].config)
        self.assertEqual(True, sources[0].enabled)
