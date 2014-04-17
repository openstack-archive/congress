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
from congress.server.service_pluggins.datasource_driver import DataSourceDriver
import datetime
import logging
from neutronclient.v2_0 import client
from congress.server.service_pluggins.settings import OS_USERNAME, \
    OS_PASSWORD, OS_AUTH_URL, OS_TENANT_NAME
import uuid

logger = logging.getLogger(__name__)


class NeutronDriver(DataSourceDriver):
    USERNAME = OS_USERNAME
    PASSWORD = OS_PASSWORD
    AUTH_URL = OS_AUTH_URL
    TENANT_NAME = OS_TENANT_NAME
    NEUTRON_NETWORKS = "neutron:networks"
    NEUTRON_NETWORKS_SUBNETS = "neutron:networks:subnets"
    NEUTRON_PORTS = "neutron:ports"
    NEUTRON_PORTS_ADDR_PAIRS = "neutron:ports:address_pairs"
    NEUTRON_PORTS_SECURITY_GROUPS = "neutron:ports:security_groups"
    NEUTRON_PORTS_BINDING_CAPABILITIES = "neutron:ports:binding_capabilities"
    NEUTRON_PORTS_FIXED_IPS = "neutron:ports:fixed_ips"
    NEUTRON_PORTS_EXTRA_DHCP_OPTS = "neutron:ports:extra_dhcp_opts"
    NEUTRON_ROUTERS = "neutron:routers"
    NEUTRON_SECURITY_GROUPS = "neutron:security_groups"
    NEUTRON_SUBNETS = "neutron:subnets"
    last_updated = -1

    def __init__(self, **creds):
        credentials = self._get_credentials()
        self.neutron = client.Client(**credentials)

    def update_from_datasource(self):
        self.networks = \
            self._get_tuple_list(self.neutron.list_networks(),
                                 self.NEUTRON_NETWORKS)
        self.ports = \
            self._get_tuple_list(self.neutron.list_ports(), self.NEUTRON_PORTS)
        self.last_updated = datetime.datetime.now()

    def get_last_updated_time(self):
            return self.last_updated

    def get_all(self, type):
        if type == self.NEUTRON_NETWORKS:
            if self.networks is None:
                self.update_from_datasource()
            return self.networks
        if type == self.NEUTRON_PORTS:
            if self.ports is None:
                self.update_from_datasource()
            return self.ports
        elif type == self.NEUTRON_NETWORKS_SUBNETS:
            if self.network_subnet is None:
                self.update_from_datasource()
            return self.network_subnet
        elif type == self.NEUTRON_PORTS_ADDR_PAIRS:
            if self.port_address_pairs is None:
                self.update_from_datasource()
            return self.port_address_pairs
        elif type == self.NEUTRON_PORTS_SECURITY_GROUPS:
            if self.port_security_groups is None:
                self.update_from_datasource()
            return self.port_security_groups
        elif type == self.NEUTRON_PORTS_BINDING_CAPABILITIES:
            if self.port_binding_capabilities is None:
                self.update_from_datasource()
            return self.port_binding_capabilities
        elif type == self.NEUTRON_PORTS_FIXED_IPS:
            if self.port_fixed_ips is None:
                self.update_from_datasource()
            return self.port_fixed_ips
        elif type == self.NEUTRON_PORTS_EXTRA_DHCP_OPTS:
            if self.port_extra_dhcp_opts is None:
                self.update_from_datasource()
            return self.port_extra_dhcp_opts

    def _get_tuple_list(self, obj, type):
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
        if type == self.NEUTRON_NETWORKS:
            n_dict_list = obj['networks']
            t_list = []
            t_subnet_list = []
            for p in n_dict_list:
                tuple = ()
                for k, v in p.items():
                    if k == 'subnets':
                        network_subnet_uuid = str(uuid.uuid1())
                        for s in v:
                            tuple_subnet = (network_subnet_uuid, s)
                            t_subnet_list.append(tuple_subnet)
                        tuple = tuple + (network_subnet_uuid,)
                    else:
                        if v in (True, False):
                            v = self.boolean_to_congress(v)
                        tuple = tuple + (v,)
                t_list.append(tuple)
                self.network_subnet = t_subnet_list
            return t_list
        elif type == self.NEUTRON_NETWORKS_SUBNETS:
            return self.network_subnet
        elif type == self.NEUTRON_PORTS:
            n_dict_list = obj['ports']
            t_list = []
            t_address_pair_list = []
            t_sg_list = []
            t_bc_list = []
            t_ip_list = []
            t_e_dhcp_list = []
            for p in n_dict_list:
                tuple = ()
                #allowed_address_pairs
                #fixed_ips
                #extra_dhcp_opts
                #security_groups
                #binding:capabilities
                for k, v in p.items():
                    if k == "allowed_address_pairs":
                        port_address_pair_uuid = str(uuid.uuid1())
                        tuple = tuple + (port_address_pair_uuid,)
                        if not v:
                            tuple_address_pair = (port_address_pair_uuid, '')
                            t_address_pair_list.append(tuple_address_pair)
                        else:
                            for a in v:
                                tuple_address_pair = (port_address_pair_uuid,
                                                      a)
                                t_address_pair_list.append(tuple_address_pair)
                        self.port_address_pairs = t_address_pair_list
                    elif k == "security_groups":
                        security_group_uuid = str(uuid.uuid1())
                        tuple = tuple + (security_group_uuid,)
                        if not v:
                            tuple_sg = (security_group_uuid, '')
                            t_sg_list.append(tuple_sg)
                        else:
                            for a in v:
                                tuple_sg = (security_group_uuid, a)
                                t_sg_list.append(tuple_sg)
                        self.port_security_groups = t_sg_list
                    elif k == "extra_dhcp_opts":
                        extra_dhcp_opts_uuid = str(uuid.uuid1())
                        tuple = tuple + (extra_dhcp_opts_uuid,)
                        if not v:
                            t_e_dhcp = (extra_dhcp_opts_uuid, '')
                            t_e_dhcp_list.append(t_e_dhcp)
                        else:
                            for a in v:
                                t_e_dhcp = (extra_dhcp_opts_uuid, a)
                                t_e_dhcp_list.append(t_e_dhcp)
                        self.port_extra_dhcp_opts = t_e_dhcp_list
                    elif k == "binding:capabilities":
                        d = v
                        d_keys = d.keys()
                        binding_cap_uuid = str(uuid.uuid1())
                        for d_keys_e in d_keys:
                            value = d[d_keys_e]
                            if value in (True, False):
                                value = self.boolean_to_congress(value)
                            t_bc = (binding_cap_uuid, d_keys_e, value)
                            t_bc_list.append(t_bc)
                        self.port_binding_capabilities = t_bc_list
                        tuple = tuple + (binding_cap_uuid,)
                    elif k == "fixed_ips":
                        for v_elements in v:
                            v_keys = v_elements.keys()
                            fixed_ips_uuid = str(uuid.uuid1())
                            for v_keys_e in v_keys:
                                t_ip = (fixed_ips_uuid, v_keys_e,
                                        v_elements[v_keys_e])
                                t_ip_list.append(t_ip)
                        self.port_fixed_ips = t_ip_list
                        tuple = tuple + (fixed_ips_uuid,)
                    else:
                        if v in (True, False):
                            v = self.boolean_to_congress(v)
                        tuple = tuple + (v,)
                t_list.append(tuple)
                self.port_address_pairs = t_address_pair_list
            return t_list
        # NEUTRON_PORTS_ADDR_PAIRs = "neutron:ports:address_pairs"
        # NEUTRON_PORTS_SECURITY_GROUPS = "neutron:ports:security_groups"
        # NEUTRON_PORTS_BINDING_CAPABILITIES =
        #    "neutron:ports:binding_capabilities"
        # NEUTRON_PORTS_FIXED_IPS = "neutron:ports:fixed_ips"
        # NEUTRON_PORTS_EXTRA_DHCP_OPTS
        #    = "neutron:ports:extra_dhcp_opts"
        elif type == self.NEUTRON_PORTS_ADDR_PAIRs:
            self.port_address_pairs
        elif type == self.NEUTRON_PORTS_SECURITY_GROUPS:
            self.port_security_groups
        elif type == self.NEUTRON_PORTS_BINDING_CAPABILITIES:
            self.port_binding_capabilities
        elif type == self.NEUTRON_PORTS_EXTRA_DHCP_OPTS:
            self.port_extra_dhcp_opts
        elif type == self.NEUTRON_PORTS_FIXED_IPS:
            self.port_fixed_ips

    def _get_credentials(self):
        d = {}
        d['username'] = self.USERNAME
        d['password'] = self.PASSWORD
        d['auth_url'] = self.AUTH_URL
        d['tenant_name'] = self.TENANT_NAME
        return d


