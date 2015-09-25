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
from congress.tests.datasources import util
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
        self.murano_client.actions.call.return_value = action_response
        args = helper.datasource_openstack_args()
        self.driver = murano_driver.MuranoDriver(args=args)
        self.driver.murano_client = self.murano_client

    def test_list_environments(self):
        """Test conversion of environments objects to tables."""
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        envs = self.driver.murano_client.environments.list()
        self.driver._translate_environments(envs)

        # datasource tables
        states = list(self.driver.state[self.driver.STATES])
        properties = list(self.driver.state[self.driver.PROPERTIES])
        parent_types = list(self.driver.state[self.driver.PARENT_TYPES])

        # verify tables
        self.assertIsNotNone(states)
        self.assertIsNotNone(properties)
        for row in expected_states:
            self.assertTrue(row in states,
                            msg=("%s not in states" % str(row)))
        for row in expected_env_properties:
            self.assertTrue(row in properties,
                            msg=("%s not in properties" % str(row)))
        for row in expected_environment_parent_types:
            self.assertTrue(row in parent_types,
                            msg=("%s not in parent_types" % str(row)))

    def test_translate_services(self):
        """Test conversion of environment services to tables."""
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver.state[self.driver.RELATIONSHIPS] = set()
        envs = self.driver.murano_client.environments.list()
        pkgs = self.driver.murano_client.packages.list()
        # package properties are needed for mapping parent_types
        self.driver._translate_packages(pkgs)
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
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver.state[self.driver.RELATIONSHIPS] = set()
        envs = self.driver.murano_client.environments.list()
        pkgs = self.driver.murano_client.packages.list()
        # package properties are needed for mapping parent_types
        self.driver._translate_packages(pkgs)

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
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        pkgs = self.driver.murano_client.packages.list()
        self.driver._translate_packages(pkgs)

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
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver.state[self.driver.RELATIONSHIPS] = set()
        envs = self.driver.murano_client.environments.list()
        pkgs = self.driver.murano_client.packages.list()
        # package properties are needed for mapping parent_types
        self.driver._translate_packages(pkgs)
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
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver.state[self.driver.RELATIONSHIPS] = set()
        envs = self.driver.murano_client.environments.list()
        pkgs = self.driver.murano_client.packages.list()
        # package properties are needed for mapping parent_types
        self.driver._translate_packages(pkgs)

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
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver.state[self.driver.RELATIONSHIPS] = set()
        self.driver.state[self.driver.CONNECTED] = set()
        envs = self.driver.murano_client.environments.list()
        self.driver._translate_services(envs)  # to populate relationships
        self.driver._translate_connected()

        # datasource tables
        connected = list(self.driver.state[self.driver.CONNECTED])

        # verify tables
        self.assertIsNotNone(connected)
        for row in expected_connected:
            self.assertTrue(row in connected,
                            msg=("%s not in connected" % str(row)))

    def test_execute(self):
        """Test action execution."""
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver.state[self.driver.RELATIONSHIPS] = set()
        envs = self.driver.murano_client.environments.list()
        pkgs = self.driver.murano_client.packages.list()
        # package properties are needed for mapping parent_types
        self.driver._translate_packages(pkgs)
        self.driver._translate_services(envs)

        action = 'muranoaction'
        action_args = {'positional': ['ad9762b2d82f44ca8b8a6ce4a19dd1cc',
                                      '769af50c-9629-4694-b623-e9b392941279',
                                      'restartVM']}
        self.driver.execute(action, action_args)
        self.assertTrue(action_response in self.driver.action_call_returns)


# Sample responses from murano-client
env_response = [
    util.ResponseObj({
        u'created': u'2015-03-24T18:35:14',
        u'id': u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
        u'name': u'quick-env-2',
        u'networking': {},
        u'status': u'deploy failure',
        u'tenant_id': u'610c6afc1fc54d23a58d316bf76e5f42',
        u'updated': u'2015-03-24T18:46:56',
        u'version': 1})]

