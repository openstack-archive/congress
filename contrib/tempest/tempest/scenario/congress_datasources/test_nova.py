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
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.scenario import manager_congress
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestNovaDriver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def check_preconditions(cls):
        super(TestNovaDriver, cls).check_preconditions()
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

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_nova_datasource_driver_servers(self):
        self._setup_network_and_servers()

        def _check_data_table_nova_servers():
            results = \
                self.admin_manager.congress_client.list_datasource_rows(
                    'nova', 'servers')
            keys = ['id', 'name', 'hostId', 'status', 'tenant_id',
                    'user_id', 'image', 'flavor']
            for row in results['results']:
                match = True
                for index in range(len(keys)):
                    if keys[index] in ['image', 'flavor']:
                        val = self.servers[0][keys[index]]['id']
                    else:
                        val = self.servers[0][keys[index]]

                    if row['data'][index] != val:
                        match = False
                        break
                if match:
                    return True
            return False

        if not test.call_until_true(func=_check_data_table_nova_servers,
                                    duration=20, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_nova_datasource_driver_flavors(self):
        _, flavors = self.flavors_client.list_flavors_with_detail()
        flavor_id_map = {}
        for flavor in flavors:
            flavor_id_map[flavor['id']] = flavor

        def _check_data_table_nova_flavors():
            results = \
                self.admin_manager.congress_client.list_datasource_rows(
                    'nova', 'flavors')
            keys = ['id', 'name', 'vcpus', 'ram', 'disk',
                    'OS-FLV-EXT-DATA:ephemeral', 'rxtx_factor']
            for row in results['results']:
                match = True
                flavor_row = flavor_id_map[row['data'][0]]
                for index in range(len(keys)):
                    if row['data'][index] != flavor_row[keys[index]]:
                        match = False
                        break
                if match:
                    return True
            return False

        if not test.call_until_true(func=_check_data_table_nova_flavors,
                                    duration=20, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")
