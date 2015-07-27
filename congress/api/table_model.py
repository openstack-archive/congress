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

from congress.api import webservice
from congress.dse import deepsix
from congress.managers import datasource as datasource_manager

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return TableModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class TableModel(deepsix.deepSix):
    """Model for handling API requests about Tables."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(TableModel, self).__init__(name, keys, inbox=inbox,
                                         dataPath=dataPath)
        self.datasource_mgr = datasource_manager.DataSourceManager()
        self.engine = policy_engine

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

        # table defined by data-source
        if 'ds_id' in context:
            datasource_id = context['ds_id']
            if datasource_id in self.engine.d6cage.getservices().keys():
                datasource = self.engine.d6cage.getservice(name=datasource_id)
            else:
                datasource = self.engine.d6cage.getservice(id_=datasource_id)

            if not datasource:
                LOG.info("data-source %s not found", datasource_id)
                return None

            service_obj = self.engine.d6cage.service_object(datasource['name'])
            tablename = context['table_id']
            if tablename not in service_obj.state:
                LOG.info("data-source %s does not have table %s",
                         datasource_id, tablename)
                return None
            return {'id': id_}

        # table defined by policy
        elif 'policy_id' in context:
            policy_name = context['policy_id']
            if policy_name not in self.engine.theory:
                return None
            tables = self.engine.theory[policy_name].tablenames()
            tablename = context['table_id']
            if tablename not in tables:
                return None
            return {'id': id_}

        # should not happen
        else:
            raise Exception("Internal error: context %s should have included "
                            "either ds_id or policy_id" % str(context))

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

        # data-source
        if 'ds_id' in context:
            # FIXME(arosen): this file needs refactoring.
            datasource = context.get('ds_id')
            try:
                datasource = self.datasource_mgr.get_datasource(
                    datasource)
            except datasource_manager.DatasourceNotFound as e:
                raise webservice.DataModelException(e.code, e.message)

            service_name = context['ds_id']
            service_obj = self.engine.d6cage.service_object(datasource['name'])
            if service_obj is None:
                LOG.info("data-source %s not found", service_name)
                return []
            LOG.info("data-source %s found", service_name)
            results = [{'id': x} for x in service_obj.state.keys()]

        # policy
        elif 'policy_id' in context:
            policy_name = context['policy_id']
            if policy_name not in self.engine.theory:
                LOG.info("policy %s not found", policy_name)
                return None
            results = [{'id': x}
                       for x in self.engine.theory[policy_name].tablenames()]

        # should not happen
        else:
            LOG.error("Blackhole for table context %s", context)
            results = []
        return {'results': results}

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
