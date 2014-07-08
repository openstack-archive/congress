#!/usr/bin/env python
# Copyright (c) 2013 VMware, Inc. All rights reserved.
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
import logging
import mock
import mox
import neutronclient.v2_0.client
import unittest

from congress.datasources.neutron_driver import NeutronDriver
import congress.dse.d6cage
import congress.policy.compile as compile
import congress.tests.helper as helper


class TestNeutronDriver(unittest.TestCase):

    def setUp(self):
        self.neutron_client = mock.MagicMock()
        self.network = network_response
        self.ports = port_response
        self.neutron_client.list_networks.return_value = self.network
        self.neutron_client.list_ports.return_value = self.ports
        self.driver = NeutronDriver(poll_time=0)

    def test_list_networks(self):
        """Test conversion of complex network objects to tables."""
        network_list = self.neutron_client.list_networks()
        network_tuple_list = \
            self.driver._get_tuple_list(network_list,
                                        self.driver.NEUTRON_NETWORKS)
        network_tuple = network_tuple_list[0]
        network_subnet_tuples = self.driver.network_subnet

        self.assertIsNotNone(network_tuple_list)
        self.assertEquals(1, len(network_tuple_list))
        self.assertEquals(1, len(network_subnet_tuples))

        key_to_index = self.driver.network_key_position_map()
        logging.info("key_to_index: " + str(key_to_index))
        logging.info("network: " + str(network_tuple))
        subnet_tuple_guid = network_tuple[key_to_index['subnets']]

        guid_key = network_subnet_tuples[0][0]
        guid_value = network_subnet_tuples[0][1]

        name = network_tuple[key_to_index['name']]
        status = network_tuple[key_to_index['status']]
        provider_physical_network = \
            network_tuple[key_to_index['provider:physical_network']]
        admin_state_up = network_tuple[key_to_index['admin_state_up']]
        tenant_id = network_tuple[key_to_index['tenant_id']]
        provider_network_type = \
            network_tuple[key_to_index['provider:network_type']]
        router_external = network_tuple[key_to_index['router:external']]
        shared = network_tuple[key_to_index['shared']]
        id = network_tuple[key_to_index['id']]
        provider_segmentation_id = \
            network_tuple[key_to_index['provider:segmentation_id']]

        self.assertEquals('ACTIVE', status)
        self.assertIsNotNone(subnet_tuple_guid)
        self.assertEqual(guid_key, subnet_tuple_guid)
        self.assertEqual('4cef03d0-1d02-40bb-8c99-2f442aac6ab0',
                         guid_value)
        self.assertEquals('test-network',
                          name)
        self.assertEquals('None', provider_physical_network)
        self.assertEquals('True', admin_state_up)
        self.assertEquals('570fe78a1dc54cffa053bd802984ede2',
                          tenant_id)
        self.assertEquals('gre', provider_network_type)
        self.assertEquals('False', router_external)
        self.assertEquals('False', shared)
        self.assertEquals('240ff9df-df35-43ae-9df5-27fae87f2492',
                          id)
        self.assertEquals(4, provider_segmentation_id)

    def test_list_ports(self):
        """Test conversion of complex port objects to tuples."""
        port_list = self.neutron_client.list_ports()
        port_tuple_list = \
            self.driver._get_tuple_list(port_list,
                                        self.driver.NEUTRON_PORTS)
        self.port_address_pairs = self.driver.port_address_pairs

        self.port_security_groups = self.driver.port_security_groups
        self.port_binding_capabilities = self.driver.port_binding_capabilities
        self.port_extra_dhcp_opts = self.driver.port_extra_dhcp_opts
        self.port_fixed_ips = self.driver.port_fixed_ips
        self.assertIsNotNone(port_tuple_list)
        self.assertEquals(1, len(port_tuple_list))

        # Input
        # [{"status": "ACTIVE",'+
        #    '"binding:host_id": "havana", "name": "",' +
        #    '"allowed_address_pairs": [],'+
        #    '"admin_state_up": True, ' +
        #    '"network_id": "240ff9df-df35-43ae-9df5-27fae87f2492",'+
        #    '"tenant_id": "570fe78a1dc54cffa053bd802984ede2",
        #     "extra_dhcp_opts": [],'+
        #    '"binding:vif_type": "ovs",' +
        #    '"device_owner": "network:router_interface",'+
        #    '"binding:capabilities": {"port_filter": True},' +
        #    '"mac_address": "fa:16:3e:ab:90:df",'+
        #    '"fixed_ips": [{"subnet_id":
        #    "4cef03d0-1d02-40bb-8c99-2f442aac6ab0",' +
        #    '"ip_address":"90.0.0.1"}],'+
        #    '"id": "0a2ce569-85a8-45ec-abb3-0d4b34ff69ba",
        #     "security_groups": [],'+
        #    '"device_id": "864e4acf-bf8e-4664-8cf7-ad5daa95681e"}]}')

        # Output
        # [('ACTIVE', 'havana', '', '90a579ea-ea45-11e3-a085-000c292422e8',
        #   'True',
        #   '240ff9df-df35-43ae-9df5-27fae87f2492',
        #   '570fe78a1dc54cffa053bd802984ede2',
        #   '90a5b5a4-ea45-11e3-a085-000c292422e8', 'ovs',
        #   'network:router_interface',
        #   '90a5f564-ea45-11e3-a085-000c292422e8', 'fa:16:3e:ab:90:df',
        #   '90a63222-ea45-11e3-a085-000c292422e8',
        #   '0a2ce569-85a8-45ec-abb3-0d4b34ff69ba',
        #   '90a6397a-ea45-11e3-a085-000c292422e8',
        #   '864e4acf-bf8e-4664-8cf7-ad5daa95681e')]

        status = port_tuple_list[0][0]
        binding_host_id = port_tuple_list[0][1]
        name = port_tuple_list[0][2]

        guid_allowed_address_pairs = port_tuple_list[0][3]
        guid_allowed_address_pairs_expected = self.port_address_pairs[0]

        admin_state_up = port_tuple_list[0][4]
        network_id = port_tuple_list[0][5]
        tenant_id = port_tuple_list[0][6]
        guid_extra_dhcp_opts = port_tuple_list[0][7]
        guid_extra_dhcp_opts_expected = self.port_extra_dhcp_opts[0][0]
        extra_dhcp_opts_value_actual = self.port_extra_dhcp_opts[0][1]

        binding_vif_type = port_tuple_list[0][8]
        device_owner = port_tuple_list[0][9]

        guid_binding_capabilities = port_tuple_list[0][10]
        guid_binding_capabilities_expected = \
            self.port_binding_capabilities[0][0]
        binding_capabilities_key_actual = self.port_binding_capabilities[0][1]
        binding_capabilities_value_actual = \
            self.port_binding_capabilities[0][2]

        mac_address = port_tuple_list[0][11]
        guid_fixed_ips = port_tuple_list[0][12]
        guid_fixed_ips_expected = self.port_fixed_ips[0][0]
        fixed_ips_key_one = self.port_fixed_ips[0][1]
        fixed_ips_value_one = self.port_fixed_ips[0][2]
        fixed_ips_key_two = self.port_fixed_ips[1][1]
        fixed_ips_value_two = self.port_fixed_ips[1][2]

        id = port_tuple_list[0][13]
        guid_security_groups = port_tuple_list[0][14]
        guid_security_groups_expected = self.port_security_groups[0][0]
        security_groups_value = self.port_security_groups[0][1]
        device_id = port_tuple_list[0][15]

        self.assertEqual('ACTIVE', status)
        self.assertEqual('havana', binding_host_id)
        self.assertEqual('', name)
        self.assertEqual(guid_allowed_address_pairs_expected[0],
                         guid_allowed_address_pairs)

        self.assertEqual(1, len(self.port_address_pairs))
        self.assertEqual('', self.port_address_pairs[0][1])
        self.assertEqual('True', admin_state_up)
        self.assertEqual('240ff9df-df35-43ae-9df5-27fae87f2492', network_id)
        self.assertEqual('570fe78a1dc54cffa053bd802984ede2', tenant_id)

        self.assertEqual(guid_extra_dhcp_opts_expected, guid_extra_dhcp_opts)
        self.assertEqual(1, len(self.port_extra_dhcp_opts))
        self.assertEqual('', extra_dhcp_opts_value_actual)

        self.assertEqual(guid_binding_capabilities_expected,
                         guid_binding_capabilities)
        self.assertEqual(1, len(self.port_binding_capabilities))
        self.assertEqual('port_filter', binding_capabilities_key_actual)
        self.assertEqual('True', binding_capabilities_value_actual)

        self.assertEqual('ovs', binding_vif_type)
        self.assertEqual('network:router_interface', device_owner)

        #    '"fixed_ips": [{"subnet_id":
        #    "4cef03d0-1d02-40bb-8c99-2f442aac6ab0",' +
        #    '"ip_address":"90.0.0.1"}],'+
        self.assertEqual(guid_fixed_ips_expected, guid_fixed_ips)
        self.assertEqual(2, len(self.port_fixed_ips))
        self.assertEqual('subnet_id', fixed_ips_key_one)
        self.assertEqual('4cef03d0-1d02-40bb-8c99-2f442aac6ab0',
                         fixed_ips_value_one)
        self.assertEqual('ip_address', fixed_ips_key_two)
        self.assertEqual('90.0.0.1', fixed_ips_value_two)

        self.assertEqual('fa:16:3e:ab:90:df', mac_address)
        self.assertEqual('0a2ce569-85a8-45ec-abb3-0d4b34ff69ba', id)

        self.assertEqual(guid_security_groups_expected,
                         guid_security_groups)
        self.assertEqual(1, len(self.port_security_groups))
        self.assertEqual('', security_groups_value)

        self.assertEqual('864e4acf-bf8e-4664-8cf7-ad5daa95681e', device_id)

    #### Tests for DataSourceDriver
    # Note: these tests are really testing the functionality of the class
    #  DataSourceDriver, but it's useful to use an actual subclass so
    #  we can test the functionality end-to-end.  We use Neutron for
    #  that subclass.  Leaving it in this file so that it is clear
    #  that when the Neutron driver changes, these tests may need
    #  to change as well.  Tried to minimize the number of changes
    #  necessary.

    def setup_polling(self, debug_mode=False):
        """Setup polling tests."""
        cage = congress.dse.d6cage.d6Cage()
        # so that we exit once test finishes; all other threads are forced
        #    to be daemons
        cage.daemon = True
        cage.start()

        # Create mock of Neutron client so we can control data
        mock_factory = mox.Mox()
        neutron_client = mock_factory.CreateMock(
            neutronclient.v2_0.client.Client)
        neutron_client.list_networks().InAnyOrder(1).AndReturn(network1)
        neutron_client.list_ports().InAnyOrder(1).AndReturn(port_response)
        neutron_client.list_networks().InAnyOrder(2).AndReturn(network2)
        neutron_client.list_ports().InAnyOrder(2).AndReturn(port_response)
        mock_factory.ReplayAll()

        # Create modules (without auto-polling)
        cage.loadModule("NeutronDriver",
                        helper.data_module_path("neutron_driver.py"))
        cage.loadModule("PolicyDriver", helper.policy_module_path())
        cage.createservice(name="policy", moduleName="PolicyDriver")
        cage.createservice(name="neutron", moduleName="NeutronDriver",
                           args={'poll_time': 0,
                                 'client': neutron_client})
        policy = cage.service_object('policy')

        # Make it so that we get detailed info from policy engine
        if debug_mode:
            policy.debug_mode()

        # insert rule into policy to make testing easier.
        #   (Some of the IDs are auto-generated each time we convert)
        policy.insert(create_network_group('p'))

        # create some garbage data
        network_key_to_index = NeutronDriver.network_key_position_map()
        network_max_index = max(network_key_to_index.values())
        args1 = ['1'] * (network_max_index + 1)
        args2 = ['2'] * (network_max_index + 1)
        args1 = ",".join(args1)
        args2 = ",".join(args2)
        fake_networks = [
            'neutron:networks({})'.format(args1),
            'neutron:networks({})'.format(args2)]

        # answer to query above for network1
        datalog1 = \
            ('p("240ff9df-df35-43ae-9df5-27fae87f2492") '
             'p("340ff9df-df35-43ae-9df5-27fae87f2492") '
             'p("440ff9df-df35-43ae-9df5-27fae87f2492")')

        # answer to query above for network2
        datalog2 = \
            ('p("240ff9df-df35-43ae-9df5-27fae87f2492") '
             'p("640ff9df-df35-43ae-9df5-27fae87f2492") '
             'p("540ff9df-df35-43ae-9df5-27fae87f2492")')

        # return value
        d = {}
        d['cage'] = cage
        d['datalog1'] = datalog1
        d['datalog2'] = datalog2
        d['fake_networks'] = fake_networks
        return d

    def test_subscribe_poll(self):
        """Test subscribing before polling.  The common case."""
        info = self.setup_polling()
        cage = info['cage']
        policy = cage.service_object('policy')
        neutron = cage.service_object('neutron')
        datalog1 = info['datalog1']
        datalog2 = info['datalog2']

        # subscribe
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.pause()  # so that subscription messages are processed

        # poll 1
        neutron.poll()
        helper.pause()  # so that data updates are processed
        e = helper.db_equal(policy.select('p(x)'), datalog1)
        self.assertTrue(e, 'Neutron insertion 1')

        # poll 2
        neutron.poll()
        helper.pause()
        e = helper.db_equal(policy.select('p(x)'), datalog2)
        self.assertTrue(e, 'Neutron insertion 2')

    def test_policy_initialization(self):
        """Test subscribing before polling.  The common case."""
        info = self.setup_polling()
        cage = info['cage']
        policy = cage.service_object('policy')
        neutron = cage.service_object('neutron')
        datalog1 = info['datalog1']
        fake_networks = info['fake_networks']

        # add garbage to policy
        for formula in fake_networks:
            logging.debug("Inserting fake_network: " + str(formula))
            policy.insert(formula)

        # subscribe
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.pause()  # so that subscription messages are processed

        # poll 1
        neutron.poll()
        helper.pause()  # so that data updates are processed
        e = helper.db_equal(policy.select('p(x)'), datalog1)
        self.assertTrue(e, 'Neutron insertion 1')

    def test_poll_subscribe(self):
        """Test polling before subscribing."""
        info = self.setup_polling()
        cage = info['cage']
        policy = cage.service_object('policy')
        neutron = cage.service_object('neutron')
        datalog1 = info['datalog1']
        datalog2 = info['datalog2']
        fake_networks = info['fake_networks']

        # add garbage to policy
        for formula in fake_networks:
            logging.debug("Inserting fake_network: " + str(formula))
            policy.insert(formula)

        # poll 1 and then subscribe; should still see first result
        neutron.poll()
        helper.pause()  # so that data is sent
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.pause()  # so that data updates are processed
        e = helper.db_equal(policy.select('p(x)'), datalog1)
        self.assertTrue(e, 'Neutron insertion 1')

        # poll 2
        neutron.poll()
        helper.pause()
        e = helper.db_equal(policy.select('p(x)'), datalog2)
        self.assertTrue(e, 'Neutron insertion 2')

    def test_double_poll_subscribe(self):
        """Test double polling before subscribing."""
        info = self.setup_polling()
        cage = info['cage']
        policy = cage.service_object('policy')
        neutron = cage.service_object('neutron')
        datalog2 = info['datalog2']

        # poll twice and then subscribe: should see 2nd result
        neutron.poll()
        helper.pause()
        neutron.poll()
        helper.pause()
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.pause()  # so that messages are processed
        e = helper.db_equal(policy.select('p(x)'), datalog2)
        self.assertTrue(e, 'Neutron insertion 2')

    def test_policy_recovery(self):
        """Test policy crashing and recovering (sort of)."""
        info = self.setup_polling()
        cage = info['cage']
        policy = cage.service_object('policy')
        neutron = cage.service_object('neutron')
        datalog1 = info['datalog1']

        # get initial data
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.pause()
        neutron.poll()
        helper.pause()
        e = helper.db_equal(policy.select('p(x)'), datalog1)
        self.assertTrue(e, 'Neutron insertion 1')

        # clear out policy's neutron:networks data (to simulate crashing)
        policy.initialize(['neutron:networks'], [])
        # subscribe again (without unsubscribing)
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.pause()
        # should get same data
        e = helper.db_equal(policy.select('p(x)'), datalog1)
        self.assertTrue(e, 'Neutron insertion 1')


