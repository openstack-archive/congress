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

from congress.dse import deepsix


def d6service(name, keys, inbox, datapath, args):
    return DatasourceModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class DatasourceModel(deepsix.deepSix):
    """Model for handling API requests about Datasources."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(DatasourceModel, self).__init__(name, keys, inbox=inbox,
                                              dataPath=dataPath)
        self.engine = policy_engine

    def get_item(self, id_, context=None):
        """Retrieve item with id id_ from model.

        Args:
            id_: The ID of the item to retrieve
            context: Key-values providing frame of reference of request

        Returns:
             The matching item or None if item with id_ does not exist.
        """
        if id_ not in self.engine.d6cage.services:
            return None
        # TODO(thinrichs): add all these meta-properties to datasources
        d = {'id': id_,
             'owner_id': 'd6cage',
             'enabled': True,
             'type': None,
             'config': None}
        return d

    def get_items(self, context=None):
        """Get items in model.

        Args:
            context: Key-values providing frame of reference of request

        Returns: A dict containing at least a 'results' key whose value is
                 a list of items in the model.  Additional keys set in the
                 dict will also be rendered for the user.
        """
        datasources = (set(self.engine.d6cage.services.keys()) -
                       self.engine.d6cage.system_service_names)
        results = [self.get_item(x, context) for x in datasources]
        return {"results": results}


    # TODO(thinrichs): It makes sense to sometimes allow users to "create"
    #  a new datasource.  It would mean giving us the Python code for
    #  the driver.  Or maybe it would mean instantiating it on the message
    #  bus.  Right now the policy engine takes care of instantiating
    #  services on the bus, so this isn't crucial as of now.

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


    # TODO(thinrichs): once we can create a data source, it will make
    #   sense to update it as well.
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
