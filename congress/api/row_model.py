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

from congress.api import api_utils
from congress.api import base
from congress.api import webservice
from congress import exception


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return RowModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class RowModel(base.APIModel):
    """Model for handling API requests about Rows."""
    def __init__(self, name, keys='', inbox=None, dataPath=None,
                 policy_engine=None, datasource_mgr=None):
        super(RowModel, self).__init__(name, keys, inbox=inbox,
                                       dataPath=dataPath,
                                       policy_engine=policy_engine,
                                       datasource_mgr=datasource_mgr)

    # TODO(thinrichs): No rows have IDs right now.  Maybe eventually
    #   could make ID the hash of the row, but then might as well
    #   just make the ID a string repr of the row.  No use case
    #   for it as of now since all rows are read-only.
    # def get_item(self, id_, context=None):
    #     """Retrieve item with id id_ from model.

    #     Args:
    #         id_: The ID of the item to retrieve
    #         context: Key-values providing frame of reference of request

    #     Returns:
    #          The matching item or None if item with id_ does not exist.
    #     """

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
        LOG.info("get_items(context=%s)", context)
        gen_trace = False
        if 'trace' in params and params['trace'].lower() == 'true':
            gen_trace = True

        # Get the caller, it should be either policy or datasource
        caller, source_id = api_utils.get_id_from_context(
            context, self.datasource_mgr, self.engine)

        table_id = context['table_id']
        try:
            args = {'table_id': table_id, 'source_id': source_id,
                    'trace': gen_trace}
            result = self.invoke_rpc(caller, 'get_row_data', args)
        except exception.CongressException as e:
            m = ("Error occurred while processing source_id '%s' for row "
                 "data of the table '%s'" % (source_id, table_id))
            LOG.exception(m)
            raise webservice.DataModelException.create(e)

        if gen_trace and caller is self.engine:
            # DSE2 returns lists instead of tuples, so correct that.
            result[0] = [{'data': tuple(x['data'])} for x in result[0]]
            return {'results': result[0],
                    'trace': result[1] or "Not available"}
        else:
            result = [{'data': tuple(x['data'])} for x in result]
            return {'results': result}

    def update_items(self, items, params, context=None):
        """Updates all data in a table.

        Args:
            id_: A table id for updating all row
            items: A data for new rows
            params: A dict-like object containing parameters from
                    request query
            context: Key-values providing frame of reference of request
        Returns: None
        Raises:
            KeyError: table id doesn't exist
            DataModelException: any error occurs during replacing rows.
        """
        LOG.info("update_items(context=%s)" % context)
        caller, source_id = api_utils.get_id_from_context(context,
                                                          self.datasource_mgr,
                                                          self.engine)
        table_id = context['table_id']
        try:
            args = {'table_id': table_id, 'source_id': source_id,
                    'objs': items}
            self.invoke_rpc(caller, 'update_entire_data', args)
        except exception.CongressException as e:
            m = ("Error occurred while processing updating rows for "
                 "source_id '%s' and table_id '%s'" % (source_id, table_id))
            LOG.exception(m)
            raise webservice.DataModelException.create(e)
        LOG.info("finish update_items(context=%s)" % context)
        LOG.debug("updated table %s with row items: %s" %
                  (table_id, str(items)))

    # TODO(thinrichs): It makes sense to sometimes allow users to create
    #  a new row for internal data sources.  But since we don't have
    #  those yet all tuples are read-only from the API.

    # def add_item(self, item, id_=None, context=None):
    #     """Add item to model.

    #     Args:
    #         item: The item to add to the model
    #         id_: The ID of the item, or None if an ID should be generated
    #         context: Key-values providing frame of reference of request

    #     Returns:
    #          Tuple of (ID, newly_created_item)

    #     Raises:
    #         KeyError: ID already exists.
    #     """

    # TODO(thinrichs): once we have internal data sources,
    #   add the ability to update a row.  (Or maybe not and implement
    #   via add+delete.)
    # def update_item(self, id_, item, context=None):
    #     """Update item with id_ with new data.

    #     Args:
    #         id_: The ID of the item to be updated
    #         item: The new item
    #         context: Key-values providing frame of reference of request

    #     Returns:
    #          The updated item.

    #     Raises:
    #         KeyError: Item with specified id_ not present.
    #     """
    #     # currently a noop since the owner_id cannot be changed
    #     if id_ not in self.items:
    #         raise KeyError("Cannot update item with ID '%s': "
    #                        "ID does not exist")
    #     return item

    # TODO(thinrichs): once we can create, we should be able to delete
    # def delete_item(self, id_, context=None):
        # """Remove item from model.

        # Args:
        #     id_: The ID of the item to be removed
        #     context: Key-values providing frame of reference of request

        # Returns:
        #      The removed item.

        # Raises:
        #     KeyError: Item with specified id_ not present.
        # """
