#!/usr/bin/env python
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
import mock

from congress.datasources.keystone_driver import KeystoneDriver
from congress.datasources.tests.unit.util import ResponseObj
from congress.tests import base
from congress.tests import helper


class TestKeystoneDriver(base.TestCase):

    def setUp(self):
        super(TestKeystoneDriver, self).setUp()
        self.keystone_client = mock.MagicMock()

        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        args['client'] = self.keystone_client
        self.driver = KeystoneDriver(args=args)

    def test_list_users(self):
        """Test conversion of complex user objects to tables."""
        users_data = [
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

        user_list = self.driver._get_tuple_list(users_data,
                                                KeystoneDriver.USERS)
        self.assertIsNotNone(user_list)
        self.assertEqual(2, len(user_list))

        # Check an individual user entry
        self.assertEqual(('alice', 'alice foo', True,
                          '019b18a15f2a44c1880d57704b2c4009',
                          '00f2c34a156c40058004ee8eb3320e04',
                          'alice@foo.com'),
                         user_list[0])
        self.assertEqual(('bob', 'bob bar', False,
                          'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
                          'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb',
                          'bob@bar.edu'),
                         user_list[1])

    def test_list_roles(self):
        """Test conversion of complex role objects to tables."""
        roles_data = [
            ResponseObj({'id': 'cccccccccccccccccccccccccccccccc',
                         'name': 'admin'}),
            ResponseObj({'id': 'dddddddddddddddddddddddddddddddd',
                         'name': 'viewer'})]

        roles_list = self.driver._get_tuple_list(roles_data,
                                                 KeystoneDriver.ROLES)
        self.assertIsNotNone(roles_list)
        self.assertEqual(2, len(roles_list))

        # Check an individual role entry
        self.assertEqual(('cccccccccccccccccccccccccccccccc', 'admin'),
                         roles_list[0])
        self.assertEqual(('dddddddddddddddddddddddddddddddd', 'viewer'),
                         roles_list[1])

    def test_list_tenants(self):
        """Test conversion of complex tenant objects to tables."""
        tenants_data = [
            ResponseObj({'enabled': True,
                         'description': 'accounting team',
                         'name': 'accounting',
                         'id': '00000000000000000000000000000001'}),
            ResponseObj({'enabled': False,
                         'description': 'eng team',
                         'name': 'eng',
                         'id': '00000000000000000000000000000002'})]

        tenants_list = self.driver._get_tuple_list(tenants_data,
                                                   KeystoneDriver.TENANTS)
        self.assertIsNotNone(tenants_list)
        self.assertEqual(2, len(tenants_list))

        # Check an individual role entry
        self.assertEqual((True, 'accounting team', 'accounting',
                          '00000000000000000000000000000001'),
                         tenants_list[0])
        self.assertEqual((False, 'eng team', 'eng',
                          '00000000000000000000000000000002'),
                         tenants_list[1])
