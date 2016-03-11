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
from tempest import config
from tempest.lib import exceptions
from tempest import test

from congress_tempest_tests.tests.scenario import helper
from congress_tempest_tests.tests.scenario import manager_congress

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestNovaDriver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def skip_checks(cls):
        super(TestNovaDriver, cls).skip_checks()
        if not CONF.service_available.nova:
            skip_msg = ("%s skipped as nova is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

        if not (CONF.network.tenant_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    def setUp(self):
        super(TestNovaDriver, self).setUp()
        self.keypairs = {}
        self.servers = []
        self.datasource_id = manager_congress.get_datasource_id(
            self.admin_manager.congress_client, 'nova')

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_nova_datasource_driver_servers(self):
        self._setup_network_and_servers()

        server_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'servers')['columns'])
        # Convert some of the column names.

        def convert_col(col):
            if col == 'host_id':
                return 'hostId'
            elif col == 'image_id':
                return 'image'
            elif col == 'flavor_id':
                return 'flavor'
            elif col == 'zone':
                return 'OS-EXT-AZ:availability_zone'
            elif col == 'host_name':
                return 'OS-EXT-SRV-ATTR:hypervisor_hostname'
            else:
                return col

        keys = [convert_col(c['name']) for c in server_schema]

        @helper.retry_on_exception
        def _check_data_table_nova_servers():
            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'servers'))
            for row in results['results']:
                match = True
                for index in range(len(keys)):
                    if keys[index] in ['image', 'flavor']:
                        val = self.servers[0][keys[index]]['id']
                    # Test servers created doesn't have this attribute,
                    # so ignoring the same in tempest tests.
                    elif keys[index] in \
                            ['OS-EXT-SRV-ATTR:hypervisor_hostname']:
                        continue
                    else:
                        val = self.servers[0][keys[index]]

                    if row['data'][index] != val:
                        match = False
                        break
                if match:
                    return True
            return False

        if not test.call_until_true(func=_check_data_table_nova_servers,
                                    duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_nova_datasource_driver_flavors(self):

        @helper.retry_on_exception
        def _check_data_table_nova_flavors():
            # Fetch data from nova each time, because this test may start
            # before nova has all the users.
            flavors = self.flavors_client.list_flavors(detail=True)
            flavor_id_map = {}
            for flavor in flavors['flavors']:
                flavor_id_map[flavor['id']] = flavor

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'flavors'))
            # TODO(alexsyip): Not sure what the following OS-FLV-EXT-DATA:
            # prefix is for.
            keys = ['id', 'name', 'vcpus', 'ram', 'disk',
                    'OS-FLV-EXT-DATA:ephemeral', 'rxtx_factor']
            for row in results['results']:
                match = True
                try:
                    flavor_row = flavor_id_map[row['data'][0]]
                except KeyError:
                    return False
                for index in range(len(keys)):
                    if row['data'][index] != flavor_row[keys[index]]:
                        match = False
                        break
                if match:
                    return True
            return False

        if not test.call_until_true(func=_check_data_table_nova_flavors,
                                    duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")
