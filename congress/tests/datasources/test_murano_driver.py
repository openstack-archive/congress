#!/usr/bin/env python
# Copyright (c) 2015 Hewlett-Packard. All rights reserved.
#
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

import mock

# mocking muranoclient so that python-muranoclient
# doesn't need to be included in requirements.txt.
# (Including python-muranoclient in requirements.txt will
# cause failures in Jenkins because python-muranoclient is not
# included in global_requirements.txt at this point)
import sys

sys.modules['muranoclient'] = mock.Mock()
sys.modules['muranoclient.client'] = mock.Mock()
sys.modules['muranoclient.common'] = mock.Mock()
sys.modules['muranoclient.common.exceptions'] = mock.Mock()

from congress.datasources import murano_driver
from congress.tests import base
from congress.tests.datasources.util import ResponseObj
from congress.tests import helper


class TestMuranoDriver(base.TestCase):
    def setUp(self):
        super(TestMuranoDriver, self).setUp()
        self.keystone_client_p = mock.patch(
            "keystoneclient.v2_0.client.Client")
        self.keystone_client_p.start()
        self.murano_client = mock.MagicMock()
        self.murano_client.environments.list.return_value = env_response
        self.murano_client.services.list.return_value = service_response
        self.murano_client.deployments.list.return_value = deployment_response
        self.murano_client.packages.list.return_value = package_response
        args = helper.datasource_openstack_args()
        self.driver = murano_driver.MuranoDriver(args=args)
        self.driver.murano_client = self.murano_client

    def test_list_environments(self):
        """Test conversion of environments objects to tables."""
        envs = self.driver.murano_client.environments.list()
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver._translate_environments(envs)

        # datasource tables
        environments = list(self.driver.state[self.driver.STATES])
        properties = list(self.driver.state[self.driver.PROPERTIES])

        # verify tables
        self.assertIsNotNone(environments)
        self.assertIsNotNone(properties)
        self.assertEqual(2, len(environments))
        for row in expected_environments:
            self.assertTrue(row in environments,
                            msg=("%s not in environments" % str(row)))
        for row in expected_env_properties:
            self.assertTrue(row in properties,
                            msg=("%s not in properties" % str(row)))

    def test_translate_services(self):
        """Test conversion of environment services to tables."""
        envs = self.driver.murano_client.environments.list()
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver.state[self.driver.RELATIONSHIPS] = set()
        self.driver.state[self.driver.CONNECTED] = set()
        self.driver._translate_services(envs)

        # datasource tables
        objects = list(self.driver.state[self.driver.OBJECTS])
        properties = list(self.driver.state[self.driver.PROPERTIES])
        parent_types = list(self.driver.state[self.driver.PARENT_TYPES])
        relationships = list(self.driver.state[self.driver.RELATIONSHIPS])

        # verify tables
        self.assertIsNotNone(objects)
        self.assertIsNotNone(properties)
        self.assertIsNotNone(parent_types)
        self.assertIsNotNone(relationships)
        for row in expected_service_objects:
            self.assertTrue(row in objects,
                            msg=("%s not in objects" % str(row)))
        for row in expected_service_properties:
            self.assertTrue(row in properties,
                            msg=("%s not in properties" % str(row)))
        for row in expected_service_parent_types:
            self.assertTrue(row in parent_types,
                            msg=("%s not in parent_types" % str(row)))
        for row in expected_service_relationships:
            self.assertTrue(row in relationships,
                            msg=("%s not in relationships" % str(row)))

    def test_translate_environment_services(self):
        """Test conversion of environment services to tables."""
        envs = self.driver.murano_client.environments.list()
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver.state[self.driver.RELATIONSHIPS] = set()
        self.driver.state[self.driver.CONNECTED] = set()

        for env in envs:
            services = self.murano_client.services.list(env.id)
            self.driver._translate_environment_services(services, env.id)

        # datasource tables
        objects = list(self.driver.state[self.driver.OBJECTS])
        properties = list(self.driver.state[self.driver.PROPERTIES])
        parent_types = list(self.driver.state[self.driver.PARENT_TYPES])
        relationships = list(self.driver.state[self.driver.RELATIONSHIPS])

        # verify tables
        self.assertIsNotNone(objects)
        self.assertIsNotNone(properties)
        self.assertIsNotNone(parent_types)
        self.assertIsNotNone(relationships)
        for row in expected_service_objects:
            self.assertTrue(row in objects,
                            msg=("%s not in objects" % str(row)))
        for row in expected_service_properties:
            self.assertTrue(row in properties,
                            msg=("%s not in properties" % str(row)))
        for row in expected_service_parent_types:
            self.assertTrue(row in parent_types,
                            msg=("%s not in parent_types" % str(row)))
        for row in expected_service_relationships:
            self.assertTrue(row in relationships,
                            msg=("%s not in relationships" % str(row)))

    def test_translate_packages(self):
        """Test conversion of application packages to tables."""
        pkg_list = self.driver.murano_client.packages.list()
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver._translate_packages(pkg_list)

        # datasource tables
        objects = list(self.driver.state[self.driver.OBJECTS])
        properties = list(self.driver.state[self.driver.PROPERTIES])

        # verify tables
        self.assertIsNotNone(objects)
        self.assertIsNotNone(properties)
        for row in expected_package_objects:
            self.assertTrue(row in objects,
                            msg=("%s not in objects" % str(row)))
        for row in expected_package_properties:
            self.assertTrue(row in properties,
                            msg=("%s not in properties" % str(row)))

    def test_translate_deployments(self):
        """Test conversion of deployments to tables."""
        envs = self.driver.murano_client.environments.list()
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver.state[self.driver.RELATIONSHIPS] = set()
        self.driver._translate_deployments(envs)

        # datasource tables
        objects = list(self.driver.state[self.driver.OBJECTS])
        properties = list(self.driver.state[self.driver.PROPERTIES])
        parent_types = list(self.driver.state[self.driver.PARENT_TYPES])

        # verify tables
        self.assertIsNotNone(objects)
        self.assertIsNotNone(properties)
        self.assertIsNotNone(parent_types)
        for row in expected_deployment_objects:
            self.assertTrue(row in objects,
                            msg=("%s not in objects" % str(row)))
        for row in expected_deployment_properties:
            self.assertTrue(row in properties,
                            msg=("%s not in properties" % str(row)))
        for row in expected_deployment_parent_types:
            self.assertTrue(row in parent_types,
                            msg=("%s not in parent_types" % str(row)))

    def test_translate_environment_deployments(self):
        """Test conversion of deployments to tables."""
        envs = self.driver.murano_client.environments.list()
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver.state[self.driver.RELATIONSHIPS] = set()
        for env in envs:
            deps = self.murano_client.deployments.list(env.id)
            self.driver._translate_environment_deployments(deps, env.id)

        # datasource tables
        objects = list(self.driver.state[self.driver.OBJECTS])
        properties = list(self.driver.state[self.driver.PROPERTIES])
        parent_types = list(self.driver.state[self.driver.PARENT_TYPES])

        # verify tables
        self.assertIsNotNone(objects)
        self.assertIsNotNone(properties)
        self.assertIsNotNone(parent_types)
        for row in expected_deployment_objects:
            self.assertTrue(row in objects,
                            msg=("%s not in objects" % str(row)))
        for row in expected_deployment_properties:
            self.assertTrue(row in properties,
                            msg=("%s not in properties" % str(row)))
        for row in expected_deployment_parent_types:
            self.assertTrue(row in parent_types,
                            msg=("%s not in parent_types" % str(row)))

    def test_translate_connected(self):
        """Test translation of relationships to connected table."""
        envs = self.driver.murano_client.environments.list()
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver.state[self.driver.RELATIONSHIPS] = set()
        self.driver.state[self.driver.CONNECTED] = set()
        self.driver._translate_services(envs)  # to populate relationships
        self.driver._translate_connected()

        # datasource tables
        connected = list(self.driver.state[self.driver.CONNECTED])

        # verify tables
        self.assertIsNotNone(connected)
        for row in expected_connected:
            self.assertTrue(row in connected,
                            msg=("%s not in connected" % str(row)))

