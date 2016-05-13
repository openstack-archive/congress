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
#

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json

from oslo_config import cfg
from oslo_log import log as logging

from congress.api import api_utils
from congress.api import base
from congress.api import error_codes
from congress.api import webservice
from congress import exception
from congress import utils

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return DatasourceModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class DatasourceModel(base.APIModel):
    """Model for handling API requests about Datasources."""
    def __init__(self, name, keys='', inbox=None, dataPath=None,
                 policy_engine=None, datasource_mgr=None, bus=None,
                 synchronizer=None):
        super(DatasourceModel, self).__init__(name, keys, inbox=inbox,
                                              dataPath=dataPath,
                                              policy_engine=policy_engine,
                                              datasource_mgr=datasource_mgr,
                                              bus=bus)
        self.synchronizer = synchronizer
        self.dist_arch = getattr(cfg.CONF, 'distributed_architecture', False)

    def get_items(self, params, context=None):
        """Get items in model.

        Args:
            params: A dict-like object containing parameters
                    from the request query string and body.
            context: Key-values providing frame of reference of request

        Returns: A dict containing at least a 'results' key whose value is
                 a list of items in the model.  Additional keys set in the
                 dict will also be rendered for the user.
        """
        if self.dist_arch:
            self.datasource_mgr = self.bus

        results = self.datasource_mgr.get_datasources(filter_secret=True)

        # Check that running datasources match the datasources in the
        # database since this is going to tell the client about those
        # datasources, and the running datasources should match the
        # datasources we show the client.

        # TODO(ramineni): Need to move this to new architecture
        if self.synchronizer:
            self.synchronizer.synchronize_datasources()
        return {"results": results}

    def add_item(self, item, params, id_=None, context=None):
        """Add item to model.

         Args:
             item: The item to add to the model
             id_: The ID of the item, or None if an ID should be generated
             context: Key-values providing frame of reference of request

         Returns:
              Tuple of (ID, newly_created_item)

         Raises:
             KeyError: ID already exists.
         """
        obj = None
        try:
            if self.dist_arch:
                obj = self.bus.add_datasource(item=item)
                utils.create_datasource_policy(self.bus, obj['name'],
                                               self.engine)
            else:
                obj = self.datasource_mgr.add_datasource(item=item)
        except (exception.BadConfig,
                exception.DatasourceNameInUse,
                exception.DriverNotFound,
                exception.DatasourceCreationError) as e:
            LOG.exception(_("Datasource creation failed."))
            if obj:
                # Do cleanup
                self.delete_datasource(obj)
            raise webservice.DataModelException(e.code, e.message,
                                                http_status_code=e.code)

        return (obj['id'], obj)

    def delete_item(self, id_, params, context=None):
        ds_id = context.get('ds_id')
        try:
            if self.dist_arch:
                datasource = self.bus.get_datasource(ds_id)
                args = {'name': datasource['name'],
                        'disallow_dangling_refs': True}
                self.invoke_rpc(self.engine, 'delete_policy', args)
                self.bus.delete_datasource(datasource)
            else:
                self.datasource_mgr.delete_datasource(ds_id)
        except (exception.DatasourceNotFound,
                exception.DanglingReference) as e:
            raise webservice.DataModelException(e.code, e.message)

    def request_refresh_action(self, params, context=None, request=None):
        caller, source_id = api_utils.get_id_from_context(context,
                                                          self.datasource_mgr)
        try:
            args = {'source_id': source_id}
            self.invoke_rpc(caller, 'request_refresh', args)
        except exception.CongressException as e:
            LOG.exception(e)
            raise webservice.DataModelException.create(e)

    def execute_action(self, params, context=None, request=None):
        "Execute the action."
        service = context.get('ds_id')
        body = json.loads(request.body)
        action = body.get('name')
        action_args = body.get('args', {})
        if (not isinstance(action_args, dict)):
            (num, desc) = error_codes.get('execute_action_args_syntax')
            raise webservice.DataModelException(num, desc)

        try:
            args = {'service_name': service, 'action': action,
                    'action_args': action_args}
            self.invoke_rpc(self.engine, 'execute_action', args)
        except exception.PolicyException as e:
            (num, desc) = error_codes.get('execute_error')
            raise webservice.DataModelException(num, desc + "::" + str(e))

        return {}
