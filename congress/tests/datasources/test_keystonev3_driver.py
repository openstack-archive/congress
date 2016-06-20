# Copyright (c) 2014 VMware, Inc. All rights reserved.
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

from congress.datasources import keystonev3_driver
from congress.tests import base
from congress.tests.datasources import util
from congress.tests import helper

ResponseObj = util.ResponseObj


class TestKeystoneDriver(base.TestCase):

    def setUp(self):
        super(TestKeystoneDriver, self).setUp()

        class FakeClient(object):
            def __init__(self):
                self.users = mock.MagicMock()
                self.roles = mock.MagicMock()
                self.projects = mock.MagicMock()
                self.domains = mock.MagicMock()

        self.users_data = [
            ResponseObj({'id': '00f2c34a156c40058004ee8eb3320e04',
                         'description': 'test user 1',
                         'name': 'alice',
                         'enabled': True,
                         'project_id': '019b18a15f2a44c1880d57704b2c4009',
                         'domain_id': 'default',
                         'email': 'alice@foo.com'}),
            ResponseObj({'id': 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
                         'description': 'test user 2',
                         'name': 'bob',
                         'enabled': False,
                         'project_id': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                         'domain_id': 'default',
                         'email': 'bob@bar.edu'})]

        self.roles_data = [
            ResponseObj({'id': 'cccccccccccccccccccccccccccccccc',
                         'name': 'admin'}),
            ResponseObj({'id': 'dddddddddddddddddddddddddddddddd',
                         'name': 'viewer'})]

        self.projects_data = [
            ResponseObj({'enabled': True,
                         'description': 'accounting team',
                         'name': 'accounting',
                         'domain_id': 'default',
                         'id': '00000000000000000000000000000001'}),
            ResponseObj({'enabled': False,
                         'description': 'eng team',
                         'domain_id': 'default',
                         'name': 'eng',
                         'id': '00000000000000000000000000000002'})]

        self.domains_data = [
            ResponseObj({'enabled': True,
                         'description': 'domain 1',
                         'name': 'default',
                         'id': '1fbe4e6fedb34050ad56c6e5dd225998'}),

            ResponseObj({'enabled': False,
                         'description': 'domain 2',
                         'name': 'test domain',
                         'id': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'})]

        self.keystone_client = mock.patch("keystoneclient.v3.client.Client",
                                          return_value=FakeClient())
        self.keystone_client.start()
        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        self.driver = keystonev3_driver.KeystoneV3Driver(args=args)
        self.driver.client.users.list.return_value = self.users_data
        self.driver.client.roles.list.return_value = self.roles_data
        self.driver.client.projects.list.return_value = self.projects_data
        self.driver.client.domains.list.return_value = self.domains_data

    def test_list_users(self):
        """Test conversion of complex user objects to tables."""
        self.driver.update_from_datasource()
        user_list = self.driver.state[keystonev3_driver.KeystoneV3Driver.USERS]
        self.assertIsNotNone(user_list)
        self.assertEqual(2, len(user_list))

        # Check an individual user entry
        self.assertTrue(('00f2c34a156c40058004ee8eb3320e04', 'test user 1',
                         'alice', 'True', '019b18a15f2a44c1880d57704b2c4009',
                         'default', 'alice@foo.com') in user_list)
        self.assertTrue(('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb', 'test user 2',
                         'bob', 'False', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                         'default', 'bob@bar.edu') in user_list)

    def test_list_roles(self):
        """Test conversion of complex role objects to tables."""
        self.driver.update_from_datasource()
        roles_table = keystonev3_driver.KeystoneV3Driver.ROLES
        roles_list = self.driver.state[roles_table]
        self.assertIsNotNone(roles_list)
        self.assertEqual(2, len(roles_list))

        # Check an individual role entry
        self.assertTrue(('cccccccccccccccccccccccccccccccc', 'admin')
                        in roles_list)
        self.assertTrue(('dddddddddddddddddddddddddddddddd', 'viewer')
                        in roles_list)

    def test_list_domains(self):
        self.driver.update_from_datasource()
        domains_table = keystonev3_driver.KeystoneV3Driver.DOMAINS
        domains_list = self.driver.state[domains_table]
        self.assertIsNotNone(domains_list)
        self.assertEqual(2, len(domains_list))

        # Check an individual role entry
        self.assertTrue(('False', 'domain 2', 'test domain',
                         'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa') in domains_list)
        self.assertTrue(('True', 'domain 1', 'default',
                         '1fbe4e6fedb34050ad56c6e5dd225998') in domains_list)

    def test_list_projects(self):
        """Test conversion of complex tenant objects to tables."""
        self.driver.update_from_datasource()
        projects_table = keystonev3_driver.KeystoneV3Driver.PROJECTS
        projects_list = self.driver.state[projects_table]
        self.assertIsNotNone(projects_list)
        self.assertEqual(2, len(projects_list))

        # Check an individual role entry
        self.assertTrue(('True', 'accounting team', 'accounting', 'default',
                         '00000000000000000000000000000001')
                        in projects_list)
        self.assertTrue(('False', 'eng team', 'eng', 'default',
                         '00000000000000000000000000000002')
                        in projects_list)

    def test_execute(self):
        class KeystoneClient(object):
            def __init__(self):
                self.testkey = None

            def enableProject(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        keystone_client = KeystoneClient()
        self.driver.client = keystone_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('enableProject', api_args)

        self.assertEqual(expected_ans, keystone_client.testkey)