def create_network_group(tablename, full_neutron_tablename=None):
    if full_neutron_tablename is None:
        full_neutron_tablename = 'neutron:networks'
    network_key_to_index = NeutronDriver.network_key_position_map()
    network_id_index = network_key_to_index['id']
    network_max_index = max(network_key_to_index.values())
    network_args = ['x' + str(i) for i in xrange(0, network_max_index + 1)]
    formula = compile.parse1(
        '{}({}) :- {}({})'.format(
        tablename,
        'x' + str(network_id_index),
        full_neutron_tablename,
        ",".join(network_args)))
    return formula


# Only diffs between network1 and network2 are the IDs
network1 = {'networks': [
    {'status': 'ACTIVE',
     'subnets': '4cef03d0-1d02-40bb-8c99-2f442aac6ab0',
     'name': 'test-network',
     'provider:physical_network': None,
     'admin_state_up': True,
     'tenant_id': '570fe78a1dc54cffa053bd802984ede2',
     'provider:network_type': 'gre',
     'router:external': False,
     'shared': False,
     'id': '240ff9df-df35-43ae-9df5-27fae87f2492',
     'provider:segmentation_id': 4},
    {'status': 'ACTIVE',
     'subnets': '4cef03d0-1d02-40bb-8c99-2f442aac6ab0',
     'name': 'test-network',
     'provider:physical_network': None,
     'admin_state_up': True,
     'tenant_id': '570fe78a1dc54cffa053bd802984ede2',
     'provider:network_type': 'gre',
     'router:external': False,
     'shared': False,
     'id': '340ff9df-df35-43ae-9df5-27fae87f2492',
     'provider:segmentation_id': 4},
    {'status': 'ACTIVE',
     'subnets': '4cef03d0-1d02-40bb-8c99-2f442aac6ab0',
     'name': 'test-network',
     'provider:physical_network': None,
     'admin_state_up': True,
     'tenant_id': '570fe78a1dc54cffa053bd802984ede2',
     'provider:network_type': 'gre',
     'router:external': False,
     'shared': False,
     'id': '440ff9df-df35-43ae-9df5-27fae87f2492',
     'provider:segmentation_id': 4}]}

