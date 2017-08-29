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

from tempest import clients
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions

from congress_tempest_tests.tests.scenario import manager_congress

CONF = config.CONF


class TestKeystoneV3Driver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def skip_checks(cls):
        super(TestKeystoneV3Driver, cls).skip_checks()
        if not (CONF.network.project_networks_reachable or
                CONF.network.public_network_id):
            msg = ('Either project_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    def setUp(self):
        super(TestKeystoneV3Driver, self).setUp()
        self.os_primary = clients.Manager(
            self.os_admin.auth_provider.credentials)
        self.keystone = self.os_primary.identity_v3_client
        self.projects_client = self.os_primary.projects_client
        self.domains_client = self.os_primary.domains_client
        self.roles_client = self.os_primary.roles_v3_client
        self.users_client = self.os_primary.users_v3_client
        self.datasource_id = manager_congress.get_datasource_id(
            self.os_admin.congress_client, 'keystonev3')

    @decorators.attr(type='smoke')
    def test_keystone_users_table(self):
        user_schema = (
            self.os_admin.congress_client.show_datasource_table_schema(
                self.datasource_id, 'users')['columns'])
        user_id_col = next(i for i, c in enumerate(user_schema)
                           if c['name'] == 'id')

        def _check_data_table_keystone_users():
            # Fetch data from keystone each time, because this test may start
            # before keystone has all the users.
            users = self.users_client.list_users()['users']
            user_map = {}
            for user in users:
                user_map[user['id']] = user

            results = (
                self.os_admin.congress_client.list_datasource_rows(
                    self.datasource_id, 'users'))
            for row in results['results']:
                try:
                    user_row = user_map[row['data'][user_id_col]]
                except KeyError:
                    return False
                for index in range(len(user_schema)):
                    if ((user_schema[index]['name'] == 'default_project_id' and
                         'default_project_id' not in user_row)):
                        # Keystone does not return the tenantId or email column
                        # if not present.
                        pass
                    elif (str(row['data'][index]) !=
                            str(user_row[user_schema[index]['name']])):
                        return False
            return True

        if not test_utils.call_until_true(
                func=_check_data_table_keystone_users,
                duration=100, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.attr(type='smoke')
    def test_keystone_roles_table(self):
        role_schema = (
            self.os_admin.congress_client.show_datasource_table_schema(
                self.datasource_id, 'roles')['columns'])
        role_id_col = next(i for i, c in enumerate(role_schema)
                           if c['name'] == 'id')

        def _check_data_table_keystone_roles():
            # Fetch data from keystone each time, because this test may start
            # before keystone has all the users.
            roles = self.roles_client.list_roles()['roles']
            roles_map = {}
            for role in roles:
                roles_map[role['id']] = role

            results = (
                self.os_admin.congress_client.list_datasource_rows(
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

        if not test_utils.call_until_true(
                func=_check_data_table_keystone_roles,
                duration=100, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.attr(type='smoke')
    def test_keystone_domains_table(self):
        domains_schema = (
            self.os_admin.congress_client.show_datasource_table_schema(
                self.datasource_id, 'domains')['columns'])
        domain_id_col = next(i for i, c in enumerate(domains_schema)
                             if c['name'] == 'id')

        def _check_data_table_keystone_domains():
            # Fetch data from keystone each time, because this test may start
            # before keystone has all the users.
            domains = self.domains_client.list_domains()['domains']
            domains_map = {}
            for domain in domains:
                domains_map[domain['id']] = domain

            results = (
                self.os_admin.congress_client.list_datasource_rows(
                    self.datasource_id, 'domains'))
            for row in results['results']:
                try:
                    domain_row = domains_map[row['data'][domain_id_col]]
                except KeyError:
                    return False
                for index in range(len(domains_schema)):
                    if (str(row['data'][index]) !=
                            str(domain_row[domains_schema[index]['name']])):
                        return False
            return True

        if not test_utils.call_until_true(
                func=_check_data_table_keystone_domains,
                duration=100, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.attr(type='smoke')
    def test_keystone_projects_table(self):
        projects_schema = (
            self.os_admin.congress_client.show_datasource_table_schema(
                self.datasource_id, 'projects')['columns'])
        project_id_col = next(i for i, c in enumerate(projects_schema)
                              if c['name'] == 'id')

        def _check_data_table_keystone_projects():
            # Fetch data from keystone each time, because this test may start
            # before keystone has all the users.
            projects = self.projects_client.list_projects()['projects']
            projects_map = {}
            for project in projects:
                projects_map[project['id']] = project

            results = (
                self.os_admin.congress_client.list_datasource_rows(
                    self.datasource_id, 'projects'))
            for row in results['results']:
                try:
                    project_row = projects_map[row['data'][project_id_col]]
                except KeyError:
                    return False
                for index in range(len(projects_schema)):
                    if (str(row['data'][index]) !=
                            str(project_row[projects_schema[index]['name']])):
                        return False
            return True

        if not test_utils.call_until_true(
                func=_check_data_table_keystone_projects,
                duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @decorators.attr(type='smoke')
    def test_update_no_error(self):
        if not test_utils.call_until_true(
                func=lambda: self.check_datasource_no_error('keystonev3'),
                duration=30, sleep_for=5):
            raise exceptions.TimeoutException('Datasource could not poll '
                                              'without error.')
