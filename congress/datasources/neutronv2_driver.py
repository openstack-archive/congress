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

import neutronclient.v2_0.client
from oslo_log import log as logging

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return NeutronV2Driver(name, keys, inbox, datapath, args)


class NeutronV2Driver(datasource_driver.DataSourceDriver,
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

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    networks_translator = {
        'translation-type': 'HDICT',
        'table-name': NETWORKS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'admin_state_up', 'translator': value_trans},
             {'fieldname': 'shared', 'translator': value_trans})}

    ports_fixed_ips_translator = {
        'translation-type': 'HDICT',
        'table-name': FIXED_IPS,
        'parent-key': 'id',
        'parent-col-name': 'port_id',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'ip_address', 'translator': value_trans},
             {'fieldname': 'subnet_id', 'translator': value_trans})}

    ports_security_groups_translator = {
        'translation-type': 'LIST',
        'table-name': SECURITY_GROUP_PORT_BINDINGS,
        'parent-key': 'id',
        'parent-col-name': 'port_id',
        'val-col': 'security_group_id',
        'translator': value_trans}

    ports_translator = {
        'translation-type': 'HDICT',
        'table-name': PORTS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'network_id', 'translator': value_trans},
             {'fieldname': 'mac_address', 'translator': value_trans},
             {'fieldname': 'admin_state_up', 'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'device_id', 'translator': value_trans},
             {'fieldname': 'device_owner', 'translator': value_trans},
             {'fieldname': 'fixed_ips',
              'translator': ports_fixed_ips_translator},
             {'fieldname': 'security_groups',
              'translator': ports_security_groups_translator})}

    subnets_allocation_pools_translator = {
        'translation-type': 'HDICT',
        'table-name': ALLOCATION_POOLS,
        'parent-key': 'id',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'start', 'translator': value_trans},
             {'fieldname': 'end', 'translator': value_trans})}

    subnets_dns_nameservers_translator = {
        'translation-type': 'LIST',
        'table-name': DNS_NAMESERVERS,
        'parent-key': 'id',
        'parent-col-name': 'subnet_id',
        'val-col': 'dns_nameserver',
        'translator': value_trans}

    subnets_routes_translator = {
        'translation-type': 'HDICT',
        'table-name': HOST_ROUTES,
        'parent-key': 'id',
        'parent-col-name': 'subnet_id',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'destination', 'translator': value_trans},
             {'fieldname': 'nexthop', 'translator': value_trans})}

    subnets_translator = {
        'translation-type': 'HDICT',
        'table-name': SUBNETS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'network_id', 'translator': value_trans},
             {'fieldname': 'ip_version', 'translator': value_trans},
             {'fieldname': 'cidr', 'translator': value_trans},
             {'fieldname': 'gateway_ip', 'translator': value_trans},
             {'fieldname': 'enable_dhcp', 'translator': value_trans},
             {'fieldname': 'ipv6_ra_mode', 'translator': value_trans},
             {'fieldname': 'ipv6_address_mode', 'translator': value_trans},
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
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'subnet_id', 'translator': value_trans},
             {'fieldname': 'ip_address', 'translator': value_trans})}

    routers_external_gateway_infos_translator = {
        'translation-type': 'HDICT',
        'table-name': EXTERNAL_GATEWAY_INFOS,
        'parent-key': 'id',
        'parent-col-name': 'router_id',
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'network_id', 'translator': value_trans},
             {'fieldname': 'enable_snat', 'translator': value_trans},
             {'fieldname': 'external_fixed_ips',
              'translator': external_fixed_ips_translator})}

    routers_translator = {
        'translation-type': 'HDICT',
        'table-name': ROUTERS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'admin_state_up', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'distributed', 'translator': value_trans},
             {'fieldname': 'external_gateway_info',
              'translator': routers_external_gateway_infos_translator})}

    security_group_rules_translator = {
        'translation-type': 'HDICT',
        'table-name': SECURITY_GROUP_RULES,
        'parent-key': 'id',
        'parent-col-name': 'security_group_id',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'remote_group_id', 'translator': value_trans},
             {'fieldname': 'direction', 'translator': value_trans},
             {'fieldname': 'ethertype', 'translator': value_trans},
             {'fieldname': 'protocol', 'translator': value_trans},
             {'fieldname': 'port_range_min', 'translator': value_trans},
             {'fieldname': 'port_range_max', 'translator': value_trans},
             {'fieldname': 'remote_ip_prefix', 'translator': value_trans})}

    security_group_translator = {
        'translation-type': 'HDICT',
        'table-name': SECURITY_GROUPS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'security_group_rules',
              'translator': security_group_rules_translator})}

    TRANSLATORS = [networks_translator, ports_translator, subnets_translator,
                   routers_translator, security_group_translator]

    def __init__(self, name='', keys='', inbox=None,
                 datapath=None, args=None):
        super(NeutronV2Driver, self).__init__(name, keys, inbox,
                                              datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = args
        self.neutron = neutronclient.v2_0.client.Client(**self.creds)
        self.inspect_builtin_methods(self.neutron, 'neutronclient.v2_0.client')
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
