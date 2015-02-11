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

from congress.api import webservice
from congress.dse import deepsix
from congress.managers import datasource as datasource_manager
from congress.openstack.common import log as logging


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return DatasourceModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class DatasourceModel(deepsix.deepSix):
    """Model for handling API requests about Datasources."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(DatasourceModel, self).__init__(name, keys, inbox=inbox,
                                              dataPath=dataPath)
        self.engine = policy_engine
        self.datasource_mgr = datasource_manager.DataSourceManager()

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
        datasources = self.datasource_mgr.get_datasources()
        results = [self.datasource_mgr.make_datasource_dict(datasource)
                   for datasource in datasources]
        return {"results": results}

    def add_item(self, item, params, id_=None, context=None):
        """Add item to model.

         Args:
             item: The item to add to the model
             id_: The ID of the item, or None if an ID should be generated
             context: Key-values providing frame of reference of request

         Returns:
              Tuple of (ID, newly_created_item)

         Raises:
             KeyError: ID already exists.
         """
        try:
            obj = self.datasource_mgr.add_datasource(
                item=item)
        except (datasource_manager.BadConfig,
                datasource_manager.DatasourceNameInUse) as e:
            LOG.info(_("Datasource Error: %s") % e.message)
            raise webservice.DataModelException(e.code, e.message,
                                                http_status_code=e.code)

        return (obj['id'], obj)

    def delete_item(self, id_, params, context=None):
        datasource = context.get('ds_id')
        try:
            self.datasource_mgr.delete_datasource(datasource)
        except datasource_manager.DatasourceDriverNotFound as e:
            raise webservice.DataModelException(e.code, e.message)
