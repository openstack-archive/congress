# Copyright (c) 2015 Hewlett-Packard. All rights reserved.
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
from tempest_lib import decorators

from tempest import config
from tempest.scenario import manager_congress
from tempest import test

import random
import string

CONF = config.CONF


class TestMuranoDriver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def check_preconditions(cls):
        super(TestMuranoDriver, cls).check_preconditions()
        if not (CONF.network.tenant_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    def setUp(self):
        super(TestMuranoDriver, self).setUp()
        self.congress_client = (
            self.admin_manager.congress_client)

    @decorators.skip_because(bug='1486246')
    @test.attr(type='smoke')
    @test.services('compute')
    def test_murano_predeployment(self):

        def _delete_policy_rules(policy_name):
            result = self.congress_client.list_policy_rules(
                policy_name)['results']
            for rule in result:
                self.congress_client.delete_policy_rule(
                    policy_name,
                    rule['id'])

        def _create_random_policy():
            policy_name = "murano_%s" % ''.join(random.choice(string.lowercase)
                                                for x in range(10))
            body = {"name": policy_name}
            resp = self.congress_client.create_policy(body)
            self.addCleanup(_delete_policy_rules, resp['name'])
            return resp['name']

        def _create_datasource():
            body = {"config": {"username": CONF.identity.admin_username,
                               "tenant_name": CONF.identity.admin_tenant_name,
                               "password": CONF.identity.admin_password,
                               "auth_url": CONF.identity.uri},
                    "driver": "murano",
                    "name": "murano"}
            datasource = self.congress_client.create_datasource(body)['id']
            self.addCleanup(self.congress_client.delete_datasource, datasource)

        def _create_rule(policy_name, rule):
            self.congress_client.create_policy_rule(policy_name, rule)

        def _simulate_policy(policy_name, query):
            resp = self.congress_client.execute_policy_action(
                policy_name,
                "simulate",
                False,
                False,
                query)
            return resp['result']

        rule1 = {
            "rule": "allowed_flavors(flavor) :- nova:flavors(flavor_id,"
            "flavor, vcpus, ram, disk, ephemeral, rxtx_factor),"
            "equal(flavor, \"m1.medium\")"
        }

        rule2 = {
            "rule": "allowed_flavors(flavor) :- nova:flavors(flavor_id,"
            "flavor, vcpus, ram, disk, ephemeral, rxtx_factor),"
            "equal(flavor, \"m1.small\")"
        }

        rule3 = {
            "rule": "allowed_flavors(flavor) :- nova:flavors(flavor_id,"
            "flavor, vcpus, ram, disk, ephemeral, rxtx_factor),"
            "equal(flavor, \"m1.tiny\")"
        }

        rule4 = {
            "rule": "murano_pending_envs(env_id) :- "
            "murano:objects(env_id, tenant_id, \"io.murano.Environment\"),"
            "murano:states(env_id, env_state),"
            "equal(env_state, \"pending\")"
        }

        rule5 = {
            "rule": "murano_instances(env_id, instance_id) :- "
            "murano:objects(env_id, tenant_id, \"io.murano.Environment\"),"
            "murano:objects(service_id, env_id, service_type),"
            "murano:parent_types(service_id, \"io.murano.Object\"),"
            "murano:parent_types(service_id, \"io.murano.Application\"),"
            "murano:parent_types(service_id, service_type),"
            "murano:objects(instance_id, service_id, instance_type),"
            "murano:parent_types(instance_id,"
            "\"io.murano.resources.Instance\"),"
            "murano:parent_types(instance_id, \"io.murano.Object\"),"
            "murano:parent_types(instance_id, instance_type)"
        }

        rule6 = {
            "rule": "murano_instance_flavors(instance_id, flavor) :- "
            "murano:properties(instance_id, \"flavor\", flavor)"
        }

        rule7 = {
            "rule": "predeploy_error(env_id) :- "
            "murano_pending_envs(env_id),"
            "murano_instances(env_id, instance_id),"
            "murano_instance_flavors(instance_id, flavor),"
            "not allowed_flavors(flavor)"
        }

        sim_query1 = {
            "query": "predeploy_error(env_id)",
            "action_policy": "action",
            "sequence": "murano:objects+(\"env_uuid\", \"tenant_uuid\","
            "\"io.murano.Environment\") murano:states+(\"env_uuid\", "
            "\"pending\") murano:objects+(\"service_uuid\", \"env_uuid\", "
            "\"service_type\") murano:parent_types+(\"service_uuid\", "
            "\"io.murano.Object\") murano:parent_types+(\"service_uuid\", "
            "\"io.murano.Application\") murano:parent_types+(\"service_uuid\","
            "\"service_type\") murano:objects+(\"instance_uuid\", "
            "\"service_uuid\", \"service_type\") murano:objects+(\""
            "instance_uuid\", \"service_uuid\", \"instance_type\") "
            "murano:parent_types+(\"instance_uuid\", "
            "\"io.murano.resources.Instance\") murano:parent_types+(\""
            "instance_uuid\", \"io.murano.Object\") murano:parent_types+(\""
            "instance_uuid\", \"instance_type\") murano:properties+(\""
            "instance_uuid\", \"flavor\", \"m1.small\")"
        }

        sim_query2 = {
            "query": "predeploy_error(env_id)",
            "action_policy": "action",
            "sequence": "murano:objects+(\"env_uuid\", \"tenant_uuid\","
            "\"io.murano.Environment\") murano:states+(\"env_uuid\", "
            "\"pending\") murano:objects+(\"service_uuid\", \"env_uuid\", "
            "\"service_type\") murano:parent_types+(\"service_uuid\", "
            "\"io.murano.Object\") murano:parent_types+(\"service_uuid\", "
            "\"io.murano.Application\") murano:parent_types+(\"service_uuid\","
            "\"service_type\") murano:objects+(\"instance_uuid\", "
            "\"service_uuid\", \"service_type\") murano:objects+(\""
            "instance_uuid\", \"service_uuid\", \"instance_type\") "
            "murano:parent_types+(\"instance_uuid\", "
            "\"io.murano.resources.Instance\") murano:parent_types+(\""
            "instance_uuid\", \"io.murano.Object\") murano:parent_types+(\""
            "instance_uuid\", \"instance_type\") murano:properties+(\""
            "instance_uuid\", \"flavor\", \"m1.large\")"
        }

        _create_datasource()
        policy_name = _create_random_policy()
        _create_rule(policy_name, rule1)
        _create_rule(policy_name, rule2)
        _create_rule(policy_name, rule3)
        _create_rule(policy_name, rule4)
        _create_rule(policy_name, rule5)
        _create_rule(policy_name, rule6)
        _create_rule(policy_name, rule7)
        result = _simulate_policy(policy_name, sim_query1)
        self.assertEqual([], result)
        result = _simulate_policy(policy_name, sim_query2)
        self.assertEqual('predeploy_error("env_uuid")', result[0])
