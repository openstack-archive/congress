# Copyright (c) 2018 NEC, Inc. All rights reserved.
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

from congress.datasources import tacker_driver
from congress.tests import base
from congress.tests import helper


class TestTackerDriver(base.TestCase):

    def setUp(self):
        super(TestTackerDriver, self).setUp()
        self.tacker_client_p = mock.patch("tackerclient.v1_0.client.Client")
        self.tacker_client_p.start()

        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        args['client'] = mock.MagicMock()

        self.driver = tacker_driver.TackerDriver(args=args)

        self.mock_vnfds = {"vnfds": [
            {"template_source": "onboarded",
             "service_types": ["vnfd"],
             "description": "Demo example",
             "tenant_id": "a9d8315792db4007b4ef2495ad88757a",
             "created_at": "2018-09-11 06:12:03",
             "updated_at": None,
             "attributes": {"vnfd": "description: Demo example\nmetadata: {template_name: sample-tosca-vnfd}\ntopology_template:\n  node_templates:\n    CP1:\n      properties: {anti_spoofing_protection: false, management: true, order: 0}\n      requirements:\n      - virtualLink: {node: VL1}\n      - virtualBinding: {node: VDU1}\n      type: tosca.nodes.nfv.CP.Tacker\n    CP2:\n      properties: {anti_spoofing_protection: false, order: 1}\n      requirements:\n      - virtualLink: {node: VL2}\n      - virtualBinding: {node: VDU1}\n      type: tosca.nodes.nfv.CP.Tacker\n    CP3:\n      properties: {anti_spoofing_protection: false, order: 2}\n      requirements:\n      - virtualLink: {node: VL3}\n      - virtualBinding: {node: VDU1}\n      type: tosca.nodes.nfv.CP.Tacker\n    VDU1:\n      capabilities:\n        nfv_compute:\n          properties: {disk_size: 1 GB, mem_size: 512 MB, num_cpus: 1}\n      properties: {availability_zone: nova, config: 'param0: key1\n\n          param1: key2\n\n          ', image: cirros-0.4.0-x86_64-disk, mgmt_driver: noop}\n      type: tosca.nodes.nfv.VDU.Tacker\n    VL1:\n      properties: {network_name: net_mgmt, vendor: Tacker}\n      type: tosca.nodes.nfv.VL\n    VL2:\n      properties: {network_name: net0, vendor: Tacker}\n      type: tosca.nodes.nfv.VL\n    VL3:\n      properties: {network_name: net1, vendor: Tacker}\n      type: tosca.nodes.nfv.VL\ntosca_definitions_version: tosca_simple_profile_for_nfv_1_0_0\n"},  # noqa
             "id": "b9a9f468-7966-422f-a6ff-b1931eea6af5",
             "name": "vnfd-hello"}]}

        self.mock_vnfs = {'vnfs': [
            {'status': 'ACTIVE',
             'description': 'sample-tosca-vnfd-scaling',
             'vnfd_id': 'b9a9f468-7966-422f-a6ff-b1931eea6af5',
             'tenant_id': '49577ebc4eaa4d30abc9ecfd9bf23757',
             'created_at': '2018-10-12 05:47:03',
             'updated_at': None,
             'instance_id': '0be0b3b3-2da4-4e27-99a0-3bbf89fb1e4c',
             'mgmt_url': '{"VDU1": "192.168.120.22", "VDU2": "192.168.120.1"}',
             'vim_id': '856057ac-97d9-4eb7-881e-4530af24b187',
             'placement_attr': {'vim_name': 'hellovim'},
             'error_reason': None,
             'attributes': {'heat_template': "heat_template_version: 2013-05-23\ndescription: 'sample-tosca-vnfd-scaling\n\n  '\nparameters: {}\nresources:\n  CP1:\n    type: OS::Neutron::Port\n    properties: {port_security_enabled: false, network: net_mgmt}\n  CP2:\n    type: OS::Neutron::Port\n    properties: {port_security_enabled: false, network: net_mgmt}\n  VDU1:\n    type: OS::Nova::Server\n    properties:\n      user_data_format: SOFTWARE_CONFIG\n      availability_zone: nova\n      image: cirros-0.4.0-x86_64-disk\n      flavor: m1.tiny\n      networks:\n      - port: {get_resource: CP1}\n      config_drive: false\n  VDU2:\n    type: OS::Nova::Server\n    properties:\n      user_data_format: SOFTWARE_CONFIG\n      availability_zone: nova\n      image: cirros-0.4.0-x86_64-disk\n      flavor: m1.tiny\n      networks:\n      - port: {get_resource: CP2}\n      config_drive: false\noutputs:\n  mgmt_ip-VDU2:\n    value:\n      get_attr: [CP2, fixed_ips, 0, ip_address]\n  mgmt_ip-VDU1:\n    value:\n      get_attr: [CP1, fixed_ips, 0, ip_address]\n"},  # noqa
             'id': 'd40ebb81-4cd2-4854-8665-77114d7c25e5',
             'name': 'sampleScalevnf123'}]}

        self.expected_state = {
            'vnfds': {('b9a9f468-7966-422f-a6ff-b1931eea6af5',
                       'vnfd-hello', 'Demo example', 'onboarded',
                       'a9d8315792db4007b4ef2495ad88757a',
                       '2018-09-11 06:12:03', None)},
            'vnfs': {('d40ebb81-4cd2-4854-8665-77114d7c25e5',
                      'sampleScalevnf123', 'ACTIVE',
                      'sample-tosca-vnfd-scaling',
                      'b9a9f468-7966-422f-a6ff-b1931eea6af5',
                      '856057ac-97d9-4eb7-881e-4530af24b187',
                      '49577ebc4eaa4d30abc9ecfd9bf23757',
                      '0be0b3b3-2da4-4e27-99a0-3bbf89fb1e4c',
                      '2018-10-12 05:47:03', None, None)},
            'vnfs.instances': {
                ('d40ebb81-4cd2-4854-8665-77114d7c25e5', 'VDU2',
                 '192.168.120.1'),
                ('d40ebb81-4cd2-4854-8665-77114d7c25e5', 'VDU1',
                 '192.168.120.22')}
        }

    def test_update_from_datasource(self):
        with base.nested(
            mock.patch.object(self.driver.tacker_client,
                              "list_vnfds",
                              return_value=self.mock_vnfds),
            mock.patch.object(self.driver.tacker_client,
                              "list_vnfs",
                              return_value=self.mock_vnfs)
                ) as (list_vnfds, list_vnfs,):
            self.driver.update_from_datasource()
            self.assertEqual(self.expected_state, self.driver.state)
