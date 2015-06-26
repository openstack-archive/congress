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
try:
    # For Python 3
    import http.client as httplib
except ImportError:
    import httplib

from oslo_log import log as logging

from congress.api import webservice
from congress.dse import deepsix
from congress.managers import datasource as datasource_manager


def d6service(name, keys, inbox, datapath, args):
    return RowModel(name, keys, inbox=inbox, dataPath=datapath, **args)


LOG = logging.getLogger(__name__)


class RowModel(deepsix.deepSix):
    """Model for handling API requests about Tables."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(RowModel, self).__init__(name, keys, inbox=inbox,
                                       dataPath=dataPath)
        self.engine = policy_engine
        self.datasource_mgr = datasource_manager.DataSourceManager()

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
        trace = "Not available"
        if 'trace' in params and params['trace'].lower() == 'true':
            gen_trace = True

        # table defined by data-source
        if 'ds_id' in context:
            service_name = context['ds_id']
            try:
                datasource = self.datasource_mgr.get_datasource(service_name)
            except datasource_manager.DatasourceNotFound as e:
                raise webservice.DataModelException(e.code, e.message,
                                                    http_status_code=e.code)

            service_name = datasource['name']
            service_obj = self.engine.d6cage.service_object(service_name)
            if service_obj is None:
                m = "Unknown datasource name '%s'" % service_name
                LOG.info(m)
                raise webservice.DataModelException(404, m, httplib.NOT_FOUND)
            tablename = context['table_id']
            if tablename not in service_obj.state:
                m = "Unknown tablename '%s' for datasource '%s'" % (
                    tablename, service_name)
                LOG.info(m)
                raise webservice.DataModelException(404, m, httplib.NOT_FOUND)
            results = []
            for tup in service_obj.state[tablename]:
                d = {}
                d['data'] = tup
                results.append(d)

        # table defined by policy
        elif 'policy_id' in context:
            policy_name = context['policy_id']
            if policy_name not in self.engine.theory:
                m = "Unknown policy name '%s'" % policy_name
                LOG.info(m)
                raise webservice.DataModelException(404, m, httplib.NOT_FOUND)
            tablename = context['table_id']
            if tablename not in self.engine.theory[policy_name].tablenames():
                m = "Unknown tablename '%s' for policy '%s'" % (
                    tablename, policy_name)
                LOG.info(m)
                raise webservice.DataModelException(404, m, httplib.NOT_FOUND)
            arity = self.engine.arity(tablename, policy_name)
            if arity is None:
                m = "Known table but unknown arity for '%s' in policy '%s'" % (
                    tablename, policy_name)
                LOG.error(m)
                raise webservice.DataModelException(404, m, httplib.NOT_FOUND)

            args = ["x" + str(i) for i in xrange(0, arity)]
            query = self.engine.parse1(tablename + "(" + ",".join(args) + ")")
            # LOG.debug("query: %s", query)
            result = self.engine.select(query, target=policy_name,
                                        trace=gen_trace)
            if gen_trace:
                literals = result[0]
                trace = result[1]
            else:
                literals = result
            # should NOT need to convert to set -- see bug 1344466
            literals = frozenset(literals)
            # LOG.info("results: %s", '\n'.join(str(x) for x in literals))
            results = []
            for lit in literals:
                d = {}
                d['data'] = [arg.name for arg in lit.arguments]
                results.append(d)

        # unknown
        else:
            m = "Unknown source for row-data"
            LOG.error(m)
            raise webservice.DataModelException(404, m, httplib.NOT_FOUND)
        if gen_trace:
            return {"results": results, "trace": trace}
        return {"results": results}

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
