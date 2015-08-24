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
from oslo_log import log as logging
from tempest_lib import decorators

from tempest import clients  # noqa
from tempest import config  # noqa
from tempest import exceptions  # noqa
from tempest.scenario import manager_congress  # noqa
from tempest import test  # noqa


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestKeystoneV2Driver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def check_preconditions(cls):
        super(TestKeystoneV2Driver, cls).check_preconditions()
        if not (CONF.network.tenant_networks_reachable or
                CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or'
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    def setUp(cls):
        super(TestKeystoneV2Driver, cls).setUp()
        cls.os = clients.Manager(cls.admin_manager.auth_provider.credentials)
        cls.keystone = cls.os.identity_client
        cls.datasource_id = manager_congress.get_datasource_id(
            cls.admin_manager.congress_client, 'keystone')

    @decorators.skip_because(bug='1486246')
    @test.attr(type='smoke')
    def test_keystone_users_table(self):
        user_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'users')['columns'])
        user_id_col = next(i for i, c in enumerate(user_schema)
                           if c['name'] == 'id')

        def _check_data_table_keystone_users():
            # Fetch data from keystone each time, because this test may start
            # before keystone has all the users.
            users = self.keystone.get_users()
            user_map = {}
            for user in users:
                user_map[user['id']] = user

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'users'))
            for row in results['results']:
                try:
                    user_row = user_map[row['data'][user_id_col]]
                except KeyError:
                    return False
                for index in range(len(user_schema)):
                    if ((user_schema[index]['name'] == 'tenantId' and
                            'tenantId' not in user_row) or
                        (user_schema[index]['name'] == 'email' and
                            'email' not in user_row)):
                        # Keystone does not return the tenantId or email column
                        # if not present.
                        pass
                    elif (str(row['data'][index]) !=
                            str(user_row[user_schema[index]['name']])):
                        return False
            return True

        if not test.call_until_true(func=_check_data_table_keystone_users,
                                    duration=100, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.skip_because(bug='1486246')
    @test.attr(type='smoke')
    def test_keystone_roles_table(self):
        role_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'roles')['columns'])
        role_id_col = next(i for i, c in enumerate(role_schema)
                           if c['name'] == 'id')

        def _check_data_table_keystone_roles():
            # Fetch data from keystone each time, because this test may start
            # before keystone has all the users.
            roles = self.keystone.list_roles()
            roles_map = {}
            for role in roles:
                roles_map[role['id']] = role

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'roles'))
            for row in results['results']:
                try:
                    role_row = roles_map[row['data'][role_id_col]]
                except KeyError:
                    return False
                for index in range(len(role_schema)):
                    if (str(row['data'][index]) !=
                            str(role_row[role_schema[index]['name']])):
                        return False
            return True

        if not test.call_until_true(func=_check_data_table_keystone_roles,
                                    duration=100, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.skip_because(bug='1486246')
    @test.attr(type='smoke')
    def test_keystone_tenants_table(self):
        tenant_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'tenants')['columns'])
        tenant_id_col = next(i for i, c in enumerate(tenant_schema)
                             if c['name'] == 'id')

        def _check_data_table_keystone_tenants():
            # Fetch data from keystone each time, because this test may start
            # before keystone has all the users.
            tenants = self.keystone.list_tenants()
            tenants_map = {}
            for tenant in tenants:
                tenants_map[tenant['id']] = tenant

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'tenants'))
            for row in results['results']:
                try:
                    tenant_row = tenants_map[row['data'][tenant_id_col]]
                except KeyError:
                    return False
                for index in range(len(tenant_schema)):
                    if (str(row['data'][index]) !=
                            str(tenant_row[tenant_schema[index]['name']])):
                        return False
            return True

        if not test.call_until_true(func=_check_data_table_keystone_tenants,
                                    duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")