# Sample responses from murano-client
env_response = [
    ResponseObj({u'status': u'ready',
                 u'updated': u'2015-01-08T22:01:52',
                 u'networking': {},
                 u'name': u'quick-env-1',
                 u'created': u'2015-01-08T21:53:08',
                 u'tenant_id': u'db4ca49cb1074cb093353b89f83615ef',
                 u'version': 1,
                 u'id': u'9d929a329182469cb11a1841db95b8da'}),
    ResponseObj({'status': u'pending',
                 'updated': u'2015-01-08T22:14:20',
                 'networking': {},
                 'name': u'second_env',
                 'created': u'2015-01-08T22:14:20',
                 'tenant_id': u'db4ca49cb1074cb093353b89f83615ef',
                 'version': 0,
                 'id': u'0c45ff66ce744568a524936da7ebaa7d'})]

service_response = [
    ResponseObj(
        {u'username': u'',
         u'name': u'MySqlDB',
         u'database': u'MySql01',
         u'instance': {u'name': u'ugrcyi619ixrn1',
                       u'assignFloatingIp': True,
                       u'keyname': u'cloud',
                       u'flavor': u'm1.medium',
                       u'image': u'ubuntu-murano',
                       u'?': {u'type':
                              u'io.murano.resources.LinuxMuranoInstance',
                              u'id': u'23bb326c-6ca3-4edf-887b-ecf5d882e596'}},
         u'password': u'',
         u'?': {u'status': u'deploy failure',
                u'_26411a1861294160833743e45d0eaad9': {u'name': u'MySQL'},
                u'type': u'io.murano.databases.MySql',
                u'id': u'847b88e2-a8a9-4d45-b0d8-c96f6ddd99ca'}}),
    ResponseObj(
        {u'instance': {u'name': u'eaxxxi619jit32',
                       u'assignFloatingIp': True,
                       u'keyname': u'cloud',
                       u'flavor': u'm1.small',
                       u'image': u'ubuntu-murano',
                       u'?': {u'type':
                              u'io.murano.resources.LinuxMuranoInstance',
                              u'id': u'290e655f-d88d-44ed-a22b-70d8d2338ddb'}},
         u'name': u'ApacheHttpServer',
         u'?': {u'status': u'deploy failure',
                u'_26411a1861294160833743e45d0eaad9':
                {u'name': u'Apache HTTP Server'},
                u'type': u'io.murano.apps.apache.ApacheHttpServer',
                u'id': u'7bc0cd98-e1bc-4377-8be6-a098c98d5397'},
         u'enablePHP': False}),
    ResponseObj(
        {u'username': u'zabbix',
         u'name': u'ZabbixServer',
         u'database': u'zabbix',
         u'instance': {u'name': u'wzouai619l3ss3',
                       u'assignFloatingIp': True,
                       u'keyname': u'cloud',
                       u'flavor': u'm1.small',
                       u'image': u'ubuntu-murano',
                       u'?': {u'type':
                              u'io.murano.resources.LinuxMuranoInstance',
                              u'id': u'8c34f7d7-5d1b-4037-bd48-6797ea4fedc7'}},
         u'password': u'Passw0rd#',
         u'?': {u'status': u'deploy failure',
                u'_26411a1861294160833743e45d0eaad9':
                {u'name': u'Zabbix Server'},
                u'type': u'io.murano.apps.ZabbixServer',
                u'id': u'7cf2fc0d-5b5f-4a85-8d61-917407b673a4'}}),
    ResponseObj(
        {u'hostname': u'zabbix',
         u'probe': u'ICMP',
         u'name': u'ZabbixAgent',
         u'?': {u'status': u'deploy failure',
                u'_26411a1861294160833743e45d0eaad9':
                {u'name': u'Zabbix Agent'},
                u'type': u'io.murano.apps.ZabbixAgent',
                u'id': u'5f8dc42c-3735-4450-ae1e-f713cc84c7d6'},
         u'server': u'7cf2fc0d-5b5f-4a85-8d61-917407b673a4'}),
    ResponseObj(
        {u'monitoring': u'5f8dc42c-3735-4450-ae1e-f713cc84c7d6',
         u'database': u'847b88e2-a8a9-4d45-b0d8-c96f6ddd99ca',
         u'server': u'7bc0cd98-e1bc-4377-8be6-a098c98d5397',
         u'dbPassword': u'Passw0rd#',
         u'dbUser': u'wp_user',
         u'dbName': u'wordpress',
         u'?': {u'status': u'deploy failure',
                u'_26411a1861294160833743e45d0eaad9': {u'name': u'WordPress'},
                u'type': u'io.murano.apps.WordPress',
                u'id': u'8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74'}})]

