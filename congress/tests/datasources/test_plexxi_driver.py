#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from congress.datasources import plexxi_driver
from congress.tests import base
from congress.tests.datasources import plexxi_fakes
from congress.tests import helper


class TestPlexxiDriver(base.TestCase):
    def setUp(self):
        super(TestPlexxiDriver, self).setUp()
        args = helper.datasource_openstack_args()
        args['unique_names'] = 'False'
        session = plexxi_fakes.MockCoreSession()
        self.driver = plexxi_driver.PlexxiDriver(args=args, session=session)
        self.driver.exchange = True
        vnic1 = plexxi_fakes.MockNIC(
            uuid='f318ac0a-9255-4af0-8a41-6f3fbc06c8aa',
            mac='B8:ED:0A:4D:82:91')
        vnic2 = plexxi_fakes.MockNIC(
            uuid='f318ac0a-9255-4af0-8a41-6f3fbc06c8a2',
            mac='B8:ED:0A:4D:82:99')
        pnic1 = plexxi_fakes.MockNIC(
            uuid='f318ac0a-9255-4af0-8a41-6f3fbc06c8ab',
            mac='B8:ED:0A:4D:82:92')
        pnic2 = plexxi_fakes.MockNIC(
            uuid='f318ac0a-9255-4af0-8a41-6f3fbc06c8ac',
            mac='B8:ED:0A:4D:82:93')
        host1 = plexxi_fakes.MockHost('eed4ebfc-25e5-4a65-9f37-b70b8e8219d3',
                                      'mock1',
                                      1,
                                      [pnic1])
        vm1 = plexxi_fakes.MockVM('2ca924f6-90aa-4ce8-a986-f62f8f64d14b',
                                  '192.168.90.2',
                                  'namevm',
                                  host1,
                                  [vnic1])
        host1.addvm(vm1)
        switch1 = plexxi_fakes.MockSwitch(
            '12da13e3-ecb2-4c26-98a0-26cb07f9c33d',
            '192.168.90.3',
            'switch1',
            'HEALTHY',
            [pnic2])
        affinity = plexxi_fakes.MockAffinity(
            'fd487ecf-5279-4d3c-9378-7fb214f5dd5a', 'Testfinnity')
        affinity2 = plexxi_fakes.MockAffinity(
            'fd487ecf-5279-4d3c-9378-7fb214f5dd5b', 'Testfinnity2')
        vswitch = plexxi_fakes.MockVSwitch(
            'fd487ecf-5279-4d3c-9378-7fb214f5dd5c',
            [host1],
            [vnic2])
        link1 = plexxi_fakes.MockNetworkLink(
            'fd487ecf-5279-4d3c-9378-7fb214f5dd5f',
            'Link1',
            host1,
            switch1)
        port = plexxi_fakes.MockPort('fd487ecf-5279-4d3c-9378-7fb214f5dd5d',
                                     'Port1',
                                     [link1])
        port2 = plexxi_fakes.MockPort('fd487ecf-5279-4d3c-9378-7fb214f5dd5e',
                                      'Port2',
                                      None)

        self.hosts = [host1]
        self.pswitches = [switch1]
        self.affinites = [affinity, affinity2]
        self.vswitches = [vswitch]
        self.vms = [vm1]
        self.ports = [port, port2]

    def test_translate_hosts(self):
        self.driver._translate_hosts(self.hosts)
        ExpectedHosts = [('eed4ebfc-25e5-4a65-9f37-b70b8e8219d3',
                          'mock1',
                          1,
                          1)]
        self.assertEqual(ExpectedHosts, self.driver.hosts)
        ExpectedHost_Macs = [('eed4ebfc-25e5-4a65-9f37-b70b8e8219d3',
                             'B8:ED:0A:4D:82:92')]
        self.assertEqual(ExpectedHost_Macs, self.driver.mac_list)
        ExpectedGuests = [('eed4ebfc-25e5-4a65-9f37-b70b8e8219d3',
                          '2ca924f6-90aa-4ce8-a986-f62f8f64d14b')]
        self.assertEqual(ExpectedGuests, self.driver.guest_list)

    def test_translate_pswitches(self):
        self.driver._translate_pswitches(self.pswitches)
        ExpectedpSwitches = [('12da13e3-ecb2-4c26-98a0-26cb07f9c33d',
                              '192.168.90.3',
                              'HEALTHY')]
        self.assertEqual(self.driver.plexxi_switches, ExpectedpSwitches)
        ExpectedPSmacs = [('12da13e3-ecb2-4c26-98a0-26cb07f9c33d',
                           'B8:ED:0A:4D:82:93')]
        self.assertEqual(ExpectedPSmacs, self.driver.ps_macs)

    def test_translate_affinites(self):
        self.driver._translate_affinites(self.affinites)
        ExpectedAffinities = [('fd487ecf-5279-4d3c-9378-7fb214f5dd5a',
                              'Testfinnity'),
                              ('fd487ecf-5279-4d3c-9378-7fb214f5dd5b',
                              'Testfinnity2')]

        self.assertEqual(ExpectedAffinities, self.driver.affinities)

    def test_translate_vswitches(self):
        self.driver._translate_vswitches(self.vswitches)
        ExpectedvSwitches = [('fd487ecf-5279-4d3c-9378-7fb214f5dd5c',
                              1,
                              1)]
        self.assertEqual(ExpectedvSwitches, self.driver.vswitches)
        ExpectedvSwitch_macs = [('fd487ecf-5279-4d3c-9378-7fb214f5dd5c',
                                 'B8:ED:0A:4D:82:99')]
        self.assertEqual(ExpectedvSwitch_macs, self.driver.vswitch_macs)
        ExpectedvSwitch_hosts = [('fd487ecf-5279-4d3c-9378-7fb214f5dd5c',
                                  'eed4ebfc-25e5-4a65-9f37-b70b8e8219d3')]

        self.assertEqual(ExpectedvSwitch_hosts, self.driver.vswitch_hosts)

    def test_translate_vms(self):
        self.driver._translate_vms(self.vms)
        ExpectedVMs = [('2ca924f6-90aa-4ce8-a986-f62f8f64d14b',
                        'namevm',
                        'eed4ebfc-25e5-4a65-9f37-b70b8e8219d3',
                        '192.168.90.2',
                        1)]

        self.assertEqual(ExpectedVMs, self.driver.vms)
        Expectedvm_macs = [('2ca924f6-90aa-4ce8-a986-f62f8f64d14b',
                            'B8:ED:0A:4D:82:91')]
        self.assertEqual(Expectedvm_macs, self.driver.vm_macs)

    def test_translate_ports(self):
        self.driver._translate_ports(self.ports)
        ExpectedPorts = [('fd487ecf-5279-4d3c-9378-7fb214f5dd5d',
                          'Port1'),
                         ('fd487ecf-5279-4d3c-9378-7fb214f5dd5e',
                          'Port2')]
        self.assertEqual(ExpectedPorts, self.driver.ports)
        ExpectedLinks = [('fd487ecf-5279-4d3c-9378-7fb214f5dd5f',
                          'Link1',
                          'fd487ecf-5279-4d3c-9378-7fb214f5dd5d',
                          '12da13e3-ecb2-4c26-98a0-26cb07f9c33d',
                          'switch1',
                          'eed4ebfc-25e5-4a65-9f37-b70b8e8219d3',
                          'mock1')]
        self.assertEqual(ExpectedLinks, self.driver.network_links)
