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
# included in global_requirements.txt)
import sys

sys.modules['muranoclient'] = mock.Mock()
sys.modules['muranoclient.client'] = mock.Mock()

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
        env_list = self.driver.murano_client.environments.list()
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver._translate_environments(env_list)

        env_list = list(self.driver.state['states'])

        # the list shouldn't be empty
        self.assertIsNotNone(env_list)

        # the list should contain two elements
        self.assertEqual(2, len(env_list))

        # check the environment states
        self.assertTrue(
            (u'0c45ff66ce744568a524936da7ebaa7d', u'pending') in env_list)
        self.assertTrue(
            (u'9d929a329182469cb11a1841db95b8da', u'ready') in env_list)

    def test_translate_services(self):
        """Test conversion of environments objects to tables."""
        env_list = self.driver.murano_client.environments.list()
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver._translate_services(env_list)

        # the object list
        obj_list = list(self.driver.state[self.driver.OBJECTS])

        # the list shouldn't be empty
        self.assertIsNotNone(obj_list)

        # the list should contain two elements
        self.assertEqual(3, len(obj_list))

        # check the environment states
        self.assertTrue(
            (u'03a0137f-4644-4943-9be9-66b612e8f885',
             u'9d929a329182469cb11a1841db95b8da',
             u'io.murano.apps.linux.Telnet') in obj_list)
        self.assertTrue(
            (u'03a0137f-4644-4943-9be9-66b612e8f885',
             u'9d929a329182469cb11a1841db95b8da',
             u'io.murano.apps.linux.Telnet') in obj_list)

    def test_translate_environment_services(self):
        """Test conversion of environments objects to tables."""
        env_list = self.driver.murano_client.environments.list()
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver._translate_services(env_list)

        for env in env_list:
            services = self.murano_client.services.list(env.id)
            self.driver._translate_environment_services(services, env.id)

        # the object list
        obj_list = list(self.driver.state[self.driver.OBJECTS])

        # the list shouldn't be empty
        self.assertIsNotNone(obj_list)

        # the list should contain two elements
        self.assertEqual(3, len(obj_list))

        # check the environment states
        self.assertTrue(
            (u'03a0137f-4644-4943-9be9-66b612e8f885',
             u'9d929a329182469cb11a1841db95b8da',
             u'io.murano.apps.linux.Telnet') in obj_list)
        self.assertTrue(
            (u'03a0137f-4644-4943-9be9-66b612e8f885',
             u'9d929a329182469cb11a1841db95b8da',
             u'io.murano.apps.linux.Telnet') in obj_list)

    def test_translate_packages(self):
        """Test conversion of environments objects to tables."""
        pkg_list = self.driver.murano_client.packages.list()
        self.driver.state[self.driver.STATES] = set()
        self.driver.state[self.driver.OBJECTS] = set()
        self.driver.state[self.driver.PROPERTIES] = set()
        self.driver.state[self.driver.PARENT_TYPES] = set()
        self.driver._translate_packages(pkg_list)

        # the object list
        obj_list = list(self.driver.state[self.driver.OBJECTS])

        properties_list = list(self.driver.state[self.driver.PROPERTIES])

        # the list shouldn't be empty
        self.assertIsNotNone(obj_list)
        self.assertIsNotNone(properties_list)

        # the list should contain two elements
        self.assertEqual(2, len(obj_list))
        self.assertEqual(17, len(properties_list))

        # check the environment states
        self.assertTrue((u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1',
                         'enabled', True) in properties_list)
        self.assertTrue((u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1',
                         'is_public', False) in properties_list)
        self.assertTrue((u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1',
                         'tag', u'Pages') in properties_list)
        self.assertTrue((u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1',
                         'tag', u'Java') in properties_list)
        self.assertTrue((u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1',
                         'tag', u'Server') in properties_list)
        self.assertTrue((u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1',
                         'tag', u'Servlets') in properties_list)
        self.assertTrue((u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1',
                         'name', u'Apache Tomcat') in properties_list)
        self.assertTrue(
            (u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1',
             'fully_qualified_name',
             u'io.murano.apps.apache.Tomcat') in properties_list)
        self.assertTrue((u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1',
                         'author', u'Mirantis, Inc') in properties_list)
        self.assertTrue((u'68cd33f3a1bc41abbd9a7b7a8e2a3ae1',
                         'category', u'Web') in properties_list)
        self.assertTrue((u'18d7a400ab034a368e2cb6f7466d8214',
                         'tag', u'connection') in properties_list)
        self.assertTrue((u'18d7a400ab034a368e2cb6f7466d8214',
                         'author', u'Mirantis, Inc') in properties_list)
        self.assertTrue(
            (u'18d7a400ab034a368e2cb6f7466d8214',
             'fully_qualified_name',
             u'io.murano.apps.linux.Telnet') in properties_list)
        self.assertTrue((u'18d7a400ab034a368e2cb6f7466d8214',
                         'name', u'Telnet') in properties_list)
        self.assertTrue((u'18d7a400ab034a368e2cb6f7466d8214',
                         'tag', u'Linux') in properties_list)
        self.assertTrue((u'18d7a400ab034a368e2cb6f7466d8214',
                         'is_public', False) in properties_list)
        self.assertTrue((u'18d7a400ab034a368e2cb6f7466d8214',
                         'enabled', True) in properties_list)

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

service_response = [ResponseObj(
    {u'instance': {u'name': u'tuerfi4oo8pp71',
                   u'securityGroupName': None,
                   u'assignFloatingIp': True,
                   u'ipAddresses': [u'10.0.8.2', u'172.24.4.4'],
                   u'networks': {u'useFlatNetwork': False,
                                 u'primaryNetwork': None,
                                 u'useEnvironmentNetwork': True,
                                 u'customNetworks': []},
                   u'keyname': u'cloud',
                   u'sharedIps': [],
                   u'floatingIpAddress': u'172.24.4.4',
                   u'flavor': u'm1.small',
                   u'image': u'ubuntu-murano',
                   u'?': {u'_actions': {},
                          u'type': u'io.murano.resources.LinuxMuranoInstance',
                          u'id': u'6392a024-ebf8-49d2-990a-d6ba33ac70c9'}},
     u'name': u'Telnet',
     u'?': {u'status': u'ready',
            u'_26411a1861294160833743e45d0eaad9': {u'name': u'Telnet'},
            u'type': u'io.murano.apps.linux.Telnet',
            u'id': u'03a0137f-4644-4943-9be9-66b612e8f885',
            u'_actions': {}}})]

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
