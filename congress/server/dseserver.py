# Copyright (c) 2014 VMware, Inc. All rights reserved.
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


import congress.dse.deepsix as deepsix


def d6service(name, keys, inbox, datapath, args):
    return DseServer(name, keys, inbox=inbox, dataPath=datapath, **args)


# Eventually inherit from API Server.  Just a mock up for now.
class DseServer(object, deepsix.deepSix):
    """DSE instance of server, so that the server can put API calls onto
       the bus.
    """
    def __init__(self, name, keys, inbox=None, dataPath=None):
        deepsix.deepSix.__init__(self, name, keys, inbox=inbox,
                                 dataPath=dataPath)
