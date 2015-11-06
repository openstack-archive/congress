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
import mock

from congress.datasources import neutronv2_driver
from congress.tests import base
from congress.tests import helper


class TestNeutronV2Driver(base.TestCase):

    def setUp(self):
        super(TestNeutronV2Driver, self).setUp()
        self.neutron_client_p = mock.patch(
            "neutronclient.v2_0.client.Client")
        self.neutron_client_p.start()

        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        args['client'] = mock.MagicMock()
        self.driver = neutronv2_driver.NeutronV2Driver(args=args)

        self.mock_networks = {'networks': [
            {u'admin_state_up': True,
             u'id': u'63ce8fbb-12e9-4ecd-9b56-1bbf8b51217d',
             u'name': u'private',
             u'router:external': False,
             u'shared': False,
             u'status': u'ACTIVE',
             u'subnets': [u'3c0eb3a3-4d16-4b1b-b327-44417182d0bb'],
             u'tenant_id': u'feee0a965cc34274917fb753623dd57d'},
            {u'admin_state_up': True,
             u'id': u'ecdea1af-7197-43c8-b3b0-34d90f72a2a8',
             u'name': u'public',
             u'router:external': True,
             u'shared': False,
             u'status': u'ACTIVE',
             u'subnets': [u'10d20df9-e8ba-4756-ba30-d573ceb2e99a'],
             u'tenant_id': u'feee0a965cc34274917fb753623dd57d'}]}

        self.mock_floatingips = {'floatingips': [
            {u"router_id": "d23abc8d-2991-4a55-ba98-2aaea84cc72f",
             u"tenant_id": "4969c491a3c74ee4af974e6d800c62de",
             u"floating_network_id": "376da547-b977-4cfe-9cba-275c80debf57",
             u"fixed_ip_address": "10.0.0.3",
             u"floating_ip_address": "172.24.4.228",
             u"port_id": "ce705c24-c1ef-408a-bda3-7bbd946164ab",
             u"id": "2f245a7b-796b-4f26-9cf9-9e82d248fda7",
             u"status": "ACTIVE"},
            {u"router_id": None,
             u"tenant_id": "4969c491a3c74ee4af974e6d800c62de",
             u"floating_network_id": "376da547-b977-4cfe-9cba-275c80debf57",
             u"fixed_ip_address": None,
             u"floating_ip_address": "172.24.4.227",
             u"port_id": None,
             u"id": "61cea855-49cb-4846-997d-801b70c71bdd",
             u"status": "DOWN"}]}

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
             u'status': u'DOWN',
             u'tenant_id': u'feee0a965cc34274917fb753623dd57d'}]}

        self.mock_subnets = {'subnets': [
            {u'allocation_pools': [{u'end': u'1.1.1.254',
                                    u'start': u'1.1.1.2'}],
             u'cidr': u'1.1.1.0/24',
             u'dns_nameservers': [],
             u'enable_dhcp': True,
             u'gateway_ip': u'1.1.1.1',
             u'host_routes': [],
             u'id': u'10d20df9-e8ba-4756-ba30-d573ceb2e99a',
             u'ip_version': 4,
             u'ipv6_address_mode': None,
             u'ipv6_ra_mode': None,
             u'name': u'',
             u'network_id': u'ecdea1af-7197-43c8-b3b0-34d90f72a2a8',
             u'tenant_id': u'feee0a965cc34274917fb753623dd57d'},
            {u'allocation_pools': [{u'end': u'10.0.0.254',
                                    u'start': u'10.0.0.2'}],
             u'cidr': u'10.0.0.0/24',
             u'dns_nameservers': [u'8.8.8.8'],
             u'enable_dhcp': True,
             u'gateway_ip': u'10.0.0.1',
             u'host_routes': [{u'destination': u'10.10.0.2/32',
                               u'nexthop': u'10.0.0.1'}],
             u'id': u'3c0eb3a3-4d16-4b1b-b327-44417182d0bb',
             u'ip_version': 4,
             u'ipv6_address_mode': None,
             u'ipv6_ra_mode': None,
             u'name': u'private-subnet',
             u'network_id': u'63ce8fbb-12e9-4ecd-9b56-1bbf8b51217d',
             u'tenant_id': u'feee0a965cc34274917fb753623dd57d'},
            {u'allocation_pools': [{u'end': u'169.254.169.254',
                                    u'start': u'169.254.169.254'}],
             u'cidr': u'169.254.169.252/30',
             u'dns_nameservers': [],
             u'enable_dhcp': True,
             u'gateway_ip': u'169.254.169.253',
             u'host_routes': [],
             u'id': u'aa9ad4f7-baf0-4a41-85c3-1cc8a3066db6',
             u'ip_version': 4,
             u'ipv6_address_mode': None,
             u'ipv6_ra_mode': None,
             u'name': u'meta-f42dc4f1-f371-48cc-95be-cf1b97112ab8',
             u'network_id': u'6743ff85-2cfd-48a7-9d3f-472cd418783e',
             u'tenant_id': u''}]}

        self.mock_routers = {'routers': [
            {u'admin_state_up': True,
             u'distributed': False,
             u'external_gateway_info': {
                 u'enable_snat': True,
                 u'external_fixed_ips': [
                     {u'ip_address': u'1.1.1.2',
                      u'subnet_id': u'10d20df9-e8ba-4756-ba30-d573ceb2e99a'}],
                 u'network_id': u'ecdea1af-7197-43c8-b3b0-34d90f72a2a8'},
             u'id': u'f42dc4f1-f371-48cc-95be-cf1b97112ab8',
             u'name': u'myrouter',
             u'routes': [],
             u'status': u'DOWN',
             u'tenant_id': u'feee0a965cc34274917fb753623dd57d'}]}

        self.mock_security_groups = {'security_groups': [
            {u'description': u'Default security group',
             u'id': u'a268fc32-1a59-4154-9a7c-f453ef92560c',
             u'name': u'default',
             u'security_group_rules': [
                 {u'direction': u'egress',
                  u'ethertype': u'IPv4',
                  u'id': u'1d943e83-e4e6-472a-9655-f74eb22f3668',
                  u'port_range_max': None,
                  u'port_range_min': None,
                  u'protocol': None,
                  u'remote_group_id': None,
                  u'remote_ip_prefix': None,
                  u'security_group_id':
                    u'a268fc32-1a59-4154-9a7c-f453ef92560c',
                  u'tenant_id': u''},
                 {u'direction': u'ingress',
                  u'ethertype': u'IPv4',
                  u'id': u'30be5ee1-5b0a-4929-aca5-0c25f1c6b733',
                  u'port_range_max': None,
                  u'port_range_min': None,
                  u'protocol': None,
                  u'remote_group_id': u'a268fc32-1a59-4154-9a7c-f453ef92560c',
                  u'remote_ip_prefix': None,
                  u'security_group_id':
                     u'a268fc32-1a59-4154-9a7c-f453ef92560c',
                  u'tenant_id': u''},
                 {u'direction': u'ingress',
                  u'ethertype': u'IPv6',
                  u'id': u'639995b8-c3ac-44a3-a4f3-c74f9172ad54',
                  u'port_range_max': None,
                  u'port_range_min': None,
                  u'protocol': None,
                  u'remote_group_id': u'a268fc32-1a59-4154-9a7c-f453ef92560c',
                  u'remote_ip_prefix': None,
                  u'security_group_id':
                     u'a268fc32-1a59-4154-9a7c-f453ef92560c',
                  u'tenant_id': u''},
                 {u'direction': u'egress',
                  u'ethertype': u'IPv6',
                  u'id': u'ed7fd9f6-e390-448a-9f5f-8dd4659282f7',
                  u'port_range_max': None,
                  u'port_range_min': None,
                  u'protocol': None,
                  u'remote_group_id': None,
                  u'remote_ip_prefix': None,
                  u'security_group_id':
                     u'a268fc32-1a59-4154-9a7c-f453ef92560c',
                  u'tenant_id': u''}],
             u'tenant_id': u''},
            {u'description': u'Default security group',
             u'id': u'e0239062-4243-4798-865f-7055f03786d6',
             u'name': u'default',
             u'security_group_rules': [
                 {u'direction': u'ingress',
                  u'ethertype': u'IPv6',
                  u'id': u'8a81fecc-ecc7-48ca-bccc-195799667e23',
                  u'port_range_max': None,
                  u'port_range_min': None,
                  u'protocol': None,
                  u'remote_group_id': u'e0239062-4243-4798-865f-7055f03786d6',
                  u'remote_ip_prefix': None,
                  u'security_group_id':
                     u'e0239062-4243-4798-865f-7055f03786d6',
                  u'tenant_id': u'feee0a965cc34274917fb753623dd57d'},
                 {u'direction': u'ingress',
                  u'ethertype': u'IPv4',
                  u'id': u'8f4d9e99-1fe8-4816-9f07-c4ecddea9427',
                  u'port_range_max': None,
                  u'port_range_min': None,
                  u'protocol': None,
                  u'remote_group_id': u'e0239062-4243-4798-865f-7055f03786d6',
                  u'remote_ip_prefix': None,
                  u'security_group_id':
                     u'e0239062-4243-4798-865f-7055f03786d6',
                  u'tenant_id': u'feee0a965cc34274917fb753623dd57d'},
                 {u'direction': u'egress',
                  u'ethertype': u'IPv4',
                  u'id': u'e70cf243-3389-4f80-82dc-92a3ec1f2d2a',
                  u'port_range_max': None,
                  u'port_range_min': None,
                  u'protocol': None,
                  u'remote_group_id': None,
                  u'remote_ip_prefix': None,
                  u'security_group_id':
                     u'e0239062-4243-4798-865f-7055f03786d6',
                  u'tenant_id': u'feee0a965cc34274917fb753623dd57d'},
                 {u'direction': u'egress',
                  u'ethertype': u'IPv6',
                  u'id': u'eca1df0f-b222-4208-8f96-8a8024fd6834',
                  u'port_range_max': None,
                  u'port_range_min': None,
                  u'protocol': None,
                  u'remote_group_id': None,
                  u'remote_ip_prefix': None,
                  u'security_group_id':
                     u'e0239062-4243-4798-865f-7055f03786d6',
                  u'tenant_id': u'feee0a965cc34274917fb753623dd57d'}],
                u'tenant_id': u'feee0a965cc34274917fb753623dd57d'}]}

        self.expected_state = {
            'subnets': set([
                ('3c0eb3a3-4d16-4b1b-b327-44417182d0bb',
                 'feee0a965cc34274917fb753623dd57d', 'private-subnet',
                 '63ce8fbb-12e9-4ecd-9b56-1bbf8b51217d', 4, '10.0.0.0/24',
                 '10.0.0.1', 'True', 'None', 'None'),
                ('aa9ad4f7-baf0-4a41-85c3-1cc8a3066db6', '',
                 'meta-f42dc4f1-f371-48cc-95be-cf1b97112ab8',
                 '6743ff85-2cfd-48a7-9d3f-472cd418783e', 4,
                 '169.254.169.252/30',
                 '169.254.169.253', 'True', 'None', 'None'),
                ('10d20df9-e8ba-4756-ba30-d573ceb2e99a',
                 'feee0a965cc34274917fb753623dd57d', '',
                 'ecdea1af-7197-43c8-b3b0-34d90f72a2a8', 4, '1.1.1.0/24',
                 '1.1.1.1', 'True', 'None', 'None')]),
            'floating_ips': set([
                ("2f245a7b-796b-4f26-9cf9-9e82d248fda7",
                 "d23abc8d-2991-4a55-ba98-2aaea84cc72f",
                 "4969c491a3c74ee4af974e6d800c62de",
                 "376da547-b977-4cfe-9cba-275c80debf57", "10.0.0.3",
                 "172.24.4.228", "ce705c24-c1ef-408a-bda3-7bbd946164ab",
                 "ACTIVE"),
                ("61cea855-49cb-4846-997d-801b70c71bdd", 'None',
                 "4969c491a3c74ee4af974e6d800c62de",
                 "376da547-b977-4cfe-9cba-275c80debf57", 'None',
                 "172.24.4.227", 'None', "DOWN")]),
            'routers':
                set([('f42dc4f1-f371-48cc-95be-cf1b97112ab8',
                      'feee0a965cc34274917fb753623dd57d', 'DOWN', 'True',
                      'myrouter', 'False')]),
            'dns_nameservers':
                set([('3c0eb3a3-4d16-4b1b-b327-44417182d0bb', '8.8.8.8')]),
            'security_group_rules':
                set([('e0239062-4243-4798-865f-7055f03786d6',
                      'e70cf243-3389-4f80-82dc-92a3ec1f2d2a',
                      'feee0a965cc34274917fb753623dd57d', 'None', 'egress',
                      'IPv4', 'None', 'None', 'None', 'None'),
                     ('a268fc32-1a59-4154-9a7c-f453ef92560c',
                      'ed7fd9f6-e390-448a-9f5f-8dd4659282f7', '', 'None',
                      'egress', 'IPv6', 'None', 'None', 'None', 'None'),
                     ('a268fc32-1a59-4154-9a7c-f453ef92560c',
                      '1d943e83-e4e6-472a-9655-f74eb22f3668', '', 'None',
                      'egress', 'IPv4', 'None', 'None', 'None', 'None'),
                     ('a268fc32-1a59-4154-9a7c-f453ef92560c',
                      '30be5ee1-5b0a-4929-aca5-0c25f1c6b733', '',
                      'a268fc32-1a59-4154-9a7c-f453ef92560c', 'ingress',
                      'IPv4', 'None', 'None', 'None', 'None'),
                     ('e0239062-4243-4798-865f-7055f03786d6',
                      '8a81fecc-ecc7-48ca-bccc-195799667e23',
                      'feee0a965cc34274917fb753623dd57d',
                      'e0239062-4243-4798-865f-7055f03786d6', 'ingress',
                      'IPv6', 'None', 'None', 'None', 'None'),
                     ('a268fc32-1a59-4154-9a7c-f453ef92560c',
                      '639995b8-c3ac-44a3-a4f3-c74f9172ad54', '',
                      'a268fc32-1a59-4154-9a7c-f453ef92560c', 'ingress',
                      'IPv6', 'None', 'None', 'None', 'None'),
                     ('e0239062-4243-4798-865f-7055f03786d6',
                      '8f4d9e99-1fe8-4816-9f07-c4ecddea9427',
                      'feee0a965cc34274917fb753623dd57d',
                      'e0239062-4243-4798-865f-7055f03786d6',
                      'ingress', 'IPv4', 'None', 'None', 'None', 'None'),
                     ('e0239062-4243-4798-865f-7055f03786d6',
                      'eca1df0f-b222-4208-8f96-8a8024fd6834',
                      'feee0a965cc34274917fb753623dd57d', 'None', 'egress',
                      'IPv6', 'None', 'None', 'None', 'None')]),
                'ports':
                    set([('c58c3246-6c2e-490a-b4d9-3b8d5191b465',
                          'feee0a965cc34274917fb753623dd57d', '',
                          '63ce8fbb-12e9-4ecd-9b56-1bbf8b51217d',
                          'fa:16:3e:08:31:6e', 'True', 'DOWN',
                          'f42dc4f1-f371-48cc-95be-cf1b97112ab8',
                          'network:router_interface'),
                         ('87f8933a-9582-48d8-ad16-9abf6e545002', '', '',
                          '6743ff85-2cfd-48a7-9d3f-472cd418783e',
                          'fa:16:3e:b7:78:e8', 'True', 'DOWN',
                          'f42dc4f1-f371-48cc-95be-cf1b97112ab8',
                          'network:router_interface'),
                         ('eb50003b-a081-4533-92aa-1cbd97f526a8',
                          'feee0a965cc34274917fb753623dd57d', '',
                          '63ce8fbb-12e9-4ecd-9b56-1bbf8b51217d',
                          'fa:16:3e:af:56:fa', 'True', 'DOWN', '', ''),
                         ('04627c85-3553-436c-a7c5-0a64f5b87bb9', '', '',
                          'ecdea1af-7197-43c8-b3b0-34d90f72a2a8',
                          'fa:16:3e:f3:19:e5', 'True', 'DOWN',
                          'f42dc4f1-f371-48cc-95be-cf1b97112ab8',
                          'network:router_gateway')]),
                'allocation_pools':
                    set([('10d20df9-e8ba-4756-ba30-d573ceb2e99a', '1.1.1.2',
                          '1.1.1.254'),
                         ('3c0eb3a3-4d16-4b1b-b327-44417182d0bb', '10.0.0.2',
                          '10.0.0.254'),
                         ('aa9ad4f7-baf0-4a41-85c3-1cc8a3066db6',
                          '169.254.169.254', '169.254.169.254')]),
                'host_routes':
                    set([('3c0eb3a3-4d16-4b1b-b327-44417182d0bb',
                          '10.10.0.2/32', '10.0.0.1')]),
                'security_group_port_bindings':
                    set([('eb50003b-a081-4533-92aa-1cbd97f526a8',
                          'e0239062-4243-4798-865f-7055f03786d6')]),
                'external_gateway_infos':
                    set([('f42dc4f1-f371-48cc-95be-cf1b97112ab8',
                          'ecdea1af-7197-43c8-b3b0-34d90f72a2a8', 'True')]),
                'fixed_ips':
                    set([('c58c3246-6c2e-490a-b4d9-3b8d5191b465', '10.0.0.1',
                          '3c0eb3a3-4d16-4b1b-b327-44417182d0bb'),
                         ('eb50003b-a081-4533-92aa-1cbd97f526a8', '10.0.0.2',
                          '3c0eb3a3-4d16-4b1b-b327-44417182d0bb'),
                         ('87f8933a-9582-48d8-ad16-9abf6e545002',
                          '169.254.169.253',
                          'aa9ad4f7-baf0-4a41-85c3-1cc8a3066db6'),
                         ('04627c85-3553-436c-a7c5-0a64f5b87bb9', '1.1.1.2',
                          '10d20df9-e8ba-4756-ba30-d573ceb2e99a')]),
                'networks':
                    set([('ecdea1af-7197-43c8-b3b0-34d90f72a2a8',
                          'feee0a965cc34274917fb753623dd57d', 'public',
                          'ACTIVE', 'True', 'False'),
                         ('63ce8fbb-12e9-4ecd-9b56-1bbf8b51217d',
                          'feee0a965cc34274917fb753623dd57d', 'private',
                          'ACTIVE', 'True', 'False')]),
                'security_groups':
                    set([('e0239062-4243-4798-865f-7055f03786d6',
                          'feee0a965cc34274917fb753623dd57d', 'default',
                          'Default security group'),
                         ('a268fc32-1a59-4154-9a7c-f453ef92560c', '',
                          'default', 'Default security group')]),
                'external_fixed_ips':
                    set([('f42dc4f1-f371-48cc-95be-cf1b97112ab8',
                          '10d20df9-e8ba-4756-ba30-d573ceb2e99a', '1.1.1.2')])}

    def test_update_from_datasource(self):
        with base.nested(
            mock.patch.object(self.driver.neutron,
                              "list_networks",
                              return_value=self.mock_networks),
            mock.patch.object(self.driver.neutron,
                              "list_ports",
                              return_value=self.mock_ports),
            mock.patch.object(self.driver.neutron,
                              "list_subnets",
                              return_value=self.mock_subnets),
            mock.patch.object(self.driver.neutron,
                              "list_routers",
                              return_value=self.mock_routers),
            mock.patch.object(self.driver.neutron,
                              "list_security_groups",
                              return_value=self.mock_security_groups),
            mock.patch.object(self.driver.neutron,
                              "list_floatingips",
                              return_value=self.mock_floatingips),
            ) as (list_networks, list_ports, list_subnets, list_routers,
                  list_security_groups, list_floatingips):
            self.driver.update_from_datasource()
            self.assertEqual(self.expected_state, self.driver.state)

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
