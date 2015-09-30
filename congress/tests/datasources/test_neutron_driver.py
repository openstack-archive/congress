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
import datetime

import mock
from mox3 import mox
import neutronclient.v2_0.client
from six.moves import range

from congress.datalog import compile
from congress.datasources import neutron_driver
from congress.dse import d6cage
from congress.tests import base
from congress.tests import helper


class TestNeutronDriver(base.TestCase):

    def setUp(self):
        super(TestNeutronDriver, self).setUp()
        self.neutron_client = mock.MagicMock()
        self.neutron_client.list_networks.return_value = network_response
        self.neutron_client.list_ports.return_value = port_response
        self.neutron_client.list_routers.return_value = router_response
        self.neutron_client.list_security_groups.return_value = (
            security_group_response)
        args = helper.datasource_openstack_args()
        self.driver = neutron_driver.NeutronDriver(args=args)
        self.driver.neutron = self.neutron_client

    def test_list_networks(self):
        """Test conversion of complex network objects to tables."""
        network_list = self.neutron_client.list_networks()
        self.driver._translate_networks(network_list)
        network_tuples = self.driver.state[self.driver.NETWORKS]
        network_subnet_tuples = self.driver.state[
            self.driver.NETWORKS_SUBNETS]

        # size of networks/subnets
        self.assertIsNotNone(network_tuples)
        self.assertEqual(1, len(network_tuples))
        self.assertEqual(1, len(network_subnet_tuples))

        # properties of first network
        key_to_index = self.driver.get_column_map(
            self.driver.NETWORKS)
        network_tuple = network_tuples.pop()
        subnet_tuple_guid = network_tuple[key_to_index['subnet_group_id']]
        name = network_tuple[key_to_index['name']]
        status = network_tuple[key_to_index['status']]
        provider_physical_network = (
            network_tuple[key_to_index['provider:physical_network']])
        admin_state_up = network_tuple[key_to_index['admin_state_up']]
        tenant_id = network_tuple[key_to_index['tenant_id']]
        provider_network_type = (
            network_tuple[key_to_index['provider:network_type']])
        router_external = network_tuple[key_to_index['router:external']]
        shared = network_tuple[key_to_index['shared']]
        id = network_tuple[key_to_index['id']]
        provider_segmentation_id = (
            network_tuple[key_to_index['provider:segmentation_id']])

        # properties of first subnet
        network_subnet_tuple = network_subnet_tuples.pop()
        guid_key = network_subnet_tuple[0]
        guid_value = network_subnet_tuple[1]

        # tests for network/subnet
        self.assertEqual('ACTIVE', status)
        self.assertIsNotNone(subnet_tuple_guid)
        self.assertEqual(guid_key, subnet_tuple_guid)
        self.assertEqual('4cef03d0-1d02-40bb-8c99-2f442aac6ab0',
                         guid_value)
        self.assertEqual('test-network',
                         name)
        self.assertEqual('None', provider_physical_network)
        self.assertEqual('True', admin_state_up)
        self.assertEqual('570fe78a1dc54cffa053bd802984ede2',
                         tenant_id)
        self.assertEqual('gre', provider_network_type)
        self.assertEqual('False', router_external)
        self.assertEqual('False', shared)
        self.assertEqual('240ff9df-df35-43ae-9df5-27fae87f2492',
                         id)
        self.assertEqual(4, provider_segmentation_id)

    def test_list_ports(self):
        """Test conversion of complex port objects to tuples."""
        # setup
        self.driver._translate_ports(self.neutron_client.list_ports())
        d = self.driver.get_column_map(self.driver.PORTS)

        # number of ports
        ports = self.driver.state[self.driver.PORTS]
        self.assertIsNotNone(ports)
        self.assertEqual(1, len(ports))

        # simple properties of a port
        port = ports.pop()
        self.assertEqual('ACTIVE', port[d['status']])
        self.assertEqual('havana', port[d['binding:host_id']])
        self.assertEqual('', port[d['name']])
        self.assertEqual('True', port[d['admin_state_up']])
        self.assertEqual('240ff9df-df35-43ae-9df5-27fae87f2492',
                         port[d['network_id']])
        self.assertEqual('570fe78a1dc54cffa053bd802984ede2',
                         port[d['tenant_id']])
        self.assertEqual('ovs', port[d['binding:vif_type']])
        self.assertEqual('network:router_interface', port[d['device_owner']])
        self.assertEqual('fa:16:3e:ab:90:df', port[d['mac_address']])
        self.assertEqual('0a2ce569-85a8-45ec-abb3-0d4b34ff69ba',
                         port[d['id']])
        self.assertEqual('864e4acf-bf8e-4664-8cf7-ad5daa95681e',
                         port[d['device_id']])

        # complex property: allowed_address_pairs
        # TODO(thinrichs): add representative allowed_address_pairs
        address_pairs = self.driver.state[
            self.driver.PORTS_ADDR_PAIRS]
        self.assertEqual(0, len(address_pairs))

        # complex property: extra_dhcp_opts
        # TODO(thinrichs): add representative port_extra_dhcp_opts
        dhcp_opts = self.driver.state[
            self.driver.PORTS_EXTRA_DHCP_OPTS]
        self.assertEqual(0, len(dhcp_opts))

        # complex property: binding:capabilities
        binding_caps = self.driver.state[
            self.driver.PORTS_BINDING_CAPABILITIES]
        cap_id = port[d['binding:capabilities_id']]
        self.assertEqual(1, len(binding_caps))
        self.assertEqual((cap_id, 'port_filter', 'True'), binding_caps.pop())

        # complex property: security_groups
        sec_grps = self.driver.state[self.driver.PORTS_SECURITY_GROUPS]
        self.assertEqual(2, len(sec_grps))
        security_grp_grp = port[d['security_groups_id']]
        security_grp1 = '15ea0516-11ec-46e9-9e8e-7d1b6e3d7523'
        security_grp2 = '25ea0516-11ec-46e9-9e8e-7d1b6e3d7523'
        security_data = set([(security_grp_grp, security_grp1),
                            (security_grp_grp, security_grp2)])
        self.assertEqual(security_data, set(sec_grps))

        # complex property: fixed_ips
        # Need to show we have the following
        # port(..., <fixed_ips>, ...)
        # fixed_ips_groups(<fixed_ips>, <fip1>)
        # fixed_ips_groups(<fixed_ips>, <fip2>)
        # fixedips(<fip1>, "subnet_id", "4cef03d0-1d02-40bb-8c99-2f442aac6ab0")
        # fixedips(<fip1>, "ip_address", "90.0.0.1")
        # fixedips(<fip2>, "subnet_id", "5cef03d0-1d02-40bb-8c99-2f442aac6ab0")
        # fixedips(<fip2>, "ip_address", "100.0.0.1")
        # TODO(thinrichs): use functionality of policy-engine
        #    to make this test simpler to understand/write
        fixed_ip_groups = self.driver.state[
            self.driver.PORTS_FIXED_IPS_GROUPS]
        fixed_ips = self.driver.state[self.driver.PORTS_FIXED_IPS]
        fixed_ip_grp = port[d['fixed_ips']]
        # ensure groups of IPs are correct
        self.assertEqual(2, len(fixed_ip_groups))
        groups = set([x[0] for x in fixed_ip_groups])
        self.assertEqual(set([fixed_ip_grp]), groups)
        # ensure the IDs for fixed_ips are the right ones
        fixed_ips_from_grp = [x[1] for x in fixed_ip_groups]
        fixed_ips_from_ips = [x[0] for x in fixed_ips]
        self.assertEqual(set(fixed_ips_from_grp), set(fixed_ips_from_ips))
        # ensure actual fixed_ips are right
        self.assertEqual(4, len(fixed_ips))
        ips = [x for x in fixed_ips if x[1] == 'ip_address']
        subnets = [x for x in fixed_ips if x[1] == 'subnet_id']
        if ips[0][0] == subnets[0][0]:
            ip0 = ips[0][2]
            subnet0 = subnets[0][2]
            ip1 = ips[1][2]
            subnet1 = subnets[1][2]
        else:
            ip0 = ips[0][2]
            subnet0 = subnets[1][2]
            ip1 = ips[1][2]
            subnet1 = subnets[0][2]
        if ip0 == "90.0.0.1":
            self.assertEqual("4cef03d0-1d02-40bb-8c99-2f442aac6ab0", subnet0)
            self.assertEqual("90.0.0.1", ip0)
            self.assertEqual("5cef03d0-1d02-40bb-8c99-2f442aac6ab0", subnet1)
            self.assertEqual("100.0.0.1", ip1)
        else:
            self.assertEqual("4cef03d0-1d02-40bb-8c99-2f442aac6ab0", subnet1)
            self.assertEqual("90.0.0.1", ip1)
            self.assertEqual("5cef03d0-1d02-40bb-8c99-2f442aac6ab0", subnet0)
            self.assertEqual("100.0.0.1", ip0)

    def test_list_routers(self):
        self.driver._translate_routers(self.neutron_client.list_routers())
        d = self.driver.get_column_map(self.driver.ROUTERS)

        # number of routers
        routers = self.driver.state[self.driver.ROUTERS]
        self.assertIsNotNone(routers)
        self.assertEqual(1, len(routers))

        # simple properties of a router
        router = routers.pop()
        self.assertEqual('ACTIVE', router[d['status']])
        self.assertEqual('router1', router[d['name']])
        self.assertEqual('True', router[d['admin_state_up']])
        self.assertEqual('abb53cc6636848218f46d01f22bf1060',
                         router[d['tenant_id']])
        self.assertEqual('4598c424-d608-4366-9beb-139adbd7cff5',
                         router[d['id']])

        # external gateway info
        gateway_info = self.driver.state[
            self.driver.ROUTERS_EXTERNAL_GATEWAYS]
        gateway_id = router[d['external_gateway_info']]
        self.assertEqual(2, len(gateway_info))
        row1 = (gateway_id, 'network_id',
                'a821b8d3-af1f-4d79-9b8e-3da9674338ae')
        row2 = (gateway_id, 'enable_snat', 'True')
        self.assertEqual(set([row1, row2]), gateway_info)

    def test_list_security_groups(self):
        self.driver._translate_security_groups(
            self.neutron_client.list_security_groups())
        d = self.driver.get_column_map(self.driver.SECURITY_GROUPS)

        # number of security groups
        sec_grps = self.driver.state[self.driver.SECURITY_GROUPS]
        self.assertIsNotNone(sec_grps)
        self.assertEqual(1, len(sec_grps))

        # simple properties
        sec_grp = sec_grps.pop()
        self.assertEqual('abb53cc6636848218f46d01f22bf1060',
                         sec_grp[d['tenant_id']])
        self.assertEqual('default', sec_grp[d['name']])
        self.assertEqual('default', sec_grp[d['description']])
        self.assertEqual('9f3860a5-87b1-499c-bf93-5ca3ef247517',
                         sec_grp[d['id']])

    def test_execute(self):
        class NeutronClient(object):
            def __init__(self):
                self.testkey = None

            def connectNetwork(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        neutron_client = NeutronClient()
        self.driver.neutron = neutron_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('connectNetwork', api_args)

        self.assertEqual(expected_ans, neutron_client.testkey)


class TestDataSourceDriver(base.TestCase):

    def setUp(self):
        """Setup polling tests."""
        super(TestDataSourceDriver, self).setUp()
        cage = d6cage.d6Cage()

        # Create mock of Neutron client so we can control data
        mock_factory = mox.Mox()
        neutron_client = mock_factory.CreateMock(
            neutronclient.v2_0.client.Client)
        neutron_client.list_networks().InAnyOrder(1).AndReturn(network1)
        neutron_client.list_ports().InAnyOrder(1).AndReturn(port_response)
        neutron_client.list_routers().InAnyOrder(1).AndReturn(router_response)
        neutron_client.list_security_groups().InAnyOrder(1).AndReturn(
            security_group_response)
        neutron_client.list_networks().InAnyOrder(2).AndReturn(network2)
        neutron_client.list_ports().InAnyOrder(2).AndReturn(port_response)
        neutron_client.list_routers().InAnyOrder(2).AndReturn(router_response)
        neutron_client.list_security_groups().InAnyOrder(2).AndReturn(
            security_group_response)
        mock_factory.ReplayAll()

        # Create modules (without auto-polling)
        cage.loadModule("NeutronDriver",
                        helper.data_module_path("neutron_driver.py"))
        cage.loadModule("PolicyDriver", helper.policy_module_path())
        cage.createservice(name="policy", moduleName="PolicyDriver",
                           args={'d6cage': cage,
                                 'rootdir': helper.data_module_path(''),
                                 'log_actions_only': True})
        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        args['client'] = neutron_client
        cage.createservice(name="neutron", moduleName="NeutronDriver",
                           args=args)
        policy = cage.service_object('policy')
        policy.create_policy('neutron')
        policy.set_schema(
            'neutron', cage.service_object('neutron').get_schema())
        cage.service_object('neutron').neutron = neutron_client
        policy.debug_mode()

        # insert rule into policy to make testing easier.
        #   (Some of the IDs are auto-generated each time we convert)
        policy.insert(create_network_group('p'))

        # create some garbage data
        args = helper.datasource_openstack_args()
        driver = neutron_driver.NeutronDriver(args=args)
        network_key_to_index = driver.get_column_map(
            neutron_driver.NeutronDriver.NETWORKS)
        network_max_index = max(network_key_to_index.values())
        args1 = ['1'] * (network_max_index + 1)
        args2 = ['2'] * (network_max_index + 1)
        args1 = ",".join(args1)
        args2 = ",".join(args2)
        fake_networks = [
            'neutron:networks({})'.format(args1),
            'neutron:networks({})'.format(args2)]

        # answer to query above for network1
        datalog1 = (
            'p("240ff9df-df35-43ae-9df5-27fae87f2492") '
            'p("340ff9df-df35-43ae-9df5-27fae87f2492") '
            'p("440ff9df-df35-43ae-9df5-27fae87f2492")')

        # answer to query above for network2
        datalog2 = (
            'p("240ff9df-df35-43ae-9df5-27fae87f2492") '
            'p("640ff9df-df35-43ae-9df5-27fae87f2492") '
            'p("540ff9df-df35-43ae-9df5-27fae87f2492")')

        # return value
        self.info = {}
        self.info['cage'] = cage
        self.info['datalog1'] = datalog1
        self.info['datalog2'] = datalog2
        self.info['fake_networks'] = fake_networks

    def test_last_updated(self):
        """Test the last_updated timestamping."""
        cage = self.info['cage']
        neutron = cage.service_object('neutron')

        # initial value
        last_updated = neutron.get_last_updated_time()
        self.assertIsNone(last_updated)

        # first time updated
        before_time = datetime.datetime.now()
        neutron.poll()
        last_updated = neutron.get_last_updated_time()
        self.assertTrue(before_time < last_updated)
        self.assertTrue(last_updated < datetime.datetime.now())

        # second time updated
        before_time = datetime.datetime.now()
        neutron.poll()
        last_updated = neutron.get_last_updated_time()
        self.assertTrue(before_time < last_updated)
        self.assertTrue(last_updated < datetime.datetime.now())

    def test_subscribe_poll(self):
        """Test subscribing before polling.  The common case."""
        cage = self.info['cage']
        policy = cage.service_object('policy')
        neutron = cage.service_object('neutron')
        datalog1 = self.info['datalog1']
        datalog2 = self.info['datalog2']

        # subscribe
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.retry_check_subscribers(neutron, [(policy.name, 'networks')])

        # poll 1
        neutron.poll()
        helper.retry_check_db_equal(policy, 'p(x)', datalog1)

        # poll 2
        neutron.poll()
        helper.retry_check_db_equal(policy, 'p(x)', datalog2)

    def test_policy_initialization(self):
        """Test subscribing before polling.  The common case."""
        cage = self.info['cage']
        policy = cage.service_object('policy')
        neutron = cage.service_object('neutron')
        datalog1 = self.info['datalog1']
        fake_networks = self.info['fake_networks']

        # add garbage to policy
        for formula in fake_networks:
            policy.insert(formula)

        # subscribe
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.retry_check_subscribers(neutron, [(policy.name, 'networks')])

        # poll 1
        neutron.poll()
        helper.retry_check_db_equal(policy, 'p(x)', datalog1)

    def test_poll_subscribe(self):
        """Test polling before subscribing."""
        cage = self.info['cage']
        policy = cage.service_object('policy')
        neutron = cage.service_object('neutron')
        datalog1 = self.info['datalog1']
        datalog2 = self.info['datalog2']
        fake_networks = self.info['fake_networks']

        # add garbage to policy
        for formula in fake_networks:
            policy.insert(formula)

        # poll 1 and then subscribe; should still see first result
        neutron.poll()
        helper.retry_check_number_of_updates(neutron, 1)
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.retry_check_db_equal(policy, 'p(x)', datalog1)

        # poll 2
        neutron.poll()
        helper.retry_check_db_equal(policy, 'p(x)', datalog2)

    def test_double_poll_subscribe(self):
        """Test double polling before subscribing."""
        cage = self.info['cage']
        policy = cage.service_object('policy')
        neutron = cage.service_object('neutron')
        datalog2 = self.info['datalog2']

        # poll twice and then subscribe: should see 2nd result
        neutron.poll()
        helper.retry_check_number_of_updates(neutron, 1)
        neutron.poll()
        helper.retry_check_number_of_updates(neutron, 2)
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.retry_check_db_equal(policy, 'p(x)', datalog2)

    def test_policy_recovery(self):
        """Test policy crashing and recovering (sort of)."""
        cage = self.info['cage']
        policy = cage.service_object('policy')
        neutron = cage.service_object('neutron')
        datalog1 = self.info['datalog1']

        # get initial data
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.retry_check_subscribers(neutron, [(policy.name, 'networks')])
        neutron.poll()
        helper.retry_check_db_equal(policy, 'p(x)', datalog1)

        # clear out policy's neutron:networks data (to simulate crashing)
        policy.initialize_tables(['neutron:networks'], [])
        # subscribe again (without unsubscribing)
        policy.subscribe('neutron', 'networks', callback=policy.receive_data)
        helper.retry_check_db_equal(policy, 'p(x)', datalog1)


def create_network_group(tablename, full_neutron_tablename=None):
    driver = neutron_driver.NeutronDriver(
        args=helper.datasource_openstack_args())
    if full_neutron_tablename is None:
        full_neutron_tablename = 'neutron:networks'
    network_key_to_index = driver.get_column_map(
        neutron_driver.NeutronDriver.NETWORKS)
    network_id_index = network_key_to_index['id']
    network_max_index = max(network_key_to_index.values())
    network_args = ['x' + str(i) for i in range(0, network_max_index + 1)]
    formula = compile.parse1(
        '{}({}) :- {}({})'.format(
            tablename,
            'x' + str(network_id_index),
            full_neutron_tablename,
            ",".join(network_args)))
    return formula


def create_networkXnetwork_group(tablename):
    """Return rule of the form:

    TABLENAME(x,y) :- neutron:network(...,x,...),neutron:network(...,y,...)
    """
    driver = neutron_driver.NeutronDriver(
        args=helper.datasource_openstack_args())
    network_key_to_index = driver.get_column_map(
        neutron_driver.NeutronDriver.NETWORKS)
    network_id_index = network_key_to_index['id']
    network_max_index = max(network_key_to_index.values())
    net1_args = ['x' + str(i) for i in range(0, network_max_index + 1)]
    net2_args = ['y' + str(i) for i in range(0, network_max_index + 1)]
    formula = compile.parse1(
        '{}({},{}) :- neutron:networks({}), neutron2:networks({})'.format(
            tablename,
            'x' + str(network_id_index),
            'y' + str(network_id_index),
            ",".join(net1_args),
            ",".join(net2_args)))
    return formula

# Only diffs between network1 and network2 are the IDs
network1 = {'networks': [
    {'status': 'ACTIVE',
     'subnets': ['4cef03d0-1d02-40bb-8c99-2f442aac6ab0'],
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
     'subnets': ['4cef03d0-1d02-40bb-8c99-2f442aac6ab0'],
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
     'subnets': ['4cef03d0-1d02-40bb-8c99-2f442aac6ab0'],
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
     'subnets': ['4cef03d0-1d02-40bb-8c99-2f442aac6ab0'],
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
     'subnets': ['4cef03d0-1d02-40bb-8c99-2f442aac6ab0'],
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
     'subnets': ['4cef03d0-1d02-40bb-8c99-2f442aac6ab0'],
     'name': 'test-network',
     'provider:physical_network': None,
     'admin_state_up': True,
     'tenant_id': '570fe78a1dc54cffa053bd802984ede2',
     'provider:network_type': 'gre',
     'router:external': False,
     'shared': False,
     'id': '640ff9df-df35-43ae-9df5-27fae87f2492',
     'provider:segmentation_id': 4}]}


# Sample responses from neutron-client, after parsing
network_response = {
    'networks':
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

port_response = {
    "ports":
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
               "ip_address": "90.0.0.1"},
              {"subnet_id": "5cef03d0-1d02-40bb-8c99-2f442aac6ab0",
               "ip_address": "100.0.0.1"}],
          "id": "0a2ce569-85a8-45ec-abb3-0d4b34ff69ba",
          "security_groups": ['15ea0516-11ec-46e9-9e8e-7d1b6e3d7523',
                              '25ea0516-11ec-46e9-9e8e-7d1b6e3d7523'],
          "device_id": "864e4acf-bf8e-4664-8cf7-ad5daa95681e"}]}