network2 = {'networks': [
    {'status': 'ACTIVE',
     'subnets': '4cef03d0-1d02-40bb-8c99-2f442aac6ab0',
     'name': 'test-network',
     'provider:physical_network': None,
     'admin_state_up': True,
     'tenant_id': '570fe78a1dc54cffa053bd802984ede2',
     'provider:network_type': 'gre',
     'router:external': False,
     'shared': False,
     'id': '240ff9df-df35-43ae-9df5-27fae87f2492',
     'provider:segmentation_id': 4},
    {'status': 'ACTIVE',
     'subnets': '4cef03d0-1d02-40bb-8c99-2f442aac6ab0',
     'name': 'test-network',
     'provider:physical_network': None,
     'admin_state_up': True,
     'tenant_id': '570fe78a1dc54cffa053bd802984ede2',
     'provider:network_type': 'gre',
     'router:external': False,
     'shared': False,
     'id': '540ff9df-df35-43ae-9df5-27fae87f2492',
     'provider:segmentation_id': 4},
    {'status': 'ACTIVE',
     'subnets': '4cef03d0-1d02-40bb-8c99-2f442aac6ab0',
     'name': 'test-network',
     'provider:physical_network': None,
     'admin_state_up': True,
     'tenant_id': '570fe78a1dc54cffa053bd802984ede2',
     'provider:network_type': 'gre',
     'router:external': False,
     'shared': False,
     'id': '640ff9df-df35-43ae-9df5-27fae87f2492',
     'provider:segmentation_id': 4}]}


