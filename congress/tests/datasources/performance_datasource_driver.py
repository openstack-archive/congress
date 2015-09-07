# Copyright (c) 2015 VMware, Inc. All rights reserved.
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

from oslo_log import log as logging

from congress.datasources import datasource_driver


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """Create dataservice instance.

    This method is called by d6cage to create a dataservice
    instance.  There are a couple of parameters we found useful
    to add to that call, so we included them here instead of
    modifying d6cage (and all the d6cage.createservice calls).
    """
    return PerformanceTestDriver(name, keys, inbox, datapath, args)


class PerformanceTestDriver(datasource_driver.DataSourceDriver):
    TABLE = 'p'

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    p_translator = {
        'translation-type': 'HDICT',
        'table-name': TABLE,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'field1', 'translator': value_trans},
             {'fieldname': 'field2', 'translator': value_trans},
             {'fieldname': 'field3', 'translator': value_trans},
             {'fieldname': 'field4', 'translator': value_trans},
             {'fieldname': 'field5', 'translator': value_trans},
             {'fieldname': 'field6', 'translator': value_trans})}

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        if args is None:
            args = self._empty_openstack_credentials()
        super(PerformanceTestDriver, self).__init__(
            name, keys, inbox, datapath, args)
        self.client_data = None
        self.register_translator(PerformanceTestDriver.p_translator)
        self._init_end_start_poll()

    def update_from_datasource(self):
        if self.client_data is not None:
            self.state = {}
            row_data = self.convert_objs(self.client_data, self.p_translator)
            self.state[self.TABLE] = set()
            for table, row in row_data:
                assert table == self.TABLE
                self.state[table].add(row)
