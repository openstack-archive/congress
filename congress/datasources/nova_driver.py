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

import novaclient.client
from oslo_log import log as logging
import six

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return NovaDriver(name, keys, inbox, datapath, args)


class NovaDriver(datasource_driver.DataSourceDriver,
                 datasource_driver.ExecutionDriver):
    SERVERS = "servers"
    FLAVORS = "flavors"
    HOSTS = "hosts"
    FLOATING_IPS = "floating_IPs"
    SERVICES = 'services'

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
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'hostId', 'col': 'host_id',
              'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'user_id', 'translator': value_trans},
             {'fieldname': 'image', 'col': 'image_id',
              'translator': {'translation-type': 'VALUE',
                             'extract-fn': safe_id}},
             {'fieldname': 'flavor', 'col': 'flavor_id',
              'translator': {'translation-type': 'VALUE',
                             'extract-fn': safe_id}})}

    flavors_translator = {
        'translation-type': 'HDICT',
        'table-name': FLAVORS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'vcpus', 'translator': value_trans},
             {'fieldname': 'ram', 'translator': value_trans},
             {'fieldname': 'disk', 'translator': value_trans},
             {'fieldname': 'ephemeral', 'translator': value_trans},
             {'fieldname': 'rxtx_factor', 'translator': value_trans})}

    hosts_translator = {
        'translation-type': 'HDICT',
        'table-name': HOSTS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'host_name', 'translator': value_trans},
             {'fieldname': 'service', 'translator': value_trans},
             {'fieldname': 'zone', 'translator': value_trans})}

    floating_ips_translator = {
        'translation-type': 'HDICT',
        'table-name': FLOATING_IPS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'fixed_ip', 'translator': value_trans},
             {'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'ip', 'translator': value_trans},
             {'fieldname': 'instance_id', 'col': 'host_id',
              'translator': value_trans},
             {'fieldname': 'pool', 'translator': value_trans})}

    services_translator = {
        'translation-type': 'HDICT',
        'table-name': SERVICES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'col': 'service_id',
              'translator': value_trans},
             {'fieldname': 'binary', 'translator': value_trans},
             {'fieldname': 'host', 'translator': value_trans},
             {'fieldname': 'zone', 'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'state', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans},
             {'fieldname': 'disabled_reason', 'translator': value_trans})}

    TRANSLATORS = [servers_translator, flavors_translator, hosts_translator,
                   floating_ips_translator, services_translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(NovaDriver, self).__init__(name, keys, inbox, datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = self.get_nova_credentials_v2(args)
        self.nova_client = novaclient.client.Client(**self.creds)
        self.initialized = True

        self.add_executable_method(self.servers_set_meta)

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'nova'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack Compute aka nova.')
        result['config'] = datasource_utils.get_openstack_required_config()
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
        self.state = {}
        servers = self.nova_client.servers.list(
            detailed=True, search_opts={"all_tenants": 1})
        self._translate_servers(servers)
        self._translate_flavors(self.nova_client.flavors.list())
        self._translate_hosts(self.nova_client.hosts.list())
        self._translate_floating_ips(self.nova_client.floating_ips.list(
            all_tenants=True))
        self._translate_services(self.nova_client.services.list())

    def _translate_servers(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.servers_translator)
        self.state[self.SERVERS] = set()
        for table, row in row_data:
            assert table == self.SERVERS
            self.state[table].add(row)

    def _translate_flavors(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.flavors_translator)
        self.state[self.FLAVORS] = set()
        for table, row in row_data:
            assert table == self.FLAVORS
            self.state[table].add(row)

    def _translate_hosts(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.hosts_translator)
        self.state[self.HOSTS] = set()
        for table, row in row_data:
            assert table == self.HOSTS
            self.state[table].add(row)

    def _translate_floating_ips(self, obj):
        row_data = NovaDriver.convert_objs(obj,
                                           NovaDriver.floating_ips_translator)
        self.state[self.FLOATING_IPS] = set()
        for table, row in row_data:
            assert table == self.FLOATING_IPS
            self.state[table].add(row)

    def _translate_services(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.services_translator)
        self.state[self.SERVICES] = set()
        for table, row in row_data:
            assert table == self.SERVICES
            self.state[table].add(row)

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
