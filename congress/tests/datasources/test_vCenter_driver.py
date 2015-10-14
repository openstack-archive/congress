# Copyright (c) 2014 Marist SDN Innovation lab Joint with Plexxi Inc.
# All rights reserved.
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

import mock

from congress.datasources import vCenter_driver
from congress.tests import base
from congress.tests.datasources import vCenter_fakes
from congress.tests import helper


class TestvCenterDriver(base.TestCase):
    def setUp(self):
        super(TestvCenterDriver, self).setUp()
        args = helper.datasource_openstack_args()
        args['max_hosts'] = 999
        args['max_vms'] = 999
        self.driver = vCenter_driver.VCenterDriver(args=args,
                                                   session="Testing")
        self.mock_rawhosts = {}
        h1_obj = {}
        h1_obj['value'] = 'Host1'
        mock_host1 = vCenter_fakes.MockvCenterHost(h1_obj)
        h1_uuid = vCenter_fakes.MockProperty(
            '9912c61d-79e0-4423-bb43-d79926e0d1f0',
            'hardware.systemInfo.uuid')
        h1_name = vCenter_fakes.MockProperty('Host1', 'name')
        h1_DNS_obj = vCenter_fakes.MockDNSInfo(['10.11.12.1', '10.11.12.2'])
        h1_DNS = vCenter_fakes.MockProperty(h1_DNS_obj,
                                            'config.network.dnsConfig.address')
        h1_pnic1 = {}
        h1_pnic1['uuid'] = '9912c61d-79e0-4423-bb43-d79926e0d1f1'
        h1_pnic1['mac'] = '3F-0B-DD-8A-F3-B9'
        h1_pnic1['device'] = 'vmnic1'
        h1_pnic1['spec'] = {}
        h1_pnic1['spec']['ip'] = {}
        h1_pnic1['spec']['ip']['ipAddress'] = '10.11.13.1'
        h1_pnic1['spec']['ip']['subnetMask'] = '255.255.255.0'
        h1_pnic2 = {}
        h1_pnic2['uuid'] = '9912c61d-79e0-4423-bb43-d79926e0d1f2'
        h1_pnic2['mac'] = '3F-0B-DD-8A-F3-BA'
        h1_pnic2['device'] = 'vmnic2'
        h1_pnic2['spec'] = {}
        h1_pnic2['spec']['ip'] = {}
        h1_pnic2['spec']['ip']['ipAddress'] = '10.11.13.2'
        h1_pnic2['spec']['ip']['subnetMask'] = '255.255.255.0'
        h1_pnic_list = (h1_pnic1, h1_pnic2)
        h1_pnic_obj = vCenter_fakes.MockNicContainer(h1_pnic_list)
        h1_pnics = vCenter_fakes.MockProperty(h1_pnic_obj,
                                              'config.network.pnic')
        h1_vnic1 = {}
        h1_vnic1['uuid'] = '9912c61d-79e0-4423-bb43-d79926e0d1f3'
        h1_vnic1['device'] = 'vmk1'
        h1_vnic1['portgroup'] = 'Management'
        h1_vnic1['spec'] = {}
        h1_vnic1['spec']['mac'] = '3F-0B-DD-8A-F3-BB'
        h1_vnic1['spec']['ip'] = {}
        h1_vnic1['spec']['ip']['ipAddress'] = '10.11.13.3'
        h1_vnic1['spec']['ip']['subnetMask'] = '255.255.255.0'
        h1_vnic2 = {}
        h1_vnic2['uuid'] = '9912c61d-79e0-4423-bb43-d79926e0d1f4'
        h1_vnic2['device'] = 'vmk2'
        h1_vnic2['portgroup'] = 'Public'
        h1_vnic2['spec'] = {}
        h1_vnic2['spec']['mac'] = '3F-0B-DD-8A-F3-BC'
        h1_vnic2['spec']['ip'] = {}
        h1_vnic2['spec']['ip']['ipAddress'] = '10.11.13.4'
        h1_vnic2['spec']['ip']['subnetMask'] = '255.255.255.0'
        h1_vnic_list = [h1_vnic1, h1_vnic2]
        h1_vnic_obj = vCenter_fakes.MockNicContainer(h1_vnic_list)
        h1_vnics = vCenter_fakes.MockProperty(h1_vnic_obj,
                                              'config.network.vnic')
        mock_host1['propSet'] = [h1_uuid, h1_name, h1_DNS, h1_pnics, h1_vnics]
        h2_obj = {}
        h2_obj['value'] = 'Host2'
        mock_host2 = vCenter_fakes.MockvCenterHost(h2_obj)
        h2_uuid = vCenter_fakes.MockProperty(
            '9912c61d-79e0-4423-bb43-d79926e0d1f5',
            'hardware.systemInfo.uuid')
        h2_name = vCenter_fakes.MockProperty('Host2', 'name')
        h2_DNS_obj = vCenter_fakes.MockDNSInfo(['10.11.12.1', '10.11.12.2'])
        h2_DNS = vCenter_fakes.MockProperty(h2_DNS_obj,
                                            'config.network.dnsConfig.address')
        h2_pnic1 = {}
        h2_pnic1['uuid'] = '9912c61d-79e0-4423-bb43-d79926e0d1f6'
        h2_pnic1['mac'] = '3F-0B-DD-8A-F3-BD'
        h2_pnic1['device'] = 'vmnic1'
        h2_pnic1['spec'] = {}
        h2_pnic1['spec']['ip'] = {}
        h2_pnic1['spec']['ip']['ipAddress'] = '10.11.14.1'
        h2_pnic1['spec']['ip']['subnetMask'] = '255.255.255.0'
        h2_pnic2 = {}
        h2_pnic2['uuid'] = '9912c61d-79e0-4423-bb43-d79926e0d1f7'
        h2_pnic2['mac'] = '3F-0B-DD-8A-F3-BE'
        h2_pnic2['device'] = 'vmnic2'
        h2_pnic2['spec'] = {}
        h2_pnic2['spec']['ip'] = {}
        h2_pnic2['spec']['ip']['ipAddress'] = '10.11.14.2'
        h2_pnic2['spec']['ip']['subnetMask'] = '255.255.255.0'
        h2_pnic_list = (h2_pnic1, h2_pnic2)
        h2_pnic_obj = vCenter_fakes.MockNicContainer(h2_pnic_list)
        h2_pnics = vCenter_fakes.MockProperty(h2_pnic_obj,
                                              'config.network.pnic')
        h2_vnic1 = {}
        h2_vnic1['uuid'] = '9912c61d-79e0-4423-bb43-d79926e0d1f8'
        h2_vnic1['device'] = 'vmk1'
        h2_vnic1['portgroup'] = 'Management'
        h2_vnic1['spec'] = {}
        h2_vnic1['spec']['mac'] = '3F-0B-DD-8A-F3-BF'
        h2_vnic1['spec']['ip'] = {}
        h2_vnic1['spec']['ip']['ipAddress'] = '10.11.14.3'
        h2_vnic1['spec']['ip']['subnetMask'] = '255.255.255.0'
        h2_vnic2 = {}
        h2_vnic2['uuid'] = '9912c61d-79e0-4423-bb43-d79926e0d1f9'
        h2_vnic2['device'] = 'vmk2'
        h2_vnic2['portgroup'] = 'Public'
        h2_vnic2['spec'] = {}
        h2_vnic2['spec']['mac'] = '3F-0B-DD-8A-F3-C0'
        h2_vnic2['spec']['ip'] = {}
        h2_vnic2['spec']['ip']['ipAddress'] = '10.11.14.4'
        h2_vnic2['spec']['ip']['subnetMask'] = '255.255.255.0'
        h2_vnic_list = [h2_vnic1, h2_vnic2]
        h2_vnic_obj = vCenter_fakes.MockNicContainer(h2_vnic_list)
        h2_vnics = vCenter_fakes.MockProperty(h2_vnic_obj,
                                              'config.network.vnic')
        mock_host2['propSet'] = [h2_uuid, h2_name, h2_DNS, h2_pnics, h2_vnics]
        mock_hostlist = [mock_host1, mock_host2]
        self.mock_rawhosts['objects'] = mock_hostlist
        self.mock_rawvms = {}
        mock_vm1 = {}
        mock_vm1['value'] = 'VM1'
        vm1_name = vCenter_fakes.MockProperty('VM1', 'name')
        vm1_uuid = vCenter_fakes.MockProperty(
            '9912c61d-79e0-4423-bb43-d79926e0d200',
            'config.uuid')
        vm1_annotation = vCenter_fakes.MockProperty('First VM',
                                                    'config.annotation')
        vm1_path = vCenter_fakes.MockProperty('[Datastore] VM1/VM1.vmtx',
                                              'summary.config.vmPathName')
        vm1_memSize = vCenter_fakes.MockProperty(4096,
                                                 'summary.config.memorySizeMB')
        vm1_status = vCenter_fakes.MockProperty('green',
                                                'summary.overallStatus')
        host1_referance = {}
        host1_referance['value'] = 'Host1'
        vm1_host = vCenter_fakes.MockProperty(host1_referance, 'runtime.host')
        vm1_quickstats = {}
        vm1_quickstats['guestMemoryUsage'] = 245
        vm1_quickstats['overallCpuDemand'] = 216
        vm1_quickstats['overallCpuUsage'] = 192
        vm1_quickstats_property = vCenter_fakes.MockProperty(
            vm1_quickstats, 'summary.quickStats')
        vm1_storage = {}
        vm1_storage['committed'] = 25294964803
        vm1_storage['uncommitted'] = 32812040762
        vm1_storage_property = vCenter_fakes.MockProperty(vm1_storage,
                                                          'summary.storage')
        mock_vm1['propSet'] = [vm1_name, vm1_uuid, vm1_annotation, vm1_path,
                               vm1_memSize, vm1_status, vm1_host,
                               vm1_quickstats_property, vm1_storage_property]
        mock_vm2 = {}
        mock_vm2['value'] = 'VM2'
        vm2_name = vCenter_fakes.MockProperty('VM2', 'name')
        vm2_uuid = vCenter_fakes.MockProperty(
            '9912c61d-79e0-4423-bb43-d79926e0d201',
            'config.uuid')
        vm2_annotation = vCenter_fakes.MockProperty('Second VM',
                                                    'config.annotation')
        vm2_path = vCenter_fakes.MockProperty('[Datastore] VM2/VM2.vmtx',
                                              'summary.config.vmPathName')
        vm2_memSize = vCenter_fakes.MockProperty(4096,
                                                 'summary.config.memorySizeMB')
        vm2_status = vCenter_fakes.MockProperty('green',
                                                'summary.overallStatus')
        host2_referance = {}
        host2_referance['value'] = 'Host2'
        vm2_host = vCenter_fakes.MockProperty(host2_referance, 'runtime.host')
        vm2_quickstats = {}
        vm2_quickstats['guestMemoryUsage'] = 0
        vm2_quickstats['overallCpuDemand'] = 0
        vm2_quickstats['overallCpuUsage'] = 0
        vm2_quickstats_property = vCenter_fakes.MockProperty(
            vm1_quickstats,
            'summary.quickStats')
        vm2_storage = {}
        vm2_storage['committed'] = 6271694636
        vm2_storage['uncommitted'] = 34110177822
        vm2_storage_property = vCenter_fakes.MockProperty(vm2_storage,
                                                          'summary.storage')
        mock_vm2['propSet'] = [vm2_name, vm2_uuid, vm2_annotation, vm2_path,
                               vm2_memSize, vm2_status, vm2_host,
                               vm2_quickstats_property, vm2_storage_property]
        mock_vmlist = [mock_vm1, mock_vm2]
        self.mock_rawvms['objects'] = mock_vmlist

    def test_translators(self):
        with mock.patch.object(self.driver, '_get_hosts_from_vcenter',
                               return_value=self.mock_rawhosts):
            hosts, pnics, vnics = self.driver._get_hosts_and_nics()
        self.driver._translate_hosts(hosts)
        self.driver._translate_pnics(pnics)
        self.driver._translate_vnics(vnics)
        expected_hosts = set([('Host1',
                               '9912c61d-79e0-4423-bb43-d79926e0d1f0',
                               '895f69d340dac8cd4c9550e745703c77'),
                              ('Host2',
                               '9912c61d-79e0-4423-bb43-d79926e0d1f5',
                               '895f69d340dac8cd4c9550e745703c77')])
        self.assertEqual(expected_hosts, self.driver.state['hosts'])
        expected_DNS = set([('895f69d340dac8cd4c9550e745703c77',
                             '10.11.12.1'),
                            ('895f69d340dac8cd4c9550e745703c77',
                             '10.11.12.2')])
        self.assertEqual(expected_DNS, self.driver.state['host.DNS_IPs'])
        expected_pnics = set([('9912c61d-79e0-4423-bb43-d79926e0d1f0',
                               'vmnic1',
                               '3F-0B-DD-8A-F3-B9',
                               '10.11.13.1',
                               '255.255.255.0'),
                              ('9912c61d-79e0-4423-bb43-d79926e0d1f0',
                               'vmnic2',
                               '3F-0B-DD-8A-F3-BA',
                               '10.11.13.2',
                               '255.255.255.0'),
                              ('9912c61d-79e0-4423-bb43-d79926e0d1f5',
                               'vmnic1',
                               '3F-0B-DD-8A-F3-BD',
                               '10.11.14.1',
                               '255.255.255.0'),
                              ('9912c61d-79e0-4423-bb43-d79926e0d1f5',
                               'vmnic2',
                               '3F-0B-DD-8A-F3-BE',
                               '10.11.14.2',
                               '255.255.255.0')])
        self.assertEqual(expected_pnics, self.driver.state['host.PNICs'])
        expected_vnics = set([('9912c61d-79e0-4423-bb43-d79926e0d1f0',
                               'vmk1',
                               '3F-0B-DD-8A-F3-BB',
                               'Management',
                               '10.11.13.3',
                               '255.255.255.0'),
                              ('9912c61d-79e0-4423-bb43-d79926e0d1f0',
                               'vmk2',
                               '3F-0B-DD-8A-F3-BC',
                               'Public',
                               '10.11.13.4',
                               '255.255.255.0'),
                              ('9912c61d-79e0-4423-bb43-d79926e0d1f5',
                               'vmk1',
                               '3F-0B-DD-8A-F3-BF',
                               'Management',
                               '10.11.14.3',
                               '255.255.255.0'),
                              ('9912c61d-79e0-4423-bb43-d79926e0d1f5',
                               'vmk2',
                               '3F-0B-DD-8A-F3-C0',
                               'Public',
                               '10.11.14.4',
                               '255.255.255.0')])
        self.assertEqual(expected_vnics, self.driver.state['host.VNICs'])
        with mock.patch.object(self.driver, '_get_vms_from_vcenter',
                               return_value=self.mock_rawvms):
            vms = self.driver._get_vms()
        self.driver._translate_vms(vms)
        expected_vms = set([('VM1',
                             '9912c61d-79e0-4423-bb43-d79926e0d200',
                             '9912c61d-79e0-4423-bb43-d79926e0d1f0',
                             '[Datastore] VM1/VM1.vmtx',
                             'green',
                             216,
                             192,
                             4096,
                             245,
                             25294964803,
                             32812040762,
                             'First VM'),
                            ('VM2',
                             '9912c61d-79e0-4423-bb43-d79926e0d201',
                             '9912c61d-79e0-4423-bb43-d79926e0d1f5',
                             '[Datastore] VM2/VM2.vmtx',
                             'green',
                             216,
                             192,
                             4096,
                             245,
                             6271694636,
                             34110177822,
                             'Second VM')])
        self.assertEqual(expected_vms, self.driver.state['vms'])

    def test_execute(self):
        class vCenterClient(object):
            def __init__(self):
                self.testkey = None

            def connectNetwork(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        vcenter_client = vCenterClient()
        self.driver.session = vcenter_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('connectNetwork', api_args)

        self.assertEqual(expected_ans, vcenter_client.testkey)
