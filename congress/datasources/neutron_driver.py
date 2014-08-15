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
    """This method is called by d6cage to create a dataservice
    instance.  There are a couple of parameters we found useful
    to add to that call, so we included them here instead of
    modifying d6cage (and all the d6cage.createservice calls).
    """
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
    NEUTRON_SECURITY_GROUPS = "security_groups"
    NEUTRON_SUBNETS = "subnets"
    last_updated = -1

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        if args is None:
            args = self.empty_credentials()
        super(NeutronDriver, self).__init__(name, keys, inbox, datapath, args)
        if 'client' in args:
            self.neutron = args['client']
        else:
            self.neutron = neutronclient.v2_0.client.Client(**self.creds)
        self.raw_state = {}

    # TODO(thinrichs): refactor this and the logic in datasource_driver.
    #  We are mixing up delta-computation and tuple generation.
    def update_from_datasource(self):
        """Called when it is time to pull new data from this datasource.
        Sets self.state[tablename] = <list of tuples of strings/numbers>
        for every tablename exported by this datasource.
        """
        # Initialize instance variables that get set during update
        self.networks = []
        self.ports = []
        self.networks_subnet = []
        self.ports = []
        self.ports_address_pairs = []
        self.ports_security_groups = []
        self.ports_binding_capabilities = []
        self.ports_fixed_ips_groups = []
        self.ports_fixed_ips = []
        self.ports_extra_dhcp_opts = []
        self.routers = []
        self.security_groups = []

        # Grab data from API calls, translate to tuples, and set
        #   instance variables.
        LOG.debug("Neutron grabbing networks")
        networks = self.neutron.list_networks()
        if ('networks' not in self.raw_state or
            networks != self.raw_state['networks']):
            self.raw_state['networks'] = networks
            self._translate_networks(networks)
        else:
            self.networks = self.state[self.NEUTRON_NETWORKS]
            self.networks_subnet = self.state[self.NEUTRON_NETWORKS_SUBNETS]

        LOG.debug("Neutron grabbing ports")
        ports = self.neutron.list_ports()
        if 'ports' not in self.raw_state or ports != self.raw_state['ports']:
            self.raw_state['ports'] = ports
            self._translate_ports(ports)
        else:
            self.ports = self.state[self.NEUTRON_PORTS]
            self.ports_address_pairs = \
                self.state[self.NEUTRON_PORTS_ADDR_PAIRS]
            self.ports_security_groups = \
                self.state[self.NEUTRON_PORTS_SECURITY_GROUPS]
            self.ports_binding_capabilities = \
                self.state[self.NEUTRON_PORTS_BINDING_CAPABILITIES]
            self.ports_fixed_ips = self.state[self.NEUTRON_PORTS_FIXED_IPS]
            self.ports_fixed_ips_groups = \
                self.state[self.NEUTRON_PORTS_FIXED_IPS_GROUPS]
            self.ports_extra_dhcp_opts = \
                self.state[self.NEUTRON_PORTS_EXTRA_DHCP_OPTS]

        LOG.debug("Neutron grabbing routers")
        routers = self.neutron.list_routers()
        if ('routers' not in self.raw_state or
            routers != self.raw_state['routers']):
            self.raw_state['routers'] = routers
            self._translate_routers(routers)
        else:
            self.routers = self.state[self.NEUTRON_ROUTERS]

        LOG.debug("Neutron grabbing security groups")
        security = self.neutron.list_security_groups()
        if ('security_groups' not in self.raw_state or
            security != self.raw_state['security_groups']):
            self.raw_state['security_groups'] = security
            self._translate_security_groups(security)
        else:
            self.security_groups = self.state[self.NEUTRON_SECURITY_GROUPS]

        # set State
        LOG.debug("Neutron setting state")
        self.state = {}
        self.state[self.NEUTRON_NETWORKS] = set(self.networks)
        self.state[self.NEUTRON_NETWORKS_SUBNETS] = set(self.networks_subnet)

        self.state[self.NEUTRON_PORTS] = set(self.ports)
        self.state[self.NEUTRON_PORTS_ADDR_PAIRS] = \
            set(self.ports_address_pairs)
        self.state[self.NEUTRON_PORTS_SECURITY_GROUPS] = \
            set(self.ports_security_groups)
        self.state[self.NEUTRON_PORTS_BINDING_CAPABILITIES] = \
            set(self.ports_binding_capabilities)
        self.state[self.NEUTRON_PORTS_FIXED_IPS] = set(self.ports_fixed_ips)
        self.state[self.NEUTRON_PORTS_FIXED_IPS_GROUPS] = \
            set(self.ports_fixed_ips_groups)
        self.state[self.NEUTRON_PORTS_EXTRA_DHCP_OPTS] = \
            set(self.ports_extra_dhcp_opts)

        self.state[self.NEUTRON_SECURITY_GROUPS] = set(self.security_groups)

        self.state[self.NEUTRON_ROUTERS] = set(self.routers)

    def get_last_updated_time(self):
        return self.last_updated

    def get_all(self, type):
        if type not in self.state:
            self.update_from_datasource()
        assert type in self.state, "Must ask for table in schema"
        return self.state[type]

    @classmethod
    def network_key_position_map(cls):
        d = {}
        d['status'] = 1
        d['name'] = 2
        d['subnets'] = 3
        d['provider:physical_network'] = 4
        d['admin_state_up'] = 5
        d['tenant_id'] = 6
        d['provider:network_type'] = 7
        d['router:external'] = 8
        d['shared'] = 9
        d['id'] = 10
        d['provider:segmentation_id'] = 11
        return d

    @classmethod
    def port_key_position_map(cls):
        d = {}
        d['allowed_address_pairs'] = 0
        d['security_groups'] = 1
        d['extra_dhcp_opts'] = 2
        d['binding:capabilities'] = 3
        d['status'] = 4
        d['name'] = 5
        d['admin_state_up'] = 6
        d['network_id'] = 7
        d['tenant_id'] = 8
        d['binding:vif_type'] = 9
        d['device_owner'] = 10
        d['mac_address'] = 11
        d['fixed_ips'] = 12
        d['id'] = 13
        d['device_id'] = 14
        d['binding:host_id'] = 15
        return d

    # TODO(thinrichs): have this function set all the appropriate
    #    variables.  Don't bother returning something.
    # TODO(thinrichs): use self.state instead of self.networks, self.ports,
    def _translate_networks(self, obj):
        LOG.debug("NEUTRON_NETWORKS: %s", str(dict(obj)))
        key_to_index = self.network_key_position_map()
        max_network_index = max(key_to_index.values()) + 1
        n_dict_list = obj['networks']
        # prepopulate list so that we can insert directly to index below
        t_list = []
        t_subnet_list = []
        for p in n_dict_list:
            row = ['None'] * max_network_index
            for k, v in p.items():
                if k == 'subnets':
                    network_subnet_uuid = str(uuid.uuid1())
                    for s in v:
                        tuple_subnet = (network_subnet_uuid, s)
                        t_subnet_list.append(tuple_subnet)
                    row[key_to_index['subnets']] = network_subnet_uuid
                else:
                    if k in key_to_index:
                        row[key_to_index[k]] = self.value_to_congress(v)
                    else:
                        LOG.info("Ignoring unexpected dict key " + k)
            t_list.append(tuple(row))
            self.networks_subnet = t_subnet_list
        self.networks = t_list
        LOG.debug("NEUTRON_NETWORKS: %s", str(self.networks))
        LOG.debug("NEUTRON_SUBNETS: %s", str(self.networks_subnet))

    def _translate_ports(self, obj):
        LOG.debug("NEUTRON_PORTS: %s", str(obj))
        n_dict_list = obj['ports']
        d = self.port_key_position_map()
        self.ports = []
        self.ports_address_pairs = []
        self.ports_security_groups = []
        self.ports_binding_capabilities = []
        self.ports_fixed_ips_groups = []
        self.ports_fixed_ips = []
        self.ports_extra_dhcp_opts = []
        for p in n_dict_list:
            row = ['None'] * (max(d.values()) + 1)
            for k, v in p.items():
                if k == "allowed_address_pairs":
                    port_address_pair_uuid = str(uuid.uuid4())
                    row[d['allowed_address_pairs']] = \
                        port_address_pair_uuid
                    if v:
                        for a in v:
                            row_address_pair = (port_address_pair_uuid, a)
                            self.ports_address_pairs.append(
                                row_address_pair)
                elif k == "security_groups":
                    security_group_uuid = str(uuid.uuid4())
                    row[d['security_groups']] = security_group_uuid
                    if v:
                        for a in v:
                            row_sg = (security_group_uuid, a)
                            self.ports_security_groups.append(row_sg)
                elif k == "extra_dhcp_opts":
                    extra_dhcp_opts_uuid = str(uuid.uuid4())
                    row[d['extra_dhcp_opts']] = extra_dhcp_opts_uuid
                    if v:
                        for a in v:
                            t_e_dhcp = (extra_dhcp_opts_uuid, a)
                            self.ports_extra_dhcp_opts.append(t_e_dhcp)
                elif k == "binding:capabilities":
                    v_keys = v.keys()
                    binding_cap_uuid = str(uuid.uuid4())
                    row[d['binding:capabilities']] = binding_cap_uuid
                    for v_keys_e in v_keys:
                        value = self.value_to_congress(v[v_keys_e])
                        t_bc = (binding_cap_uuid, v_keys_e, value)
                        self.ports_binding_capabilities.append(t_bc)
                elif k == "fixed_ips":
                    fixed_ips_group_uuid = str(uuid.uuid4())
                    row[d['fixed_ips']] = fixed_ips_group_uuid
                    for v_elements in v:
                        v_keys = v_elements.keys()
                        fixed_ips_uuid = str(uuid.uuid4())
                        t_group = (fixed_ips_group_uuid, fixed_ips_uuid)
                        self.ports_fixed_ips_groups.append(t_group)
                        for v_keys_e in v_keys:
                            t_ip = (fixed_ips_uuid, v_keys_e,
                                    v_elements[v_keys_e])
                            self.ports_fixed_ips.append(t_ip)
                else:
                    if k in d:
                        row[d[k]] = self.value_to_congress(v)
            self.ports.append(tuple(row))
        LOG.debug("NEUTRON_PORTS: %s", str(self.ports))
        LOG.debug("NEUTRON_PORTS_FIXED_IPS_GROUPS: %s",
                  str(self.ports_fixed_ips_groups))
        LOG.debug("NEUTRON_PORTS_FIXEDIPS: %s", str(self.ports_fixed_ips))
        LOG.debug("NEUTRON_PORTS_BINDING_CAPABILITIES: %s",
                  str(self.ports_binding_capabilities))
        LOG.debug("NEUTRON_PORTS_EXTRA_DHCP_OPTS: %s",
                  str(self.ports_extra_dhcp_opts))
        LOG.debug("NEUTRON_PORTS_SECURITY_GROUPS: %s",
                  str(self.ports_security_groups))
        LOG.debug("NEUTRON_PORTS_ADDR_PAIRS: %s",
                  str(self.ports_address_pairs))

    def _translate_routers(self, obj):
        LOG.debug("NEUTRON_ROUTERS: %s", str(dict(obj)))
        self.routers = []
        d = {}
        d['status'] = 0
        d['external_gateway_info'] = 1
        d['networks'] = 2
        d['name'] = 3
        d['admin_state_up'] = 4
        d['tenant_id'] = 5
        d['id'] = 6
        for router in obj['routers']:
            row = ['None'] * (max(d.values()) + 1)
            for key, value in router.items():
                if key == 'external_gateway_info':
                    if value is not None:
                        row[d[key]] = "<Placeholder>"  # hack
                elif key in d:
                    row[d[key]] = self.value_to_congress(value)
            self.routers.append(tuple(row))
        LOG.debug("NEUTRON_ROUTERS: %s", str(self.routers))

    def _translate_security_groups(self, obj):
        LOG.debug("NEUTRON_SECURITY_GROUPS: %s", str(dict(obj)))
        self.security_groups = []
        d = {}
        d['tenant_id'] = 0
        d['name'] = 1
        d['description'] = 2
        d['id'] = 3
        for sec_group in obj['security_groups']:
            row = ['None'] * (max(d.values()) + 1)
            for key, value in sec_group.items():
                if key in d:
                    row[d[key]] = self.value_to_congress(value)
            self.security_groups.append(tuple(row))
        LOG.debug("NEUTRON_SECURITY_GROUPS: %s",
                  str(self.security_groups))


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


