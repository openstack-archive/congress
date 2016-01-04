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

import keystoneclient.v2_0.client

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    d = KeystoneDriver(name, keys, inbox, datapath, args)
    return d


class KeystoneDriver(datasource_driver.PollingDataSourceDriver,
                     datasource_driver.ExecutionDriver):
    # Table names
    USERS = "users"
    ROLES = "roles"
    TENANTS = "tenants"

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    users_translator = {
        'translation-type': 'HDICT',
        'table-name': USERS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'username', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'enabled', 'translator': value_trans},
             {'fieldname': 'tenantId', 'translator': value_trans},
             {'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'email', 'translator': value_trans})}

    roles_translator = {
        'translation-type': 'HDICT',
        'table-name': ROLES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans})}

    tenants_translator = {
        'translation-type': 'HDICT',
        'table-name': TENANTS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'enabled', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'id', 'translator': value_trans})}

    TRANSLATORS = [users_translator, roles_translator, tenants_translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(KeystoneDriver, self).__init__(name, keys, inbox, datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = self.get_keystone_credentials_v2(args)
        self.client = keystoneclient.v2_0.client.Client(**self.creds)
        self.add_executable_client_methods(self.client,
                                           'keystoneclient.v2_0.client')
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'keystone'
        result['description'] = ('Datasource driver that interfaces with '
                                 'keystone.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

    def get_keystone_credentials_v2(self, args):
        creds = args
        d = {}
        d['version'] = '2'
        d['username'] = creds['username']
        d['password'] = creds['password']
        d['auth_url'] = creds['auth_url']
        d['tenant_name'] = creds['tenant_name']
        return d

    def update_from_datasource(self):
        users = self.client.users.list()
        self._translate_users(users)
        roles = self.client.roles.list()
        self._translate_roles(roles)
        tenants = self.client.tenants.list()
        self._translate_tenants(tenants)

    @ds_utils.update_state_on_changed(USERS)
    def _translate_users(self, obj):
        row_data = KeystoneDriver.convert_objs(obj,
                                               KeystoneDriver.users_translator)
        return row_data

    @ds_utils.update_state_on_changed(ROLES)
    def _translate_roles(self, obj):
        row_data = KeystoneDriver.convert_objs(obj,
                                               KeystoneDriver.roles_translator)
        return row_data

    @ds_utils.update_state_on_changed(TENANTS)
    def _translate_tenants(self, obj):
        row_data = KeystoneDriver.convert_objs(
            obj, KeystoneDriver.tenants_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.client, action, action_args)
