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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import mock

# Sample responses from neutron-client, after parsing
network_response = {
    'networks':
        [{'status': 'ACTIVE',
          'subnets': ['4cef03d0-1d02-40bb-8c99-2f442aac6ab0'],
          'name': 'test-network',
          'provider:physical_network': None,
          'admin_state_up': True,
          'tenant_id': '570fe78a1dc54cffa053bd802984ede2',
          'provider:network_type': 'gre',
          'router:external': False,
          'shared': False,
          'id': '240ff9df-df35-43ae-9df5-27fae87f2492',
          'provider:segmentation_id': 4}]}

port_response = {
    "ports":
        [{"status": "ACTIVE",
          "binding:host_id": "havana",
          "name": "",
          "allowed_address_pairs": [],
          "admin_state_up": True,
          "network_id": "240ff9df-df35-43ae-9df5-27fae87f2492",
          "tenant_id": "570fe78a1dc54cffa053bd802984ede2",
          "extra_dhcp_opts": [],
          "binding:vif_type": "ovs",
          "device_owner": "network:router_interface",
          "binding:capabilities": {"port_filter": True},
          "mac_address": "fa:16:3e:ab:90:df",
          "fixed_ips": [
              {"subnet_id": "4cef03d0-1d02-40bb-8c99-2f442aac6ab0",
               "ip_address": "90.0.0.1"},
              {"subnet_id": "5cef03d0-1d02-40bb-8c99-2f442aac6ab0",
               "ip_address": "100.0.0.1"}],
          "id": "0a2ce569-85a8-45ec-abb3-0d4b34ff69ba",
          "security_groups": ['15ea0516-11ec-46e9-9e8e-7d1b6e3d7523',
                              '25ea0516-11ec-46e9-9e8e-7d1b6e3d7523'],
          "device_id": "864e4acf-bf8e-4664-8cf7-ad5daa95681e"}]}


router_response = {
    'routers':
        [{u'status': u'ACTIVE',
          u'external_gateway_info':
            {u'network_id': u'a821b8d3-af1f-4d79-9b8e-3da9674338ae',
             u'enable_snat': True},
          u'name': u'router1',
          u'admin_state_up': True,
          u'tenant_id': u'abb53cc6636848218f46d01f22bf1060',
          u'routes': [],
          u'id': u'4598c424-d608-4366-9beb-139adbd7cff5'}]}

security_group_response = {
    'security_groups':
        [{u'tenant_id': u'abb53cc6636848218f46d01f22bf1060',
          u'name': u'default',
          u'description': u'default',
          u'security_group_rules': [
              {u'remote_group_id': u'9f3860a5-87b1-499c-bf93-5ca3ef247517',
               u'direction': u'ingress',
               u'remote_ip_prefix': None,
               u'protocol': None,
               u'tenant_id': u'abb53cc6636848218f46d01f22bf1060',
               u'port_range_max': None,
               u'security_group_id': u'9f3860a5-87b1-499c-bf93-5ca3ef247517',
               u'port_range_min': None,
               u'ethertype': u'IPv6',
               u'id': u'15ea0516-11ec-46e9-9e8e-7d1b6e3d7523'}],
          u'id': u'9f3860a5-87b1-499c-bf93-5ca3ef247517'}]}


