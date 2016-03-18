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

import datetime
from oslo_log import log as logging

from congress.datasources import constants
from congress.datasources import datasource_driver

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return PushDriver(name, keys, inbox, datapath, args)


class PushDriver(datasource_driver.PushedDataSourceDriver):
    """A DataSource Driver for pushing tuples of data.

    To use this driver, run the following API:

    PUT /v1/data-sources/<the driver id>/tables/<table id>/rows

    Still a work in progress, but intent is to allow a request body
    to be any list of lists where the internal lists all have
    the same number of elements.

    request body:
    [ [1,2], [3,4] ]
    """

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(PushDriver, self).__init__(name, keys, inbox, datapath, args)
        self._table_deps['data'] = ['data']

    @classmethod
    def get_schema(cls):
        schema = {}
        # Hardcode the tables for now.  Later, create the tables on the fly.
        # May be as easy as deleting the following line.
        schema['data'] = []
        return schema

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'push'
        result['description'] = ('Datasource driver that allows external '
                                 'systems to push data.')
        # TODO(masa): Remove the REQUIRED config once python-congressclient
        # has been able to retrieve non-dict object in config fields at
        # $ openstack congress datasource list command
        result['config'] = {'description': constants.REQUIRED}
        return result

    def update_entire_data(self, table_id, objs):
        LOG.info('update %s table in %s datasource' % (table_id, self.name))
        tablename = 'data'  # hard code
        self.prior_state = dict(self.state)
        self._update_state(tablename,
                           [tuple([table_id, tuple(x)]) for x in objs])
        LOG.debug('publish a new state %s in %s' %
                  (self.state[tablename], tablename))
        self.publish(tablename, self.state[tablename])
        self.number_of_updates += 1
        self.last_updated_time = datetime.datetime.now()
