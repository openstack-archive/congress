# Copyright 2017 Orange. All Rights Reserved.
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

"Tempest tests for config datasource"

from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions

from congress_tempest_tests.tests.scenario import manager_congress

CONF = config.CONF


def find_col(schema, name):
    "Finds the index of a column in a congress table."
    return next(i for i, c in enumerate(schema) if c['name'] == name)


class TestCfgValidatorDriver(manager_congress.ScenarioPolicyBase):
    """Tempest tests for the config datasource.

    Checks that the datasource is available and test it on congress
    configuration files.
    """

    def setUp(self):
        super(TestCfgValidatorDriver, self).setUp()
        self.keypairs = {}
        self.servers = []
        datasources = self.os_admin.congress_client.list_datasources()
        for datasource in datasources['results']:
            if datasource['name'] == 'config':
                self.datasource_id = datasource['id']
                return
        self.skipTest('no datasource config configured.')

    @decorators.attr(type='smoke')
    def test_update_no_error(self):
        "Test that config datasource is correctly launched."

        if not test_utils.call_until_true(
                func=lambda: self.check_datasource_no_error('config'),
                duration=30, sleep_for=5):
            raise exceptions.TimeoutException('Datasource could not poll '
                                              'without error.')

    @decorators.attr(type='smoke')
    def test_metadata_sent(self):
        "Test that metadata on congress options are sent."

        client = self.os_admin.congress_client
        schema1 = (
            client.show_datasource_table_schema(
                self.datasource_id, 'option')['columns'])
        col1_name = find_col(schema1, 'name')
        col1_group = find_col(schema1, 'group')
        col1_namespace = find_col(schema1, 'namespace')
        schema2 = (
            client.show_datasource_table_schema(
                self.datasource_id, 'namespace')['columns'])
        col2_name = find_col(schema2, 'name')
        col2_id = find_col(schema2, 'id')

        def _check_metadata():
            res1 = (
                self.os_admin.congress_client.list_datasource_rows(
                    self.datasource_id, 'option')).get('results', None)
            res2 = (
                self.os_admin.congress_client.list_datasource_rows(
                    self.datasource_id, 'namespace')).get('results', None)
            if res1 is None or res2 is None:
                return False
            row1 = next((r for r in res1
                         if r['data'][col1_name] == u'datasource_file'),
                        None)
            row2 = next((r for r in res2
                         if r['data'][col2_name] == u'congress'),
                        None)
            if row1 is None or row2 is None:
                return False
            if row1['data'][col1_group] != 'DEFAULT':
                return False
            return row1['data'][col1_namespace] == row2['data'][col2_id]
        if not test_utils.call_until_true(
                func=_check_metadata,
                duration=100, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.attr(type='smoke')
    def test_options_sent(self):
        "Test that there is at least one value for congress option."

        driver = u'congress.datasources.cfgvalidator_driver.ValidatorDriver'
        client = self.os_admin.congress_client
        schema = (
            client.show_datasource_table_schema(
                self.datasource_id, 'binding')['columns'])
        col_value = find_col(schema, 'val')

        def _check_value():
            res = (
                self.os_admin.congress_client.list_datasource_rows(
                    self.datasource_id, 'binding')).get('results', None)
            if res is None:
                return False
            row = next((r for r in res
                        if r['data'][col_value] == driver),
                       None)
            return row is not None
        if not test_utils.call_until_true(
                func=_check_value,
                duration=100, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")
