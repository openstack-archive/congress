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
import datetime
import keystoneclient.v2_0.client

from congress.datasources.datasource_driver import DataSourceDriver


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return KeystoneDriver(name, keys, inbox, datapath, args)


# TODO(thinrichs): figure out how to move even more of this boilerplate
#   into DataSourceDriver.  E.g. change all the classes to Driver instead of
#   NeutronDriver, NovaDriver, etc. and move the d6instantiate function to
#   DataSourceDriver.
class KeystoneDriver(DataSourceDriver):
    # Table names
    USERS = "users"
    ROLES = "roles"
    TENANTS = "tenants"

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        if args is None:
            args = self.empty_credentials()
        super(KeystoneDriver, self).__init__(name, keys, inbox, datapath, args)
        if 'client' in args:
            self.client = args['client']
        else:
            self.creds = self.get_keystone_credentials_v2(name, args)
            self.client = keystoneclient.v2_0.client.Client(**self.creds)

    def update_from_datasource(self):
        # Fetch state from keystone
        self.state = {}
        self.users = self._get_tuple_list(self.client.users.list(),
                                          self.USERS)
        self.roles = self._get_tuple_list(self.client.roles.list(), self.ROLES)
        self.tenants = self._get_tuple_list(self.client.tenants.list(),
                                            self.TENANTS)

        self.last_updated = datetime.datetime.now()

        # Set local state
        # TODO(thinrichs): use self.state everywhere instead of self.servers...
        self.state[self.USERS] = set(self.users)
        self.state[self.ROLES] = set(self.roles)
        self.state[self.TENANTS] = set(self.tenants)

    @classmethod
    def get_schema(cls):
        """Returns a dictionary mapping tablenames to the list of
        column names for that table.  Both tablenames and columnnames
        are strings.
        """
        d = {}
        d[cls.USERS] = ('username', 'name', 'enabled', 'tenantId', 'id',
                        'email')
        d[cls.ROLES] = ('id', 'name')
        d[cls.TENANTS] = ('enabled', 'description', 'name', 'id')
        return d

    def get_keystone_credentials_v2(self, name, args):
        creds = self.get_credentials(name, args)
        d = {}
        d['version'] = '2'
        d['username'] = creds['username']
        d['password'] = creds['password']
        d['auth_url'] = creds['auth_url']
        d['tenant_name'] = creds['tenant_name']
        return d

    def _get_tuple_list(self, obj, type):
        if type == self.USERS:
            t_list = [(u.username, u.name, u.enabled, u.tenantId, u.id,
                       u.email) for u in obj]
        elif type == self.ROLES:
            t_list = [(r.id, r.name) for r in obj]
        elif type == self.TENANTS:
            t_list = [(t.enabled, t.description, t.name, t.id) for t in obj]
        else:
            raise AssertionError('Unexpected tuple type: %s' % type)
        return t_list


def main():
    def get_all(self, type):
        if type not in self.state:
            self.update_from_datasource()
        assert type in self.state, "Must choose existing tablename"
        return self.state[type]

    driver = KeystoneDriver()
    print "Last updated: %s" % driver.get_last_updated_time()

    print "Starting Keystone Sync Service"

    # sync with the keystone service
    driver.update_from_datasource()
    print "Users: %s" % driver.get_all(driver.USERS)
    print "Roles: %s" % driver.get_all(driver.ROLES)
    print "Tenants: %s" % driver.get_all(driver.TENANTS)
    print "Last updated: %s" % driver.get_last_updated_time()
    print "Sync completed"
    print "-----------------------------------------"


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        raise
