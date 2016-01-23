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

import mock
import novaclient

from congress.datalog import compile
from congress.datasources import nova_driver
from congress.dse import d6cage
from congress import exception
from congress.tests import base
from congress.tests.datasources import fakes
from congress.tests import helper


class TestNovaDriver(base.TestCase):

    def setUp(self):
        super(TestNovaDriver, self).setUp()
        nova_client = mock.MagicMock()
        self.nova = fakes.NovaFakeClient()
        with mock.patch.object(novaclient.client.Client, '__init__',
                               return_value=nova_client):
            self.driver = nova_driver.NovaDriver(
                name='nova',
                args=helper.datasource_openstack_args())

    def test_driver_called(self):
        self.assertIsNotNone(self.driver.nova_client)

    def test_servers(self):
        servers_raw = self.nova.servers.list(detailed=True)
        self.driver._translate_servers(servers_raw)
        server_tuples = self.driver.state[self.driver.SERVERS]

        self.assertEqual(3, len(server_tuples))
        #  tuple = (s.id, s.name, s.hostId, s.status, s.tenant_id,
        #   s.user_id, image, flavor)
        for t in server_tuples:
            id = t[0]
            name = t[1]
            host_id = t[2]
            status = t[3]
            tenant_id = t[4]
            user_id = t[5]
            image_id = t[6]
            flavor_id = t[7]
            zone = t[8]
            host_name = t[9]
            self.assertIn(id, [1234, 5678, 9012])
            # see congress.datasources.tests.unit.fakes for actual values
            if id == 1234:
                self.assertEqual("sample-server", name)
                self.assertEqual("e4d909c290d0fb1ca068ffaddf22cbd0", host_id)
                self.assertEqual("BUILD", status)
                self.assertEqual("33ea0494-2bdf-4382-a445-9068997430b9",
                                 user_id)
                self.assertEqual("50e14867-7c64-4ec9-be8d-ed2470ca1d24",
                                 tenant_id)
                self.assertEqual(2, image_id)
                self.assertEqual(1, flavor_id)
                self.assertEqual('default', zone)
                self.assertEqual('host1', host_name)

            elif id == 5678:
                self.assertEqual("sample-server2", name)
                self.assertEqual("9e107d9d372bb6826bd81d3542a419d6", host_id)
                self.assertEqual("ACTIVE", status)
                self.assertEqual("33ea0494-2bdf-4382-a445-9068997430b9",
                                 user_id)
                self.assertEqual("50e14867-7c64-4ec9-be8d-ed2470ca1d24",
                                 tenant_id)
                self.assertEqual(2, image_id)
                self.assertEqual(1, flavor_id)
                self.assertEqual('None', zone)
                self.assertEqual('None', host_name)

            elif id == 9012:
                self.assertEqual("sample-server3", name)
                self.assertEqual("9e107d9d372bb6826bd81d3542a419d6", host_id)
                self.assertEqual("ACTIVE", status)
                self.assertEqual("33ea0494-2bdf-4382-a445-9068997430b9",
                                 user_id)
                self.assertEqual("50e14867-7c64-4ec9-be8d-ed2470ca1d24",
                                 tenant_id)
                self.assertEqual(2, image_id)
                self.assertEqual(1, flavor_id)
                self.assertEqual('foo', zone)
                self.assertEqual('host2', host_name)

    def test_flavors(self):
        flavor_raw = self.nova.flavors.list(detailed=True)
        self.driver._translate_flavors(flavor_raw)

        flavor_tuples = self.driver.state[self.driver.FLAVORS]

        self.assertEqual(4, len(flavor_tuples))
        # "id", "name", "vcpus", "ram", "disk", "ephemeral",
        #            "rxtx_factor")
        for f in flavor_tuples:
            id = f[0]
            name = f[1]
            vcpus = f[2]
            ram = f[3]
            disk = f[4]
            ephemeral = f[5]
            rxtx_factor = f[6]

            self.assertIn(id, [1, 2, 3, 4])

            # {'id': 1, 'name': '256 MB Server', 'ram': 256, 'disk': 10,
            # 'vcpus' : 1, 'OS-FLV-EXT-DATA:ephemeral': 10,
            # 'os-flavor-access:is_public': True, 'rxtx_factor' : 1.0,
            # 'links': {}},
            if id == 1:
                self.assertEqual('256 MB Server', name)
                self.assertEqual(256, ram)
                self.assertEqual(10, disk)
                self.assertEqual(1, vcpus)
                self.assertEqual(10, ephemeral)
                self.assertEqual(1.0, rxtx_factor)
            # {'id': 2, 'name': '512 MB Server', 'ram': 512, 'disk': 20,
            #  'vcpus' :2, 'OS-FLV-EXT-DATA:ephemeral': 20,
            #  'os-flavor-access:is_public': False, 'rxtx_factor' : 1.0,
            #  'links': {}},
            elif id == 2:
                self.assertEqual('512 MB Server', name)
                self.assertEqual(512, ram)
                self.assertEqual(20, disk)
                self.assertEqual(2, vcpus)
                self.assertEqual(20, ephemeral)
                self.assertEqual(1.0, rxtx_factor)
            # {'id': 3, 'name': '128 MB Server', 'ram': 128, 'disk': 0,
            #  'vcpus' : 4, 'OS-FLV-EXT-DATA:ephemeral': 0,
            #  'os-flavor-access:is_public': True, 'rxtx_factor' : 3.0,
            #  'links': {}}
            elif id == 3:
                self.assertEqual('128 MB Server', name)
                self.assertEqual(128, ram)
                self.assertEqual(0, disk)
                self.assertEqual(4, vcpus)
                self.assertEqual(0, ephemeral)
                self.assertEqual(3.0, rxtx_factor)
            # {'id': 4, 'name': '1024 MB Server', 'ram': 1024, 'disk': 10,
            #  'vcpus' : 3, 'OS-FLV-EXT-DATA:ephemeral': 10,
            #  'os-flavor-access:is_public': True, 'rxtx_factor' : 2.0,
            #  'links': {}},
            elif id == 4:
                self.assertEqual('1024 MB Server', name)
                self.assertEqual(1024, ram)
                self.assertEqual(10, disk)
                self.assertEqual(3, vcpus)
                self.assertEqual(10, ephemeral)
                self.assertEqual(2.0, rxtx_factor)
                self.assertEqual('1024 MB Server', name)

    def test_hosts(self):
        host_list = self.nova.hosts.list()
        self.driver._translate_hosts(host_list)
        host_tuples = self.driver.state[self.driver.HOSTS]
        self.assertEqual(2, len(host_tuples))
        # {'hosts':
        #      [{'host_name': 'host1',
        #        'service': 'nova-compute',
        #        'zone': zone},
        #       {'host_name': 'host2',
        #        'service': 'nova-cert',
        #        'zone': zone}]}
        for host in host_tuples:
            host_name = host[0]
            service = host[1]
            zone = host[2]

            if host_name == 'host1':
                self.assertEqual('nova-compute', service)
                self.assertEqual('nova1', str(zone))
            elif host_name == 'host2':
                self.assertEqual('nova-cert', service)
                self.assertEqual('nova1', str(zone))

    def test_services(self):
        service_list = self.nova.services.list()
        self.driver._translate_services(service_list)
        expected_ret = {
            1: [1, 'nova-compute', 'nova', 'nova1', 'enabled', 'up',
                '2015-07-28T08:28:37.000000', 'None'],
            2: [2, 'nova-schedule', 'nova', 'nova1', 'disabled', 'up',
                '2015-07-28T08:28:38.000000', 'daily maintenance']
        }
        service_tuples = self.driver.state[self.driver.SERVICES]

        self.assertEqual(2, len(service_tuples))

        for s in service_tuples:
            map(self.assertEqual, expected_ret[s[0]], s)

    def test_availability_zones(self):
        az_list = self.nova.availability_zones.list()
        self.driver._translate_availability_zones(az_list)
        expected_ret = {
            'AZ1': ['AZ1', 'available'],
            'AZ2': ['AZ2', 'not available']
        }
        az_tuples = self.driver.state[self.driver.AVAILABILITY_ZONES]

        self.assertEqual(2, len(az_tuples))

        for az in az_tuples:
            map(self.assertEqual, expected_ret[az[0]], az)

    def test_communication(self):
        """Test for communication.

        Test the module's ability to be loaded into the DSE
        by checking its ability to communicate on the message bus.
        """
        cage = d6cage.d6Cage()

        # Create modules.
        # Turn off polling so we don't need to deal with real data.
        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        cage.loadModule("NovaDriver",
                        helper.data_module_path("nova_driver.py"))
        cage.loadModule("PolicyDriver", helper.policy_module_path())
        cage.createservice(name="policy", moduleName="PolicyDriver",
                           args={'d6cage': cage,
                                 'rootdir': helper.data_module_path(''),
                                 'log_actions_only': True})
        cage.createservice(name="nova", moduleName="NovaDriver", args=args)

        # Check that data gets sent from nova to policy as expected
        nova = cage.service_object('nova')
        policy = cage.service_object('policy')
        policy.debug_mode()
        policy.create_policy('nova')
        policy.set_schema('nova', compile.Schema({'server': (1,)}))
        policy.subscribe('nova', 'server',
                         callback=policy.receive_data)

        # publishing is slightly convoluted b/c deltas are computed
        #  automatically.  (Not just convenient--useful so that DSE
        #  properly handles the initial state problem.)
        # Need to set nova.state and nova.prior_state and then publish
        #  anything.

        # publish server(1), server(2), server(3)
        helper.retry_check_subscribers(nova, [(policy.name, 'server')])
        nova.prior_state = {}
        nova.state['server'] = set([(1,), (2,), (3,)])
        nova.publish('server', None)
        helper.retry_check_db_equal(
            policy, 'nova:server(x)',
            'nova:server(1) nova:server(2) nova:server(3)')

        # publish server(1), server(4), server(5)
        nova.prior_state['server'] = nova.state['server']
        nova.state['server'] = set([(1,), (4,), (5,)])
        nova.publish('server', None)
        helper.retry_check_db_equal(
            policy, 'nova:server(x)',
            'nova:server(1) nova:server(4) nova:server(5)')

    # TODO(thinrichs): test that Nova's polling functionality
    #   works properly.  Or perhaps could bundle this into the
    #   tests above if we check self.state results.
    #   See Neutron's test_polling

    def test_execute(self):
        class NovaClient(object):
            def __init__(self):
                self.testkey = None

            def connectNetwork(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        nova_client = NovaClient()
        self.driver.nova_client = nova_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('connectNetwork', api_args)

        self.assertEqual(expected_ans, nova_client.testkey)

    def test_execute_servers_set_meta(self):
        class server(object):
            def __init__(self):
                self.testkey = None

            def set_meta(self, server=None, metadata=None):
                self.testkey = 'server=%s, metadata=%s' % (server, metadata)

        class NovaClient(object):
            def __init__(self):
                self.servers = server()

        nova_client = NovaClient()
        self.driver.nova_client = nova_client
        expected_ans = "server=1, metadata={'meta-key1': 'meta-value1'}"

        action_args = {'positional': ['1', 'meta-key1', 'meta-value1']}
        self.driver.execute('servers_set_meta', action_args)

        self.assertEqual(expected_ans, nova_client.servers.testkey)

    def test_execute_with_non_executable_method(self):
        action_args = {'positional': ['1', 'meta-key1', 'meta-value1']}
        self.assertRaises(exception.CongressException,
                          self.driver.execute,
                          'get_nova_credentials_v2', action_args)
