# Copyright (c) 2016 NEC Corporation. All rights reserved.
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

from aodhclient import client as aodh_client
from oslo_log import log as logging
import six

from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils

LOG = logging.getLogger(__name__)


class AodhDriver(datasource_driver.PollingDataSourceDriver,
                 datasource_driver.ExecutionDriver):
    ALARMS = "alarms"

    value_trans = {'translation-type': 'VALUE'}
    # TODO(ramineni): enable ALARM_RULES translator

    alarms_translator = {
        'translation-type': 'HDICT',
        'table-name': ALARMS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'alarm_id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'state', 'translator': value_trans},
             {'fieldname': 'enabled', 'translator': value_trans},
             {'fieldname': 'type', 'translator': value_trans},
             {'fieldname': 'description', 'translator': value_trans},
             {'fieldname': 'time_constraints', 'translator': value_trans},
             {'fieldname': 'user_id', 'translator': value_trans},
             {'fieldname': 'project_id', 'translator': value_trans},
             {'fieldname': 'alarm_actions', 'translator': value_trans},
             {'fieldname': 'ok_actions', 'translator': value_trans},
             {'fieldname': 'insufficient_data_actions', 'translator':
             value_trans},
             {'fieldname': 'repeat_actions', 'translator': value_trans},
             {'fieldname': 'timestamp', 'translator': value_trans},
             {'fieldname': 'state_timestamp', 'translator': value_trans},
             )}

    def safe_id(x):
        if isinstance(x, six.string_types):
            return x
        try:
            return x['resource_id']
        except KeyError:
            return str(x)

    TRANSLATORS = [alarms_translator]

    def __init__(self, name='', args=None):
        super(AodhDriver, self).__init__(name, args=args)
        datasource_driver.ExecutionDriver.__init__(self)
        session = ds_utils.get_keystone_session(args)
        endpoint = session.get_endpoint(service_type='alarming',
                                        interface='publicURL')
        self.aodh_client = aodh_client.Client(version='2', session=session,
                                              endpoint_override=endpoint)
        self.add_executable_client_methods(self.aodh_client, 'aodhclient.v2.')
        self.initialize_update_method()
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'aodh'
        result['description'] = ('Datasource driver that interfaces with '
                                 'aodh.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['config']['lazy_tables'] = constants.OPTIONAL
        result['secret'] = ['password']
        return result

    def initialize_update_method(self):
        alarms_method = lambda: self._translate_alarms(
            self.aodh_client.alarm.list())
        self.add_update_method(alarms_method, self.alarms_translator)

    @ds_utils.update_state_on_changed(ALARMS)
    def _translate_alarms(self, obj):
        """Translate the alarms represented by OBJ into tables."""
        LOG.debug("ALARMS: %s", str(obj))
        row_data = AodhDriver.convert_objs(obj, self.alarms_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.aodh_client, action, action_args)