def main():
    driver = NeutronDriver()
    # logger.setLevel(logging.DEBUG)
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.INFO)
    # # create formatter
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -'
    #                               ' %(message)s')
    # ch.setFormatter(formatter)
    # logger.addHandler(ch)
    # logger.info("Last updated: %s" % driver.get_last_updated_time())
    # logger.info("Starting Neutron Sync Service")
    # #sync with the neutron service
    driver.update_from_datasource()
    print "Original api data"
    print str(driver.raw_state)
    print "Resulting state"
    print str(driver.state)
    # logger.info("Last updated: %s" % driver.get_last_updated_time())
    # logger.info("Sync completed")

    # logger.info("-----------------------------------------")
    # logger.info("Networks %s" % driver.get_all(driver.NEUTRON_NETWORKS))
    # logger.info("Networks and subnets %s" %
    #             driver.get_all(driver.NEUTRON_NETWORKS_SUBNETS))
    # logger.info("-----------------------------------------")
    # logger.info("Ports %s" % driver.get_all(driver.NEUTRON_PORTS))
    # logger.info("Ports and Address Pairs %s"
    #             % driver.get_all(driver.NEUTRON_PORTS_ADDR_PAIRS))
    # logger.info("Ports and Security Groups %s"
    #             % driver.get_all(driver.NEUTRON_PORTS_SECURITY_GROUPS))
    # logger.info("Ports and Binding Capabilities %s"
    #             % driver.get_all(driver.NEUTRON_PORTS_BINDING_CAPABILITIES))
    # logger.info("Ports and Fixed IPs %s" %
    #             driver.get_all(driver.NEUTRON_PORTS_FIXED_IPS))
    # logger.info("Ports and Extra dhcp opts %s" %
    #             driver.get_all(driver.NEUTRON_PORTS_EXTRA_DHCP_OPTS))
    # logger.info("-----------------------------------------")


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        raise
