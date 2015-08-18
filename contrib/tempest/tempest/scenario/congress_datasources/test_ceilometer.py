# Copyright 2014 OpenStack Foundation
# All Rights Reserved.
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
from oslo_log import log as logging
from tempest_lib import decorators

from tempest import clients  # noqa
from tempest import config  # noqa
from tempest import exceptions  # noqa
from tempest.scenario import manager_congress  # noqa
from tempest import test  # noqa


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestCeilometerDriver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def check_preconditions(cls):
        super(TestCeilometerDriver, cls).check_preconditions()

    def setUp(cls):
        super(TestCeilometerDriver, cls).setUp()
        if not CONF.service_available.ceilometer:
            msg = ("%s skipped as ceilometer is not available" % \
                   cls.__class__.__name__)
            raise cls.skipException(msg)
        cls.os = clients.Manager(cls.admin_manager.auth_provider.credentials)
        cls.telemetry_client = cls.os.telemetry_client
        cls.datasource_id = manager_congress.get_datasource_id(
            cls.admin_manager.congress_client, 'ceilometer')

    @decorators.skip_because(bug='1486246')
    @test.attr(type='smoke')
    def test_ceilometer_meters_table(self):
        meter_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'meters')['columns'])
        meter_id_col = next(i for i, c in enumerate(meter_schema)
                            if c['name'] == 'meter_id')

        def _check_data_table_ceilometer_meters():
            # Fetch data from ceilometer each time, because this test may start
            # before ceilometer has all the users.
            meters = self.telemetry_client.list_meters()
            meter_map = {}
            for meter in meters:
                meter_map[meter['meter_id']] = meter

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'meters'))
            for row in results['results']:
                try:
                    meter_row = meter_map[row['data'][meter_id_col]]
                except KeyError:
                    return False
                for index in range(len(meter_schema)):
                    if (str(row['data'][index]) !=
                            str(meter_row[meter_schema[index]['name']])):
                        return False
            return True

        if not test.call_until_true(func=_check_data_table_ceilometer_meters,
                                    duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")
