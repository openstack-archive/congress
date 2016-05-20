# Copyright 2016 NTT All Rights Reserved.
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

from tempest.lib import exceptions
from tempest import test

from congress_tempest_tests.tests.scenario import manager_congress


class TestDoctorDriver(manager_congress.ScenarioPolicyBase):
    def setUp(self):
        super(TestDoctorDriver, self).setUp()
        doctor_setting = {
            'name': 'doctor',
            'driver': 'doctor',
            'config': None,
            }
        self.client = self.admin_manager.congress_client

        response = self.client.create_datasource(doctor_setting)
        self.datasource_id = response['id']

    def tearDown(self):
        super(TestDoctorDriver, self).tearDown()
        self.client.delete_datasource(self.datasource_id)

    def _list_datasource_rows(self, datasource, table):
        return self.client.list_datasource_rows(datasource, table)

    @test.attr(type='smoke')
    def test_doctor_event_tables(self):
        rows = [
            {
                "id": "0123-4567-89ab",
                "time": "2016-02-22T11:48:55Z",
                "type": "compute.host.down",
                "details": {
                    "hostname": "compute1",
                    "status": "down",
                    "monitor": "zabbix1",
                    "monitor_event_id": "111"
                    }
                }
            ]

        expected_row = [
            "0123-4567-89ab",
            "2016-02-22T11:48:55Z",
            "compute.host.down",
            "compute1",
            "down",
            "zabbix1",
            "111"
            ]

        self.client.update_datasource_row(self.datasource_id, 'events', rows)

        results = self._list_datasource_rows(self.datasource_id, 'events')
        if len(results['results']) != 1:
            error_msg = ('Unexpected additional rows are '
                         'inserted. row details: %s' % results['results'])
            raise exceptions.InvalidStructure(error_msg)

        if results['results'][0]['data'] != expected_row:
            msg = ('inserted row %s is not expected row %s'
                   % (results['data'], expected_row))
            raise exceptions.InvalidStructure(msg)
