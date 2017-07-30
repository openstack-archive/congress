# Copyright 2014 OpenStack Foundation
# All Rights Reserved.
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
import time

from tempest import clients
from tempest.common import utils as tempest_utils
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions
from tempest import test

from congress_tempest_tests.tests.scenario import helper
from congress_tempest_tests.tests.scenario import manager_congress

CONF = config.CONF

RULE_TYPE = "bandwidth_limit_rules"


class TestNeutronV2QosDriver(manager_congress.ScenarioPolicyBase):

    DATASOURCE_NAME = 'neutronv2_qos'

    @classmethod
    def skip_checks(cls):
        super(TestNeutronV2QosDriver, cls).skip_checks()
        # TODO(qos): check whether QoS extension is enabled
        if not (CONF.network.project_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either project_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

        if not CONF.service_available.neutron:
            skip_msg = ("%s skipped as neutron is not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)

        if not tempest_utils.is_extension_enabled('qos', 'network'):
            skip_msg = ("%s skipped as neutron QoS extension is not available"
                        % cls.__name__)
            raise cls.skipException(skip_msg)

    def setUp(self):
        super(TestNeutronV2QosDriver, self).setUp()
        self.qos_rules = []
        self.qos_policies = []

        self.os_primary = clients.Manager(
            self.os_admin.auth_provider.credentials)

        body = {"config": {"username": CONF.auth.admin_username,
                           "tenant_name": CONF.auth.admin_project_name,
                           "password": CONF.auth.admin_password,
                           "auth_url": CONF.identity.uri},
                "driver": self.DATASOURCE_NAME,
                "name": self.DATASOURCE_NAME}
        try:
            self.os_admin.congress_client.create_datasource(body)['id']
        except exceptions.Conflict:
            pass

        self.datasource_id = manager_congress.get_datasource_id(
            self.os_admin.congress_client, self.DATASOURCE_NAME)

        # Get client
        self.admin_qos_client = self.os_admin.qos_client
        self.admin_qos_rule_client = self.os_admin.qos_rule_client
        self.networks_client = self.os_primary.networks_client
        self.ports_client = self.os_primary.ports_client

        # Create qos and qos rule
        self.qos_policy = self._create_qos_policy('test_qos_policy',
                                                  description="test",
                                                  share=True)
        self.qos_rule = self._create_qos_bandwidth_limit_rule(
            self.qos_policy['id'], 1000, 1000)

        # Associate policy with port
        body = self.networks_client.create_network(
            name="test_qos_network")
        self.network = body["network"]
        body = self.ports_client.create_port(
            network_id=self.network['id'])
        self.port = body["port"]
        self.ports_client.update_port(
            self.port['id'], qos_policy_id=self.qos_policy['id'])

    def tearDown(self):
        super(TestNeutronV2QosDriver, self).tearDown()
        # Clear port and net
        self.ports_client.delete_port(self.port['id'])
        self.networks_client.delete_network(self.network["id"])

        # Clear qos policy and qos rule
        self.admin_qos_rule_client.delete_qos_rule(
            self.qos_policy['id'], RULE_TYPE, self.qos_rule['id'])
        self.admin_qos_client.delete_qos_policy(self.qos_policy['id'])

    def _create_qos_policy(self, name, description=None, share=False):
        """Wrapper utility that returns a test QoS policy."""
        body = self.admin_qos_client.create_qos_policy(
            name=name, description=description, shared=share)
        qos_policy = body['policy']
        self.qos_policies.append(qos_policy)
        return qos_policy

    def _create_qos_bandwidth_limit_rule(self, policy_id, max_kbps,
                                         max_burst_kbps,
                                         direction='egress'):
        """Wrapper utility that returns a test QoS bandwidth limit rule."""
        rule_type = RULE_TYPE
        body = self.admin_qos_rule_client.create_qos_rule(
            policy_id, rule_type,
            max_kbps=max_kbps, max_burst_kbps=max_burst_kbps,
            direction=direction)
        qos_rule = body['bandwidth_limit_rule']
        self.qos_rules.append(qos_rule)
        return qos_rule

    @decorators.attr(type='smoke')
    @test.services('network')
    def test_neutronv2_ports_tables(self):
        port_schema = (
            self.os_admin.congress_client.show_datasource_table_schema(
                self.datasource_id, 'ports')['columns'])

        port_qos_binding_schema = (
            self.os_admin.congress_client.show_datasource_table_schema(
                self.datasource_id, 'qos_policy_port_bindings')['columns'])

        qos_policy_schema = (
            self.os_admin.congress_client.show_datasource_table_schema(
                self.datasource_id, 'policies')['columns'])

        qos_rule_schema = (
            self.os_admin.congress_client.show_datasource_table_schema(
                self.datasource_id, 'rules')['columns'])

        @helper.retry_on_exception
        def _check_data_for_port():
            ports_from_neutron = self.ports_client.list_ports()
            port_map = {}
            for port in ports_from_neutron['ports']:
                port_map[port['id']] = port

            client = self.os_admin.congress_client
            client.request_refresh(self.datasource_id)
            time.sleep(1)

            ports = (client.list_datasource_rows(self.datasource_id, 'ports'))
            qos_policy_port_bindings = (
                client.list_datasource_rows(
                    self.datasource_id, 'qos_policy_port_bindings'))

            # Validate ports table
            for row in ports['results']:
                port_row = port_map[row['data'][0]]
                for index in range(len(port_schema)):
                    if (str(row['data'][index]) !=
                            str(port_row[port_schema[index]['name']])):
                        return False

            # validate qos_policy_port_bindings table
            for row in qos_policy_port_bindings['results']:
                port_row = port_map[row['data'][0]]
                for index in range(len(port_qos_binding_schema)):
                    row_index = port_qos_binding_schema[index]['name']
                    # Translate port_id -> id
                    if row_index == 'port_id':
                        if (str(row['data'][index]) !=
                                str(port_row['id'])):
                            return False
                    elif row_index == 'qos_policy_id':
                        if (str(row['data'][index]) not in
                                port_row['policies']):
                            return False
            return True

        @helper.retry_on_exception
        def _check_data_for_qos():
            qos_from_neutron = self.admin_qos_client.list_qos_policy()
            rule_from_neutron = self.admin_qos_rule_client.list_qos_rule(
                self.qos_policy['id'])
            policy_map = {}
            rule_map = {}
            for policy in qos_from_neutron['policies']:
                policy_map[policy['id']] = policy

            for rule in rule_from_neutron['policy']['rules']:
                rule_map[self.qos_policy['id']] = rule
            client = self.os_admin.congress_client
            client.request_refresh(self.datasource_id)
            time.sleep(1)
            qos_policies = (client.list_datasource_rows(
                self.datasource_id, 'policies'))
            qos_rules = (client.list_datasource_rows(
                self.datasource_id, 'rules'))

            # Validate policies table
            for row in qos_policies['results']:
                policy_row = policy_map[row['data'][0]]
                for index in range(len(qos_policy_schema)):
                    if (str(row['data'][index]) !=
                            str(policy_row[qos_policy_schema[index]['name']])):
                        return False

            # Validate rules table
            for row in qos_rules['results']:
                rule_row = rule_map[row['data'][0]]
                for index in range(len(qos_rule_schema)):
                    if str(row['data'][index]) != "None":
                        if (str(row['data'][index]) !=
                                str(rule_row[qos_rule_schema[index]['name']])):
                            return False
            return True

        if not test_utils.call_until_true(func=_check_data_for_port,
                                          duration=200, sleep_for=10):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

        if not test_utils.call_until_true(func=_check_data_for_qos,
                                          duration=200, sleep_for=10):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.attr(type='smoke')
    def test_update_no_error(self):
        if not test_utils.call_until_true(
                func=lambda: self.check_datasource_no_error(
                    self.DATASOURCE_NAME),
                duration=30, sleep_for=5):
            raise exceptions.TimeoutException('Datasource could not poll '
                                              'without error.')
