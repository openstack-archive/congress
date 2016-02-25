# Copyright (c) 2016 NTT All rights reserved.
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

from oslo_log import log as logging
import six

from congress.datasources import datasource_driver

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return DoctorDriver(name, keys, inbox, datapath, args)


class DoctorDriver(datasource_driver.PushedDataSourceDriver):
    """A DataSource Driver for OPNFV Doctor project.

    This driver has a table for Doctor project's Inspector. Please check
    https://wiki.opnfv.org/display/doctor/Doctor+Home for the details
    about OPNFV Doctor project.

    To update the table, call Update row API.

    PUT /v1/data-sources/<the driver id>/tables/<table id>/rows

    For updating 'events' table, the request body should be following
    style. The request will replace all rows in the table with the body,
    which means if you update the table with [] it will clear the table.
    One {} object in the list represents one row of the table.

    request body:
    [
      {
        "id": "0123-4567-89ab",
        "time": "2016-02-22T11:48:55Z",
        "type": "compute.host.down",
        "details": {
            "hostname": "compute1",
            "status": "down",
            "monitor": "zabbix1",
            "monitor_event_id": "111"
        }
      },
      .....
    ]
    """

    value_trans = {'translation-type': 'VALUE'}

    def safe_id(x):
        if isinstance(x, six.string_types):
            return x
        try:
            return x['id']
        except Exception:
            return str(x)

    def flatten_events(row_events):
        flatten = []
        for event in row_events:
            details = event.pop('details')
            for k, v in details.items():
                event[k] = v
            flatten.append(event)
        return flatten

    events_translator = {
        'translation-type': 'HDICT',
        'table-name': 'events',
        'selector-type': 'DICT_SELECTOR',
        'objects-extract-fn': flatten_events,
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'time', 'translator': value_trans},
             {'fieldname': 'type', 'translator': value_trans},
             {'fieldname': 'hostname', 'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'monitor', 'translator': value_trans},
             {'fieldname': 'monitor_event_id', 'translator': value_trans},)
        }

    TRANSLATORS = [events_translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(DoctorDriver, self).__init__(name, keys, inbox, datapath, args)

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'doctor'
        result['description'] = ('Datasource driver that interfaces with '
                                 'OpenStack Compute aka nova.')
        result['config'] = {}
        return result