service_response = [
    util.ResponseObj({
        u'?': {u'_26411a1861294160833743e45d0eaad9': {u'name': u'MySQL'},
               u'_actions': {u'74f5b2d2-1f8d-4b1a-8238-4155ce2cadb2_restartVM':
                             {u'enabled': True, u'name': u'restartVM'}},
               u'id': u'769af50c-9629-4694-b623-e9b392941279',
               u'status': u'deploy failure',
               u'type': u'io.murano.databases.MySql'},
        u'database': u'',
        u'instance': {u'?': {u'_actions': {},
                             u'id': u'76b9ca88-c668-4e37-a830-5845adc10b0e',
                             u'type':
                             u'io.murano.resources.LinuxMuranoInstance'},
                      u'assignFloatingIp': True,
                      u'availabilityZone': u'nova',
                      u'flavor': u'm1.small',
                      u'floatingIpAddress': u'172.24.4.4',
                      u'image': u'66e015aa-33c5-41ff-9b81-d8d17f9b02c3',
                      u'ipAddresses': [u'10.0.11.3', u'172.24.4.4'],
                      u'keyname': u'',
                      u'name': u'bcnfli7nn738y1',
                      u'networks': {u'customNetworks': [],
                                    u'primaryNetwork': None,
                                    u'useEnvironmentNetwork': True,
                                    u'useFlatNetwork': False},
                      u'securityGroupName': None,
                      u'sharedIps': []},
        u'name': u'MySqlDB',
        u'password': u'Passw0rd.',
        u'username': u''}),
    util.ResponseObj({
        u'?': {u'_26411a1861294160833743e45d0eaad9':
               {u'name': u'Apache Tomcat'},
               u'_actions': {},
               u'id': u'ea6a7d9b-7799-4d00-9db3-4573cb94daec',
               u'status': u'deploy failure',
               u'type': u'io.murano.apps.apache.Tomcat'},
        u'instance': {u'?': {u'_actions': {},
                             u'id': u'c52dda24-38d6-4f2f-9184-abca0beaa6e9',
                             u'type':
                             u'io.murano.resources.LinuxMuranoInstance'},
                      u'assignFloatingIp': True,
                      u'availabilityZone': u'nova',
                      u'flavor': u'm1.small',
                      u'floatingIpAddress': u'172.24.4.4',
                      u'image': u'66e015aa-33c5-41ff-9b81-d8d17f9b02c3',
                      u'ipAddresses': [u'10.0.11.4', u'172.24.4.4'],
                      u'keyname': u'',
                      u'name': u'woydqi7nn7ipc2',
                      u'networks': {u'customNetworks': [],
                                    u'primaryNetwork': None,
                                    u'useEnvironmentNetwork': True,
                                    u'useFlatNetwork': False},
                      u'securityGroupName': None,
                      u'sharedIps': []},
        u'name': u'Tomcat'}),
    util.ResponseObj({
        u'?': {u'_26411a1861294160833743e45d0eaad9': {u'name': u'PetClinic'},
               u'_actions': {},
               u'id': u'fda74653-8b66-42e2-be16-12ebc87d7570',
               u'status': u'deploy failure',
               u'type': u'io.murano.apps.java.PetClinic'},
        u'database': u'769af50c-9629-4694-b623-e9b392941279',
        u'dbName': u'pet_db',
        u'dbPassword': u'Passw0rd.',
        u'dbUser': u'pet_user',
        u'name': u'PetClinic',
        u'tomcat': u'ea6a7d9b-7799-4d00-9db3-4573cb94daec',
        u'warLocation':
        u'https://dl.dropboxusercontent.com/u/1684617/petclinic.war'})]

