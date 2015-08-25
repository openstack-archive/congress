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
import time

from oslo_log import log as logging
from tempest_lib import decorators

from tempest import clients  # noqa
from tempest import config  # noqa
from tempest import exceptions  # noqa
from tempest.scenario import manager_congress  # noqa
from tempest import test  # noqa

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestNeutronV2Driver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def check_preconditions(cls):
        super(TestNeutronV2Driver, cls).check_preconditions()
        if not (CONF.network.tenant_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    def setUp(cls):
        super(TestNeutronV2Driver, cls).setUp()
        if not CONF.service_available.neutron:
            skip_msg = ("%s skipped as neutron is not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)
        cls.os = clients.Manager(cls.admin_manager.auth_provider.credentials)
        cls.neutron_client = cls.os.network_client
        cls.datasource_id = manager_congress.get_datasource_id(
            cls.admin_manager.congress_client, 'neutronv2')

    @decorators.skip_because(bug='1486246')
    @test.attr(type='smoke')
    @test.services('network')
    def test_neutronv2_networks_table(self):
        def _check_data():
            networks = self.neutron_client.list_networks()
            network_map = {}
            for network in networks['networks']:
                network_map[network['id']] = network

            client = self.admin_manager.congress_client
            client.request_refresh(self.datasource_id)
            time.sleep(1)

            network_schema = (client.show_datasource_table_schema(
                self.datasource_id, 'networks')['columns'])

            results = (client.list_datasource_rows(
                self.datasource_id, 'networks'))
            for row in results['results']:
                network_row = network_map[row['data'][0]]
                for index in range(len(network_schema)):
                    if (str(row['data'][index]) !=
                            str(network_row[network_schema[index]['name']])):
                        return False
            return True

        if not test.call_until_true(func=_check_data,
                                    duration=200, sleep_for=10):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.skip_because(bug='1486246')
    @test.attr(type='smoke')
    @test.services('network')
    def test_neutronv2_ports_tables(self):
        port_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'ports')['columns'])

        port_sec_binding_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'security_group_port_bindings')['columns'])

        fixed_ips_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'fixed_ips')['columns'])

        def _check_data():
            ports_from_neutron = self.neutron_client.list_ports()
            port_map = {}
            for port in ports_from_neutron['ports']:
                port_map[port['id']] = port

            client = self.admin_manager.congress_client
            client.request_refresh(self.datasource_id)
            time.sleep(1)

            ports = (client.list_datasource_rows(self.datasource_id, 'ports'))
            security_group_port_bindings = (
                client.list_datasource_rows(
                    self.datasource_id, 'security_group_port_bindings'))
            fixed_ips = (
                client.list_datasource_rows(self.datasource_id, 'fixed_ips'))

            # Validate ports table
            for row in ports['results']:
                port_row = port_map[row['data'][0]]
                for index in range(len(port_schema)):
                    if (str(row['data'][index]) !=
                            str(port_row[port_schema[index]['name']])):
                        return False

            # validate security_group_port_bindings table
            for row in security_group_port_bindings['results']:
                port_row = port_map[row['data'][0]]
                for index in range(len(port_sec_binding_schema)):
                    row_index = port_sec_binding_schema[index]['name']
                    # Translate port_id -> id
                    if row_index == 'port_id':
                        if (str(row['data'][index]) !=
                                str(port_row['id'])):
                            return False
                    elif row_index == 'security_group_id':
                        if (str(row['data'][index]) not in
                                port_row['security_groups']):
                            return False

            # validate fixed_ips
            for row in fixed_ips['results']:
                port_row = port_map[row['data'][0]]
                for index in range(len(fixed_ips_schema)):
                    row_index = fixed_ips_schema[index]['name']
                    if row_index in ['subnet_id', 'ip_address']:
                        if not port_row['fixed_ips']:
                            continue
                        for fixed_ip in port_row['fixed_ips']:
                            if row['data'][index] == fixed_ip[row_index]:
                                break
                        else:
                            # no subnet_id/ip_address match found
                            return False
            return True

        if not test.call_until_true(func=_check_data,
                                    duration=200, sleep_for=10):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.skip_because(bug='1486246')
    @test.attr(type='smoke')
    @test.services('network')
    def test_neutronv2_subnets_tables(self):
        subnet_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'subnets')['columns'])

        host_routes_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'host_routes')['columns'])

        dns_nameservers_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'dns_nameservers')['columns'])

        allocation_pools_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'allocation_pools')['columns'])

        def _check_data():
            subnets_from_neutron = self.neutron_client.list_subnets()
            subnet_map = {}
            for subnet in subnets_from_neutron['subnets']:
                subnet_map[subnet['id']] = subnet

            client = self.admin_manager.congress_client
            client.request_refresh(self.datasource_id)
            time.sleep(1)

            subnets = (
                client.list_datasource_rows(self.datasource_id, 'subnets'))
            host_routes = (
                client.list_datasource_rows(self.datasource_id, 'host_routes'))
            dns_nameservers = (
                client.list_datasource_rows(
                    self.datasource_id, 'dns_nameservers'))
            allocation_pools = (
                client.list_datasource_rows(
                    self.datasource_id, 'allocation_pools'))

            # Validate subnets table
            for row in subnets['results']:
                subnet_row = subnet_map[row['data'][0]]
                for index in range(len(subnet_schema)):
                    if (str(row['data'][index]) !=
                            str(subnet_row[subnet_schema[index]['name']])):
                        return False

            # validate dns_nameservers
            for row in dns_nameservers['results']:
                subnet_row = subnet_map[row['data'][0]]
                for index in range(len(dns_nameservers_schema)):
                    row_index = dns_nameservers_schema[index]['name']
                    if row_index in ['dns_nameserver']:
                        if (row['data'][index]
                                not in subnet_row['dns_nameservers']):
                            return False

            # validate host_routes
            for row in host_routes['results']:
                subnet_row = subnet_map[row['data'][0]]
                for index in range(len(host_routes_schema)):
                    row_index = host_routes_schema[index]['name']
                    if row_index in ['destination', 'nexthop']:
                        if not subnet_row['host_routes']:
                            continue
                        for host_route in subnet_row['host_routes']:
                            if row['data'][index] == host_route[row_index]:
                                break
                        else:
                            # no destination/nexthop match found
                            return False

            # validate allocation_pools
            for row in allocation_pools['results']:
                subnet_row = subnet_map[row['data'][0]]
                for index in range(len(allocation_pools_schema)):
                    row_index = allocation_pools_schema[index]['name']
                    if row_index in ['start', 'end']:
                        if not subnet_row['allocation_pools']:
                            continue
                        for allocation_pool in subnet_row['allocation_pools']:
                            if (row['data'][index] ==
                                    allocation_pool[row_index]):
                                break
                        else:
                            # no destination/nexthop match found
                            return False
            return True

        if not test.call_until_true(func=_check_data,
                                    duration=200, sleep_for=10):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.skip_because(bug='1486246')
    @test.attr(type='smoke')
    @test.services('network')
    def test_neutronv2_routers_tables(self):
        router_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'routers')['columns'])

        ext_gw_info_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'external_gateway_infos')['columns'])

        def _check_data():
            routers_from_neutron = self.neutron_client.list_routers()
            router_map = {}
            for router in routers_from_neutron['routers']:
                router_map[router['id']] = router

            client = self.admin_manager.congress_client
            client.request_refresh(self.datasource_id)
            time.sleep(1)

            routers = (
                client.list_datasource_rows(self.datasource_id, 'routers'))

            ext_gw_info = (
                client.list_datasource_rows(
                    self.datasource_id, 'external_gateway_infos'))

            # Validate routers table
            for row in routers['results']:
                router_row = router_map[row['data'][0]]
                for index in range(len(router_schema)):
                    if (str(row['data'][index]) !=
                            str(router_row[router_schema[index]['name']])):
                        return False

            # validate external_gateway_infos
            for row in ext_gw_info['results']:
                router_ext_gw_info = (
                    router_map[row['data'][0]]['external_gateway_info'])
                # populate router_id
                router_ext_gw_info['router_id'] = row['data'][0]
                for index in range(len(ext_gw_info_schema)):
                    val = router_ext_gw_info[ext_gw_info_schema[index]['name']]
                    if (str(row['data'][index]) != str(val)):
                        return False
            return True

        if not test.call_until_true(func=_check_data,
                                    duration=200, sleep_for=10):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.skip_because(bug='1486246')
    @test.attr(type='smoke')
    @test.services('network')
    def test_neutronv2_security_groups_table(self):
        sg_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'security_groups')['columns'])

        def _check_data():
            client = self.neutron_client
            security_groups_neutron = client.list_security_groups()
            security_groups_map = {}
            for security_group in security_groups_neutron['security_groups']:
                security_groups_map[security_group['id']] = security_group

            client = self.admin_manager.congress_client
            client.request_refresh(self.datasource_id)
            time.sleep(1)

            security_groups = (
                client.list_datasource_rows(
                    self.datasource_id, 'security_groups'))

            # Validate security_group table
            for row in security_groups['results']:
                sg_row = security_groups_map[row['data'][0]]
                for index in range(len(sg_schema)):
                    if (str(row['data'][index]) !=
                            str(sg_row[sg_schema[index]['name']])):
                        return False
            return True

        if not test.call_until_true(func=_check_data,
                                    duration=200, sleep_for=10):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.skip_because(bug='1486246')
    @test.attr(type='smoke')
    @test.services('network')
    def test_neutronv2_security_group_rules_table(self):
        sgrs_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'security_group_rules')['columns'])

        def _check_data():
            client = self.neutron_client
            security_groups_neutron = client.list_security_groups()
            sgrs_map = {}  # security_group_rules
            for sg in security_groups_neutron['security_groups']:
                for sgr in sg['security_group_rules']:
                    sgrs_map[sgr['id']] = sgr

            client = self.admin_manager.congress_client
            client.request_refresh(self.datasource_id)
            time.sleep(1)

            security_group_rules = (
                client.list_datasource_rows(
                    self.datasource_id, 'security_group_rules'))

            # Validate security_group_rules table
            for row in security_group_rules['results']:
                sg_rule_row = sgrs_map[row['data'][1]]
                for index in range(len(sgrs_schema)):
                    if (str(row['data'][index]) !=
                            str(sg_rule_row[sgrs_schema[index]['name']])):
                        return False
            return True

        if not test.call_until_true(func=_check_data,
                                    duration=200, sleep_for=10):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")
