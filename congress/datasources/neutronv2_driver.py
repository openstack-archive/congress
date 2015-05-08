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

from congress.datasources.datasource_driver import DataSourceDriver
from congress.datasources.datasource_driver import ExecutionDriver
from congress.datasources import datasource_utils
from congress.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return NeutronV2Driver(name, keys, inbox, datapath, args)


class NeutronV2Driver(DataSourceDriver, ExecutionDriver):

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    networks_translator = {
        'translation-type': 'HDICT',
        'table-name': 'networks',
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
        'table-name': 'fixed_ips',
        'parent-key': 'id',
        'parent-col-name': 'port_id',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'ip_address', 'translator': value_trans},
             {'fieldname': 'subnet_id', 'translator': value_trans})}

    ports_security_groups_translator = {
        'translation-type': 'LIST',
        'table-name': 'security_group_port_bindings',
        'parent-key': 'id',
        'parent-col-name': 'port_id',
        'val-col': 'security_group_id',
        'translator': value_trans}

    ports_translator = {
        'translation-type': 'HDICT',
        'table-name': 'ports',
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
        'table-name': 'allocation_pools',
        'parent-key': 'id',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'start', 'translator': value_trans},
             {'fieldname': 'end', 'translator': value_trans})}

    subnets_dns_nameservers_translator = {
        'translation-type': 'LIST',
        'table-name': 'dns_nameservers',
        'parent-key': 'id',
        'parent-col-name': 'subnet_id',
        'val-col': 'dns_nameserver',
        'translator': value_trans}

    subnets_routes_translator = {
        'translation-type': 'HDICT',
        'table-name': 'host_routes',
        'parent-key': 'id',
        'parent-col-name': 'subnet_id',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'destination', 'translator': value_trans},
             {'fieldname': 'nexthop', 'translator': value_trans})}

    subnets_translator = {
        'translation-type': 'HDICT',
        'table-name': 'subnets',
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
        'table-name': 'external_fixed_ips',
        'parent-key': 'router_id',
        'parent-col-name': 'router_id',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'subnet_id', 'translator': value_trans},
             {'fieldname': 'ip_address', 'translator': value_trans})}

    routers_external_gateway_infos_translator = {
        'translation-type': 'HDICT',
        'table-name': 'external_gateway_infos',
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
        'table-name': 'routers',
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
        'table-name': 'security_group_rules',
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
        'table-name': 'security_groups',
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
        self._initialize_tables()
        self.creds = args
        self.neutron = neutronclient.v2_0.client.Client(**self.creds)

        # Store raw state (result of API calls) so that we can
        #   avoid re-translating and re-sending if no changes occurred.
        #   Because translation is not deterministic (we're generating
        #   UUIDs), it's hard to tell if no changes occurred
        #   after performing the translation.
        self.raw_state = {}
        self.initialized = True

    def _initialize_tables(self):
        self.state['networks'] = set()
        self.state['ports'] = set()
        self.state['fixed_ips'] = set()
        self.state['security_group_port_bindings'] = set()
        self.state['subnets'] = set()
        self.state['host_routes'] = set()
        self.state['dns_nameservers'] = set()
        self.state['allocation_pools'] = set()
        self.state['routers'] = set()
        self.state['external_gateway_infos'] = set()
        self.state['security_groups'] = set()
        self.state['security_group_rules'] = set()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'neutronv2'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack Networking aka Neutron.')
        result['config'] = datasource_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

    def update_from_datasource(self):
        LOG.debug("Neutron grabbing networks")
        networks = self.neutron.list_networks()
        if ('networks' not in self.raw_state or
                networks != self.raw_state['networks']):
            self.raw_state['networks'] = networks
            self._translate_networks(networks)

        LOG.debug("Neutron grabbing ports")
        ports = self.neutron.list_ports()
        if 'ports' not in self.raw_state or ports != self.raw_state['ports']:
            self.raw_state['ports'] = ports
            self._translate_ports(ports)

        subnets = self.neutron.list_subnets()
        if ('subnets' not in self.raw_state
                or subnets != self.raw_state['subnets']):
            self.raw_state['subnets'] = subnets
            self._translate_subnets(subnets)
        routers = self.neutron.list_routers()
        if ('routers' not in self.raw_state
                or routers != self.raw_state['routers']):
            self.raw_state['routers'] = routers
            self._translate_routers(routers)

        security_groups = self.neutron.list_security_groups()
        if ('security_groups' not in self.raw_state
                or security_groups != self.raw_state['security_groups']):
            self.raw_state['security_groups'] = security_groups
            self._translate_security_groups(security_groups)

    def _translate_networks(self, obj):
        LOG.debug("networks: %s", dict(obj))

        row_data = NeutronV2Driver.convert_objs(obj['networks'],
                                                self.networks_translator)
        self.state['networks'] = set()
        for table, row in row_data:
            self.state[table].add(row)

    def _translate_ports(self, obj):
        LOG.debug("ports: %s", obj)
        row_data = NeutronV2Driver.convert_objs(obj['ports'],
                                                self.ports_translator)
        self.state['ports'] = set()
        self.state['fixed_ips'] = set()
        self.state['security_group_port_bindings'] = set()
        for table, row in row_data:
            self.state[table].add(row)

    def _translate_subnets(self, obj):
        LOG.debug("subnets: %s", obj)
        row_data = NeutronV2Driver.convert_objs(obj['subnets'],
                                                self.subnets_translator)
        self.state['subnets'] = set()
        self.state['host_routes'] = set()
        self.state['dns_nameservers'] = set()
        self.state['allocation_pools'] = set()
        for table, row in row_data:
            self.state[table].add(row)

    def _translate_routers(self, obj):
        LOG.debug("routers: %s", obj)
        row_data = NeutronV2Driver.convert_objs(obj['routers'],
                                                self.routers_translator)
        self.state['routers'] = set()
        self.state['external_gateway_infos'] = set()
        for table, row in row_data:
            self.state[table].add(row)

    def _translate_security_groups(self, obj):
        LOG.debug("security_groups: %s", obj)
        row_data = NeutronV2Driver.convert_objs(obj['security_groups'],
                                                self.security_group_translator)
        self.state['security_groups'] = set()
        self.state['security_group_rules'] = set()
        for table, row in row_data:
            self.state[table].add(row)

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        # action_agrs can be utilized for distinguishing the two.
        # This is an API call via client:
        LOG.info("%s:: executing %s on %s", self.name, action, action_args)
        self._execute_api(self.neutron, action, action_args)
