# Copyright (c) 2017 VMware, Inc. All rights reserved.
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

from congress.api import base
from congress.api import error_codes
from congress.api import webservice
from congress import exception

LOG = logging.getLogger(__name__)


class LibraryPolicyModel(base.APIModel):
    """Model for handling API requests about Library Policies."""

    # Note(thread-safety): blocking function
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
        try:
            # Note(thread-safety): blocking call
            return {"results": self.invoke_rpc(base.LIBRARY_SERVICE_ID,
                                               'get_policies',
                                               {})}
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)

    # Note(thread-safety): blocking function
    def get_item(self, id_, params, context=None):
        """Retrieve item with name name from model.

        Args:
            name: The unique name of the item to retrieve
            params: A dict-like object containing parameters
                    from the request query string and body.
            context: Key-values providing frame of reference of request

        Returns:
             The matching item or None if no item named name exists.
        """
        try:
            # Note(thread-safety): blocking call
            return self.invoke_rpc(base.LIBRARY_SERVICE_ID,
                                   'get_policy',
                                   {'id_': id_, 'include_rules': True})
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)

    # Note(thread-safety): blocking function
    def add_item(self, item, params, id_=None, context=None):
        """Add item to model.

        Args:
            item: The item to add to the model
            params: A dict-like object containing parameters
                    from the request query string and body.
            id_: The unique name of the item
            context: Key-values providing frame of reference of request

        Returns:
             Tuple of (ID, newly_created_item)

        Raises:
            KeyError: ID already exists.
            DataModelException: Addition cannot be performed.
        """
        if id_ is not None:
            (num, desc) = error_codes.get('policy_id_must_not_be_provided')
            raise webservice.DataModelException(num, desc)

        try:
            # Note(thread-safety): blocking call
            policy_metadata = self.invoke_rpc(
                base.LIBRARY_SERVICE_ID, 'create_policy',
                {'policy_dict': item})
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)

        return (policy_metadata['id'], policy_metadata)

    # Note(thread-safety): blocking function
    def delete_item(self, id_, params, context=None):
        """Remove item from model.

        Args:
            id_: The unique name of the item to be removed
            params:
            context: Key-values providing frame of reference of request

        Returns:
             The removed item.

        Raises:
            KeyError: Item with specified id_ not present.
        """
        # Note(thread-safety): blocking call
        return self.invoke_rpc(base.LIBRARY_SERVICE_ID,
                               'delete_policy',
                               {'id_': id_})

    def update_item(self, id_, item, params, context=None):
        """Update item with id_ with new data.

        Args:
            id_: The ID of the item to be updated
            item: The new item
            params: A dict-like object containing parameters
                    from the request query string and body.
            context: Key-values providing frame of reference of request

        Returns:
             The updated item.

        Raises:
            KeyError: Item with specified id_ not present.
        """
        # Note(thread-safety): blocking call
        try:
            return self.invoke_rpc(base.LIBRARY_SERVICE_ID,
                                   'replace_policy',
                                   {'id_': id_,
                                    'policy_dict': item})
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)
