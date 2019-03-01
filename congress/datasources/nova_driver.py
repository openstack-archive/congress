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

"""Schema change history
date: 2019-03-07
changes:

 - Added the `created_at` column to the servers table.

date: 2018-10-18
changes:

 - Added the `servers.addresses` table for server address information.

date: 2018-03-15
changes:

 - (incompatible) Removed the `hosts` table for OS hosts information because
   access to the information has been removed from the latest Nova API and
   client.
 - Added the `hypervisors` table for hypervisor information.

date: 2017-10-01
changes:

 - Added the `tags` table for server tags information.
"""

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import novaclient.client
from oslo_log import log as logging
import six

from congress import data_types
from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils


LOG = logging.getLogger(__name__)


class NovaDriver(datasource_driver.PollingDataSourceDriver,
                 datasource_driver.ExecutionDriver):
    SERVERS = "servers"
    FLAVORS = "flavors"
    HYPERVISORS = "hypervisors"
    SERVICES = 'services'
    AVAILABILITY_ZONES = "availability_zones"
    ADDRESSES = SERVERS + ".addresses"
    TAGS = "tags"

    value_trans_str = ds_utils.typed_value_trans(data_types.Str)
    value_trans_bool = ds_utils.typed_value_trans(data_types.Bool)
    value_trans_int = ds_utils.typed_value_trans(data_types.Int)

    def safe_id(x):
        if isinstance(x, six.string_types):
            return x
        try:
            return x['id']
        except Exception:
            return str(x)

    def extract_addresses(addresses):
        addresses_list = []
        for network_name, net_detail in addresses.items():
            for address in net_detail:
                address['network_name'] = network_name
                addresses_list.append(address)
        return addresses_list

    servers_translator = {
        'translation-type': 'HDICT',
        'table-name': SERVERS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'The UUID for the server',
              'translator': value_trans_str},
             {'fieldname': 'name', 'desc': 'Name of the server',
              'translator': value_trans_str},
             {'fieldname': 'hostId', 'col': 'host_id',
              'desc': 'The UUID for the host', 'translator': value_trans_str},
             {'fieldname': 'status', 'desc': 'The server status',
              'translator': value_trans_str},
             {'fieldname': 'tenant_id', 'desc': 'The tenant ID',
              'translator': value_trans_str},
             {'fieldname': 'user_id',
              'desc': 'The user ID of the user who owns the server',
              'translator': value_trans_str},
             {'fieldname': 'image', 'col': 'image_id',
              'desc': 'Name or ID of image',
              'translator': {'translation-type': 'VALUE',
                             'extract-fn': safe_id}},
             {'fieldname': 'flavor', 'col': 'flavor_id',
              'desc': 'ID of the flavor',
              'translator': {'translation-type': 'VALUE',
                             'extract-fn': safe_id}},
             {'fieldname': 'OS-EXT-AZ:availability_zone', 'col': 'zone',
              'desc': 'The availability zone of host',
              'translator': value_trans_str},
             {'fieldname': 'OS-EXT-SRV-ATTR:hypervisor_hostname',
              'desc': ('The hostname of hypervisor where the server is '
                       'running'),
              'col': 'host_name', 'translator': value_trans_str},
             {'fieldname': 'created', 'col': 'created_at',
              'desc': 'Time at which server is created',
              'translator': value_trans_str},
             {'fieldname': 'addresses',
              'translator': {'translation-type': 'HDICT',
                             'table-name': ADDRESSES,
                             'parent-key': 'id',
                             'parent-col-name': 'server_id',
                             'parent-key-desc': 'UUID of server',
                             'objects-extract-fn': extract_addresses,
                             'selector-type': 'DICT_SELECTOR',
                             'in-list': True,
                             'field-translators':
                                 ({'fieldname': 'network_name',
                                   'desc': ('Name of attached network to '
                                            'server'),
                                   'translator': value_trans_str},
                                  {'fieldname': 'addr',
                                   'desc': 'IP address of the server',
                                   'col': 'address',
                                   'translator': value_trans_str},
                                  {'fieldname': 'version',
                                   'desc': ('Internet Protocol Version of '
                                            'network'),
                                   'translator': value_trans_int},
                                  {'fieldname': 'OS-EXT-IPS-MAC:mac_addr',
                                   'desc': ('MAC address associated to the '
                                            'IP of the server'),
                                   'col': 'mac_address',
                                   'translator': value_trans_str},
                                  {'fieldname': 'OS-EXT-IPS:type',
                                   'desc': 'IP address type',
                                   'col': 'address_type',
                                   'translator': value_trans_str})}},
             {'fieldname': 'tags',
              'translator': {'translation-type': 'LIST',
                             'table-name': TAGS,
                             'parent-key': 'id',
                             'parent-col-name': 'server_id',
                             'parent-key-desc': 'UUID of server',
                             'val-col': 'tag',
                             'val-col-desc': 'server tag string',
                             'translator': value_trans_str}})}

    flavors_translator = {
        'translation-type': 'HDICT',
        'table-name': FLAVORS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'ID of the flavor',
              'translator': value_trans_str},
             {'fieldname': 'name', 'desc': 'Name of the flavor',
              'translator': value_trans_str},
             {'fieldname': 'vcpus', 'desc': 'Number of vcpus',
              'translator': value_trans_int},
             {'fieldname': 'ram', 'desc': 'Memory size in MB',
              'translator': value_trans_int},
             {'fieldname': 'disk', 'desc': 'Disk size in GB',
              'translator': value_trans_int},
             {'fieldname': 'ephemeral', 'desc': 'Ephemeral space size in GB',
              'translator': value_trans_int},
             {'fieldname': 'rxtx_factor', 'desc': 'RX/TX factor',
              'translator': ds_utils.typed_value_trans(data_types.Float)})}

    hypervisors_translator = {
        'translation-type': 'HDICT',
        'table-name': HYPERVISORS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'hypervisor_hostname', 'desc': 'Hypervisor host',
              'translator': value_trans_str},
             {'fieldname': 'id', 'desc': 'hypervisori id',
              # untyped: depends on api microversion
              'translator': {'translation-type': 'VALUE'}},
             {'fieldname': 'state', 'desc': 'State of the hypervisor',
              'translator': value_trans_str},
             {'fieldname': 'status', 'desc': 'Status of the hypervisor',
              'translator': value_trans_str})}

    services_translator = {
        'translation-type': 'HDICT',
        'table-name': SERVICES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'col': 'service_id', 'desc': 'Service ID',
              'translator': value_trans_int},
             {'fieldname': 'binary', 'desc': 'Service binary',
              'translator': value_trans_str},
             {'fieldname': 'host', 'desc': 'Host Name',
              'translator': value_trans_str},
             {'fieldname': 'zone', 'desc': 'Availability Zone',
              'translator': value_trans_str},
             {'fieldname': 'status', 'desc': 'Status of service',
              'translator': value_trans_str},
             {'fieldname': 'state', 'desc': 'State of service',
              'translator': value_trans_str},
             {'fieldname': 'updated_at', 'desc': 'Last updated time',
              'translator': value_trans_str},
             {'fieldname': 'disabled_reason', 'desc': 'Disabled reason',
              'translator': value_trans_str})}

    availability_zones_translator = {
        'translation-type': 'HDICT',
        'table-name': AVAILABILITY_ZONES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'zoneName', 'col': 'zone',
              'desc': 'Availability zone name', 'translator': value_trans_str},
             {'fieldname': 'zoneState', 'col': 'state',
              'desc': 'Availability zone state',
              'translator': value_trans_str})}

    TRANSLATORS = [servers_translator, flavors_translator, services_translator,
                   hypervisors_translator, availability_zones_translator]

    def __init__(self, name='', args=None):
        super(NovaDriver, self).__init__(name, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = args
        session = ds_utils.get_keystone_session(self.creds)
        self.nova_client = novaclient.client.Client(
            version=self.creds.get('api_version', '2.26'), session=session)
        self.add_executable_method('servers_set_meta',
                                   [{'name': 'server',
                                    'description': 'server id'},
                                    {'name': 'meta-key1',
                                     'description': 'meta key 1'},
                                    {'name': 'meta-value1',
                                     'description': 'value for meta key1'},
                                    {'name': 'meta-keyN',
                                     'description': 'meta key N'},
                                    {'name': 'meta-valueN',
                                     'description': 'value for meta keyN'}],
                                   "A wrapper for servers.set_meta()")
        self.add_executable_client_methods(self.nova_client, 'novaclient.v2.')
        self.initialize_update_methods()
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'nova'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack Compute aka nova.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['config']['api_version'] = constants.OPTIONAL
        result['config']['lazy_tables'] = constants.OPTIONAL
        result['secret'] = ['password']
        return result

    def initialize_update_methods(self):
        servers_method = lambda: self._translate_servers(
            self.nova_client.servers.list(
                detailed=True, search_opts={"all_tenants": 1}))
        self.add_update_method(servers_method, self.servers_translator)

        flavors_method = lambda: self._translate_flavors(
            self.nova_client.flavors.list())
        self.add_update_method(flavors_method, self.flavors_translator)

        hypervisors_method = lambda: self._translate_hypervisors(
            self.nova_client.hypervisors.list())
        self.add_update_method(hypervisors_method,
                               self.hypervisors_translator)

        services_method = lambda: self._translate_services(
            self.nova_client.services.list())
        self.add_update_method(services_method, self.services_translator)

        az_method = lambda: self._translate_availability_zones(
            self.nova_client.availability_zones.list())
        self.add_update_method(az_method, self.availability_zones_translator)

    @ds_utils.update_state_on_changed(SERVERS)
    def _translate_servers(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.servers_translator)
        return row_data

    @ds_utils.update_state_on_changed(FLAVORS)
    def _translate_flavors(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.flavors_translator)
        return row_data

    @ds_utils.update_state_on_changed(HYPERVISORS)
    def _translate_hypervisors(self, obj):
        row_data = NovaDriver.convert_objs(
            obj,
            NovaDriver.hypervisors_translator)
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
        :param: <list> args: expected server ID and pairs of meta
        data in positional args such as::

            {'positional': ['server_id', 'meta1', 'value1', 'meta2', 'value2']}

        Usage::

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