## Sample responses from neutron-client, after parsing
network_response = \
    {'networks':
        [{'status': 'ACTIVE',
          'subnets': ['4cef03d0-1d02-40bb-8c99-2f442aac6ab0'],
          'name': 'test-network',
          'provider:physical_network': None,
          'admin_state_up': True,
          'tenant_id': '570fe78a1dc54cffa053bd802984ede2',
          'provider:network_type': 'gre',
          'router:external': False,
          'shared': False,
          'id': '240ff9df-df35-43ae-9df5-27fae87f2492',
          'provider:segmentation_id': 4}]}

port_response = \
    {"ports":
        [{"status": "ACTIVE",
          "binding:host_id": "havana",
          "name": "",
          "allowed_address_pairs": [],
          "admin_state_up": True,
          "network_id": "240ff9df-df35-43ae-9df5-27fae87f2492",
          "tenant_id": "570fe78a1dc54cffa053bd802984ede2",
          "extra_dhcp_opts": [],
          "binding:vif_type": "ovs",
          "device_owner": "network:router_interface",
          "binding:capabilities": {"port_filter": True},
          "mac_address": "fa:16:3e:ab:90:df",
          "fixed_ips": [
              {"subnet_id": "4cef03d0-1d02-40bb-8c99-2f442aac6ab0",
               "ip_address": "90.0.0.1"}],
          "id": "0a2ce569-85a8-45ec-abb3-0d4b34ff69ba",
          "security_groups": [],
          "device_id": "864e4acf-bf8e-4664-8cf7-ad5daa95681e"}]}
