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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import mock

from congress.datasources import neutronv2_qos_driver
from congress.tests import base
from congress.tests import helper


class TestNeutronV2QosDriver(base.TestCase):

    def setUp(self):
        super(TestNeutronV2QosDriver, self).setUp()
        self.neutron_client_p = mock.patch(
            "neutronclient.v2_0.client.Client")
        self.neutron_client_p.start()

        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        args['client'] = mock.MagicMock()
        self.driver = neutronv2_qos_driver.NeutronV2QosDriver(args=args)

        self.mock_ports = {'ports': [
            {u'admin_state_up': True,
             u'allowed_address_pairs': [],
             u'binding:host_id': None,
             u'binding:vif_details': {u'port_filter': True},
             u'binding:vif_type': u'ovs',
             u'binding:vnic_type': u'normal',
             u'device_id': u'f42dc4f1-f371-48cc-95be-cf1b97112ab8',
             u'device_owner': u'network:router_gateway',
             u'fixed_ips': [
                 {u'ip_address': u'1.1.1.2',
                  u'subnet_id': u'10d20df9-e8ba-4756-ba30-d573ceb2e99a'}],
             u'id': u'04627c85-3553-436c-a7c5-0a64f5b87bb9',
             u'mac_address': u'fa:16:3e:f3:19:e5',
             u'name': u'',
             u'network_id': u'ecdea1af-7197-43c8-b3b0-34d90f72a2a8',
             u'port_security_enabled': False,
             u'security_groups': [],
             u'status': u'DOWN',
             u'tenant_id': u''},
            {u'admin_state_up': True,
             u'allowed_address_pairs': [],
             u'binding:host_id': None,
             u'binding:vif_details': {u'port_filter': True},
             u'binding:vif_type': u'ovs',
             u'binding:vnic_type': u'normal',
             u'device_id': u'f42dc4f1-f371-48cc-95be-cf1b97112ab8',
             u'device_owner': u'network:router_interface',
             u'fixed_ips': [
                 {u'ip_address': u'169.254.169.253',
                  u'subnet_id': u'aa9ad4f7-baf0-4a41-85c3-1cc8a3066db6'}],
             u'id': u'87f8933a-9582-48d8-ad16-9abf6e545002',
             u'mac_address': u'fa:16:3e:b7:78:e8',
             u'name': u'',
             u'network_id': u'6743ff85-2cfd-48a7-9d3f-472cd418783e',
             u'port_security_enabled': False,
             u'security_groups': [],
             u'status': u'DOWN',
             u'tenant_id': u''},
            {u'admin_state_up': True,
             u'allowed_address_pairs': [],
             u'binding:host_id': None,
             u'binding:vif_details': {u'port_filter': True},
             u'binding:vif_type': u'ovs',
             u'binding:vnic_type': u'normal',
             u'device_id': u'f42dc4f1-f371-48cc-95be-cf1b97112ab8',
             u'device_owner': u'network:router_interface',
             u'fixed_ips': [
                 {u'ip_address': u'10.0.0.1',
                  u'subnet_id': u'3c0eb3a3-4d16-4b1b-b327-44417182d0bb'}],
             u'id': u'c58c3246-6c2e-490a-b4d9-3b8d5191b465',
             u'mac_address': u'fa:16:3e:08:31:6e',
             u'name': u'',
             u'network_id': u'63ce8fbb-12e9-4ecd-9b56-1bbf8b51217d',
             u'port_security_enabled': False,
             u'security_groups': [],
             u'status': u'DOWN',
             u'tenant_id': u'feee0a965cc34274917fb753623dd57d'},
            {u'admin_state_up': True,
             u'allowed_address_pairs': [],
             u'binding:host_id': None,
             u'binding:vif_details': {u'port_filter': True},
             u'binding:vif_type': u'ovs',
             u'binding:vnic_type': u'normal',
             u'device_id': u'',
             u'device_owner': u'',
             u'fixed_ips': [
                 {u'ip_address': u'10.0.0.2',
                  u'subnet_id': u'3c0eb3a3-4d16-4b1b-b327-44417182d0bb'}],
             u'id': u'eb50003b-a081-4533-92aa-1cbd97f526a8',
             u'mac_address': u'fa:16:3e:af:56:fa',
             u'name': u'',
             u'network_id': u'63ce8fbb-12e9-4ecd-9b56-1bbf8b51217d',
             u'port_security_enabled': True,
             u'security_groups': [u'e0239062-4243-4798-865f-7055f03786d6'],
             u'qos_policies': [u'be50b732-4508-4a94-9c3c-8dc4b96a2b43'],
             u'status': u'DOWN',
             u'tenant_id': u'feee0a965cc34274917fb753623dd57d'}]}

        self.mock_qos_policies = {'policies': [
            {u'name': u'ysm',
             u'rules': [
                 {u'max_kbps': 100,
                  u'direction': u'egress',
                  u'qos_policy_id': u'be50b732-4508-4a94-9c3c-8dc4b96a2b43',
                  u'type': u'bandwidth_limit',
                  u'id': u'9daaa87a-5441-49ef-8f25-2810d37c3a60',
                  u'max_burst_kbps': 500},
                 {u'dscp_mark': 10,
                  u'type': u'dscp_marking',
                  u'id': u'6be91937-b9ec-4209-a430-0c2694df1095',
                  u'qos_policy_id': u'be50b732-4508-4a94-9c3c-8dc4b96a2b43'},
                 {u'id': u'015f3dc8-7d3e-4598-8996-0597328c4db5',
                  u'direction': u'egress',
                  u'type': u'minimum_bandwidth',
                  u'qos_policy_id': u'be50b732-4508-4a94-9c3c-8dc4b96a2b43',
                  u'min_kbps': 100}],
             u'tenant_id': u'feee0a965cc34274917fb753623dd57d',
             u'is_default': False,
             u'shared': False,
             u'project_id': u'feee0a965cc34274917fb753623dd57d',
             u'id': u'be50b732-4508-4a94-9c3c-8dc4b96a2b43',
             u'description': u''}]}

        self.expected_state = {
            'ports': set([(u'04627c85-3553-436c-a7c5-0a64f5b87bb9',),
                          (u'87f8933a-9582-48d8-ad16-9abf6e545002',),
                          (u'c58c3246-6c2e-490a-b4d9-3b8d5191b465',),
                          (u'eb50003b-a081-4533-92aa-1cbd97f526a8',)]),
            'qos_policy_port_bindings':
                set([('eb50003b-a081-4533-92aa-1cbd97f526a8',
                      'be50b732-4508-4a94-9c3c-8dc4b96a2b43')]),
            'policies':
                set([('be50b732-4508-4a94-9c3c-8dc4b96a2b43',
                      'feee0a965cc34274917fb753623dd57d',
                      'ysm',
                      '',
                      False)]),
            'rules':
                set([('be50b732-4508-4a94-9c3c-8dc4b96a2b43',
                      '015f3dc8-7d3e-4598-8996-0597328c4db5',
                      100,
                      'egress',
                      'minimum_bandwidth',
                      None,
                      None,
                      None),
                     ('be50b732-4508-4a94-9c3c-8dc4b96a2b43',
                      '6be91937-b9ec-4209-a430-0c2694df1095',
                      None,
                      None,
                      'dscp_marking',
                      10,
                      None,
                      None),
                     ('be50b732-4508-4a94-9c3c-8dc4b96a2b43',
                      '9daaa87a-5441-49ef-8f25-2810d37c3a60',
                      None,
                      'egress',
                      'bandwidth_limit',
                      None,
                      500,
                      100)])}

    def test_update_from_datasource(self):
        with base.nested(
            mock.patch.object(self.driver.neutron,
                              "list_ports",
                              return_value=self.mock_ports),
            mock.patch.object(self.driver.neutron,
                              "list_qos_policies",
                              return_value=self.mock_qos_policies)):
            self.driver.update_from_datasource()
            self.assertEqual(self.expected_state, self.driver.state)
