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


class TestCinderDriver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def check_preconditions(cls):
        super(TestCinderDriver, cls).check_preconditions()
        if not (CONF.network.tenant_networks_reachable or
                CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or'
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    def setUp(cls):
        super(TestCinderDriver, cls).setUp()
        cls.os = clients.Manager(cls.admin_credentials())
        cls.cinder = cls.os.volumes_client

    @test.attr(type='smoke')
    def test_cinder_volumes_table(self):
        volume_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                'cinder', 'volumes')['columns'])

        def _check_data_table_cinder_volumes():
            # Fetch data from cinder each time, because this test may start
            # before cinder has all the users.
            _, volumes = self.cinder.list_volumes()
            volumes_map = {}
            for volume in volumes:
                volumes_map[volume['id']] = volume

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    'cinder', 'volumes'))
            for row in results['results']:
                try:
                    volume_row = volumes_map[row['data'][0]]
                except KeyError:
                    return False
                for index in range(len(volume_schema)):
                    if (str(row['data'][index]) !=
                            str(volume_row[volume_schema[index]['name']])):
                        return False
            return True

        if not test.call_until_true(func=_check_data_table_cinder_volumes,
                                    duration=20, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")
