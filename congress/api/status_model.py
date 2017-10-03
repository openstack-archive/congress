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

from congress.api import api_utils
from congress.api import base
from congress.api import webservice
from congress import exception


class StatusModel(base.APIModel):
    """Model for handling API requests about Statuses."""

    # Note(thread-safety): blocking function
    def get_item(self, id_, params, context=None):
        """Retrieve item with id id\_ from model.

        :param: id\_: The ID of the item to retrieve
        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: context: Key-values providing frame of reference of request

        :returns: The matching item or None if item with id\_ does not exist.
        """
        # Note(thread-safety): blocking call
        caller, source_id = api_utils.get_id_from_context(context)
        # FIXME(threod-safety): in DSE2, the returned caller can be a
        #   datasource name. But the datasource name may now refer to a new,
        #   unrelated datasource. Causing the rest of this code to operate on
        #   an unintended datasource.
        #   Fix: check UUID of datasource before operating. Abort if mismatch

        try:
            rpc_args = {'params': context, 'source_id': source_id}
            # Note(thread-safety): blocking call
            status = self.invoke_rpc(caller, 'get_status', rpc_args)
        except exception.CongressException as e:
            raise webservice.DataModelException(
                exception.NotFound.code, str(e),
                http_status_code=exception.NotFound.code)

        return status
