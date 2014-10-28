#!/usr/bin/env python
# Copyright (c) 2014 Montavista Software, LLC.
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
import cinderclient.client

from congress.datasources.datasource_driver import DataSourceDriver
from congress.utils import value_to_congress


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return CinderDriver(name, keys, inbox, datapath, args)


class CinderDriver(DataSourceDriver):
    VOLUMES = "volumes"
    SNAPSHOTS = "snapshots"
    SERVICES = "services"

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        if args is None:
            args = self.empty_credentials()
        super(CinderDriver, self).__init__(name, keys, inbox, datapath, args)
        if 'client' in args:
            self.cinder_client = args['client']
        else:
            self.creds = self.get_cinder_credentials_v2(name, args)
            self.cinder_client = cinderclient.client.Client(**self.creds)

    def update_from_datasource(self):
        self.state = {}
        volumes = self.cinder_client.volumes.list(
            detailed=True, search_opts={"all_tenants": 1})
        self.volumes = self._translate_volumes(volumes)
        snapshots = self.cinder_client.volume_snapshots.list(
            detailed=True, search_opts={"all_tenants": 1})
        self.snapshots = self._translate_snapshots(snapshots)
        services = self.cinder_client.services.list(
            host=None, binary=None)
        self.services = self._translate_services(services)

        self.state[self.VOLUMES] = set(self.volumes)
        self.state[self.SNAPSHOTS] = set(self.snapshots)
        self.state[self.SERVICES] = set(self.services)

    def get_tuple_names(self):
        return (self.VOLUMES, self.SNAPSHOTS, self.SERVICES)

    @classmethod
    def get_schema(cls):
        """Returns a dictionary mapping tablenames to the list of
        column names for that table.  Both tablenames and columnnames
        are strings.
        """
        d = {}
        d[cls.VOLUMES] = ('id', 'size', 'user_id', 'status',
                          'description', 'name', 'bootable',
                          'created_at', 'volume_type')
        d[cls.SNAPSHOTS] = ('status', 'created_at', 'volume_id',
                            'size', 'id', 'name')
        d[cls.SERVICES] = ('status', 'binary', 'zone',
                           'state', 'updated_at', 'host',
                           'disabled_reason')
        return d

    def get_cinder_credentials_v2(self, name, args):
        creds = self.get_credentials(name, args)
        d = {}
        d['version'] = '2'
        d['username'] = creds['username']
        d['api_key'] = creds['password']
        d['auth_url'] = creds['auth_url']
        d['project_id'] = creds['tenant_name']
        return d

    def _translate_volumes(self, obj):
        t_list = []
        for v in obj:
            vtuple = (v.id, v.size, v.user_id, v.status,
                      v.description, v.name, v.bootable,
                      v.created_at, v.volume_type)
            row = list(vtuple)
            for s in row:
                row[row.index(s)] = value_to_congress(s)
            t_list.append(tuple(row))

        return t_list

    def _translate_snapshots(self, obj):
        t_list = []
        for s in obj:
            stuple = (s.status, s.created_at, s.volume_id,
                      s.size, s.id, s.name)
            row = list(stuple)
            for v in row:
                row[row.index(v)] = value_to_congress(v)
            t_list.append(tuple(row))

        return t_list

    def _translate_services(self, obj):
        t_list = []
        for s in obj:
            stuple = (s.status, s.binary, s.zone,
                      s.state, s.updated_at, s.host,
                      s.disabled_reason)
            row = list(stuple)
            for v in row:
                row[row.index(v)] = value_to_congress(v)
            t_list.append(tuple(row))

        return t_list


def main():
    driver = CinderDriver()
    driver.update_from_datasource()
    print "Original api data"
    print str(driver.raw_state)
    print "Resulting state"
    print str(driver.state)

if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        raise
