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

""" Base class for all API models."""

from __future__ import absolute_import

from oslo_config import cfg

from congress import exception


class APIModel(object):
    """Base Class for handling API requests."""

    def __init__(self, name, keys='', inbox=None, dataPath=None,
                 policy_engine=None, datasource_mgr=None, bus=None):
        self.dist_arch = getattr(cfg.CONF, 'distributed_architecture', False)
        self.engine = policy_engine
        if self.dist_arch:
            self.engine = 'engine'
        self.datasource_mgr = datasource_mgr
        self.bus = bus
        self.name = name

    def invoke_rpc(self, caller, name, kwargs):
        if self.dist_arch:
            return self.bus.rpc(caller, name, kwargs)
        else:
            func = getattr(caller, name, None)
            if func:
                return func(**kwargs)
            raise exception.CongressException('method: %s is not defined in %s'
                                              % (name, caller.__name__))
