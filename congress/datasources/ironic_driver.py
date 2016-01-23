# Copyright (c) 2015 Intel Corporation. All rights reserved.
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

from ironicclient import client
import keystoneclient.v2_0.client as ksclient
from oslo_log import log as logging
import six

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return IronicDriver(name, keys, inbox, datapath, args)


class IronicDriver(datasource_driver.PollingDataSourceDriver,
                   datasource_driver.ExecutionDriver):
    CHASSISES = "chassises"
    NODES = "nodes"
    NODE_PROPERTIES = "node_properties"
    PORTS = "ports"
    DRIVERS = "drivers"
    ACTIVE_HOSTS = "active_hosts"

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    def safe_id(x):
        if isinstance(x, six.string_types):
            return x
        try:
            return x['id']
        except KeyError:
            return str(x)

    def safe_port_extra(x):
        try:
            return x['vif_port_id']
        except KeyError:
            return ""

    chassises_translator = {
        'translation-type': 'HDICT',
        'table-name': CHASSISES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'uuid', 'col': 'id', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans})}

    nodes_translator = {
        'translation-type': 'HDICT',
        'table-name': NODES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'uuid', 'col': 'id', 'translator': value_trans},
             {'fieldname': 'chassis_uuid', 'col': 'owner_chassis',
                                           'translator': value_trans},
             {'fieldname': 'power_state', 'translator': value_trans},
             {'fieldname': 'maintenance', 'translator': value_trans},
             {'fieldname': 'properties', 'translator':
                                         {'translation-type': 'HDICT',
                                          'table-name': NODE_PROPERTIES,
                                          'parent-key': 'id',
                                          'parent-col-name': 'properties',
                                          'selector-type': 'DICT_SELECTOR',
                                          'in-list': False,
                                          'field-translators':
                                              ({'fieldname': 'memory_mb',
                                                'translator': value_trans},
                                               {'fieldname': 'cpu_arch',
                                                'translator': value_trans},
                                               {'fieldname': 'local_gb',
                                                'translator': value_trans},
                                               {'fieldname': 'cpus',
                                                'translator': value_trans})}},
             {'fieldname': 'driver', 'translator': value_trans},
             {'fieldname': 'instance_uuid', 'col': 'running_instance',
                                            'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'provision_updated_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans})}

    ports_translator = {
        'translation-type': 'HDICT',
        'table-name': PORTS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'uuid', 'col': 'id', 'translator': value_trans},
             {'fieldname': 'node_uuid', 'col': 'owner_node',
                                        'translator': value_trans},
             {'fieldname': 'address', 'col': 'mac_address',
                                      'translator': value_trans},
             {'fieldname': 'extra', 'col': 'vif_port_id', 'translator':
                                    {'translation-type': 'VALUE',
                                     'extract-fn': safe_port_extra}},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans})}

    drivers_translator = {
        'translation-type': 'HDICT',
        'table-name': DRIVERS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'hosts', 'translator':
                                    {'translation-type': 'LIST',
                                     'table-name': ACTIVE_HOSTS,
                                     'parent-key': 'name',
                                     'parent-col-name': 'name',
                                     'val-col': 'hosts',
                                     'translator':
                                     {'translation-type': 'VALUE'}}})}

    TRANSLATORS = [chassises_translator, nodes_translator, ports_translator,
                   drivers_translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(IronicDriver, self).__init__(name, keys, inbox, datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = self.get_ironic_credentials(args)
        self.ironic_client = client.get_client(**self.creds)
        self.add_executable_client_methods(self.ironic_client,
                                           'ironicclient.v1.')
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'ironic'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack bare metal aka ironic.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

    def get_ironic_credentials(self, creds):
        d = {}
        d['api_version'] = '1'
        d['insecure'] = False
        # save a copy to renew auth token
        d['username'] = creds['username']
        d['password'] = creds['password']
        d['auth_url'] = creds['auth_url']
        d['tenant_name'] = creds['tenant_name']
        # ironicclient.get_client() uses different names
        d['os_username'] = creds['username']
        d['os_password'] = creds['password']
        d['os_auth_url'] = creds['auth_url']
        d['os_tenant_name'] = creds['tenant_name']
        return d

    def update_from_datasource(self):
        try:
            chassises = self.ironic_client.chassis.list(detail=True, limit=0)
            self._translate_chassises(chassises)

            nodes = self.ironic_client.node.list(detail=True, limit=0)
            self._translate_nodes(nodes)

            ports = self.ironic_client.port.list(detail=True, limit=0)
            self._translate_ports(ports)

            drivers = self.ironic_client.driver.list()
            self._translate_drivers(drivers)
        except Exception as e:
            # TODO(zhenzanz): this is a workaround. The ironic client should
            # handle 401 error.
            if e.http_status == 401:
                keystone = ksclient.Client(**self.creds)
                self.ironic_client.http_client.auth_token = keystone.auth_token
            else:
                raise e

    @ds_utils.update_state_on_changed(CHASSISES)
    def _translate_chassises(self, obj):
        row_data = IronicDriver.convert_objs(obj,
                                             IronicDriver.chassises_translator)
        return row_data

    @ds_utils.update_state_on_changed(NODES)
    def _translate_nodes(self, obj):
        row_data = IronicDriver.convert_objs(obj,
                                             IronicDriver.nodes_translator)
        return row_data

    @ds_utils.update_state_on_changed(PORTS)
    def _translate_ports(self, obj):
        row_data = IronicDriver.convert_objs(obj,
                                             IronicDriver.ports_translator)
        return row_data

    @ds_utils.update_state_on_changed(DRIVERS)
    def _translate_drivers(self, obj):
        row_data = IronicDriver.convert_objs(obj,
                                             IronicDriver.drivers_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.ironic_client, action, action_args)
