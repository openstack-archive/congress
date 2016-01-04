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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

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
    return TestDriver(name, keys, inbox, datapath, args)


class TestDriver(datasource_driver.PollingDataSourceDriver):
    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        if args is None:
            args = self._empty_openstack_credentials()
        super(TestDriver, self).__init__(name, keys, inbox, datapath, args)
        self.msg = None
        self.state = {}
        self._init_end_start_poll()

    def receive_msg(self, msg):
        LOG.info("TestDriver: received msg %s", msg)
        self.msg = msg

    def get_msg_data(self):
        msgstr = ""
        if self.msg is None:
            return msgstr
        # only support list and set now
        if isinstance(self.msg.body.data, (list, set)):
            for di in self.msg.body.data:
                msgstr += str(di)
        else:
            msgstr = str(self.msg.body.data)
        LOG.info("TestDriver: current received msg: %s", msgstr)
        return msgstr

    def update_from_datasource(self):
        pass

    def prepush_processor(self, data, dataindex, type=None):
        # don't change data before transfer
        return data