deployment_response = [
    util.ResponseObj({
        u'action': {u'args': {},
                    u'method': u'deploy',
                    u'object_id': u'ad9762b2d82f44ca8b8a6ce4a19dd1cc'},
        u'created': u'2015-03-24T18:36:23',
        u'description':
        {u'?': {u'id': u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
                u'type': u'io.murano.Environment'},
         u'defaultNetworks':
         {u'environment':
          {u'?': {u'id':
                  u'a2be8265b01743c0bdf645772d632bf0',
                  u'type': u'io.murano.resources.NeutronNetwork'},
           u'name': u'quick-env-2-network'},
          u'flat': None},
         u'name': u'quick-env-2',
         u'services':
         [{u'?':
           {u'_26411a1861294160833743e45d0eaad9':
            {u'name': u'MySQL'},
            u'id': u'769af50c-9629-4694-b623-e9b392941279',
            u'type': u'io.murano.databases.MySql'},
           u'database': u'',
           u'instance':
           {u'?': {u'id': u'76b9ca88-c668-4e37-a830-5845adc10b0e',
                   u'type': u'io.murano.resources.LinuxMuranoInstance'},
            u'assignFloatingIp': True,
            u'availabilityZone': u'nova',
            u'flavor': u'm1.small',
            u'image': u'66e015aa-33c5-41ff-9b81-d8d17f9b02c3',
            u'keyname': u'',
            u'name': u'bcnfli7nn738y1'},
           u'name': u'MySqlDB',
           u'password': u'*** SANITIZED ***',
           u'username': u''},
          {u'?':
           {u'_26411a1861294160833743e45d0eaad9': {u'name': u'Apache Tomcat'},
            u'id': u'ea6a7d9b-7799-4d00-9db3-4573cb94daec',
            u'type': u'io.murano.apps.apache.Tomcat'},
           u'instance':
           {u'?': {u'id': u'c52dda24-38d6-4f2f-9184-abca0beaa6e9',
                   u'type': u'io.murano.resources.LinuxMuranoInstance'},
            u'assignFloatingIp': True,
            u'availabilityZone': u'nova',
            u'flavor': u'm1.small',
            u'image': u'66e015aa-33c5-41ff-9b81-d8d17f9b02c3',
            u'keyname': u'',
            u'name': u'woydqi7nn7ipc2'},
           u'name': u'Tomcat'},
          {u'?': {u'_26411a1861294160833743e45d0eaad9':
                  {u'name': u'PetClinic'},
                  u'id': u'fda74653-8b66-42e2-be16-12ebc87d7570',
                  u'type': u'io.murano.apps.java.PetClinic'},
           u'database': u'769af50c-9629-4694-b623-e9b392941279',
           u'dbName': u'pet_db',
           u'dbPassword': u'*** SANITIZED ***',
           u'dbUser': u'pet_user',
           u'name': u'PetClinic',
           u'tomcat': u'ea6a7d9b-7799-4d00-9db3-4573cb94daec',
           u'warLocation':
           u'https://dl.dropboxusercontent.com/u/1684617/petclinic.war'}]},
        u'environment_id': u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
        u'finished': u'2015-03-24T18:46:56',
        u'id': u'4aa60b31d8ce434284e03aa13c6e11e0',
        u'result': {u'isException': True,
                    u'result':
                    {u'details': u'murano.common.exceptions.TimeoutException:'
                     ' The Agent does not respondwithin 600 seconds',
                     u'message': u'[murano.common.exceptions.TimeoutException]'
                     ': The Agent does not respondwithin 600 seconds'}},
        u'started': u'2015-03-24T18:36:23',
        u'state': u'completed_w_errors',
        u'updated': u'2015-03-24T18:46:56'})]