deployment_response = [ResponseObj(
    {u'updated': u'2015-01-08T22:01:52',
     u'environment_id': u'9d929a329182469cb11a1841db95b8da',
     u'description': {u'services':
                      [{u'instance':
                        {u'name': u'tuerfi4oo8pp71',
                         u'assignFloatingIp': True,
                         u'keyname': u'cloud',
                         u'flavor': u'm1.small',
                         u'image': u'ubuntu-murano',
                         u'?': {u'type':
                                u'io.murano.resources.LinuxMuranoInstance',
                                u'id':
                                u'6392a024-ebf8-49d2-990a-d6ba33ac70c9'}},
                        u'name': u'Telnet',
                        u'?': {u'_26411a1861294160833743e45d0eaad9':
                               {u'name': u'Telnet'},
                               u'type': u'io.murano.apps.linux.Telnet',
                               u'id':
                               u'03a0137f-4644-4943-9be9-66b612e8f885'}}],
                      u'defaultNetworks':
                      {u'environment':
                       {u'name': u'quick-env-1-network',
                        u'?': {u'type': u'io.murano.resources.NeutronNetwork',
                               u'id': u'afcfe791222a408989bf8c29ce1562f3'}},
                       u'flat': None},
                      u'name': u'quick-env-1',
                      u'?': {u'type': u'io.murano.Environment',
                             u'id': u'9d929a329182469cb11a1841db95b8da'}},
     u'created': u'2015-01-08T21:53:14',
     u'started': u'2015-01-08T21:53:14',
     u'state': u'success',
     u'finished': u'2015-01-08T22:01:52',
     u'action': {u'args': {},
                 u'method': u'deploy',
                 u'object_id': u'9d929a329182469cb11a1841db95b8da'},
     u'id': u'77102e350687424ebdad048cde92bac2'})]

