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
import uuid

from congress.datasources.datasource_driver import DataSourceDriver
from congress.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return NeutronDriver(name, keys, inbox, datapath, args)


class NeutronDriver(DataSourceDriver):
    NEUTRON_NETWORKS = "networks"
    NEUTRON_NETWORKS_SUBNETS = "networks.subnets"
    NEUTRON_PORTS = "ports"
    NEUTRON_PORTS_ADDR_PAIRS = "ports.address_pairs"
    NEUTRON_PORTS_SECURITY_GROUPS = "ports.security_groups"
    NEUTRON_PORTS_BINDING_CAPABILITIES = "ports.binding_capabilities"
    NEUTRON_PORTS_FIXED_IPS = "ports.fixed_ips"
    NEUTRON_PORTS_FIXED_IPS_GROUPS = "ports.fixed_ips_groups"
    NEUTRON_PORTS_EXTRA_DHCP_OPTS = "ports.extra_dhcp_opts"
    NEUTRON_ROUTERS = "routers"
    NEUTRON_ROUTERS_EXTERNAL_GATEWAYS = "routers.external_gateways"
    NEUTRON_SECURITY_GROUPS = "security_groups"

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        # make driver easy to test
        if args is None:
            args = self.empty_credentials()
        super(NeutronDriver, self).__init__(name, keys, inbox, datapath, args)

        # make it easy to mock during testing
        if 'client' in args:
            self.neutron = args['client']
        else:
            self.neutron = neutronclient.v2_0.client.Client(**self.creds)

        # Store raw state (result of API calls) so that we can
        #   avoid re-translating and re-sending if no changes occurred.
        #   Because translation is not deterministic (we're generating
        #   UUIDs), it's hard to tell if no changes occurred
        #   after performing the translation.
        self.raw_state = {}

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

    @classmethod
    def get_schema(cls):
        """Returns a dictionary mapping tablenames to the list of
        column names for that table.  Both tablenames and columnnames
        are strings.
        """
        d = {}
        d[cls.NEUTRON_NETWORKS] = (
            'status', 'name', 'subnets', 'provider:physical_network',
            'admin_state_up', 'tenant_id', 'provider:network_type',
            'router:external', 'shared', 'id', 'provider:segmentation_id')
        d[cls.NEUTRON_NETWORKS_SUBNETS] = ('subnet_group_id', 'subnet')
        d[cls.NEUTRON_PORTS] = (
            'allowed_address_pairs', 'security_groups',
            'extra_dhcp_opts', 'binding:capabilities', 'status',
            'name', 'admin_state_up', 'network_id', 'tenant_id',
            'binding:vif_type', 'device_owner', 'mac_address',
            'fixed_ips', 'id', 'device_id', 'binding:host_id')
        d[cls.NEUTRON_PORTS_ADDR_PAIRS] = (
            'allowed_address_pairs_id', 'address')
        d[cls.NEUTRON_PORTS_SECURITY_GROUPS] = (
            'security_groups_id', 'security_group_id')
        d[cls.NEUTRON_PORTS_BINDING_CAPABILITIES] = (
            'binding:capabilities_id', 'key', 'value')
        d[cls.NEUTRON_PORTS_FIXED_IPS] = (
            'fixed_ip_id', 'key', 'value')
        d[cls.NEUTRON_PORTS_FIXED_IPS_GROUPS] = (
            'fixed_ips_group_id', 'fixed_ip_id')
        d[cls.NEUTRON_PORTS_EXTRA_DHCP_OPTS] = (
            'extra_dhcp_opt_group_id', 'dhcp_opt')
        # TODO(thinrichs): add 'routes' column
        d[cls.NEUTRON_ROUTERS] = (
            'status', 'external_gateway_info', 'networks', 'name',
            'admin_state_up', 'tenant_id', 'id')
        # TODO(thinrichs): add 'rules' column
        d[cls.NEUTRON_SECURITY_GROUPS] = (
            'tenant_id', 'name', 'description', 'id')
        d[cls.NEUTRON_ROUTERS_EXTERNAL_GATEWAYS] = (
            'external_gateway_info', 'key', 'value')
        return d

    def _translate_networks(self, obj):
        """Translate the networks represented by OBJ into tables.
        Assigns self.state[tablename] for all those TABLENAMEs
        generated from OBJ: NEUTRON_NETWORKS, NEUTRON_NETWORKS_SUBNETS
        """
        LOG.debug("NEUTRON_NETWORKS: %s", str(dict(obj)))
        key_to_index = self.get_column_map(self.NEUTRON_NETWORKS)
        max_network_index = max(key_to_index.values()) + 1
        self.state[self.NEUTRON_NETWORKS] = set()
        self.state[self.NEUTRON_NETWORKS_SUBNETS] = set()
        for network in obj['networks']:
            # prepopulate list so that we can insert directly to index below
            row = ['None'] * max_network_index
            for key, value in network.items():
                if key == 'subnets':
                    network_subnet_uuid = str(uuid.uuid1())
                    for subnet in value:
                        self.state[self.NEUTRON_NETWORKS_SUBNETS].add(
                            (network_subnet_uuid, subnet))
                    row[key_to_index['subnets']] = network_subnet_uuid
                else:
                    if key in key_to_index:
                        row[key_to_index[key]] = self.value_to_congress(value)
                    else:
                        LOG.info("Ignoring unexpected dict key " + str(key))
            self.state[self.NEUTRON_NETWORKS].add(tuple(row))
        LOG.debug("NEUTRON_NETWORKS: %s",
                  str(self.state[self.NEUTRON_NETWORKS]))
        LOG.debug("NEUTRON_NETWORKS_SUBNETS: %s",
                  str(self.state[self.NEUTRON_NETWORKS_SUBNETS]))

    def _translate_ports(self, obj):
        """Translate the ports represented by OBJ into tables.
        Assigns self.state[tablename] for all those TABLENAMEs
        generated from OBJ: NEUTRON_PORTS, NEUTRON_PORTS_ADDR_PAIRS,
        NEUTRON_PORTS_SECURITY_GROUPS, NEUTRON_PORTS_BINDING_CAPABILITIES,
        NEUTRON_PORTS_FIXED_IPS, NEUTRON_PORTS_FIXED_IPS_GROUPS,
        NEUTRON_PORTS_EXTRA_DHCP_OPTS.
        """
        LOG.debug("NEUTRON_PORTS: %s", str(obj))
        d = self.get_column_map(self.NEUTRON_PORTS)
        self.state[self.NEUTRON_PORTS] = set()
        self.state[self.NEUTRON_PORTS_ADDR_PAIRS] = set()
        self.state[self.NEUTRON_PORTS_SECURITY_GROUPS] = set()
        self.state[self.NEUTRON_PORTS_BINDING_CAPABILITIES] = set()
        self.state[self.NEUTRON_PORTS_FIXED_IPS] = set()
        self.state[self.NEUTRON_PORTS_FIXED_IPS_GROUPS] = set()
        self.state[self.NEUTRON_PORTS_EXTRA_DHCP_OPTS] = set()

        for port in obj['ports']:
            # prepopulate list so that we can insert directly to index below
            row = ['None'] * (max(d.values()) + 1)
            for key, value in port.items():
                if key == "allowed_address_pairs":
                    port_address_pair_uuid = str(uuid.uuid4())
                    row[d['allowed_address_pairs']] = \
                        port_address_pair_uuid
                    if value:
                        for addr in value:
                            row_address_pair = (port_address_pair_uuid, addr)
                            self.state[self.NEUTRON_PORTS_ADDR_PAIRS].add(
                                row_address_pair)
                elif key == "security_groups":
                    security_group_uuid = str(uuid.uuid4())
                    row[d['security_groups']] = security_group_uuid
                    if value:
                        for sec_grp in value:
                            sec_grp = self.value_to_congress(sec_grp)
                            row_sg = (security_group_uuid, sec_grp)
                            self.state[self.NEUTRON_PORTS_SECURITY_GROUPS].add(
                                row_sg)
                elif key == "extra_dhcp_opts":
                    extra_dhcp_opts_uuid = str(uuid.uuid4())
                    row[d['extra_dhcp_opts']] = extra_dhcp_opts_uuid
                    # value is a list of opts
                    if value:
                        for opt in value:
                            opt = self.value_to_congress(opt)
                            dhcp_row = (extra_dhcp_opts_uuid, opt)
                            self.state[self.NEUTRON_PORTS_EXTRA_DHCP_OPTS].add(
                                dhcp_row)
                elif key == "binding:capabilities":
                    binding_cap_uuid = str(uuid.uuid4())
                    row[d['binding:capabilities']] = binding_cap_uuid
                    for v_key, v_value in value.items():
                        v_key = self.value_to_congress(v_key)
                        v_value = self.value_to_congress(v_value)
                        bc_row = (binding_cap_uuid, v_key, v_value)
                        self.state[
                            self.NEUTRON_PORTS_BINDING_CAPABILITIES].add(
                                bc_row)
                elif key == "fixed_ips":
                    fip_group_uuid = str(uuid.uuid4())
                    row[d['fixed_ips']] = fip_group_uuid
                    # value is a list of dictionaries
                    for fip in value:
                        fip_uuid = str(uuid.uuid4())
                        fip_group_row = (fip_group_uuid, fip_uuid)
                        self.state[self.NEUTRON_PORTS_FIXED_IPS_GROUPS].add(
                            fip_group_row)
                        for fip_key, fip_value in fip.items():
                            fip_value = self.value_to_congress(fip_value)
                            fip_row = (fip_uuid, fip_key, fip_value)
                            self.state[self.NEUTRON_PORTS_FIXED_IPS].add(
                                fip_row)
                else:
                    if key in d:
                        row[d[key]] = self.value_to_congress(value)
            self.state[self.NEUTRON_PORTS].add(tuple(row))

        LOG.debug("NEUTRON_PORTS: %s",
                  str(self.state[self.NEUTRON_PORTS]))
        LOG.debug("NEUTRON_PORTS_FIXED_IPS_GROUPS: %s",
                  str(self.state[self.NEUTRON_PORTS_FIXED_IPS_GROUPS]))
        LOG.debug("NEUTRON_PORTS_FIXEDIPS: %s",
                  str(self.state[self.NEUTRON_PORTS_FIXED_IPS]))
        LOG.debug("NEUTRON_PORTS_BINDING_CAPABILITIES: %s",
                  str(self.state[self.NEUTRON_PORTS_BINDING_CAPABILITIES]))
        LOG.debug("NEUTRON_PORTS_EXTRA_DHCP_OPTS: %s",
                  str(self.state[self.NEUTRON_PORTS_EXTRA_DHCP_OPTS]))
        LOG.debug("NEUTRON_PORTS_SECURITY_GROUPS: %s",
                  str(self.state[self.NEUTRON_PORTS_SECURITY_GROUPS]))
        LOG.debug("NEUTRON_PORTS_ADDR_PAIRS: %s",
                  str(self.state[self.NEUTRON_PORTS_ADDR_PAIRS]))

    def _translate_routers(self, obj):
        """Translates the routers represented by OBJ into a single table.
        Assigns self.state[NEUTRON_SECURITY_GROUPS] to that table.
        """
        LOG.debug("NEUTRON_ROUTERS: %s", str(dict(obj)))
        self.state[self.NEUTRON_ROUTERS] = set()
        self.state[self.NEUTRON_ROUTERS_EXTERNAL_GATEWAYS] = set()
        d = self.get_column_map(self.NEUTRON_ROUTERS)
        for router in obj['routers']:
            # prepopulate list so that we can insert directly to index below
            row = ['None'] * (max(d.values()) + 1)
            for key, value in router.items():
                if key == 'external_gateway_info':
                    if value is not None:
                        external_gateway_uuid = str(uuid.uuid4())
                        row[d[key]] = external_gateway_uuid
                        for v_key, v_value in value.items():
                            v_key = self.value_to_congress(v_key)
                            v_value = self.value_to_congress(v_value)
                            eg_row = (external_gateway_uuid, v_key, v_value)
                            self.state[
                                self.NEUTRON_ROUTERS_EXTERNAL_GATEWAYS].add(
                                    eg_row)
                elif key in d:
                    row[d[key]] = self.value_to_congress(value)
            self.state[self.NEUTRON_ROUTERS].add(tuple(row))
        LOG.debug("NEUTRON_ROUTERS: %s", str(self.state[self.NEUTRON_ROUTERS]))
        LOG.debug("NEUTRON_EXTERNAL_GATEWAYS: %s",
                  str(self.state[self.NEUTRON_ROUTERS_EXTERNAL_GATEWAYS]))

    def _translate_security_groups(self, obj):
        LOG.debug("NEUTRON_SECURITY_GROUPS: %s", str(dict(obj)))
        self.state[self.NEUTRON_SECURITY_GROUPS] = set()
        d = self.get_column_map(self.NEUTRON_SECURITY_GROUPS)
        for sec_group in obj['security_groups']:
            # prepopulate list so that we can insert directly to index below
            row = ['None'] * (max(d.values()) + 1)
            for key, value in sec_group.items():
                if key in d:
                    row[d[key]] = self.value_to_congress(value)
            self.state[self.NEUTRON_SECURITY_GROUPS].add(tuple(row))
        LOG.debug("NEUTRON_SECURITY_GROUPS: %s",
                  str(self.state[self.NEUTRON_SECURITY_GROUPS]))


# Useful to have a main so we can run manual tests easily
#   and see the Input/Output for a live Neutron
def main():
    driver = NeutronDriver()
    driver.update_from_datasource()
    print "Original api data"
    print str(driver.raw_state)
    print "Resulting state"
    print str(driver.state)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        raise


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
