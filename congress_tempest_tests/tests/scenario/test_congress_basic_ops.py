# Copyright 2012 OpenStack Foundation
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from oslo_log import log as logging
from tempest_lib import exceptions

from tempest import config  # noqa
from tempest import test  # noqa

from congress_tempest_tests.tests.scenario import helper
from congress_tempest_tests.tests.scenario import manager_congress

import random
import string


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestPolicyBasicOps(manager_congress.ScenarioPolicyBase):

    @classmethod
    def skip_checks(cls):
        super(TestPolicyBasicOps, cls).skip_checks()
        if not (CONF.network.tenant_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    def setUp(self):
        super(TestPolicyBasicOps, self).setUp()
        self.keypairs = {}
        self.servers = []

    def _create_random_policy(self):
        policy_name = "nova_%s" % ''.join(random.choice(string.lowercase)
                                          for x in range(10))
        body = {"name": policy_name}
        resp = self.admin_manager.congress_client.create_policy(body)
        self.addCleanup(self.admin_manager.congress_client.delete_policy,
                        resp['id'])
        return resp['name']

    def _create_policy_rule(self, policy_name, rule, rule_name=None,
                            comment=None):
        body = {'rule': rule}
        if rule_name:
            body['name'] = rule_name
        if comment:
            body['comment'] = comment
        client = self.admin_manager.congress_client
        response = client.create_policy_rule(policy_name, body)
        if response:
            self.addCleanup(client.delete_policy_rule, policy_name,
                            response['id'])
            return response
        else:
            raise Exception('Failed to create policy rule (%s, %s)'
                            % (policy_name, rule))

    def _create_test_server(self, name=None):
        image_ref = CONF.compute.image_ref
        flavor_ref = CONF.compute.flavor_ref
        keypair = self.create_keypair()
        security_group = self._create_security_group()
        security_groups = [{'name': security_group['name']}]
        create_kwargs = {'key_name': keypair['name'],
                         'security_groups': security_groups}
        instance = self.create_server(name=name,
                                      image_id=image_ref,
                                      flavor=flavor_ref,
                                      wait_until='ACTIVE',
                                      **create_kwargs)
        return instance

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_execution_action(self):
        metadata = {'testkey1': 'value3'}
        res = {'meta': {'testkey1': 'value3'}}
        server = self._create_test_server()
        congress_client = self.admin_manager.congress_client
        servers_client = self.admin_manager.servers_client
        policy = self._create_random_policy()
        service = 'nova'
        action = 'servers.set_meta'
        action_args = {'args': {'positional': [],
                                'named': {'server': server['id'],
                                          'metadata': metadata}}}
        body = action_args

        f = lambda: servers_client.show_server_metadata_item(server['id'],
                                                             'testkey1')
        # execute via datasource api
        body.update({'name': action})
        congress_client.execute_datasource_action(service, "execute", body)
        helper.retry_check_function_return_value(f, res)

        # execute via policy api
        body.update({'name': service + ':' + action})
        congress_client.execute_policy_action(policy, "execute", False,
                                              False, body)
        helper.retry_check_function_return_value(f, res)

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_policy_basic_op(self):
        self._setup_network_and_servers()
        body = {"rule": "port_security_group(id, security_group_name) "
                        ":-neutronv2:ports(id, tenant_id, name, network_id,"
                        "mac_address, admin_state_up, status, device_id, "
                        "device_owner),"
                        "neutronv2:security_group_port_bindings(id, "
                        "security_group_id), neutronv2:security_groups("
                        "security_group_id, tenant_id1, security_group_name,"
                        "description)"}
        results = self.admin_manager.congress_client.create_policy_rule(
            'classification', body)
        rule_id = results['id']
        self.addCleanup(
            self.admin_manager.congress_client.delete_policy_rule,
            'classification', rule_id)

        # Find the ports of on this server
        ports = self._list_ports(device_id=self.servers[0]['id'])

        def check_data():
            results = self.admin_manager.congress_client.list_policy_rows(
                'classification', 'port_security_group')
            for row in results['results']:
                if (row['data'][0] == ports[0]['id'] and
                    row['data'][1] ==
                        self.servers[0]['security_groups'][0]['name']):
                        return True
            else:
                return False

        if not test.call_until_true(func=check_data,
                                    duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_reactive_enforcement(self):
        servers_client = self.admin_manager.servers_client
        server_name = 'server_under_test'
        server = self._create_test_server(name=server_name)
        policy_name = self._create_random_policy()
        meta_key = 'meta_test_key1'
        meta_val = 'value1'
        meta_data = {'meta': {meta_key: meta_val}}
        rules = [
            'execute[nova:servers_set_meta(id, "%s", "%s")] :- '
            'test_servers(id)' % (meta_key, meta_val),
            'test_servers(id) :- '
            'nova:servers(id, name, host_id, status, tenant_id,'
            'user_id, image_id, flavor_id, zone, host_name),'
            'equal(name, "%s")' % server_name]

        for rule in rules:
            self._create_policy_rule(policy_name, rule)
        f = lambda: servers_client.show_server_metadata_item(server['id'],
                                                             meta_key)
        helper.retry_check_function_return_value(f, meta_data)


class TestCongressDataSources(manager_congress.ScenarioPolicyBase):

    @classmethod
    def skip_checks(cls):
        super(TestCongressDataSources, cls).skip_checks()
        if not (CONF.network.tenant_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    def test_all_loaded_datasources_are_initialized(self):
        datasources = self.admin_manager.congress_client.list_datasources()

        def _check_all_datasources_are_initialized():
            for datasource in datasources['results']:
                results = (
                    self.admin_manager.congress_client.list_datasource_status(
                        datasource['id']))
                if results['initialized'] != 'True':
                    return False
            return True

        if not test.call_until_true(
            func=_check_all_datasources_are_initialized,
                duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    def test_all_datasources_have_tables(self):
        datasources = self.admin_manager.congress_client.list_datasources()

        def check_data():
            for datasource in datasources['results']:
                results = (
                    self.admin_manager.congress_client.list_datasource_tables(
                        datasource['id']))
                # NOTE(arosen): if there are no results here we return false as
                # there is something wrong with a driver as it doesn't expose
                # any tables.
                if not results['results']:
                    return False
            return True

        if not test.call_until_true(func=check_data,
                                    duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")
