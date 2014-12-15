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
from congress.openstack.common import log as logging


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return SchemaModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class SchemaModel(deepsix.deepSix):
    """Model for handling API requests about Schemas."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(SchemaModel, self).__init__(name, keys, inbox=inbox,
                                          dataPath=dataPath)
        self.engine = policy_engine

    def _create_table_dict(self, tablename, schema):
        cols = [{'name': x, 'description': 'None'}
                for x in schema[tablename]]
        return {'table_id': tablename,
                'columns': cols}

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

        # TODO(thinrichs): either pass id_=None or incorporate id_ into
        #    the logic below.  Ignore id_ for now as it is
        #    always part of CONTEXT.
        if 'ds_id' not in context:
            raise Exception(
                "The only element that currently has a schema is datasource "
                "but ds_id does not exist in context: " + str(context))
        service_name = context['ds_id']
        service_obj = self.engine.d6cage.service_object(service_name)
        if service_obj is None:
            return None
        schema = service_obj.get_schema()

        # one table
        if 'table_id' in context:
            table = context['table_id']
            if table not in schema:
                raise KeyError("Table '{}' for datasource '{}' has no "
                               "schema ".format(id_, service_name))
            return self._create_table_dict(table, schema)

        # all tables
        tables = [self._create_table_dict(table_, schema) for table_ in schema]
        return {'tables': tables}