package_response = [
    util.ResponseObj({
        u'author': u'Mirantis, Inc',
        u'categories': [],
        u'class_definitions': [u'io.murano.apps.apache.Tomcat'],
        u'created': u'2015-03-23T21:28:11',
        u'description': u'Apache Tomcat is an open source software '
        'implementation of the Java Servlet and JavaServer Pages '
        'technologies.\n',
        u'enabled': True,
        u'fully_qualified_name': u'io.murano.apps.apache.Tomcat',
        u'id': u'a7d64980999948dc96401cdce5ae2141',
        u'is_public': False,
        u'name': u'Apache Tomcat',
        u'owner_id': u'610c6afc1fc54d23a58d316bf76e5f42',
        u'supplier': {},
        u'tags': [u'Servlets', u'Server', u'Pages', u'Java'],
        u'type': u'Application',
        u'updated': u'2015-03-23T21:28:11'}),
    util.ResponseObj({
        u'author': u'Mirantis, Inc',
        u'categories': [],
        u'class_definitions': [u'io.murano.apps.linux.Git'],
        u'created': u'2015-03-23T21:26:56',
        u'description': u'Simple Git repo hosted on Linux VM.\n',
        u'enabled': True,
        u'fully_qualified_name': u'io.murano.apps.linux.Git',
        u'id': u'3ff58cdfeb27487fb3127fb8fd45109c',
        u'is_public': False,
        u'name': u'Git',
        u'owner_id': u'610c6afc1fc54d23a58d316bf76e5f42',
        u'supplier': {},
        u'tags': [u'Linux', u'connection'],
        u'type': u'Application',
        u'updated': u'2015-03-23T21:26:56'}),
    util.ResponseObj({
        u'author': u'Mirantis, Inc',
        u'categories': [],
        u'class_definitions': [u'io.murano.databases.MySql'],
        u'created': u'2015-03-23T21:28:58',
        u'description': u'MySql is a relational database management system '
        '(RDBMS), and ships with\nno GUI tools to administer MySQL databases '
        'or manage data contained within\nthe databases.\n',
        u'enabled': True,
        u'fully_qualified_name': u'io.murano.databases.MySql',
        u'id': u'884b764c0ce6439d8566b3b2da967687',
        u'is_public': False,
        u'name': u'MySQL',
        u'owner_id': u'610c6afc1fc54d23a58d316bf76e5f42',
        u'supplier': {},
        u'tags': [u'Database', u'MySql', u'SQL', u'RDBMS'],
        u'type': u'Application',
        u'updated': u'2015-03-23T21:28:58'}),
    util.ResponseObj({
        u'author': u'Mirantis, Inc',
        u'categories': [],
        u'class_definitions': [u'io.murano.apps.java.PetClinic'],
        u'created': u'2015-03-24T18:25:24',
        u'description': u'An example of a Java app running on a '
        'Apache Tomcat Servlet container and using the either Postgre SQL, '
        'or MySql database\n',
        u'enabled': True,
        u'fully_qualified_name': u'io.murano.apps.java.PetClinic',
        u'id': u'9f7c9e2ed8f9462a8f9037032ab64755',
        u'is_public': False,
        u'name': u'PetClinic',
        u'owner_id': u'610c6afc1fc54d23a58d316bf76e5f42',
        u'supplier': {},
        u'tags': [u'Servlets', u'Server', u'Pages', u'Java'],
        u'type': u'Application',
        u'updated': u'2015-03-24T18:25:24'}),
    util.ResponseObj({
        u'author': u'Mirantis, Inc',
        u'categories': [],
        u'class_definitions': [u'io.murano.databases.PostgreSql'],
        u'created': u'2015-03-23T21:29:10',
        u'description': u'PostgreSQL is a powerful, open source '
        'object-relational database system.\nIt has more than 15 years '
        'of active development and a proven architecture\nthat has earned '
        'it a strong reputation for reliability, data integrity,\nand '
        'correctness.\n',
        u'enabled': True,
        u'fully_qualified_name': u'io.murano.databases.PostgreSql',
        u'id': u'4b9c6a24c2e64f928156e0c87324c394',
        u'is_public': False,
        u'name': u'PostgreSQL',
        u'owner_id': u'610c6afc1fc54d23a58d316bf76e5f42',
        u'supplier': {},
        u'tags': [u'Database', u'Postgre', u'SQL', u'RDBMS'],
        u'type': u'Application',
        u'updated': u'2015-03-23T21:29:10'}),
    util.ResponseObj({
        u'author': u'Mirantis, Inc',
        u'categories': [],
        u'class_definitions': [u'io.murano.databases.SqlDatabase'],
        u'created': u'2015-03-24T18:26:32',
        u'description': u'This is the interface defining API for different '
        'SQL - RDBMS databases\n',
        u'enabled': True,
        u'fully_qualified_name': u'io.murano.databases',
        u'id': u'5add5a561da341c4875495c5887957a8',
        u'is_public': False,
        u'name': u'SQL Library',
        u'owner_id': u'610c6afc1fc54d23a58d316bf76e5f42',
        u'supplier': {},
        u'tags': [u'SQL', u'RDBMS'],
        u'type': u'Library',
        u'updated': u'2015-03-24T18:26:32'})]

action_response = 'c79eb72600024fa1995345a2b2eb3acd'

# Expected datasource table content
expected_states = [
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc', u'deploy failure'),
]

expected_environment_parent_types = [
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc', 'io.murano.Object'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc', 'io.murano.Environment'),
]

