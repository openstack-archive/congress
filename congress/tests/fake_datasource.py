# Copyright (c) 2015 OpenStack Foundation
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

import mock
from oslo_log import log as logging

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils
from congress.datasources.json_ingester import exec_api
from congress.datasources.json_ingester import json_ingester

LOG = logging.getLogger(__name__)


class FakeDataSource(datasource_driver.PollingDataSourceDriver,
                     datasource_driver.PushedDataSourceDriver,
                     datasource_driver.ExecutionDriver):

    value_trans = {'translation-type': 'VALUE'}
    fake_translator = {
        'translation-type': 'HDICT',
        'table-name': 'fake_table',
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans})}

    TRANSLATORS = [fake_translator]

    def __init__(self, name='', args=None):
        super(FakeDataSource, self).__init__(name, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.add_executable_method('fake_act',
                                   [{'name': 'server_id',
                                    'description': 'server to act'}],
                                   'fake action')

        self.update_number = 0
        self.initialize_update_method()
        self.exec_history = []
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'fake_datasource'
        result['description'] = 'This is a fake driver used for testing'
        result['config'] = datasource_utils.get_openstack_required_config()
        result['secret'] = ['password']
        return result

    def initialize_update_method(self):
        self.add_update_method(self.update_fake_table, self.fake_translator)

    def update_fake_table(self):
        LOG.info("fake:: update_from_datasource")
        self.update_number += 1

    def execute(self, action, action_args):
        self.exec_history.append((action, action_args))

    def _webhook_handler(self, payload):
        self.webhook_payload = payload


class FakeJsonIngester(json_ingester.JsonIngester):

    def __init__(self, name='fake_json', config=None):
        if config is None:
            config = {
                "tables": {
                    "alarms": {
                        "webhook": {
                            "record_jsonpath": "$.payload",
                            "id_jsonpath": "$.id"
                        }
                    }
                },
                "name": name
            }
        super(FakeJsonIngester, self).__init__(
            name, config, mock.Mock(spec_set=exec_api.ExecApiManager))

    # override for unit testing
    def _create_schema_and_tables(self):
        pass

    # override for unit testing
    def json_ingester_webhook_handler(self, table_name, body):
        self.webhook_table_name = table_name
        self.webhook_payload = body
