# Copyright (c) 2015 OpenStack Foundation
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
    return DatasourceConfigModel(name, keys, inbox=inbox,
                                 dataPath=datapath, **args)


class DatasourceConfigModel(deepsix.deepSix):
    """Model for handling API requests about Schemas."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(DatasourceConfigModel, self).__init__(name, keys, inbox=inbox,
                                                    dataPath=dataPath)
        self.engine = policy_engine
        self.datasource_mgr = datasource_manager.DataSourceManager

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
        driver = context.get('ds_id')
        try:
            datasource_info = self.datasource_mgr.get_driver_info(
                driver)
        except datasource_manager.DriverNotFound as e:
            raise webservice.DataModelException(e.code, e.message)
        return datasource_info
