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

from oslo_log import log as logging

from congress.api import api_utils
from congress.dse import deepsix
from congress import exception

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return TableModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class TableModel(deepsix.deepSix):
    """Model for handling API requests about Tables."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None, datasource_mgr=None):
        super(TableModel, self).__init__(name, keys, inbox=inbox,
                                         dataPath=dataPath)
        self.datasource_mgr = datasource_mgr
        self.engine = policy_engine

    def rpc(self, caller, name, *args, **kwargs):
        func = getattr(caller, name, None)
        if func:
            return func(*args, **kwargs)
        raise exception.CongressException('method: %s is not defined in %s' %
                                          (name, caller.__name__))

    def get_item(self, id_, params, context=None):
        """Retrieve item with id id_ from model.

        Args:
            id_: The ID of the item to retrieve
            params: A dict-like object containing parameters
                    from the request query string and body.
            context: Key-values providing frame of reference of request

        Returns:
             The matching item or None if item with id_ does not exist.
        """

        caller, source_id = api_utils.get_id_from_context(context,
                                                          self.datasource_mgr,
                                                          self.engine)

        tablename = self.rpc(caller, 'get_tablename', source_id, id_)
        if tablename:
            return {'id': tablename}

        LOG.info('source id %s or table id %s is not found',
                 source_id, id_)

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
        LOG.info('get_items has context %s', context)

        caller, source_id = api_utils.get_id_from_context(context,
                                                          self.datasource_mgr,
                                                          self.engine)

        tablenames = self.rpc(caller, 'get_tablenames', source_id)
        # when the source_id doesn't have any table, 'tablenames' is set([])
        # when the source_id doesn't exist 'tablenames' is None
        if isinstance(tablenames, set):
            return {'results': [{'id': x} for x in tablenames]}

        LOG.info('source id %s not found', source_id)

    # Tables can only be created/updated/deleted by writing policy
    #   or by adding new data sources.  Once we have internal data sources
    #   we need to implement all of these.

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
