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
from congress.api import webservice
from congress.dse import deepsix
from congress.managers import datasource as datasource_manager

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return SchemaModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class SchemaModel(deepsix.deepSix):
    """Model for handling API requests about Schemas."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 datasource_mgr=None):
        super(SchemaModel, self).__init__(name, keys, inbox=inbox,
                                          dataPath=dataPath)

        self.datasource_mgr = datasource_mgr

    def rpc(self, caller, name, *args, **kwargs):
        f = getattr(caller, name)
        return f(*args, **kwargs)

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
        datasource = context.get('ds_id')
        table = context.get('table_id')
        try:
            schema = self.rpc(self.datasource_mgr, 'get_datasource_schema',
                              datasource)
        except (datasource_manager.DatasourceNotFound,
                datasource_manager.DriverNotFound) as e:
            raise webservice.DataModelException(e.code, str(e),
                                                http_status_code=e.code)

        # request to see the schema for one table
        if table:
            if table not in schema:
                raise webservice.DataModelException(
                    404, ("Table '{}' for datasource '{}' has no "
                          "schema ".format(id_, datasource)),
                    http_status_code=404)
            return api_utils.create_table_dict(table, schema)

        tables = [api_utils.create_table_dict(table_, schema)
                  for table_ in schema]
        return {'tables': tables}
