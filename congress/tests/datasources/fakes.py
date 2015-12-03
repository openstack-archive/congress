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

import mock


class NovaFakeClient(mock.MagicMock):
    # TODO(rajdeepd): Replace Fake with mocks directly in test_neutron_driver
    def __init__(self, *args, **kwargs):
        super(NovaFakeClient, self).__init__(*args, **kwargs)
        self.servers = mock.MagicMock()
        self.servers.list.return_value = self.get_server_list()
        self.flavors = mock.MagicMock()
        self.flavors.list.return_value = self.get_flavor_list()

        self.hosts = mock.MagicMock()
        self.hosts.list.return_value = self.get_host_list()
        self.services = mock.MagicMock()
        self.services.list.return_value = self.get_service_list()

        self.availability_zones = mock.MagicMock()
        self.availability_zones.list.return_value = self.get_zone_list()

    def get_mock_server(self, id, name, host_id, status, tenant_id, user_id,
                        flavor, image, zone=None, host_name=None):
        server = mock.MagicMock()
        server.id = id
        server.hostId = host_id
        server.tenant_id = tenant_id
        server.user_id = user_id
        server.status = status
        server.name = name
        server.image = image
        server.flavor = flavor
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
            self.get_mock_server(1234, 'sample-server',
                                 "e4d909c290d0fb1ca068ffaddf22cbd0",
                                 'BUILD',
                                 '50e14867-7c64-4ec9-be8d-ed2470ca1d24',
                                 '33ea0494-2bdf-4382-a445-9068997430b9',
                                 {"id": 1}, {"id": 2}, 'default', 'host1'))

        server_two = (
            self.get_mock_server(5678, 'sample-server2',
                                 "9e107d9d372bb6826bd81d3542a419d6",
                                 'ACTIVE',
                                 '50e14867-7c64-4ec9-be8d-ed2470ca1d24',
                                 '33ea0494-2bdf-4382-a445-9068997430b9',
                                 {"id": 1}, {"id": 2}))

        server_three = (
            self.get_mock_server(9012, 'sample-server3',
                                 "9e107d9d372bb6826bd81d3542a419d6",
                                 'ACTIVE',
                                 '50e14867-7c64-4ec9-be8d-ed2470ca1d24',
                                 '33ea0494-2bdf-4382-a445-9068997430b9',
                                 {"id": 1}, {"id": 2}, 'foo', 'host2'))

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
        flavor_one = self.get_flavor(1, "256 MB Server", 1, 256, 10, 10, 1.0)
        flavor_two = self.get_flavor(2, "512 MB Server", 2, 512, 20, 20, 1.0)
        flavor_three = self.get_flavor(3, "128 MB Server", 4, 128, 0, 0, 3.0)
        flavor_four = self.get_flavor(4, "1024 MB Server", 3, 1024, 10, 10,
                                      2.0)

        return [flavor_one, flavor_two, flavor_three, flavor_four]

    def get_host(self, host_name, service, zone):
        h = mock.MagicMock()
        h.host_name = host_name
        h.service = service
        h.zone = zone
        return h

    def get_host_list(self):
        h_one = self.get_host('host1', 'nova-compute', 'nova1')
        h_two = self.get_host('host2', 'nova-cert', 'nova1')

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
