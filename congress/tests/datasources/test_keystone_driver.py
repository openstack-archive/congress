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

from congress.datasources import keystone_driver
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
                self.tenants = mock.MagicMock()

        self.users_data = [
            ResponseObj({'username': 'alice',
                         'name': 'alice foo',
                         'enabled': True,
                         'tenantId': '019b18a15f2a44c1880d57704b2c4009',
                         'id': '00f2c34a156c40058004ee8eb3320e04',
                         'email': 'alice@foo.com'}),
            ResponseObj({'username': 'bob',
                         'name': 'bob bar',
                         'enabled': False,
                         'tenantId': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                         'id': 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
                         'email': 'bob@bar.edu'})]

        self.roles_data = [
            ResponseObj({'id': 'cccccccccccccccccccccccccccccccc',
                         'name': 'admin'}),
            ResponseObj({'id': 'dddddddddddddddddddddddddddddddd',
                         'name': 'viewer'})]

        self.tenants_data = [
            ResponseObj({'enabled': True,
                         'description': 'accounting team',
                         'name': 'accounting',
                         'id': '00000000000000000000000000000001'}),
            ResponseObj({'enabled': False,
                         'description': 'eng team',
                         'name': 'eng',
                         'id': '00000000000000000000000000000002'})]

        self.keystone_client = mock.patch("keystoneclient.v2_0.client.Client",
                                          return_value=FakeClient())
        self.keystone_client.start()
        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        self.driver = keystone_driver.KeystoneDriver(args=args)
        self.driver.client.users.list.return_value = self.users_data
        self.driver.client.roles.list.return_value = self.roles_data
        self.driver.client.tenants.list.return_value = self.tenants_data

    def test_list_users(self):
        """Test conversion of complex user objects to tables."""
        self.driver.update_from_datasource()
        user_list = self.driver.state[keystone_driver.KeystoneDriver.USERS]
        self.assertIsNotNone(user_list)
        self.assertEqual(2, len(user_list))

        # Check an individual user entry
        self.assertTrue(('alice', 'alice foo', 'True',
                         '019b18a15f2a44c1880d57704b2c4009',
                         '00f2c34a156c40058004ee8eb3320e04',
                         'alice@foo.com') in user_list)
        self.assertTrue(('bob', 'bob bar', 'False',
                         'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                         'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
                         'bob@bar.edu') in user_list)

    def test_list_roles(self):
        """Test conversion of complex role objects to tables."""
        self.driver.update_from_datasource()
        roles_list = self.driver.state[keystone_driver.KeystoneDriver.ROLES]
        self.assertIsNotNone(roles_list)
        self.assertEqual(2, len(roles_list))

        # Check an individual role entry
        self.assertTrue(('cccccccccccccccccccccccccccccccc', 'admin')
                        in roles_list)
        self.assertTrue(('dddddddddddddddddddddddddddddddd', 'viewer')
                        in roles_list)

    def test_list_tenants(self):
        """Test conversion of complex tenant objects to tables."""
        self.driver.update_from_datasource()
        tenants_key = keystone_driver.KeystoneDriver.TENANTS
        tenants_list = self.driver.state[tenants_key]
        self.assertIsNotNone(tenants_list)
        self.assertEqual(2, len(tenants_list))

        # Check an individual role entry
        self.assertTrue(('True', 'accounting team', 'accounting',
                         '00000000000000000000000000000001')
                        in tenants_list)
        self.assertTrue(('False', 'eng team', 'eng',
                         '00000000000000000000000000000002')
                        in tenants_list)

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