expected_env_properties = [
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc', u'created', '2015-03-24T18:35:14'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc', u'version', 1),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc', u'status', 'deploy failure'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc', u'name', 'quick-env-2'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc', u'updated', '2015-03-24T18:46:56'),
]

expected_service_properties = [
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e', u'ipAddresses', '10.0.11.3'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e', u'ipAddresses', '172.24.4.4'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e',
     u'networks.useFlatNetwork', 'False'),
    (u'769af50c-9629-4694-b623-e9b392941279', u'name', 'MySqlDB'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9',
     u'networks.useEnvironmentNetwork', 'True'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9',
     u'floatingIpAddress', '172.24.4.4'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570', u'dbPassword', 'Passw0rd.'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570',
     u'database', '769af50c-9629-4694-b623-e9b392941279'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570',
     u'tomcat', 'ea6a7d9b-7799-4d00-9db3-4573cb94daec'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570', u'warLocation',
     'https://dl.dropboxusercontent.com/u/1684617/petclinic.war'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9', u'availabilityZone', 'nova'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e', u'name', 'bcnfli7nn738y1'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570', u'dbUser', 'pet_user'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9',
     u'image', '66e015aa-33c5-41ff-9b81-d8d17f9b02c3'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e', u'flavor', 'm1.small'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9', u'ipAddresses', '10.0.11.4'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9', u'name', 'woydqi7nn7ipc2'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570', u'name', 'PetClinic'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9', u'assignFloatingIp', 'True'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e', u'assignFloatingIp', 'True'),
    (u'769af50c-9629-4694-b623-e9b392941279', u'password', 'Passw0rd.'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9', u'flavor', 'm1.small'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570', u'dbName', 'pet_db'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9',
     u'networks.useFlatNetwork', 'False'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e',
     u'networks.useEnvironmentNetwork', 'True'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e', u'availabilityZone', 'nova'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e',
     u'floatingIpAddress', '172.24.4.4'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9', u'ipAddresses', '172.24.4.4'),
    (u'ea6a7d9b-7799-4d00-9db3-4573cb94daec', u'name', 'Tomcat'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e',
     u'image', '66e015aa-33c5-41ff-9b81-d8d17f9b02c3'),
]

