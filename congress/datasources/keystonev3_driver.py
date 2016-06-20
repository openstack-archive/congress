# Copyright (c) 2016 VMware, Inc. All rights reserved.
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

from keystoneclient.v3 import client

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    d = KeystoneV3Driver(name, keys, inbox, datapath, args)
    return d


class KeystoneV3Driver(datasource_driver.PollingDataSourceDriver,
                       datasource_driver.ExecutionDriver):
    # Table names
    USERS = "users"
    ROLES = "roles"
    PROJECTS = "projects"
    DOMAINS = "domains"

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    users_translator = {
        'translation-type': 'HDICT',
        'table-name': USERS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'The ID for the user.',
              'translator': value_trans},
             {'fieldname': 'description', 'desc': 'user description',
              'translator': value_trans},
             {'fieldname': 'name', 'desc': 'username, unique within domain',
              'translator': value_trans},
             {'fieldname': 'enabled', 'desc': 'user is enabled or not',
              'translator': value_trans},
             {'fieldname': 'project_id',
              'desc': 'ID of the default project for the user',
              'translator': value_trans},
             {'fieldname': 'domain_id',
              'desc': 'The ID of the domain for the user.',
              'translator': value_trans},
             {'fieldname': 'email', 'desc': 'email address for the user',
              'translator': value_trans})}

    roles_translator = {
        'translation-type': 'HDICT',
        'table-name': ROLES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'role ID', 'translator': value_trans},
             {'fieldname': 'name', 'desc': 'role name',
              'translator': value_trans})}

    projects_translator = {
        'translation-type': 'HDICT',
        'table-name': PROJECTS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'enabled', 'desc': 'project is enabled or not',
              'translator': value_trans},
             {'fieldname': 'description', 'desc': 'project description',
              'translator': value_trans},
             {'fieldname': 'name', 'desc': 'project name',
              'translator': value_trans},
             {'fieldname': 'domain_id',
              'desc': 'The ID of the domain for the project',
              'translator': value_trans},
             {'fieldname': 'id', 'desc': 'ID for the project',
              'translator': value_trans})}

    domains_translator = {
        'translation-type': 'HDICT',
        'table-name': DOMAINS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'enabled', 'desc': 'domain is enabled or disabled',
              'translator': value_trans},
             {'fieldname': 'description', 'desc': 'domain description',
              'translator': value_trans},
             {'fieldname': 'name', 'desc': 'domain name',
              'translator': value_trans},
             {'fieldname': 'id', 'desc': 'domain ID',
              'translator': value_trans})}

    TRANSLATORS = [users_translator, roles_translator, projects_translator,
                   domains_translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(KeystoneV3Driver, self).__init__(name, keys, inbox, datapath,
                                               args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = args
        session = ds_utils.get_keystone_session(args)
        self.client = client.Client(session=session)
        self.add_executable_client_methods(self.client,
                                           'keystoneclient.v3.client')
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'keystonev3'
        result['description'] = ('Datasource driver that interfaces with '
                                 'keystone.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

    def update_from_datasource(self):
        users = self.client.users.list()
        self._translate_users(users)
        roles = self.client.roles.list()
        self._translate_roles(roles)
        projects = self.client.projects.list()
        self._translate_projects(projects)
        domains = self.client.domains.list()
        self._translate_domains(domains)

    @ds_utils.update_state_on_changed(USERS)
    def _translate_users(self, obj):
        row_data = KeystoneV3Driver.convert_objs(
            obj, KeystoneV3Driver.users_translator)
        return row_data

    @ds_utils.update_state_on_changed(ROLES)
    def _translate_roles(self, obj):
        row_data = KeystoneV3Driver.convert_objs(
            obj, KeystoneV3Driver.roles_translator)
        return row_data

    @ds_utils.update_state_on_changed(PROJECTS)
    def _translate_projects(self, obj):
        row_data = KeystoneV3Driver.convert_objs(
            obj, KeystoneV3Driver.projects_translator)
        return row_data

    @ds_utils.update_state_on_changed(DOMAINS)
    def _translate_domains(self, obj):
        row_data = KeystoneV3Driver.convert_objs(
            obj, KeystoneV3Driver.domains_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.client, action, action_args)
