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

"""Schema version history

version: 2.1
date: 2016-03-27
changes:

 - Added columns to the volumes table: encrypted, availability_zone,
   replication_status, multiattach, snapshot_id, source_volid,
   consistencygroup_id, migration_status
 - Added the attachments table for volume attachment information.

version: 2.0
Initial schema version.
"""

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import cinderclient.client

from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils


class CinderDriver(datasource_driver.PollingDataSourceDriver,
                   datasource_driver.ExecutionDriver):
    VOLUMES = "volumes"
    ATTACHMENTS = "attachments"
    SNAPSHOTS = "snapshots"
    SERVICES = "services"

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    volumes_translator = {
        'translation-type': 'HDICT',
        'table-name': VOLUMES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'size', 'translator': value_trans},
             {'fieldname': 'user_id', 'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'bootable', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'volume_type', 'translator': value_trans},
             {'fieldname': 'encrypted', 'translator': value_trans},
             {'fieldname': 'availability_zone', 'translator': value_trans},
             {'fieldname': 'replication_status', 'translator': value_trans},
             {'fieldname': 'multiattach', 'translator': value_trans},
             {'fieldname': 'snapshot_id', 'translator': value_trans},
             {'fieldname': 'source_volid', 'translator': value_trans},
             {'fieldname': 'consistencygroup_id', 'translator': value_trans},
             {'fieldname': 'migration_status', 'translator': value_trans},
             {'fieldname': 'attachments',
              'translator': {'translation-type': 'HDICT',
                             'table-name': ATTACHMENTS,
                             'parent-key': 'id',
                             'parent-col-name': 'volume_id',
                             'parent-key-desc': 'UUID of volume',
                             'selector-type': 'DICT_SELECTOR',
                             'in-list': True,
                             'field-translators':
                                 ({'fieldname': 'server_id',
                                   'translator': value_trans},
                                  {'fieldname': 'attachment_id',
                                   'translator': value_trans},
                                  {'fieldname': 'host_name',
                                   'translator': value_trans},
                                  {'fieldname': 'device',
                                   'translator': value_trans})}}
             )}

    snapshots_translator = {
        'translation-type': 'HDICT',
        'table-name': SNAPSHOTS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'size', 'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'volume_id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans})}

    services_translator = {
        'translation-type': 'HDICT',
        'table-name': SERVICES,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'binary', 'translator': value_trans},
             {'fieldname': 'zone', 'translator': value_trans},
             {'fieldname': 'state', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans},
             {'fieldname': 'host', 'translator': value_trans},
             {'fieldname': 'disabled_reason', 'translator': value_trans})}

    TRANSLATORS = [volumes_translator, snapshots_translator,
                   services_translator]

    def __init__(self, name='', args=None):
        super(CinderDriver, self).__init__(name, args=args)
        datasource_driver.ExecutionDriver.__init__(self)
        session = ds_utils.get_keystone_session(args)
        self.cinder_client = cinderclient.client.Client(version='2',
                                                        session=session)
        self.add_executable_client_methods(self.cinder_client,
                                           'cinderclient.v2.')
        self.initialize_update_method()
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'cinder'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack cinder.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['config']['lazy_tables'] = constants.OPTIONAL
        result['secret'] = ['password']
        return result

    def initialize_update_method(self):
        volumes_method = lambda: self._translate_volumes(
            self.cinder_client.volumes.list(detailed=True,
                                            search_opts={'all_tenants': 1}))
        self.add_update_method(volumes_method, self.volumes_translator)

        snapshots_method = lambda: self._translate_snapshots(
            self.cinder_client.volume_snapshots.list(
                detailed=True, search_opts={'all_tenants': 1}))
        self.add_update_method(snapshots_method, self.snapshots_translator)

        services_method = lambda: self._translate_services(
            self.cinder_client.services.list(host=None, binary=None))
        self.add_update_method(services_method, self.services_translator)

    @ds_utils.update_state_on_changed(VOLUMES)
    def _translate_volumes(self, obj):
        row_data = CinderDriver.convert_objs(obj, self.volumes_translator)
        return row_data

    @ds_utils.update_state_on_changed(SNAPSHOTS)
    def _translate_snapshots(self, obj):
        row_data = CinderDriver.convert_objs(obj, self.snapshots_translator)
        return row_data

    @ds_utils.update_state_on_changed(SERVICES)
    def _translate_services(self, obj):
        row_data = CinderDriver.convert_objs(obj, self.services_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.cinder_client, action, action_args)
