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


from oslo_log import log as logging
from oslo_serialization import jsonutils as json

from congress.api import api_utils
from congress.api import base
from congress.api import error_codes
from congress.api import webservice
from congress import exception

LOG = logging.getLogger(__name__)


class DatasourceModel(base.APIModel):
    """Model for handling API requests about Datasources."""

    # Note(thread-safety): blocking function
    def get_items(self, params, context=None):
        """Get items in model.

        :param: params: A dict-like object containing parameters
            from the request query string and body.
        :param: context: Key-values providing frame of reference of request

        :returns: A dict containing at least a 'results' key whose value is
                 a list of items in the model.  Additional keys set in the
                 dict will also be rendered for the user.
        """

        # Note(thread-safety): blocking call
        results = self.bus.get_datasources(filter_secret=True)

        # Check that running datasources match the datasources in the
        # database since this is going to tell the client about those
        # datasources, and the running datasources should match the
        # datasources we show the client.

        return {"results": results}

    def get_item(self, id_, params, context=None):
        """Get datasource corresponding to id\_ in model."""
        try:
            datasource = self.bus.get_datasource(id_)
            return datasource
        except exception.DatasourceNotFound as e:
            LOG.debug("Datasource '%s' not found", id_)
            raise webservice.DataModelException(e.code, str(e),
                                                http_status_code=e.code)

    # Note(thread-safety): blocking function
    def add_item(self, item, params, id_=None, context=None):
        """Add item to model.

         :param: item: The item to add to the model
         :param: id\_: The ID of the item, or None if an ID should be generated
         :param: context: Key-values providing frame of reference of request

         :returns:  Tuple of (ID, newly_created_item)

         :raises  KeyError: ID already exists.
         """
        obj = None
        try:
            # Note(thread-safety): blocking call
            obj = self.invoke_rpc(base.DS_MANAGER_SERVICE_ID,
                                  'add_datasource',
                                  {'items': item},
                                  timeout=self.dse_long_timeout)
            # Let PE synchronizer take care of creating the policy.
        except (exception.BadConfig,
                exception.DatasourceNameInUse,
                exception.DriverNotFound,
                exception.DatasourceCreationError) as e:
            LOG.debug(_("Datasource creation failed."))
            raise webservice.DataModelException(
                e.code, webservice.original_msg(e), http_status_code=e.code)
        except exception.RpcTargetNotFound as e:
            LOG.debug("Datasource creation failed.")
            LOG.warning(webservice.original_msg(e))
            raise webservice.DataModelException(
                e.code, webservice.original_msg(e), http_status_code=503)

        return (obj['id'], obj)

    # Note(thread-safety): blocking function
    def delete_item(self, id_, params, context=None):
        ds_id = context.get('ds_id')
        try:
            # Note(thread-safety): blocking call
            datasource = self.bus.get_datasource(ds_id)
            # FIXME(thread-safety):
            #  by the time greenthread resumes, the
            #  returned datasource name could refer to a totally different
            #  datasource, causing the rest of this code to unintentionally
            #  delete a different datasource
            #  Fix: check UUID of datasource before operating.
            #  Abort if mismatch
            self.invoke_rpc(base.DS_MANAGER_SERVICE_ID,
                            'delete_datasource',
                            {'datasource': datasource},
                            timeout=self.dse_long_timeout)
            # Let PE synchronizer takes care of deleting policy
        except (exception.DatasourceNotFound,
                exception.DanglingReference) as e:
            LOG.debug("Datasource deletion failed.")
            raise webservice.DataModelException(e.code, str(e))
        except exception.RpcTargetNotFound as e:
            LOG.debug("Datasource deletion failed.")
            LOG.warning(webservice.original_msg(e))
            raise webservice.DataModelException(
                e.code, webservice.original_msg(e), http_status_code=503)

    # Note(thread-safety): blocking function
    def request_refresh_action(self, params, context=None, request=None):
        caller, source_id = api_utils.get_id_from_context(context)
        try:
            args = {'source_id': source_id}
            # Note(thread-safety): blocking call
            self.invoke_rpc(caller, 'request_refresh', args)
        except exception.CongressException as e:
            LOG.debug(e)
            raise webservice.DataModelException.create(e)

    # Note(thread-safety): blocking function
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
            # TODO(ekcs): perhaps keep execution synchronous when explicitly
            #   called via API
            # Note(thread-safety): blocking call
            self.invoke_rpc(base.ENGINE_SERVICE_ID, 'execute_action', args)
        except exception.PolicyException as e:
            (num, desc) = error_codes.get('execute_error')
            raise webservice.DataModelException(num, desc + "::" + str(e))

        return {}
