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
from tempest import clients
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.scenario import manager_congress
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestCeilometerDriver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def check_preconditions(cls):
        super(TestCeilometerDriver, cls).check_preconditions()

    def setUp(cls):
        super(TestCeilometerDriver, cls).setUp()
        if not CONF.service_available.ceilometer:
            msg = ("%s skipped as ceilometer is not available" % cls.__name__)
            raise cls.skipException(msg)
        cls.os = clients.Manager(cls.admin_credentials())
        cls.telemetry_client = cls.os.telemetry_client

    @test.attr(type='smoke')
    def test_ceilometer_meters_table(self):
        meter_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                'ceilometer', 'meters')['columns'])

        def _check_data_table_ceilometer_meters():
            # Fetch data from ceilometer each time, because this test may start
            # before ceilometer has all the users.
            _, meters = self.telemetry_client.list_meters()
            meter_map = {}
            for meter in meters:
                meter_map[meter['meter_id']] = meter

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    'ceilometer', 'meters'))
            for row in results['results']:
                try:
                    meter_row = meter_map[row['data'][0]]
                except KeyError:
                    return False
                for index in range(len(meter_schema)):
                    if (str(row['data'][index]) !=
                            str(meter_row[meter_schema[index]['name']])):
                        return False
            return True

        if not test.call_until_true(func=_check_data_table_ceilometer_meters,
                                    duration=20, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")
