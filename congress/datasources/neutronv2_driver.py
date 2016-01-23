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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
import neutronclient.v2_0.client
from oslo_log import log as logging

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return NeutronV2Driver(name, keys, inbox, datapath, args)


class NeutronV2Driver(datasource_driver.PollingDataSourceDriver,
                      datasource_driver.ExecutionDriver):

    NETWORKS = 'networks'
    FIXED_IPS = 'fixed_ips'
    SECURITY_GROUP_PORT_BINDINGS = 'security_group_port_bindings'
    PORTS = 'ports'
    ALLOCATION_POOLS = 'allocation_pools'
    DNS_NAMESERVERS = 'dns_nameservers'
    HOST_ROUTES = 'host_routes'
    SUBNETS = 'subnets'
    EXTERNAL_FIXED_IPS = 'external_fixed_ips'
    EXTERNAL_GATEWAY_INFOS = 'external_gateway_infos'
    ROUTERS = 'routers'
    SECURITY_GROUP_RULES = 'security_group_rules'
    SECURITY_GROUPS = 'security_groups'
    FLOATING_IPS = 'floating_ips'

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    floating_ips_translator = {
        'translation-type': 'HDICT',
        'table-name': FLOATING_IPS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'The UUID of the floating IP address',
              'translator': value_trans},
             {'fieldname': 'router_id', 'desc': 'UUID of router',
              'translator': value_trans},
             {'fieldname': 'tenant_id', 'desc': 'Tenant ID',
              'translator': value_trans},
             {'fieldname': 'floating_network_id',
              'desc': 'The UUID of the network associated with floating IP',
              'translator': value_trans},
             {'fieldname': 'fixed_ip_address',
              'desc': 'Fixed IP address associated with floating IP address',
              'translator': value_trans},
             {'fieldname': 'floating_ip_address',
              'desc': 'The floating IP address', 'translator': value_trans},
             {'fieldname': 'port_id', 'desc': 'UUID of port',
              'translator': value_trans},
             {'fieldname': 'status', 'desc': 'The floating IP status',
              'translator': value_trans})}

    networks_translator = {
        'translation-type': 'HDICT',
        'table-name': NETWORKS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'Network ID',
              'translator': value_trans},
             {'fieldname': 'tenant_id', 'desc': 'Tenant ID',
              'translator': value_trans},
             {'fieldname': 'name', 'desc': 'Network name',
              'translator': value_trans},
             {'fieldname': 'status', 'desc': 'Network status',
              'translator': value_trans},
             {'fieldname': 'admin_state_up',
              'desc': 'Administrative state of the network (true/false)',
              'translator': value_trans},
             {'fieldname': 'shared',
              'desc': 'Indicates if network is shared across all tenants',
              'translator': value_trans})}

    ports_fixed_ips_translator = {
        'translation-type': 'HDICT',
        'table-name': FIXED_IPS,
        'parent-key': 'id',
        'parent-col-name': 'port_id',
        'parent-key-desc': 'UUID of Port',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'ip_address',
              'desc': 'The IP addresses for the port',
              'translator': value_trans},
             {'fieldname': 'subnet_id',
              'desc': 'The UUID of the subnet to which the port is attached',
              'translator': value_trans})}

    ports_security_groups_translator = {
        'translation-type': 'LIST',
        'table-name': SECURITY_GROUP_PORT_BINDINGS,
        'parent-key': 'id',
        'parent-col-name': 'port_id',
        'parent-key-desc': 'UUID of port',
        'val-col': 'security_group_id',
        'val-col-desc': 'UUID of security group',
        'translator': value_trans}

    ports_translator = {
        'translation-type': 'HDICT',
        'table-name': PORTS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'UUID of port',
              'translator': value_trans},
             {'fieldname': 'tenant_id', 'desc': 'tenant ID',
              'translator': value_trans},
             {'fieldname': 'name', 'desc': 'port name',
              'translator': value_trans},
             {'fieldname': 'network_id', 'desc': 'UUID of attached network',
              'translator': value_trans},
             {'fieldname': 'mac_address', 'desc': 'MAC address of the port',
              'translator': value_trans},
             {'fieldname': 'admin_state_up',
              'desc': 'Administrative state of the port',
              'translator': value_trans},
             {'fieldname': 'status', 'desc': 'Port status',
              'translator': value_trans},
             {'fieldname': 'device_id',
              'desc': 'The UUID of the device that uses this port',
              'translator': value_trans},
             {'fieldname': 'device_owner',
              'desc': 'The UUID of the entity that uses this port',
              'translator': value_trans},
             {'fieldname': 'fixed_ips',
              'desc': 'The IP addresses for the port',
              'translator': ports_fixed_ips_translator},
             {'fieldname': 'security_groups',
              'translator': ports_security_groups_translator})}

    subnets_allocation_pools_translator = {
        'translation-type': 'HDICT',
        'table-name': ALLOCATION_POOLS,
        'parent-key': 'id',
        'parent-col-name': 'subnet_id',
        'parent-key-desc': 'UUID of subnet',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'start',
              'desc': 'The start address for the allocation pools',
              'translator': value_trans},
             {'fieldname': 'end',
              'desc': 'The end address for the allocation pools',
              'translator': value_trans})}

    subnets_dns_nameservers_translator = {
        'translation-type': 'LIST',
        'table-name': DNS_NAMESERVERS,
        'parent-key': 'id',
        'parent-col-name': 'subnet_id',
        'parent-key-desc': 'UUID of subnet',
        'val-col': 'dns_nameserver',
        'val-col-desc': 'The DNS server',
        'translator': value_trans}

    subnets_routes_translator = {
        'translation-type': 'HDICT',
        'table-name': HOST_ROUTES,
        'parent-key': 'id',
        'parent-col-name': 'subnet_id',
        'parent-key-desc': 'UUID of subnet',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'destination',
              'desc': 'The destination for static route',
              'translator': value_trans},
             {'fieldname': 'nexthop',
              'desc': 'The next hop for the destination',
              'translator': value_trans})}

    subnets_translator = {
        'translation-type': 'HDICT',
        'table-name': SUBNETS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'UUID of subnet',
              'translator': value_trans},
             {'fieldname': 'tenant_id', 'desc': 'tenant ID',
              'translator': value_trans},
             {'fieldname': 'name', 'desc': 'subnet name',
              'translator': value_trans},
             {'fieldname': 'network_id', 'desc': 'UUID of attached network',
              'translator': value_trans},
             {'fieldname': 'ip_version',
              'desc': 'The IP version, which is 4 or 6',
              'translator': value_trans},
             {'fieldname': 'cidr', 'desc': 'The CIDR',
              'translator': value_trans},
             {'fieldname': 'gateway_ip', 'desc': 'The gateway IP address',
              'translator': value_trans},
             {'fieldname': 'enable_dhcp', 'desc': 'Is DHCP is enabled or not',
              'translator': value_trans},
             {'fieldname': 'ipv6_ra_mode', 'desc': 'The IPv6 RA mode',
              'translator': value_trans},
             {'fieldname': 'ipv6_address_mode',
              'desc': 'The IPv6 address mode', 'translator': value_trans},
             {'fieldname': 'allocation_pools',
              'translator': subnets_allocation_pools_translator},
             {'fieldname': 'dns_nameservers',
              'translator': subnets_dns_nameservers_translator},
             {'fieldname': 'host_routes',
              'translator': subnets_routes_translator})}

    external_fixed_ips_translator = {
        'translation-type': 'HDICT',
        'table-name': EXTERNAL_FIXED_IPS,
        'parent-key': 'router_id',
        'parent-col-name': 'router_id',
        'parent-key-desc': 'UUID of router',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'subnet_id', 'desc': 'UUID of the subnet',
              'translator': value_trans},
             {'fieldname': 'ip_address', 'desc': 'IP Address',
              'translator': value_trans})}

    routers_external_gateway_infos_translator = {
        'translation-type': 'HDICT',
        'table-name': EXTERNAL_GATEWAY_INFOS,
        'parent-key': 'id',
        'parent-col-name': 'router_id',
        'parent-key-desc': 'UUID of router',
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'network_id', 'desc': 'Network ID',
              'translator': value_trans},
             {'fieldname': 'enable_snat',
              'desc': 'current Source NAT status for router',
              'translator': value_trans},
             {'fieldname': 'external_fixed_ips',
              'translator': external_fixed_ips_translator})}

    routers_translator = {
        'translation-type': 'HDICT',
        'table-name': ROUTERS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'uuid of the router',
              'translator': value_trans},
             {'fieldname': 'tenant_id', 'desc': 'tenant ID',
              'translator': value_trans},
             {'fieldname': 'status', 'desc': 'router status',
              'translator': value_trans},
             {'fieldname': 'admin_state_up',
              'desc': 'administrative state of router',
              'translator': value_trans},
             {'fieldname': 'name', 'desc': 'router name',
              'translator': value_trans},
             {'fieldname': 'distributed',
              'desc': "indicates if it's distributed router ",
              'translator': value_trans},
             {'fieldname': 'external_gateway_info',
              'translator': routers_external_gateway_infos_translator})}

    security_group_rules_translator = {
        'translation-type': 'HDICT',
        'table-name': SECURITY_GROUP_RULES,
        'parent-key': 'id',
        'parent-col-name': 'security_group_id',
        'parent-key-desc': 'uuid of security group',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'id', 'desc': 'The UUID of the security group rule',
              'translator': value_trans},
             {'fieldname': 'tenant_id', 'desc': 'tenant ID',
              'translator': value_trans},
             {'fieldname': 'remote_group_id',
              'desc': 'remote group id to associate with security group rule',
              'translator': value_trans},
             {'fieldname': 'direction',
              'desc': 'Direction in which the security group rule is applied',
              'translator': value_trans},
             {'fieldname': 'ethertype', 'desc': 'IPv4 or IPv6',
              'translator': value_trans},
             {'fieldname': 'protocol',
              'desc': 'protocol that is matched by the security group rule.',
              'translator': value_trans},
             {'fieldname': 'port_range_min',
              'desc': 'Min port number in the range',
              'translator': value_trans},
             {'fieldname': 'port_range_max',
              'desc': 'Max port number in the range',
              'translator': value_trans},
             {'fieldname': 'remote_ip_prefix',
              'desc': 'Remote IP prefix to be associated',
              'translator': value_trans})}

    security_group_translator = {
        'translation-type': 'HDICT',
        'table-name': SECURITY_GROUPS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'The UUID for the security group',
              'translator': value_trans},
             {'fieldname': 'tenant_id', 'desc': 'Tenant ID',
              'translator': value_trans},
             {'fieldname': 'name', 'desc': 'The security group name',
              'translator': value_trans},
             {'fieldname': 'description', 'desc': 'security group description',
              'translator': value_trans},
             {'fieldname': 'security_group_rules',
              'translator': security_group_rules_translator})}

    TRANSLATORS = [networks_translator, ports_translator, subnets_translator,
                   routers_translator, security_group_translator,
                   floating_ips_translator]

    def __init__(self, name='', keys='', inbox=None,
                 datapath=None, args=None):
        super(NeutronV2Driver, self).__init__(name, keys, inbox,
                                              datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = args
        self.neutron = neutronclient.v2_0.client.Client(**self.creds)
        self.add_executable_client_methods(self.neutron,
                                           'neutronclient.v2_0.client')
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'neutronv2'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack Networking aka Neutron.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

    def update_from_datasource(self):

        LOG.debug("Neutron grabbing networks")
        networks = self.neutron.list_networks()
        self._translate_networks(networks)

        LOG.debug("Neutron grabbing ports")
        ports = self.neutron.list_ports()
        self._translate_ports(ports)

        subnets = self.neutron.list_subnets()
        self._translate_subnets(subnets)

        routers = self.neutron.list_routers()
        self._translate_routers(routers)

        security_groups = self.neutron.list_security_groups()
        self._translate_security_groups(security_groups)

        floating_ips = self.neutron.list_floatingips()
        self._translate_floating_ips(floating_ips)

    @ds_utils.update_state_on_changed(FLOATING_IPS)
    def _translate_floating_ips(self, obj):
        LOG.debug("floating_ips: %s", dict(obj))

        row_data = NeutronV2Driver.convert_objs(obj['floatingips'],
                                                self.floating_ips_translator)
        return row_data

    @ds_utils.update_state_on_changed(NETWORKS)
    def _translate_networks(self, obj):
        LOG.debug("networks: %s", dict(obj))

        row_data = NeutronV2Driver.convert_objs(obj['networks'],
                                                self.networks_translator)
        return row_data

    @ds_utils.update_state_on_changed(PORTS)
    def _translate_ports(self, obj):
        LOG.debug("ports: %s", obj)
        row_data = NeutronV2Driver.convert_objs(obj['ports'],
                                                self.ports_translator)
        return row_data

    @ds_utils.update_state_on_changed(SUBNETS)
    def _translate_subnets(self, obj):
        LOG.debug("subnets: %s", obj)
        row_data = NeutronV2Driver.convert_objs(obj['subnets'],
                                                self.subnets_translator)
        return row_data

    @ds_utils.update_state_on_changed(ROUTERS)
    def _translate_routers(self, obj):
        LOG.debug("routers: %s", obj)
        row_data = NeutronV2Driver.convert_objs(obj['routers'],
                                                self.routers_translator)
        return row_data

    @ds_utils.update_state_on_changed(SECURITY_GROUPS)
    def _translate_security_groups(self, obj):
        LOG.debug("security_groups: %s", obj)
        row_data = NeutronV2Driver.convert_objs(obj['security_groups'],
                                                self.security_group_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.neutron, action, action_args)
