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

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils
from congress import utils


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return CinderDriver(name, keys, inbox, datapath, args)


class CinderDriver(datasource_driver.DataSourceDriver,
                   datasource_driver.ExecutionDriver):
    VOLUMES = "volumes"
    SNAPSHOTS = "snapshots"
    SERVICES = "services"

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(CinderDriver, self).__init__(name, keys, inbox, datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = self.get_cinder_credentials_v2(args)
        self.cinder_client = cinderclient.client.Client(**self.creds)
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'cinder'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack cinder.')
        result['config'] = datasource_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

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
        """Mapping between table and column names.

        Returns a dictionary mapping tablenames to the list of
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

    def get_cinder_credentials_v2(self, creds):
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
                row[row.index(s)] = utils.value_to_congress(s)
            t_list.append(tuple(row))

        return t_list

    def _translate_snapshots(self, obj):
        t_list = []
        for s in obj:
            stuple = (s.status, s.created_at, s.volume_id,
                      s.size, s.id, s.name)
            row = list(stuple)
            for v in row:
                row[row.index(v)] = utils.value_to_congress(v)
            t_list.append(tuple(row))

        return t_list

    def _translate_services(self, obj):
        t_list = []
        for s in obj:
            try:
                stuple = (s.status, s.binary, s.zone,
                          s.state, s.updated_at, s.host,
                          s.disabled_reason)
            # Havana has no disabled_reason
            except AttributeError:
                stuple = (s.status, s.binary, s.zone,
                          s.state, s.updated_at, s.host,
                          None)
            row = list(stuple)
            for v in row:
                row[row.index(v)] = utils.value_to_congress(v)
            t_list.append(tuple(row))

        return t_list

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.cinder_client, action, action_args)
