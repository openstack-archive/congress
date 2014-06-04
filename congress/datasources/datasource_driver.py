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

import dse.deepsix


class DataSourceDriver(dse.deepsix.deepSix):
    def __init__(self, name, keys, inbox=None, datapath=None, **creds):
        super(DataSourceDriver, self).__init__(name, keys, inbox, datapath)
        self.creds = creds

    def get_all(self, type):
        raise NotImplementedError()

    def get_last_updated_time(self):
        raise NotImplementedError()

    def boolean_to_congress(self, bool):
        return str(bool)