package_response = [
    ResponseObj({u'class_definitions': [u'io.murano.apps.apache.Tomcat'],
                 u'description': u'Apache Tomcat is an open source software ' +
                 'implementation of the Java Servlet and JavaServer ' +
                 'Pages technologies.\n',
                 u'tags': [u'Servlets', u'Server',
                           u'Pages', u'Java'],
                 u'owner_id': u'db4ca49cb1074cb093353b89f83615ef',
                 u'author': u'Mirantis, Inc',
                 u'enabled': True,
                 u'updated': u'2015-01-08T21:45:57',
                 u'created': u'2015-01-08T21:45:57',
                 u'supplier': {},
                 u'is_public': False,
                 u'fully_qualified_name': u'io.murano.apps.apache.Tomcat',
                 u'type': u'Application',
                 u'id': u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1',
                 u'categories': [u'Web'],
                 u'name': u'Apache Tomcat'}),
    ResponseObj({u'class_definitions': [u'io.murano.apps.linux.Telnet'],
                 u'description': u'Telnet is the traditional protocol for ' +
                 'making remote console connections over TCP.\n',
                 u'tags': [u'Linux', u'connection'],
                 u'owner_id': u'db4ca49cb1074cb093353b89f83615ef',
                 u'author': u'Mirantis, Inc',
                 u'enabled': True,
                 u'updated': u'2015-01-08T21:45:32',
                 u'created': u'2015-01-08T21:45:32',
                 u'supplier': {},
                 u'is_public': False,
                 u'fully_qualified_name': u'io.murano.apps.linux.Telnet',
                 u'type': u'Application',
                 u'id': u'18d7a400ab034a368e2cb6f7466d8214',
                 u'categories': [],
                 u'name': u'Telnet'})]

