# Copyright (c) 2013 VMware, Inc. All rights reserved.
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

import novaclient.client
from oslo_log import log as logging
import six

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return NovaDriver(name, keys, inbox, datapath, args)


class NovaDriver(datasource_driver.PollingDataSourceDriver,
                 datasource_driver.ExecutionDriver):
    SERVERS = "servers"
    FLAVORS = "flavors"
    HOSTS = "hosts"
    FLOATING_IPS = "floating_IPs"
    SERVICES = 'services'
    AVAILABILITY_ZONES = "availability_zones"

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    def safe_id(x):
        if isinstance(x, six.string_types):
            return x
        try:
            return x['id']
        except Exception:
            return str(x)

    servers_translator = {
        'translation-type': 'HDICT',
        'table-name': SERVERS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'The UUID for the server',
              'translator': value_trans},
             {'fieldname': 'name', 'desc': 'Name of the server',
              'translator': value_trans},
             {'fieldname': 'hostId', 'col': 'host_id',
              'desc': 'The UUID for the host', 'translator': value_trans},
             {'fieldname': 'status', 'desc': 'The server status',
              'translator': value_trans},
             {'fieldname': 'tenant_id', 'desc': 'The tenant ID',
              'translator': value_trans},
             {'fieldname': 'user_id',
              'desc': 'The user ID of the user who owns the server',
              'translator': value_trans},
             {'fieldname': 'image', 'col': 'image_id',
              'desc': 'Name or ID of image',
              'translator': {'translation-type': 'VALUE',
                             'extract-fn': safe_id}},
             {'fieldname': 'flavor', 'col': 'flavor_id',
              'desc': 'Name of the flavor',
              'translator': {'translation-type': 'VALUE',
                             'extract-fn': safe_id}},
             {'fieldname': 'OS-EXT-AZ:availability_zone', 'col': 'zone',
              'desc': 'The availability zone of host',
              'translator': value_trans},
             {'fieldname': 'OS-EXT-SRV-ATTR:hypervisor_hostname',
              'desc': ('The hostname of hypervisor where the server is' +
                       'running'),
              'col': 'host_name', 'translator': value_trans})}

    flavors_translator = {
        'translation-type': 'HDICT',
        'table-name': FLAVORS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'ID of the flavor',
              'translator': value_trans},
             {'fieldname': 'name', 'desc': 'Name of the flavor',
              'translator': value_trans},
             {'fieldname': 'vcpus', 'desc': 'Number of vcpus',
              'translator': value_trans},
             {'fieldname': 'ram', 'desc': 'Memory size in MB',
              'translator': value_trans},
             {'fieldname': 'disk', 'desc': 'Disk size in GB',
              'translator': value_trans},
             {'fieldname': 'ephemeral', 'desc': 'Ephemeral space size in GB',
              'translator': value_trans},
             {'fieldname': 'rxtx_factor', 'desc': 'RX/TX factor',
              'translator': value_trans})}

    hosts_translator = {
        'translation-type': 'HDICT',
        'table-name': HOSTS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'host_name', 'desc': 'Name of host',
              'translator': value_trans},
             {'fieldname': 'service', 'desc': 'Enabled service',
              'translator': value_trans},
             {'fieldname': 'zone', 'desc': 'The availability zone of host',
              'translator': value_trans})}

    floating_ips_translator = {
        'translation-type': 'HDICT',
        'table-name': FLOATING_IPS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'fixed_ip', 'desc': 'Fixed IP Address',
              'translator': value_trans},
             {'fieldname': 'id', 'desc': 'Unique ID',
              'translator': value_trans},
             {'fieldname': 'ip', 'desc': 'IP Address',
              'translator': value_trans},
             {'fieldname': 'instance_id',
              'desc': 'Name or ID of host', 'translator': value_trans},
             {'fieldname': 'pool', 'desc': 'Name of Floating IP Pool',
              'translator': value_trans})}

    services_translator = {
        'translation-type': 'HDICT',
        'table-name': SERVICES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'col': 'service_id', 'desc': 'Service ID',
              'translator': value_trans},
             {'fieldname': 'binary', 'desc': 'Service binary',
              'translator': value_trans},
             {'fieldname': 'host', 'desc': 'Host Name',
              'translator': value_trans},
             {'fieldname': 'zone', 'desc': 'Availability Zone',
              'translator': value_trans},
             {'fieldname': 'status', 'desc': 'Status of service',
              'translator': value_trans},
             {'fieldname': 'state', 'desc': 'State of service',
              'translator': value_trans},
             {'fieldname': 'updated_at', 'desc': 'Last updated time',
              'translator': value_trans},
             {'fieldname': 'disabled_reason', 'desc': 'Disabled reason',
              'translator': value_trans})}

    availability_zones_translator = {
        'translation-type': 'HDICT',
        'table-name': AVAILABILITY_ZONES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'zoneName', 'col': 'zone',
              'desc': 'Availability zone name', 'translator': value_trans},
             {'fieldname': 'zoneState', 'col': 'state',
              'desc': 'Availability zone state',
              'translator': value_trans})}

    TRANSLATORS = [servers_translator, flavors_translator, hosts_translator,
                   floating_ips_translator, services_translator,
                   availability_zones_translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(NovaDriver, self).__init__(name, keys, inbox, datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = self.get_nova_credentials_v2(args)
        self.nova_client = novaclient.client.Client(**self.creds)
        self.add_executable_method('servers_set_meta',
                                   [{'name': 'server',
                                    'description': 'server id'},
                                    {'name': 'meta',
                                     'description': 'metadata pairs, ' +
                                     'e.g. meta1=val1 meta2=val2'}],
                                   "A wrapper for servers.set_meta()")
        self.add_executable_client_methods(self.nova_client, 'novaclient.v2.')
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'nova'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack Compute aka nova.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

    def get_nova_credentials_v2(self, creds):
        d = {}
        d['version'] = '2'
        d['username'] = creds['username']
        d['api_key'] = creds['password']
        d['auth_url'] = creds['auth_url']
        d['project_id'] = creds['tenant_name']
        return d

    def update_from_datasource(self):
        servers = self.nova_client.servers.list(
            detailed=True, search_opts={"all_tenants": 1})
        self._translate_servers(servers)
        self._translate_flavors(self.nova_client.flavors.list())
        self._translate_hosts(self.nova_client.hosts.list())
        self._translate_floating_ips(self.nova_client.floating_ips.list())
        self._translate_services(self.nova_client.services.list())
        self._translate_availability_zones(
            self.nova_client.availability_zones.list())

    @ds_utils.update_state_on_changed(SERVERS)
    def _translate_servers(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.servers_translator)
        return row_data

    @ds_utils.update_state_on_changed(FLAVORS)
    def _translate_flavors(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.flavors_translator)
        return row_data

    @ds_utils.update_state_on_changed(HOSTS)
    def _translate_hosts(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.hosts_translator)
        return row_data

    @ds_utils.update_state_on_changed(FLOATING_IPS)
    def _translate_floating_ips(self, obj):
        row_data = NovaDriver.convert_objs(obj,
                                           NovaDriver.floating_ips_translator)
        return row_data

    @ds_utils.update_state_on_changed(SERVICES)
    def _translate_services(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.services_translator)
        return row_data

    @ds_utils.update_state_on_changed(AVAILABILITY_ZONES)
    def _translate_availability_zones(self, obj):
        row_data = NovaDriver.convert_objs(
            obj,
            NovaDriver.availability_zones_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.nova_client, action, action_args)

    # "action" methods - to be used with "execute"
    def servers_set_meta(self, args):
        """A wrapper for servers.set_meta().

        'execute[p(x)]' doesn't take optional args at the moment.
        Therefore, this function translates the positional ARGS
        to optional args and call the servers.set_meta() api.
        :param <list> args: expected server ID and pairs of meta
        data in positional args such as:
        {'positional': ['server_id', 'meta1', 'value1', 'meta2', 'value2']}

        Usage:
        execute[nova.servers_set_meta(svr_id, meta1, val1, meta2, val2) :-
            triggering_table(id)
        """
        action = 'servers.set_meta'
        positional_args = args.get('positional', [])
        if not positional_args:
            LOG.error('Args not found for servers_set_meta()')
            return

        # Strip off the server_id before converting meta data pairs
        server_id = positional_args.pop(0)
        meta_data = self._convert_args(positional_args)

        action_args = {'named': {'server': server_id,
                                 'metadata': meta_data}}
        self._execute_api(self.nova_client, action, action_args)