class NovaFakeClient(mock.MagicMock):
    # TODO(rajdeepd): Replace Fake with mocks directly in test_neutron_driver
    def __init__(self, *args, **kwargs):
        super(NovaFakeClient, self).__init__(*args, **kwargs)
        self.servers = mock.MagicMock()
        self.servers.list.return_value = self.get_server_list()
        self.flavors = mock.MagicMock()
        self.flavors.list.return_value = self.get_flavor_list()

        # self.hosts = mock.MagicMock()
        # self.hosts.list.return_value = self.get_host_list()
        self.hypervisors = mock.MagicMock()
        self.hypervisors.list.return_value = self.get_hypervisor_list()
        self.services = mock.MagicMock()
        self.services.list.return_value = self.get_service_list()

        self.availability_zones = mock.MagicMock()
        self.availability_zones.list.return_value = self.get_zone_list()

    def get_mock_server(self, id, name, host_id, status, tenant_id, user_id,
                        flavor, image, created, zone=None, host_name=None,
                        addresses=None, tags=None):
        server = mock.MagicMock()
        server.id = id
        server.hostId = host_id
        server.tenant_id = tenant_id
        server.user_id = user_id
        server.status = status
        server.name = name
        server.image = image
        server.flavor = flavor
        server.created = created
        server.addresses = addresses if addresses else {}
        server.tags = tags if tags else []
        if zone is not None:
            setattr(server, 'OS-EXT-AZ:availability_zone', zone)
        else:
            # This ensures that the magic mock raises an AttributeError
            delattr(server, 'OS-EXT-AZ:availability_zone')
        if host_name is not None:
            setattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname',
                    host_name)
        else:
            # This ensures that the magic mock raises an AttributeError
            delattr(server, 'OS-EXT-SRV-ATTR:hypervisor_hostname')
        return server

    def get_server_list(self):
        server_one = (
            self.get_mock_server('1234', 'sample-server',
                                 "e4d909c290d0fb1ca068ffaddf22cbd0",
                                 'BUILD',
                                 '50e14867-7c64-4ec9-be8d-ed2470ca1d24',
                                 '33ea0494-2bdf-4382-a445-9068997430b9',
                                 {"id": "1"}, {"id": "2"},
                                 '2019-02-26T08:48:15Z', 'default', 'host1',
                                 {'net_mgmt': [{
                                     'addr': '192.168.0.60',
                                     'version': 4,
                                     'OS-EXT-IPS-MAC:mac_addr': '11:11:11:11',
                                     'OS-EXT-IPS:type': 'fixed'}]}))

        server_two = (
            self.get_mock_server('5678', 'sample-server2',
                                 "9e107d9d372bb6826bd81d3542a419d6",
                                 'ACTIVE',
                                 '50e14867-7c64-4ec9-be8d-ed2470ca1d24',
                                 '33ea0494-2bdf-4382-a445-9068997430b9',
                                 {"id": "1"}, {"id": "2"},
                                 '2019-02-26T08:48:15Z',
                                 addresses={'net1': []},
                                 tags=['tag1', 'tag2']))

        server_three = (
            self.get_mock_server('9012', 'sample-server3',
                                 "9e107d9d372bb6826bd81d3542a419d6",
                                 'ACTIVE',
                                 '50e14867-7c64-4ec9-be8d-ed2470ca1d24',
                                 '33ea0494-2bdf-4382-a445-9068997430b9',
                                 {"id": "1"}, {"id": "2"},
                                 '2019-02-26T08:48:15Z', 'foo', 'host2',
                                 tags=['tag1', 'tag2', 'tag3']))

        return [server_one, server_two, server_three]

    def get_flavor(self, id, name, vcpus, ram, disk, ephemeral, rxtx_factor):
        f = mock.MagicMock()
        f.id = id
        f.name = name
        f.vcpus = vcpus
        f.ram = ram
        f.disk = disk
        f.ephemeral = ephemeral
        f.rxtx_factor = rxtx_factor
        return f

    def get_flavor_list(self):
        flavor_one = self.get_flavor("1", "256 MB Server", 1, 256, 10, 10, 1.0)
        flavor_two = self.get_flavor("2", "512 MB Server", 2, 512, 20, 20, 1.0)
        flavor_three = self.get_flavor("3", "128 MB Server", 4, 128, 0, 0, 3.0)
        flavor_four = self.get_flavor("4", "1024 MB Server", 3, 1024, 10, 10,
                                      2.0)

        return [flavor_one, flavor_two, flavor_three, flavor_four]

#    def get_host(self, host_name, service, zone):
#        h = mock.MagicMock()
#        h.host_name = host_name
#        h.service = service
#        h.zone = zone
#        return h
#
#    def get_host_list(self):
#        h_one = self.get_host('host1', 'nova-compute', 'nova1')
#        h_two = self.get_host('host2', 'nova-cert', 'nova1')
#
#        return [h_one, h_two]

    def get_hypervisor(self, host_name, id_, state, status):
        h = mock.MagicMock()
        h.hypervisor_hostname = host_name
        h.id = id_
        h.state = state
        h.status = status
        return h

    def get_hypervisor_list(self, nova_api_version='2.26'):
        from distutils.version import StrictVersion
        if StrictVersion(nova_api_version) <= StrictVersion('2.52'):
            h_one = self.get_hypervisor('host1', 2, 'up', 'enabled')
            h_two = self.get_hypervisor('host2', 3, 'down', 'enabled')
        else:
            h_one = self.get_hypervisor('host1', '2', 'up', 'enabled')
            h_two = self.get_hypervisor('host2', '3', 'down', 'enabled')

        return [h_one, h_two]

    def get_service(self, id, binary, host, zone, status, state,
                    updated_at, disabled_reason):
        s = mock.MagicMock()
        s.id = id
        s.binary = binary
        s.host = host
        s.zone = zone
        s.status = status
        s.state = state
        s.updated_at = updated_at
        s.disabled_reason = disabled_reason

        return s

    def get_service_list(self):
        service_one = self.get_service(1, 'nova-compute', 'nova',
                                       'nova1', 'enabled', 'up',
                                       '2015-07-28T08:28:37.000000', None)
        service_two = self.get_service(2, 'nova-schedule', 'nova',
                                       'nova1', 'disabled', 'up',
                                       '2015-07-28T08:28:38.000000',
                                       'daily maintenance')

        return [service_one, service_two]

    def get_availability_zone(self, name, state):
        zone = mock.MagicMock()
        zone.zoneName = name
        zone.zoneState = state
        return zone

    def get_zone_list(self):
        zone_one = self.get_availability_zone('AZ1', 'available')
        zone_two = self.get_availability_zone('AZ2', 'not available')

        return [zone_one, zone_two]