router_response = {
    'routers':
        [{u'status': u'ACTIVE',
          u'external_gateway_info':
            {u'network_id': u'a821b8d3-af1f-4d79-9b8e-3da9674338ae',
             u'enable_snat': True},
          u'name': u'router1',
          u'admin_state_up': True,
          u'tenant_id': u'abb53cc6636848218f46d01f22bf1060',
          u'routes': [],
          u'id': u'4598c424-d608-4366-9beb-139adbd7cff5'}]}

security_group_response = {
    'security_groups':
        [{u'tenant_id': u'abb53cc6636848218f46d01f22bf1060',
          u'name': u'default',
          u'description': u'default',
          u'security_group_rules': [
              {u'remote_group_id': u'9f3860a5-87b1-499c-bf93-5ca3ef247517',
               u'direction': u'ingress',
               u'remote_ip_prefix': None,
               u'protocol': None,
               u'tenant_id': u'abb53cc6636848218f46d01f22bf1060',
               u'port_range_max': None,
               u'security_group_id': u'9f3860a5-87b1-499c-bf93-5ca3ef247517',
               u'port_range_min': None,
               u'ethertype': u'IPv6',
               u'id': u'15ea0516-11ec-46e9-9e8e-7d1b6e3d7523'},
              {u'remote_group_id': None, u'direction': u'egress',
               u'remote_ip_prefix': None,
               u'protocol': None,
               u'tenant_id': u'abb53cc6636848218f46d01f22bf1060',
               u'port_range_max': None,
               u'security_group_id': u'9f3860a5-87b1-499c-bf93-5ca3ef247517',
               u'port_range_min': None,
               u'ethertype': u'IPv6',
               u'id': u'5a2a86c5-c63c-4f17-b625-f9cd809c8331'},
              {u'remote_group_id': u'9f3860a5-87b1-499c-bf93-5ca3ef247517',
               u'direction': u'ingress',
               u'remote_ip_prefix': None,
               u'protocol': None,
               u'tenant_id': u'abb53cc6636848218f46d01f22bf1060',
               u'port_range_max': None,
               u'security_group_id': u'9f3860a5-87b1-499c-bf93-5ca3ef247517',
               u'port_range_min': None,
               u'ethertype': u'IPv4',
               u'id': u'6499e807-af24-4486-9fa4-4897da2eb1dd'},
              {u'remote_group_id': None,
               u'direction': u'egress',
               u'remote_ip_prefix': None,
               u'protocol': None,
               u'tenant_id': u'abb53cc6636848218f46d01f22bf1060',
               u'port_range_max': None,
               u'security_group_id': u'9f3860a5-87b1-499c-bf93-5ca3ef247517',
               u'port_range_min': None,
               u'ethertype': u'IPv4',
               u'id': u'bb03ea93-b984-48de-8752-d816f1c4fbfa'}],
          u'id': u'9f3860a5-87b1-499c-bf93-5ca3ef247517'}]}