# Expected datasource table content
expected_environments = [
    ('0c45ff66ce744568a524936da7ebaa7d', 'pending'),
    ('9d929a329182469cb11a1841db95b8da', 'ready')
]

expected_env_properties = [
    ('9d929a329182469cb11a1841db95b8da', 'name', 'quick-env-1'),
    ('0c45ff66ce744568a524936da7ebaa7d', 'name', 'second_env'),
    ('9d929a329182469cb11a1841db95b8da', 'created', '2015-01-08T21:53:08'),
    ('0c45ff66ce744568a524936da7ebaa7d', 'created', '2015-01-08T22:14:20'),
]

expected_service_properties = [
    ('847b88e2-a8a9-4d45-b0d8-c96f6ddd99ca', 'name', 'MySqlDB'),
    ('847b88e2-a8a9-4d45-b0d8-c96f6ddd99ca', 'database', 'MySql01'),
    ('7bc0cd98-e1bc-4377-8be6-a098c98d5397', 'name', 'ApacheHttpServer'),
    ('7bc0cd98-e1bc-4377-8be6-a098c98d5397', 'enablePHP', 'False'),
    ('7cf2fc0d-5b5f-4a85-8d61-917407b673a4', 'name', 'ZabbixServer'),
    ('7cf2fc0d-5b5f-4a85-8d61-917407b673a4', 'username', 'zabbix'),
    ('7cf2fc0d-5b5f-4a85-8d61-917407b673a4', 'database', 'zabbix'),
    ('5f8dc42c-3735-4450-ae1e-f713cc84c7d6', 'name', 'ZabbixAgent'),
    ('5f8dc42c-3735-4450-ae1e-f713cc84c7d6', 'hostname', 'zabbix'),
    ('5f8dc42c-3735-4450-ae1e-f713cc84c7d6', 'hostname', 'zabbix'),
]