def main():
    driver = NeutronDriver()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -'
                                  ' %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.info("Last updated: %s" % driver.get_last_updated_time())
    logger.info("Starting Neutron Sync Service")
    #sync with the neutron service
    driver.update_from_datasource()
    logger.info("Last updated: %s" % driver.get_last_updated_time())
    logger.info("Sync completed")

    logger.info("-----------------------------------------")
    logger.info("Networks %s" % driver.get_all(driver.NEUTRON_NETWORKS))
    logger.info("Networks and subnets %s" %
                driver.get_all(driver.NEUTRON_NETWORKS_SUBNETS))
    logger.info("-----------------------------------------")
    logger.info("Ports %s" % driver.get_all(driver.NEUTRON_PORTS))
    logger.info("Ports and Address Pairs %s"
                % driver.get_all(driver.NEUTRON_PORTS_ADDR_PAIRS))
    logger.info("Ports and Security Groups %s"
                % driver.get_all(driver.NEUTRON_PORTS_SECURITY_GROUPS))
    logger.info("Ports and Binding Capabilities %s"
                % driver.get_all(driver.NEUTRON_PORTS_BINDING_CAPABILITIES))
    logger.info("Ports and Fixed IPs %s" %
                driver.get_all(driver.NEUTRON_PORTS_FIXED_IPS))
    logger.info("Ports and Extra dhcp opts %s" %
                driver.get_all(driver.NEUTRON_PORTS_EXTRA_DHCP_OPTS))
    logger.info("-----------------------------------------")

if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        raise
