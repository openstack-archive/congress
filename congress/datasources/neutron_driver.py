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
from congress.datasources import datasource_utils

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return NeutronDriver(name, keys, inbox, datapath, args)


class NeutronDriver(datasource_driver.PollingDataSourceDriver,
                    datasource_driver.ExecutionDriver):

    NETWORKS = "networks"
    NETWORKS_SUBNETS = "networks.subnets"
    PORTS = "ports"
    PORTS_ADDR_PAIRS = "ports.address_pairs"
    PORTS_SECURITY_GROUPS = "ports.security_groups"
    PORTS_BINDING_CAPABILITIES = "ports.binding_capabilities"
    PORTS_FIXED_IPS = "ports.fixed_ips"
    PORTS_FIXED_IPS_GROUPS = "ports.fixed_ips_groups"
    PORTS_EXTRA_DHCP_OPTS = "ports.extra_dhcp_opts"
    ROUTERS = "routers"
    ROUTERS_EXTERNAL_GATEWAYS = "routers.external_gateways"
    SECURITY_GROUPS = "security_groups"

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    networks_translator = {
        'translation-type': 'HDICT',
        'table-name': NETWORKS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'subnets', 'col': 'subnet_group_id',
              'translator': {'translation-type': 'LIST',
                             'table-name': 'networks.subnets',
                             'id-col': 'subnet_group_id',
                             'val-col': 'subnet',
                             'translator': value_trans}},
             {'fieldname': 'provider:physical_network',
              'translator': value_trans},
             {'fieldname': 'admin_state_up', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'provider:network_type', 'translator': value_trans},
             {'fieldname': 'router:external', 'translator': value_trans},
             {'fieldname': 'shared', 'translator': value_trans},
             {'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'provider:segmentation_id',
              'translator': value_trans})}

    ports_translator = {
        'translation-type': 'HDICT',
        'table-name': PORTS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'allowed_address_pairs',
              'col': 'allowed_address_pairs_id',
              'translator': {'translation-type': 'LIST',
                             'table-name': PORTS_ADDR_PAIRS,
                             'id-col': 'allowed_address_pairs_id',
                             'val-col': 'address',
                             'translator': value_trans}},
             {'fieldname': 'security_groups',
              'col': 'security_groups_id',
              'translator': {'translation-type': 'LIST',
                             'table-name': PORTS_SECURITY_GROUPS,
                             'id-col': 'security_groups_id',
                             'val-col': 'security_group_id',
                             'translator': value_trans}},
             {'fieldname': 'extra_dhcp_opts',
              'col': 'extra_dhcp_opt_group_id',
              'translator': {'translation-type': 'LIST',
                             'table-name': PORTS_EXTRA_DHCP_OPTS,
                             'id-col': 'extra_dhcp_opt_group_id',
                             'val-col': 'dhcp_opt',
                             'translator': value_trans}},
             {'fieldname': 'binding:capabilities',
              'col': 'binding:capabilities_id',
              'translator': {'translation-type': 'VDICT',
                             'table-name': PORTS_BINDING_CAPABILITIES,
                             'id-col': 'binding:capabilities_id',
                             'key-col': 'key', 'val-col': 'value',
                             'translator': value_trans}},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'admin_state_up', 'translator': value_trans},
             {'fieldname': 'network_id', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'binding:vif_type', 'translator': value_trans},
             {'fieldname': 'device_owner', 'translator': value_trans},
             {'fieldname': 'mac_address', 'translator': value_trans},

             {'fieldname': 'fixed_ips',
              'col': 'fixed_ips',
              'translator': {'translation-type': 'LIST',
                             'table-name': PORTS_FIXED_IPS_GROUPS,
                             'id-col': 'fixed_ips_group_id',
                             'val-col': 'fixed_ip_id',
                             'translator': {'translation-type': 'VDICT',
                                            'table-name': PORTS_FIXED_IPS,
                                            'id-col': 'fixed_ip_id',
                                            'key-col': 'key',
                                            'val-col': 'value',
                                            'translator': value_trans}}},
             {'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'device_id', 'translator': value_trans},
             {'fieldname': 'binding:host_id', 'translator': value_trans})}

    routers_translator = {
        'translation-type': 'HDICT',
        'table-name': ROUTERS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'external_gateway_info',
              'translator': {'translation-type': 'VDICT',
                             'table-name': ROUTERS_EXTERNAL_GATEWAYS,
                             'id-col': 'external_gateway_info',
                             'key-col': 'key', 'val-col': 'value',
                             'translator': value_trans}},
             {'fieldname': 'networks', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'admin_state_up', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'id', 'translator': value_trans})}

    security_groups_translator = {
        'translation-type': 'HDICT',
        'table-name': SECURITY_GROUPS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'id', 'translator': value_trans})}

    TRANSLATORS = [networks_translator, ports_translator, routers_translator,
                   security_groups_translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(NeutronDriver, self).__init__(name, keys, inbox, datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = self.get_neutron_credentials(args)
        self.neutron = neutronclient.v2_0.client.Client(**self.creds)

        # Store raw state (result of API calls) so that we can
        #   avoid re-translating and re-sending if no changes occurred.
        #   Because translation is not deterministic (we're generating
        #   UUIDs), it's hard to tell if no changes occurred
        #   after performing the translation.
        self.raw_state = {}
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'neutron'
        result['description'] = ('Do not use this driver is deprecated')
        result['config'] = datasource_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

    def get_neutron_credentials(self, creds):
        d = {}
        d['username'] = creds['username']
        d['tenant_name'] = creds['tenant_name']
        d['password'] = creds['password']
        d['auth_url'] = creds['auth_url']
        return d

    def update_from_datasource(self):
        """Called when it is time to pull new data from this datasource.

        Sets self.state[tablename] = <set of tuples of strings/numbers>
        for every tablename exported by this datasource.
        """
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

        LOG.debug("Neutron grabbing routers")
        routers = self.neutron.list_routers()
        if ('routers' not in self.raw_state or
                routers != self.raw_state['routers']):
            self.raw_state['routers'] = routers
            self._translate_routers(routers)

        LOG.debug("Neutron grabbing security groups")
        security = self.neutron.list_security_groups()
        if ('security_groups' not in self.raw_state or
                security != self.raw_state['security_groups']):
            self.raw_state['security_groups'] = security
            self._translate_security_groups(security)

    def _translate_networks(self, obj):
        """Translate the networks represented by OBJ into tables.

        Assigns self.state[tablename] for all those TABLENAMEs
        generated from OBJ: NETWORKS, NETWORKS_SUBNETS
        """
        LOG.debug("NETWORKS: %s", dict(obj))

        row_data = NeutronDriver.convert_objs(obj['networks'],
                                              self.networks_translator)
        network_tables = (self.NETWORKS, self.NETWORKS_SUBNETS)
        for table in network_tables:
            self.state[table] = set()
        for table, row in row_data:
            assert table in network_tables
            self.state[table].add(row)
        LOG.debug("NETWORKS: %s", self.state[self.NETWORKS])
        LOG.debug("NETWORKS_SUBNETS: %s", self.state[self.NETWORKS_SUBNETS])

    def _translate_ports(self, obj):
        """Translate the ports represented by OBJ into tables.

        Assigns self.state[tablename] for all those TABLENAMEs
        generated from OBJ: PORTS, PORTS_ADDR_PAIRS,
        PORTS_SECURITY_GROUPS, PORTS_BINDING_CAPABILITIES,
        PORTS_FIXED_IPS, PORTS_FIXED_IPS_GROUPS,
        PORTS_EXTRA_DHCP_OPTS.
        """
        LOG.debug("PORTS: %s", obj)

        row_data = NeutronDriver.convert_objs(obj['ports'],
                                              self.ports_translator)
        port_tables = (self.PORTS, self.PORTS_ADDR_PAIRS,
                       self.PORTS_SECURITY_GROUPS,
                       self.PORTS_BINDING_CAPABILITIES, self.PORTS_FIXED_IPS,
                       self.PORTS_FIXED_IPS_GROUPS,
                       self.PORTS_EXTRA_DHCP_OPTS)
        for table in port_tables:
            self.state[table] = set()
        for table, row in row_data:
            assert table in port_tables
            self.state[table].add(row)
        for table in port_tables:
            LOG.debug('%s: %s', table, self.state[table])

    def _translate_routers(self, obj):
        """Translates the routers represented by OBJ into a single table.

        Assigns self.state[SECURITY_GROUPS] to that table.
        """
        LOG.debug("ROUTERS: %s", dict(obj))

        row_data = NeutronDriver.convert_objs(obj['routers'],
                                              self.routers_translator)
        router_tables = (self.ROUTERS, self.ROUTERS_EXTERNAL_GATEWAYS)
        for table in router_tables:
            self.state[table] = set()
        for table, row in row_data:
            assert table in router_tables
            self.state[table].add(row)
        for table in router_tables:
            LOG.debug('%s: %s', table, self.state[table])

    def _translate_security_groups(self, obj):
        LOG.debug("SECURITY_GROUPS: %s", dict(obj))

        row_data = NeutronDriver.convert_objs(obj['security_groups'],
                                              self.security_groups_translator)
        security_group_tables = (self.SECURITY_GROUPS,)
        for table in security_group_tables:
            self.state[table] = set()
        for table, row in row_data:
            assert table in security_group_tables
            self.state[table].add(row)
        for table in security_group_tables:
            LOG.debug('%s: %s', table, self.state[table])

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.neutron, action, action_args)

# Sample Mapping
# Network :
# ========
#
# json
# ------
# {u'status': u'ACTIVE', u'subnets':
#  [u'4cef03d0-1d02-40bb-8c99-2f442aac6ab0'],
# u'name':u'test-network', u'provider:physical_network': None,
# u'admin_state_up': True,
# u'tenant_id': u'570fe78a1dc54cffa053bd802984ede2',
# u'provider:network_type': u'gre',
# u'router:external': False, u'shared': False, u'id':
# u'240ff9df-df35-43ae-9df5-27fae87f2492',
# u'provider:segmentation_id': 4}
#
# tuple
# -----
#
# Networks : (u'ACTIVE', 'cdca5538-ae2d-11e3-92c1-bcee7bdf8d69',
# u'vova_network', None,
# True, u'570fe78a1dc54cffa053bd802984ede2', u'gre', 'False', 'False',
# u'1e3bc4fe-85c2-4b04-9b7f-ee40239787ef', 7)
#
# Networks and subnets
# ('cdcaa1a0-ae2d-11e3-92c1-bcee7bdf8d69',
#  u'4cef03d0-1d02-40bb-8c99-2f442aac6ab0')
#
#
# Ports
# ======
# json
# ----
# {u'status': u'ACTIVE',
# u'binding:host_id': u'havana', u'name': u'',
# u'allowed_address_pairs': [],
# u'admin_state_up': True, u'network_id':
# u'240ff9df-df35-43ae-9df5-27fae87f2492',
# u'tenant_id': u'570fe78a1dc54cffa053bd802984ede2',
# u'extra_dhcp_opts': [],
# u'binding:vif_type': u'ovs', u'device_owner':
# u'network:router_interface',
# u'binding:capabilities': {u'port_filter': True},
# u'mac_address': u'fa:16:3e:ab:90:df',
# u'fixed_ips': [{u'subnet_id':
# u'4cef03d0-1d02-40bb-8c99-2f442aac6ab0',
# u'ip_address': u'90.0.0.1'}], u'id':
# u'0a2ce569-85a8-45ec-abb3-0d4b34ff69ba',u'security_groups': [],
# u'device_id': u'864e4acf-bf8e-4664-8cf7-ad5daa95681e'},
# tuples
# -------
# Ports [(u'ACTIVE', u'havana', u'',
# '6425751e-ae2c-11e3-bba1-bcee7bdf8d69', 'True',
# u'240ff9df-df35-43ae-9df5-27fae87f2492',
# u'570fe78a1dc54cffa053bd802984ede2',
# '642579e2-ae2c-11e3-bba1-bcee7bdf8d69', u'ovs',
# u'network:router_interface', '64257dac-ae2c-11e3-bba1-bcee7bdf8d69',
# u'fa:16:3e:ab:90:df',
# '64258126-ae2c-11e3-bba1-bcee7bdf8d69',
# u'0a2ce569-85a8-45ec-abb3-0d4b34ff69ba',
# '64258496-ae2c-11e3-bba1-bcee7bdf8d69',
# u'864e4acf-bf8e-4664-8cf7-ad5daa95681e')
#
# Ports and Address Pairs
# [('6425751e-ae2c-11e3-bba1-bcee7bdf8d69', '')
# Ports and Security Groups
# [('64258496-ae2c-11e3-bba1-bcee7bdf8d69', '')
# Ports and Binding Capabilities [
# ('64257dac-ae2c-11e3-bba1-bcee7bdf8d69',u'port_filter','True')
# Ports and Fixed IPs [('64258126-ae2c-11e3-bba1-bcee7bdf8d69',
# u'subnet_id',u'4cef03d0-1d02-40bb-8c99-2f442aac6ab0'),
# ('64258126-ae2c-11e3-bba1-bcee7bdf8d69', u'ip_address',
# u'90.0.0.1')
#
# Ports and Extra dhcp opts [
# ('642579e2-ae2c-11e3-bba1-bcee7bdf8d69', '')