expected_package_properties = [
    (u'18d7a400ab034a368e2cb6f7466d8214', u'tags', 'connection'),
    (u'18d7a400ab034a368e2cb6f7466d8214', u'author', 'Mirantis, Inc'),
    (u'18d7a400ab034a368e2cb6f7466d8214', u'tags', 'Linux'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'updated', '2015-01-08T21:45:57'),
    (u'18d7a400ab034a368e2cb6f7466d8214', u'fully_qualified_name',
     'io.murano.apps.linux.Telnet'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'enabled', 'True'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'created', '2015-01-08T21:45:57'),
    (u'18d7a400ab034a368e2cb6f7466d8214', u'name', 'Telnet'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'tags', 'Servlets'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'name', 'Apache Tomcat'),
    (u'18d7a400ab034a368e2cb6f7466d8214', u'created', '2015-01-08T21:45:32'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'fully_qualified_name',
     'io.murano.apps.apache.Tomcat'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'author', 'Mirantis, Inc'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'categories', 'Web'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'tags', 'Pages'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'tags', 'Java'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'tags', 'Server'),
    (u'18d7a400ab034a368e2cb6f7466d8214', u'enabled', 'True'),
    (u'18d7a400ab034a368e2cb6f7466d8214', u'updated', '2015-01-08T21:45:32'),
    (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1', u'is_public', 'False'),
    (u'18d7a400ab034a368e2cb6f7466d8214', u'is_public', 'False'),
]

expected_service_objects = [
    ('290e655f-d88d-44ed-a22b-70d8d2338ddb',
     '7bc0cd98-e1bc-4377-8be6-a098c98d5397',
     'io.murano.resources.LinuxMuranoInstance'),
    ('847b88e2-a8a9-4d45-b0d8-c96f6ddd99ca',
     '9d929a329182469cb11a1841db95b8da',
     'io.murano.databases.MySql'),
    ('7cf2fc0d-5b5f-4a85-8d61-917407b673a4',
     '0c45ff66ce744568a524936da7ebaa7d',
     'io.murano.apps.ZabbixServer'),
    ('7bc0cd98-e1bc-4377-8be6-a098c98d5397',
     '9d929a329182469cb11a1841db95b8da',
     'io.murano.apps.apache.ApacheHttpServer'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '9d929a329182469cb11a1841db95b8da',
     'io.murano.apps.WordPress'),
    ('5f8dc42c-3735-4450-ae1e-f713cc84c7d6',
     '9d929a329182469cb11a1841db95b8da',
     'io.murano.apps.ZabbixAgent'),
    ('7cf2fc0d-5b5f-4a85-8d61-917407b673a4',
     '9d929a329182469cb11a1841db95b8da',
     'io.murano.apps.ZabbixServer'),
    ('847b88e2-a8a9-4d45-b0d8-c96f6ddd99ca',
     '0c45ff66ce744568a524936da7ebaa7d',
     'io.murano.databases.MySql'),
    ('23bb326c-6ca3-4edf-887b-ecf5d882e596',
     '847b88e2-a8a9-4d45-b0d8-c96f6ddd99ca',
     'io.murano.resources.LinuxMuranoInstance'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '0c45ff66ce744568a524936da7ebaa7d',
     'io.murano.apps.WordPress'),
    ('7bc0cd98-e1bc-4377-8be6-a098c98d5397',
     '0c45ff66ce744568a524936da7ebaa7d',
     'io.murano.apps.apache.ApacheHttpServer'),
    ('5f8dc42c-3735-4450-ae1e-f713cc84c7d6',
     '0c45ff66ce744568a524936da7ebaa7d',
     'io.murano.apps.ZabbixAgent'),
    ('8c34f7d7-5d1b-4037-bd48-6797ea4fedc7',
     '7cf2fc0d-5b5f-4a85-8d61-917407b673a4',
     'io.murano.resources.LinuxMuranoInstance'),
]

expected_package_objects = [
    ('68cd33f3a1bc41abbd9a7b7a8e2a3ae1', 'db4ca49cb1074cb093353b89f83615ef',
     'io.murano.Application'),
    ('18d7a400ab034a368e2cb6f7466d8214', 'db4ca49cb1074cb093353b89f83615ef',
     'io.murano.Application'),
]

expected_service_parent_types = [
    ('290e655f-d88d-44ed-a22b-70d8d2338ddb',
     'io.murano.Object'),
    ('290e655f-d88d-44ed-a22b-70d8d2338ddb',
     'io.murano.resources.Instance'),
    ('290e655f-d88d-44ed-a22b-70d8d2338ddb',
     'io.murano.resources.LinuxInstance'),
    ('290e655f-d88d-44ed-a22b-70d8d2338ddb',
     'io.murano.resources.LinuxMuranoInstance'),

    ('7bc0cd98-e1bc-4377-8be6-a098c98d5397',
     'io.murano.Object'),
    ('7bc0cd98-e1bc-4377-8be6-a098c98d5397',
     'io.murano.Application'),
    ('7bc0cd98-e1bc-4377-8be6-a098c98d5397',
     'io.murano.apps.apache.ApacheHttpServer'),

    ('23bb326c-6ca3-4edf-887b-ecf5d882e596',
     'io.murano.Object'),
    ('23bb326c-6ca3-4edf-887b-ecf5d882e596',
     'io.murano.resources.Instance'),
    ('23bb326c-6ca3-4edf-887b-ecf5d882e596',
     'io.murano.resources.LinuxInstance'),
    ('23bb326c-6ca3-4edf-887b-ecf5d882e596',
     'io.murano.resources.LinuxMuranoInstance'),

    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     'io.murano.Object'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     'io.murano.Application'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     'io.murano.apps.WordPress'),

    ('8c34f7d7-5d1b-4037-bd48-6797ea4fedc7',
     'io.murano.Object'),
    ('8c34f7d7-5d1b-4037-bd48-6797ea4fedc7',
     'io.murano.resources.Instance'),
    ('8c34f7d7-5d1b-4037-bd48-6797ea4fedc7',
     'io.murano.resources.LinuxInstance'),
    ('8c34f7d7-5d1b-4037-bd48-6797ea4fedc7',
     'io.murano.resources.LinuxMuranoInstance'),

    ('7cf2fc0d-5b5f-4a85-8d61-917407b673a4',
     'io.murano.Object'),
    ('7cf2fc0d-5b5f-4a85-8d61-917407b673a4',
     'io.murano.Application'),
    ('7cf2fc0d-5b5f-4a85-8d61-917407b673a4',
     'io.murano.apps.ZabbixServer'),

    ('5f8dc42c-3735-4450-ae1e-f713cc84c7d6',
     'io.murano.Object'),
    ('5f8dc42c-3735-4450-ae1e-f713cc84c7d6',
     'io.murano.Application'),
    ('5f8dc42c-3735-4450-ae1e-f713cc84c7d6',
     'io.murano.apps.ZabbixAgent'),
]

