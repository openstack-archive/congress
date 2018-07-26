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

from congress import data_types
from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils

LOG = logging.getLogger(__name__)


IngressEgress = data_types.create_congress_enum_type(
    'IngressEgress', ('ingress', 'egress'), data_types.Str)
data_types.TypesRegistry.register(IngressEgress)

FloatingIPStatus = data_types.create_congress_enum_type(
    'FloatingIPStatus', ('ACTIVE', 'DOWN', 'ERROR'), data_types.Str,
    catch_all_default_value='OTHER')
data_types.TypesRegistry.register(FloatingIPStatus)

NeutronStatus = data_types.create_congress_enum_type(
    'NeutronStatus', ('ACTIVE', 'DOWN', 'BUILD', 'ERROR'), data_types.Str,
    catch_all_default_value='OTHER')
data_types.TypesRegistry.register(NeutronStatus)

IPVersion = data_types.create_congress_enum_type(
    'IPv4IPv6', (4, 6), data_types.Int)
data_types.TypesRegistry.register(IPVersion)


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

    value_trans_str = ds_utils.typed_value_trans(data_types.Str)
    value_trans_bool = ds_utils.typed_value_trans(data_types.Bool)
    value_trans_int = ds_utils.typed_value_trans(data_types.Int)

    floating_ips_translator = {
        'translation-type': 'HDICT',
        'table-name': FLOATING_IPS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'The UUID of the floating IP address',
              'translator': value_trans_str},
             {'fieldname': 'router_id', 'desc': 'UUID of router',
              'translator': value_trans_str},
             {'fieldname': 'tenant_id', 'desc': 'Tenant ID',
              'translator': value_trans_str},
             {'fieldname': 'floating_network_id',
              'desc': 'The UUID of the network associated with floating IP',
              'translator': value_trans_str},
             {'fieldname': 'fixed_ip_address',
              'desc': 'Fixed IP address associated with floating IP address',
              'translator': ds_utils.typed_value_trans(data_types.IPAddress)},
             {'fieldname': 'floating_ip_address',
              'desc': 'The floating IP address',
              'translator': ds_utils.typed_value_trans(data_types.IPAddress)},
             {'fieldname': 'port_id', 'desc': 'UUID of port',
              'translator': value_trans_str},
             {'fieldname': 'status', 'desc': 'The floating IP status',
              'translator': ds_utils.typed_value_trans(FloatingIPStatus)})}

    networks_translator = {
        'translation-type': 'HDICT',
        'table-name': NETWORKS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'Network ID',
              'translator': value_trans_str},
             {'fieldname': 'tenant_id', 'desc': 'Tenant ID',
              'translator': value_trans_str},
             {'fieldname': 'name', 'desc': 'Network name',
              'translator': value_trans_str},
             {'fieldname': 'status', 'desc': 'Network status',
              'translator': ds_utils.typed_value_trans(NeutronStatus)},
             {'fieldname': 'admin_state_up',
              'desc': 'Administrative state of the network (true/false)',
              'translator': value_trans_bool},
             {'fieldname': 'shared',
              'desc': 'Indicates if network is shared across all tenants',
              'translator': value_trans_bool})}

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
              'translator': ds_utils.typed_value_trans(data_types.IPAddress)},
             {'fieldname': 'subnet_id',
              'desc': 'The UUID of the subnet to which the port is attached',
              'translator': value_trans_str})}

    ports_security_groups_translator = {
        'translation-type': 'LIST',
        'table-name': SECURITY_GROUP_PORT_BINDINGS,
        'parent-key': 'id',
        'parent-col-name': 'port_id',
        'parent-key-desc': 'UUID of port',
        'val-col': 'security_group_id',
        'val-col-desc': 'UUID of security group',
        'translator': value_trans_str}

    ports_translator = {
        'translation-type': 'HDICT',
        'table-name': PORTS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'UUID of port',
              'translator': value_trans_str},
             {'fieldname': 'tenant_id', 'desc': 'tenant ID',
              'translator': value_trans_str},
             {'fieldname': 'name', 'desc': 'port name',
              'translator': value_trans_str},
             {'fieldname': 'network_id', 'desc': 'UUID of attached network',
              'translator': value_trans_str},
             {'fieldname': 'mac_address', 'desc': 'MAC address of the port',
              'translator': value_trans_str},
             {'fieldname': 'admin_state_up',
              'desc': 'Administrative state of the port',
              'translator': value_trans_bool},
             {'fieldname': 'status', 'desc': 'Port status',
              'translator': ds_utils.typed_value_trans(NeutronStatus)},
             {'fieldname': 'device_id',
              'desc': 'The ID of the device that uses this port',
              'translator': value_trans_str},
             {'fieldname': 'device_owner',
              'desc': 'The entity type that uses this port.'
                      'E.g., compute:nova, network:router_interface',
              'translator': value_trans_str},
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
              'translator': value_trans_str},
             {'fieldname': 'end',
              'desc': 'The end address for the allocation pools',
              'translator': value_trans_str})}

    subnets_dns_nameservers_translator = {
        'translation-type': 'LIST',
        'table-name': DNS_NAMESERVERS,
        'parent-key': 'id',
        'parent-col-name': 'subnet_id',
        'parent-key-desc': 'UUID of subnet',
        'val-col': 'dns_nameserver',
        'val-col-desc': 'The DNS server',
        'translator': value_trans_str}

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
              'translator': value_trans_str},
             {'fieldname': 'nexthop',
              'desc': 'The next hop for the destination',
              'translator': value_trans_str})}

    subnets_translator = {
        'translation-type': 'HDICT',
        'table-name': SUBNETS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'UUID of subnet',
              'translator': value_trans_str},
             {'fieldname': 'tenant_id', 'desc': 'tenant ID',
              'translator': value_trans_str},
             {'fieldname': 'name', 'desc': 'subnet name',
              'translator': value_trans_str},
             {'fieldname': 'network_id', 'desc': 'UUID of attached network',
              'translator': value_trans_str},
             {'fieldname': 'ip_version',
              'desc': 'The IP version, which is 4 or 6',
              'translator': ds_utils.typed_value_trans(IPVersion)},
             {'fieldname': 'cidr', 'desc': 'The CIDR',
              'translator': ds_utils.typed_value_trans(data_types.IPNetwork)},
             {'fieldname': 'gateway_ip', 'desc': 'The gateway IP address',
              'translator': ds_utils.typed_value_trans(data_types.IPAddress)},
             {'fieldname': 'enable_dhcp', 'desc': 'Is DHCP is enabled or not',
              'translator': value_trans_bool},
             {'fieldname': 'ipv6_ra_mode', 'desc': 'The IPv6 RA mode',
              'translator': value_trans_str},
             {'fieldname': 'ipv6_address_mode',
              'desc': 'The IPv6 address mode', 'translator': value_trans_str},
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
              'translator': value_trans_str},
             {'fieldname': 'ip_address', 'desc': 'IP Address',
              'translator': ds_utils.typed_value_trans(data_types.IPAddress)})}

    routers_external_gateway_infos_translator = {
        'translation-type': 'HDICT',
        'table-name': EXTERNAL_GATEWAY_INFOS,
        'parent-key': 'id',
        'parent-col-name': 'router_id',
        'parent-key-desc': 'UUID of router',
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'network_id', 'desc': 'Network ID',
              'translator': value_trans_str},
             {'fieldname': 'enable_snat',
              'desc': 'current Source NAT status for router',
              'translator': value_trans_bool},
             {'fieldname': 'external_fixed_ips',
              'translator': external_fixed_ips_translator})}

    routers_translator = {
        'translation-type': 'HDICT',
        'table-name': ROUTERS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'uuid of the router',
              'translator': value_trans_str},
             {'fieldname': 'tenant_id', 'desc': 'tenant ID',
              'translator': value_trans_str},
             {'fieldname': 'status', 'desc': 'router status',
              'translator': ds_utils.typed_value_trans(NeutronStatus)},
             {'fieldname': 'admin_state_up',
              'desc': 'administrative state of router',
              'translator': value_trans_bool},
             {'fieldname': 'name', 'desc': 'router name',
              'translator': value_trans_str},
             {'fieldname': 'distributed',
              'desc': "indicates if it's distributed router ",
              'translator': value_trans_bool},
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
              'translator': value_trans_str},
             {'fieldname': 'tenant_id', 'desc': 'tenant ID',
              'translator': value_trans_str},
             {'fieldname': 'remote_group_id',
              'desc': 'remote group id to associate with security group rule',
              'translator': value_trans_str},
             {'fieldname': 'direction',
              'desc': 'Direction in which the security group rule is applied',
              'translator': ds_utils.typed_value_trans(IngressEgress)},
             {'fieldname': 'ethertype', 'desc': 'IPv4 or IPv6',
              'translator': value_trans_str},
             {'fieldname': 'protocol',
              'desc': 'protocol that is matched by the security group rule.',
              'translator': value_trans_str},
             {'fieldname': 'port_range_min',
              'desc': 'Min port number in the range',
              'translator': value_trans_int},
             {'fieldname': 'port_range_max',
              'desc': 'Max port number in the range',
              'translator': value_trans_int},
             {'fieldname': 'remote_ip_prefix',
              'desc': 'Remote IP prefix to be associated',
              'translator': value_trans_str})}

    security_group_translator = {
        'translation-type': 'HDICT',
        'table-name': SECURITY_GROUPS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'The UUID for the security group',
              'translator': value_trans_str},
             {'fieldname': 'tenant_id', 'desc': 'Tenant ID',
              'translator': value_trans_str},
             {'fieldname': 'name', 'desc': 'The security group name',
              'translator': value_trans_str},
             {'fieldname': 'description', 'desc': 'security group description',
              'translator': value_trans_str},
             {'fieldname': 'security_group_rules',
              'translator': security_group_rules_translator})}

    TRANSLATORS = [networks_translator, ports_translator, subnets_translator,
                   routers_translator, security_group_translator,
                   floating_ips_translator]

    def __init__(self, name='', args=None):
        super(NeutronV2Driver, self).__init__(name, args=args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = args
        session = ds_utils.get_keystone_session(self.creds)
        self.neutron = neutronclient.v2_0.client.Client(session=session)

        # specify the arg name for all method structured args
        self.method_structured_args = {
            'add_bgp_speaker_to_dragent': {'named': frozenset(['body'])},
            'add_gateway_router': {'named': frozenset(['body'])},
            'add_interface_router': {'named': frozenset(['body'])},
            'add_network_to_bgp_speaker': {'named': frozenset(['body'])},
            'add_network_to_dhcp_agent': {'named': frozenset(['body'])},
            'add_peer_to_bgp_speaker': {'named': frozenset(['body'])},
            'add_router_to_l3_agent': {'named': frozenset(['body'])},
            'associate_flavor': {'named': frozenset(['body'])},
            'associate_health_monitor': {'named': frozenset(['body'])},
            'connect_network_gateway': {'named': frozenset(['body'])},
            'create_address_scope': {'named': frozenset(['body'])},
            'create_bandwidth_limit_rule': {'named': frozenset(['body'])},
            'create_bgp_peer': {'named': frozenset(['body'])},
            'create_bgp_speaker': {'named': frozenset(['body'])},
            'create_bgpvpn': {'named': frozenset(['body'])},
            'create_bgpvpn_network_assoc': {'named': frozenset(['body'])},
            'create_bgpvpn_port_assoc': {'named': frozenset(['body'])},
            'create_bgpvpn_router_assoc': {'named': frozenset(['body'])},
            'create_dscp_marking_rule': {'named': frozenset(['body'])},
            'create_endpoint_group': {'named': frozenset(['body'])},
            'create_ext': {'named': frozenset(['body'])},
            'create_firewall': {'named': frozenset(['body'])},
            'create_firewall_policy': {'named': frozenset(['body'])},
            'create_firewall_rule': {'named': frozenset(['body'])},
            'create_flavor': {'named': frozenset(['body'])},
            'create_floatingip': {'named': frozenset(['body'])},
            'create_fwaas_firewall_group': {'named': frozenset(['body'])},
            'create_fwaas_firewall_policy': {'named': frozenset(['body'])},
            'create_fwaas_firewall_rule': {'named': frozenset(['body'])},
            'create_gateway_device': {'named': frozenset(['body'])},
            'create_health_monitor': {'named': frozenset(['body'])},
            'create_ikepolicy': {'named': frozenset(['body'])},
            'create_ipsec_site_connection': {'named': frozenset(['body'])},
            'create_ipsecpolicy': {'named': frozenset(['body'])},
            'create_lbaas_healthmonitor': {'named': frozenset(['body'])},
            'create_lbaas_l7policy': {'named': frozenset(['body'])},
            'create_lbaas_l7rule': {'named': frozenset(['body'])},
            'create_lbaas_member': {'named': frozenset(['body'])},
            'create_lbaas_pool': {'named': frozenset(['body'])},
            'create_listener': {'named': frozenset(['body'])},
            'create_loadbalancer': {'named': frozenset(['body'])},
            'create_member': {'named': frozenset(['body'])},
            'create_metering_label': {'named': frozenset(['body'])},
            'create_metering_label_rule': {'named': frozenset(['body'])},
            'create_minimum_bandwidth_rule': {'named': frozenset(['body'])},
            'create_network': {'named': frozenset(['body'])},
            'create_network_gateway': {'named': frozenset(['body'])},
            'create_network_log': {'named': frozenset(['body'])},
            'create_pool': {'named': frozenset(['body'])},
            'create_port': {'named': frozenset(['body'])},
            'create_qos_policy': {'named': frozenset(['body'])},
            'create_qos_queue': {'named': frozenset(['body'])},
            'create_rbac_policy': {'named': frozenset(['body'])},
            'create_router': {'named': frozenset(['body'])},
            'create_security_group': {'named': frozenset(['body'])},
            'create_security_group_rule': {'named': frozenset(['body'])},
            'create_service_profile': {'named': frozenset(['body'])},
            'create_sfc_flow_classifier': {'named': frozenset(['body'])},
            'create_sfc_port_chain': {'named': frozenset(['body'])},
            'create_sfc_port_pair': {'named': frozenset(['body'])},
            'create_sfc_port_pair_group': {'named': frozenset(['body'])},
            'create_sfc_service_graph': {'named': frozenset(['body'])},
            'create_subnet': {'named': frozenset(['body'])},
            'create_subnetpool': {'named': frozenset(['body'])},
            'create_trunk': {'named': frozenset(['body'])},
            'create_vip': {'named': frozenset(['body'])},
            'create_vpnservice': {'named': frozenset(['body'])},
            'disconnect_network_gateway': {'named': frozenset(['body'])},
            'firewall_policy_insert_rule': {'named': frozenset(['body'])},
            'firewall_policy_remove_rule': {'named': frozenset(['body'])},
            'insert_rule_fwaas_firewall_policy': {
                'named': frozenset(['body'])},
            'remove_interface_router': {'named': frozenset(['body'])},
            'remove_network_from_bgp_speaker': {'named': frozenset(['body'])},
            'remove_peer_from_bgp_speaker': {'named': frozenset(['body'])},
            'remove_rule_fwaas_firewall_policy': {
                'named': frozenset(['body'])},
            'replace_tag': {'named': frozenset(['body'])},
            'retry_request': {'named': frozenset(['body'])},
            'show_minimum_bandwidth_rule': {'named': frozenset(['body'])},
            'trunk_add_subports': {'named': frozenset(['body'])},
            'trunk_remove_subports': {'named': frozenset(['body'])},
        }

        self.add_executable_method('update_resource_attrs',
                                   [{'name': 'resource_type',
                                     'description': 'resource type (e.g. ' +
                                                    'port, network, subnet)'},
                                    {'name': 'id',
                                     'description': 'ID of the resource'},
                                    {'name': 'attr1',
                                     'description': 'attribute name to ' +
                                     'update (e.g. admin_state_up)'},
                                    {'name': 'attr1-value',
                                     'description': 'updated attr1 value'},
                                    {'name': 'attrN',
                                     'description': 'attribute name to ' +
                                     'update'},
                                    {'name': 'attrN-value',
                                     'description': 'updated attrN value'}],
                                   "A wrapper for update_<resource_type>()")
        self.add_executable_method('attach_port_security_group',
                                   [{'name': 'port_id',
                                     'description': 'ID of target port'},
                                    {'name': 'security_group_id',
                                     'description': 'ID security group to be '
                                                    'attached'}],
                                   "Attach a security group to port (WARNING: "
                                   "may overwrite concurrent changes to "
                                   "port's security groups list.")
        self.add_executable_method('detach_port_security_group',
                                   [{'name': 'port_id',
                                     'description': 'ID of target port'},
                                    {'name': 'security_group_id',
                                     'description': 'ID security group to be '
                                                    'detached'}],
                                   "Detach a security group to port (WARNING: "
                                   "may overwrite concurrent changes to "
                                   "port's security groups list.")

        # add action methods from client, but exclude 'update_*' because those
        # are covered by the update_resource_attr method.
        exclude_methods = ['update_address_scope', 'update_agent',
                           'update_bandwidth_limit_rule', 'update_bgp_peer',
                           'update_bgp_speaker', 'update_bgpvpn',
                           'update_bgpvpn_network_assoc',
                           'update_bgpvpn_port_assoc',
                           'update_bgpvpn_router_assoc',
                           'update_dscp_marking_rule', 'update_endpoint_group',
                           'update_ext', 'update_firewall',
                           'update_firewall_policy', 'update_firewall_rule',
                           'update_flavor', 'update_floatingip',
                           'update_fwaas_firewall_group',
                           'update_fwaas_firewall_policy',
                           'update_fwaas_firewall_rule',
                           'update_gateway_device', 'update_health_monitor',
                           'update_ikepolicy', 'update_ipsec_site_connection',
                           'update_ipsecpolicy', 'update_lbaas_healthmonitor',
                           'update_lbaas_l7policy', 'update_lbaas_l7rule',
                           'update_lbaas_member', 'update_lbaas_pool',
                           'update_listener', 'update_loadbalancer',
                           'update_member', 'update_minimum_bandwidth_rule',
                           'update_network', 'update_network_gateway',
                           'update_network_log', 'update_pool', 'update_port',
                           'update_qos_policy', 'update_quota',
                           'update_rbac_policy', 'update_router',
                           'update_security_group', 'update_service_profile',
                           'update_sfc_flow_classifier',
                           'update_sfc_port_chain', 'update_sfc_port_pair',
                           'update_sfc_port_pair_group',
                           'update_sfc_service_graph', 'update_subnet',
                           'update_subnetpool', 'update_trunk', 'update_vip',
                           'update_vpnservice']
        self.add_executable_client_methods(self.neutron,
                                           'neutronclient.v2_0.client',
                                           exclude_methods)
        self.initialize_update_methods()
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'neutronv2'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack Networking aka Neutron.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['config']['lazy_tables'] = constants.OPTIONAL
        result['secret'] = ['password']
        return result

    def initialize_update_methods(self):
        networks_method = lambda: self._translate_networks(
            self.neutron.list_networks())
        self.add_update_method(networks_method, self.networks_translator)

        subnets_method = lambda: self._translate_subnets(
            self.neutron.list_subnets())
        self.add_update_method(subnets_method, self.subnets_translator)

        ports_method = lambda: self._translate_ports(self.neutron.list_ports())
        self.add_update_method(ports_method, self.ports_translator)

        routers_method = lambda: self._translate_routers(
            self.neutron.list_routers())
        self.add_update_method(routers_method, self.routers_translator)

        security_method = lambda: self._translate_security_groups(
            self.neutron.list_security_groups())
        self.add_update_method(security_method,
                               self.security_group_translator)

        floatingips_method = lambda: self._translate_floating_ips(
            self.neutron.list_floatingips())
        self.add_update_method(floatingips_method,
                               self.floating_ips_translator)

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

    def update_resource_attrs(self, args):
        positional_args = args.get('positional', [])
        if not positional_args or len(positional_args) < 4:
            LOG.error('Args for update_resource_attrs() must contain resource '
                      'type, resource ID and pairs of key-value attributes to '
                      'update')
            return

        resource_type = positional_args.pop(0)
        resource_id = positional_args.pop(0)
        action = 'update_%s' % resource_type
        update_attrs = self._convert_args(positional_args)
        body = {resource_type: update_attrs}

        action_args = {'named': {resource_type: resource_id,
                                 'body': body}}
        self._execute_api(self.neutron, action, action_args)

    def attach_port_security_group(self, args):
        self._attach_detach_port_security_group(args, attach=True)

    def detach_port_security_group(self, args):
        self._attach_detach_port_security_group(args, attach=False)

    def _attach_detach_port_security_group(self, args, attach):
        positional_args = args.get('positional', [])
        if not positional_args or len(positional_args) < 2:
            LOG.error('Args for attach_port_security_group() must contain '
                      'port id and security group id')
            return

        port_id = positional_args[0]
        security_group_id = positional_args[1]

        # get existing port security groups
        port_state = self.neutron.show_port(port_id).get('port')
        if not port_state:
            return
        port_security_groups = port_state.get('security_groups', [])

        # add/remove security group
        if security_group_id in port_security_groups:
            if attach:  # no change needed
                return
            port_security_groups.remove(security_group_id)
        else:
            if not attach:  # no change needed
                return
            port_security_groups.append(security_group_id)

        # call client to make change
        # WARNING: intervening changes to security groups binding may be lost
        body = {
            "port": {
                "security_groups": port_security_groups,
            }
        }
        self.neutron.update_port(port_id, body)
