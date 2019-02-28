# Copyright (c) 2018 NEC, Inc.
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
import json
from tackerclient.v1_0 import client as tacker_client

from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils


class TackerDriver(datasource_driver.PollingDataSourceDriver,
                   datasource_driver.ExecutionDriver):

    VNFS = 'vnfs'
    VNFDS = 'vnfds'
    INSTANCES = VNFS + '.instances'
    value_trans = {'translation-type': 'VALUE'}

    def extract_mgmt_urls(mgmt_url):
        return json.loads(mgmt_url)

    vnfds_translator = {
        'translation-type': 'HDICT',
        'table-name': VNFDS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'template_source', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans})
    }

    vnfs_translator = {
        'translation-type': 'HDICT',
        'table-name': VNFS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'vnfd_id', 'translator': value_trans},
             {'fieldname': 'vim_id', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'instance_id', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans},
             {'fieldname': 'error_reason', 'translator': value_trans},
             {'fieldname': 'mgmt_url',
              'translator': {'translation-type': 'VDICT',
                             'table-name': INSTANCES,
                             'parent-key': 'id',
                             'parent-col-name': 'vnf_id',
                             'key-col': 'key',
                             'val-col': 'value',
                             'objects-extract-fn': extract_mgmt_urls,
                             'translator': value_trans}})
    }

    TRANSLATORS = [vnfds_translator, vnfs_translator]

    def __init__(self, name='', args=None):
        super(TackerDriver, self).__init__(name, args=args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = args
        session = ds_utils.get_keystone_session(self.creds)
        self.tacker_client = tacker_client.Client(session=session)
        self.add_executable_client_methods(self.tacker_client,
                                           'tackerclient.v1_0.client')
        self.initialize_update_methods()
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'tacker'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack tacker.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['config']['api_version'] = constants.OPTIONAL
        result['config']['lazy_tables'] = constants.OPTIONAL
        result['secret'] = ['password']
        return result

    def initialize_update_methods(self):
        vnfds_method = lambda: self._translate_vnfds(
            self.tacker_client.list_vnfds()['vnfds'])
        self.add_update_method(vnfds_method, self.vnfds_translator)

        vnf_method = lambda: self._translate_vnf(
            self.tacker_client.list_vnfs()['vnfs'])
        self.add_update_method(vnf_method, self.vnfs_translator)

    @ds_utils.update_state_on_changed(VNFDS)
    def _translate_vnfds(self, obj):
        row_data = TackerDriver.convert_objs(obj, self.vnfds_translator)
        return row_data

    @ds_utils.update_state_on_changed(VNFS)
    def _translate_vnf(self, obj):
        row_data = TackerDriver.convert_objs(obj, self.vnfs_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.tacker_client, action, action_args)