expected_service_relationships = [
    ('847b88e2-a8a9-4d45-b0d8-c96f6ddd99ca',
     '23bb326c-6ca3-4edf-887b-ecf5d882e596', 'instance'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '7bc0cd98-e1bc-4377-8be6-a098c98d5397', 'server'),
    ('5f8dc42c-3735-4450-ae1e-f713cc84c7d6',
     '7cf2fc0d-5b5f-4a85-8d61-917407b673a4', 'server'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '5f8dc42c-3735-4450-ae1e-f713cc84c7d6', 'monitoring'),
    ('7bc0cd98-e1bc-4377-8be6-a098c98d5397',
     '290e655f-d88d-44ed-a22b-70d8d2338ddb', 'instance'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '847b88e2-a8a9-4d45-b0d8-c96f6ddd99ca', 'database'),
    ('7cf2fc0d-5b5f-4a85-8d61-917407b673a4',
     '8c34f7d7-5d1b-4037-bd48-6797ea4fedc7', 'instance'),
]

expected_connected = [
    ('847b88e2-a8a9-4d45-b0d8-c96f6ddd99ca',
     '23bb326c-6ca3-4edf-887b-ecf5d882e596'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '7cf2fc0d-5b5f-4a85-8d61-917407b673a4'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '5f8dc42c-3735-4450-ae1e-f713cc84c7d6'),
    ('5f8dc42c-3735-4450-ae1e-f713cc84c7d6',
     '7cf2fc0d-5b5f-4a85-8d61-917407b673a4'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '847b88e2-a8a9-4d45-b0d8-c96f6ddd99ca'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '290e655f-d88d-44ed-a22b-70d8d2338ddb'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '23bb326c-6ca3-4edf-887b-ecf5d882e596'),
    ('5f8dc42c-3735-4450-ae1e-f713cc84c7d6',
     '8c34f7d7-5d1b-4037-bd48-6797ea4fedc7'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '7bc0cd98-e1bc-4377-8be6-a098c98d5397'),
    ('8e81eb8c-a1f8-4096-9a2d-5e8f29b15c74',
     '8c34f7d7-5d1b-4037-bd48-6797ea4fedc7'),
    ('7cf2fc0d-5b5f-4a85-8d61-917407b673a4',
     '8c34f7d7-5d1b-4037-bd48-6797ea4fedc7'),
    ('7bc0cd98-e1bc-4377-8be6-a098c98d5397',
     '290e655f-d88d-44ed-a22b-70d8d2338ddb'),
]

expected_deployment_objects = [
    ('afcfe791222a408989bf8c29ce1562f3',
     '9d929a329182469cb11a1841db95b8da',
     'io.murano.resources.NeutronNetwork'),
    ('afcfe791222a408989bf8c29ce1562f3',
     '0c45ff66ce744568a524936da7ebaa7d',
     'io.murano.resources.NeutronNetwork'),
]

expected_deployment_properties = [
    ('afcfe791222a408989bf8c29ce1562f3', 'name', 'quick-env-1-network'),
]

expected_deployment_parent_types = [
    ('afcfe791222a408989bf8c29ce1562f3', 'io.murano.resources.Network'),
    ('afcfe791222a408989bf8c29ce1562f3', 'io.murano.Object'),
    ('afcfe791222a408989bf8c29ce1562f3', 'io.murano.resources.NeutronNetwork'),
]