expected_package_properties = [
    (u'4b9c6a24c2e64f928156e0c87324c394', u'is_public', 'False'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c', u'tags', 'connection'),
    (u'884b764c0ce6439d8566b3b2da967687', u'created', '2015-03-23T21:28:58'),
    (u'884b764c0ce6439d8566b3b2da967687', u'tags', 'SQL'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'tags', 'Servlets'),
    (u'a7d64980999948dc96401cdce5ae2141', u'tags', 'Servlets'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'created', '2015-03-23T21:29:10'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'fully_qualified_name',
     'io.murano.apps.java.PetClinic'),
    (u'884b764c0ce6439d8566b3b2da967687', u'type', 'Application'),
    (u'5add5a561da341c4875495c5887957a8', u'created', '2015-03-24T18:26:32'),
    (u'884b764c0ce6439d8566b3b2da967687', u'name', 'MySQL'),
    (u'884b764c0ce6439d8566b3b2da967687', u'tags', 'Database'),
    (u'5add5a561da341c4875495c5887957a8', u'enabled', 'True'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'tags', 'Pages'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'tags', 'Database'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c', u'type', 'Application'),
    (u'5add5a561da341c4875495c5887957a8', u'type', 'Library'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'type', 'Application'),
    (u'884b764c0ce6439d8566b3b2da967687', u'tags', 'MySql'),
    (u'5add5a561da341c4875495c5887957a8', u'fully_qualified_name',
     'io.murano.databases'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c', u'author', 'Mirantis, Inc'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c', u'is_public', 'False'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'tags', 'SQL'),
    (u'884b764c0ce6439d8566b3b2da967687', u'enabled', 'True'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'updated', '2015-03-23T21:29:10'),
    (u'884b764c0ce6439d8566b3b2da967687', u'fully_qualified_name',
     'io.murano.databases.MySql'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'name', 'PetClinic'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'fully_qualified_name',
     'io.murano.databases.PostgreSql'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'tags', 'Java'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'tags', 'Postgre'),
    (u'a7d64980999948dc96401cdce5ae2141', u'is_public', 'False'),
    (u'a7d64980999948dc96401cdce5ae2141', u'type', 'Application'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'name', 'PostgreSQL'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c', u'tags', 'Linux'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'author', 'Mirantis, Inc'),
    (u'5add5a561da341c4875495c5887957a8', u'is_public', 'False'),
    (u'5add5a561da341c4875495c5887957a8', u'tags', 'SQL'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'author', 'Mirantis, Inc'),
    (u'5add5a561da341c4875495c5887957a8', u'class_definitions',
     'io.murano.databases.SqlDatabase'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c', u'updated', '2015-03-23T21:26:56'),
    (u'5add5a561da341c4875495c5887957a8', u'tags', 'RDBMS'),
    (u'a7d64980999948dc96401cdce5ae2141', u'enabled', 'True'),
    (u'5add5a561da341c4875495c5887957a8', u'updated', '2015-03-24T18:26:32'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'class_definitions',
     'io.murano.apps.java.PetClinic'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c', u'enabled', 'True'),
    (u'a7d64980999948dc96401cdce5ae2141', u'class_definitions',
     'io.murano.apps.apache.Tomcat'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'created', '2015-03-24T18:25:24'),
    (u'5add5a561da341c4875495c5887957a8', u'author', 'Mirantis, Inc'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'is_public', 'False'),
    (u'884b764c0ce6439d8566b3b2da967687', u'class_definitions',
     'io.murano.databases.MySql'),
    (u'884b764c0ce6439d8566b3b2da967687', u'is_public', 'False'),
    (u'884b764c0ce6439d8566b3b2da967687', u'tags', 'RDBMS'),
    (u'a7d64980999948dc96401cdce5ae2141', u'author', 'Mirantis, Inc'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c', u'name', 'Git'),
    (u'a7d64980999948dc96401cdce5ae2141', u'fully_qualified_name',
     'io.murano.apps.apache.Tomcat'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'tags', 'Server'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'tags', 'RDBMS'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'class_definitions',
     'io.murano.databases.PostgreSql'),
    (u'a7d64980999948dc96401cdce5ae2141', u'tags', 'Pages'),
    (u'4b9c6a24c2e64f928156e0c87324c394', u'enabled', 'True'),
    (u'a7d64980999948dc96401cdce5ae2141', u'tags', 'Server'),
    (u'a7d64980999948dc96401cdce5ae2141', u'updated', '2015-03-23T21:28:11'),
    (u'884b764c0ce6439d8566b3b2da967687', u'updated', '2015-03-23T21:28:58'),
    (u'a7d64980999948dc96401cdce5ae2141', u'name', 'Apache Tomcat'),
    (u'884b764c0ce6439d8566b3b2da967687', u'author', 'Mirantis, Inc'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'enabled', 'True'),
    (u'a7d64980999948dc96401cdce5ae2141', u'created', '2015-03-23T21:28:11'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c', u'created', '2015-03-23T21:26:56'),
    (u'5add5a561da341c4875495c5887957a8', u'name', 'SQL Library'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'type', 'Application'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c', u'fully_qualified_name',
     'io.murano.apps.linux.Git'),
    (u'a7d64980999948dc96401cdce5ae2141', u'tags', 'Java'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755', u'updated', '2015-03-24T18:25:24'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c', u'class_definitions',
     'io.murano.apps.linux.Git'),
]

expected_service_objects = [
    (u'769af50c-9629-4694-b623-e9b392941279',
     u'ad9762b2d82f44ca8b8a6ce4a19dd1cc', u'io.murano.databases.MySql'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570',
     u'ad9762b2d82f44ca8b8a6ce4a19dd1cc', u'io.murano.apps.java.PetClinic'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e',
     u'769af50c-9629-4694-b623-e9b392941279',
     u'io.murano.resources.LinuxMuranoInstance'),
    (u'ea6a7d9b-7799-4d00-9db3-4573cb94daec',
     u'ad9762b2d82f44ca8b8a6ce4a19dd1cc', u'io.murano.apps.apache.Tomcat'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9',
     u'ea6a7d9b-7799-4d00-9db3-4573cb94daec',
     u'io.murano.resources.LinuxMuranoInstance'),
]

expected_package_objects = [
    (u'5add5a561da341c4875495c5887957a8',
     u'610c6afc1fc54d23a58d316bf76e5f42', u'Library'),
    (u'4b9c6a24c2e64f928156e0c87324c394',
     u'610c6afc1fc54d23a58d316bf76e5f42', 'io.murano.Application'),
    (u'3ff58cdfeb27487fb3127fb8fd45109c',
     u'610c6afc1fc54d23a58d316bf76e5f42', 'io.murano.Application'),
    (u'a7d64980999948dc96401cdce5ae2141',
     u'610c6afc1fc54d23a58d316bf76e5f42', 'io.murano.Application'),
    (u'9f7c9e2ed8f9462a8f9037032ab64755',
     u'610c6afc1fc54d23a58d316bf76e5f42', 'io.murano.Application'),
    (u'884b764c0ce6439d8566b3b2da967687',
     u'610c6afc1fc54d23a58d316bf76e5f42', 'io.murano.Application'),
]

expected_service_parent_types = [
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e', 'io.murano.resources.Instance'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e',
     'io.murano.resources.LinuxInstance'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e', 'io.murano.Object'),
    (u'76b9ca88-c668-4e37-a830-5845adc10b0e',
     'io.murano.resources.LinuxMuranoInstance'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9',
     'io.murano.resources.LinuxInstance'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9',
     'io.murano.resources.LinuxMuranoInstance'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9', 'io.murano.Object'),
    (u'c52dda24-38d6-4f2f-9184-abca0beaa6e9', 'io.murano.resources.Instance'),
]

expected_service_relationships = [
    (u'fda74653-8b66-42e2-be16-12ebc87d7570',
     u'769af50c-9629-4694-b623-e9b392941279', u'database'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
     u'ea6a7d9b-7799-4d00-9db3-4573cb94daec', 'services'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570',
     u'ea6a7d9b-7799-4d00-9db3-4573cb94daec', u'tomcat'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
     u'769af50c-9629-4694-b623-e9b392941279', 'services'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
     u'fda74653-8b66-42e2-be16-12ebc87d7570', 'services'),
    (u'769af50c-9629-4694-b623-e9b392941279',
     u'76b9ca88-c668-4e37-a830-5845adc10b0e', 'instance'),
    (u'ea6a7d9b-7799-4d00-9db3-4573cb94daec',
     u'c52dda24-38d6-4f2f-9184-abca0beaa6e9', 'instance'),
]

expected_connected = [
    (u'fda74653-8b66-42e2-be16-12ebc87d7570',
     u'ea6a7d9b-7799-4d00-9db3-4573cb94daec'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570',
     u'c52dda24-38d6-4f2f-9184-abca0beaa6e9'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
     u'769af50c-9629-4694-b623-e9b392941279'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
     u'ea6a7d9b-7799-4d00-9db3-4573cb94daec'),
    (u'769af50c-9629-4694-b623-e9b392941279',
     u'76b9ca88-c668-4e37-a830-5845adc10b0e'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
     u'fda74653-8b66-42e2-be16-12ebc87d7570'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570',
     u'769af50c-9629-4694-b623-e9b392941279'),
    (u'fda74653-8b66-42e2-be16-12ebc87d7570',
     u'76b9ca88-c668-4e37-a830-5845adc10b0e'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
     u'76b9ca88-c668-4e37-a830-5845adc10b0e'),
    (u'ea6a7d9b-7799-4d00-9db3-4573cb94daec',
     u'c52dda24-38d6-4f2f-9184-abca0beaa6e9'),
    (u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
     u'c52dda24-38d6-4f2f-9184-abca0beaa6e9'),
]

expected_deployment_objects = [
    (u'a2be8265b01743c0bdf645772d632bf0', u'ad9762b2d82f44ca8b8a6ce4a19dd1cc',
     u'io.murano.resources.NeutronNetwork')
]

expected_deployment_properties = [
    (u'a2be8265b01743c0bdf645772d632bf0', u'name', 'quick-env-2-network')
]

expected_deployment_parent_types = [
    (u'a2be8265b01743c0bdf645772d632bf0', 'io.murano.Object'),
    (u'a2be8265b01743c0bdf645772d632bf0', 'io.murano.resources.Network'),
    (u'a2be8265b01743c0bdf645772d632bf0', 'io.murano.resources.NeutronNetwork')
]
