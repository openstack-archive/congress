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
from congress.datasources import datasource_driver


def d6service(name, keys, inbox, datapath, args):
    """Create a dataservice instance.

    This method is called by d6cage to create a dataservice
    instance.  There are a couple of parameters we found useful
    to add to that call, so we included them here instead of
    modifying d6cage (and all the d6cage.createservice calls).
    """
    return BenchmarkDriver(name, keys, inbox, datapath, args)


class BenchmarkDriver(datasource_driver.DataSourceDriver):
    BENCHTABLE = 'benchtable'
    value_trans = {'translation-type': 'VALUE'}
    translator = {
        'translation-type': 'HDICT',
        'table-name': BENCHTABLE,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'field1', 'translator': value_trans},
             {'fieldname': 'field2', 'translator': value_trans})}

    TRANSLATORS = [translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(BenchmarkDriver, self).__init__(name, keys,
                                              inbox, datapath, args)
        # used by update_from_datasources to manufacture data. Default small.
        self.datarows = 10
        self._init_end_start_poll()

    def update_from_datasource(self):
        self.state = {}
        # TODO(sh): using self.convert_objs() takes about 10x the time. Needs
        # optimization efforts.
        row_data = tuple((self.BENCHTABLE, ('val1_%d' % i, 'val2_%d' % i))
                         for i in xrange(self.datarows))
        for table, row in row_data:
            if table not in self.state:
                self.state[table] = set()
            self.state[table].add(row)

    def get_credentials(self, *args, **kwargs):
        return {}
