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

ENGINE_SERVICE_ID = '__engine'
LIBRARY_SERVICE_ID = '__library'
DS_MANAGER_SERVICE_ID = '_ds_manager'
JSON_DS_SERVICE_PREFIX = '__json__'


class APIModel(object):
    """Base Class for handling API requests."""

    def __init__(self, name, bus=None):
        self.name = name
        self.dse_long_timeout = cfg.CONF.dse.long_timeout
        self.action_retry_timeout = cfg.CONF.dse.execute_action_retry_timeout
        self.bus = bus

    # Note(thread-safety): blocking function
    def invoke_rpc(self, caller, name, kwargs, timeout=None):
            local = (caller is ENGINE_SERVICE_ID and
                     self.bus.node.service_object(
                         ENGINE_SERVICE_ID) is not None)
            return self.bus.rpc(
                caller, name, kwargs, timeout=timeout, local=local)
