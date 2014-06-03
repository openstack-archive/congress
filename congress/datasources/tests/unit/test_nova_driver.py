#!/usr/bin/env python
# Copyright (c) 2014 VMware, Inc. All rights reserved.
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
#
from congress.datasources.nova_driver import NovaDriver
from congress.datasources.tests.unit import fakes
from congress.tests import base
from mock import MagicMock
from mock import patch
import novaclient


class TestNovaDriver(base.TestCase):

    def setUp(self):
        super(base.TestCase, self).setUp()
        nova_client = MagicMock()
        self.cs = fakes.NovaFakeClient()

        with patch.object(novaclient.client.Client, '__init__',
                          return_value=nova_client):
            self.driver = NovaDriver()

    def test_driver_called(self):
        self.assertIsNotNone(self.driver.nova_client)

    def test_get_tuple_list_servers(self):
        servers_list = self.cs.servers.list(detailed=True)
        server_tuples = self.driver._get_tuple_list(servers_list,
                                                    self.driver.SERVERS)
        self.assertEqual(3, len(server_tuples))
        #  tuple = (s.id, s.name, s.hostId, s.status, s.tenant_id,
        #   s.user_id, image, flavor)
        for t in server_tuples:
            id = t[0]
            name = t[1]
            host_id = t[2]
            status = t[3]
            tenant_id = t[4]
            user_id = t[5]
            image_id = t[6]
            flavor_id = t[7]
            self.assertIn(id, [1234, 5678, 9012])
            # see congress.datasources.tests.unit.fakes for actual values
            if id == 1234:
                self.assertEqual("sample-server", name)
                self.assertEqual("e4d909c290d0fb1ca068ffaddf22cbd0", host_id)
                self.assertEqual("BUILD", status)
                self.assertEqual("4c7057c23b9c46c5ac21-b91bd8b5462b", user_id)
                self.assertEqual("4ffc664c198e435e9853f2538fbcd7a7", tenant_id)
                self.assertEqual(2, image_id)
                self.assertEqual(1, flavor_id)

            elif id == 5678:
                self.assertEqual("sample-server2", name)
                self.assertEqual("9e107d9d372bb6826bd81d3542a419d6", host_id)
                self.assertEqual("ACTIVE", status)
                self.assertEqual("4c7057c23b9c46c5ac21-b91bd8b5462b", user_id)
                self.assertEqual("4ffc664c198e435e9853f2538fbcd7a7", tenant_id)
                self.assertEqual(2, image_id)
                self.assertEqual(1, flavor_id)

            elif id == 9012:
                self.assertEqual("sample-server3", name)
                self.assertEqual("9e107d9d372bb6826bd81d3542a419d6", host_id)
                self.assertEqual("ACTIVE", status)
                self.assertEqual("4c7057c23b9c46c5ac21-b91bd8b5462b", user_id)
                self.assertEqual("4ffc664c198e435e9853f2538fbcd7a7", tenant_id)
                self.assertEqual(2, image_id)
                self.assertEqual(1, flavor_id)

    def test_get_tuple_list_flavors(self):
        flavor_list = self.cs.flavors.list(detailed=True)
        flavor_tuples = self.driver._get_tuple_list(flavor_list,
                                                    self.driver.FLAVORS)
        self.assertEqual(4, len(flavor_tuples))
        # "id", "name", "vcpus", "ram", "disk", "ephemeral",
        #            "rxtx_factor")
        for f in flavor_tuples:
            id = f[0]
            name = f[1]
            vcpus = f[2]
            ram = f[3]
            disk = f[4]
            ephemeral = f[5]
            rxtx_factor = f[6]

            self.assertIn(id, [1, 2, 3, 4])

            # {'id': 1, 'name': '256 MB Server', 'ram': 256, 'disk': 10,
            # 'vcpus' : 1, 'OS-FLV-EXT-DATA:ephemeral': 10,
            # 'os-flavor-access:is_public': True, 'rxtx_factor' : 1.0,
            # 'links': {}},
            if id == 1:
                self.assertEqual('256 MB Server', name)
                self.assertEqual(256, ram)
                self.assertEqual(10, disk)
                self.assertEqual(1, vcpus)
                self.assertEqual(10, ephemeral)
                self.assertEqual(1.0, rxtx_factor)
            # {'id': 2, 'name': '512 MB Server', 'ram': 512, 'disk': 20,
            #  'vcpus' :2, 'OS-FLV-EXT-DATA:ephemeral': 20,
            #  'os-flavor-access:is_public': False, 'rxtx_factor' : 1.0,
            #  'links': {}},
            elif id == 2:
                self.assertEqual('512 MB Server', name)
                self.assertEqual(512, ram)
                self.assertEqual(20, disk)
                self.assertEqual(2, vcpus)
                self.assertEqual(20, ephemeral)
                self.assertEqual(1.0, rxtx_factor)
            # {'id': 3, 'name': '128 MB Server', 'ram': 128, 'disk': 0,
            #  'vcpus' : 4, 'OS-FLV-EXT-DATA:ephemeral': 0,
            #  'os-flavor-access:is_public': True, 'rxtx_factor' : 3.0,
            #  'links': {}}
            elif id == 3:
                self.assertEqual('128 MB Server', name)
                self.assertEqual(128, ram)
                self.assertEqual(0, disk)
                self.assertEqual(4, vcpus)
                self.assertEqual(0, ephemeral)
                self.assertEqual(3.0, rxtx_factor)
            # {'id': 4, 'name': '1024 MB Server', 'ram': 1024, 'disk': 10,
            #  'vcpus' : 3, 'OS-FLV-EXT-DATA:ephemeral': 10,
            #  'os-flavor-access:is_public': True, 'rxtx_factor' : 2.0,
            #  'links': {}},
            elif id == 4:
                self.assertEqual('1024 MB Server', name)
                self.assertEqual(1024, ram)
                self.assertEqual(10, disk)
                self.assertEqual(3, vcpus)
                self.assertEqual(10, ephemeral)
                self.assertEqual(2.0, rxtx_factor)
                self.assertEqual('1024 MB Server', name)

    def test_get_tuple_list_hosts(self):
        host_list = self.cs.hosts.list()
        host_tuples = self.driver._get_tuple_list(host_list,
                                                  self.driver.HOSTS)
        self.assertEqual(2, len(host_tuples))
        # {'hosts':
        #      [{'host_name': 'host1',
        #        'service': 'nova-compute',
        #        'zone': zone},
        #       {'host_name': 'host2',
        #        'service': 'nova-cert',
        #        'zone': zone}]}
        for host in host_tuples:
            host_name = host[0]
            service = host[1]
            zone = host[2]

            if host_name == 'host1':
                self.assertEqual('nova-compute', service)
                self.assertEqual('nova1', str(zone))
            elif host_name == 'host2':
                self.assertEqual('nova-cert', service)
                self.assertEqual('nova1', str(zone))
