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

import json

from oslo_log import log as logging

from congress.api import error_codes
from congress.api import webservice
from congress.dse import deepsix
from congress import exception
from congress.managers import datasource as datasource_manager


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return DatasourceModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class DatasourceModel(deepsix.deepSix):
    """Model for handling API requests about Datasources."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(DatasourceModel, self).__init__(name, keys, inbox=inbox,
                                              dataPath=dataPath)
        self.engine = policy_engine
        self.datasource_mgr = datasource_manager.DataSourceManager()

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
        datasources = self.datasource_mgr.get_datasources(filter_secret=True)
        results = [self.datasource_mgr.make_datasource_dict(datasource)
                   for datasource in datasources]

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
        try:
            obj = self.datasource_mgr.add_datasource(
                item=item)
        except (datasource_manager.BadConfig,
                datasource_manager.DatasourceNameInUse,
                datasource_manager.DriverNotFound) as e:
            LOG.info(_("Datasource Error: %s") % e.message)
            raise webservice.DataModelException(e.code, e.message,
                                                http_status_code=e.code)

        return (obj['id'], obj)

    def delete_item(self, id_, params, context=None):
        datasource = context.get('ds_id')
        try:
            self.datasource_mgr.delete_datasource(datasource)
        except (datasource_manager.DatasourceNotFound,
                exception.DanglingReference) as e:
            raise webservice.DataModelException(e.code, e.message)

    def request_refresh_action(self, params, context=None, request=None):
        ds_id = context.get('ds_id')
        try:
            self.datasource_mgr.request_refresh(ds_id)
        except (datasource_manager.DatasourceNotFound) as e:
            raise webservice.DataModelException(e.code, e.message)

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
            self.engine.execute_action(service, action, action_args)
        except exception.PolicyException as e:
            (num, desc) = error_codes.get('execute_error')
            raise webservice.DataModelException(num, desc + "::" + str(e))

        return {}
