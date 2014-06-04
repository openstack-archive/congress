#!/usr/bin/env python
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

from congress.datasources.datasource_driver import DataSourceDriver
import logging


def d6service(name, keys, inbox, datapath, args):
    return TestDriver(name, keys, inbox=inbox, datapath=datapath, **args)


class TestDriver(DataSourceDriver):
    def __init__(self, name, keys, inbox=None, datapath=None, **creds):
        super(TestDriver, self).__init__(name,
                                         keys,
                                         inbox=inbox,
                                         datapath=datapath,
                                         **creds)
        self.msg = None

    def receive_msg(self, msg):
        logging.info("TestDriver: received msg " + str(msg))
        self.msg = msg
