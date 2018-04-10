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

from congress.api import api_utils
from congress.api import base
from congress.api import webservice
from congress import exception


class DatasourceDriverModel(base.APIModel):
    """Model for handling API requests about DatasourceDriver."""

    def get_items(self, params, context=None):
        """Get items in model.

        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: context: Key-values providing frame of reference of request

        :returns: A dict containing at least a 'results' key whose value is
                 a list of items in the model.  Additional keys set in the
                 dict will also be rendered for the user.
        """
        drivers = self.bus.get_drivers_info()
        fields = ['id', 'description']
        results = [self.bus.make_datasource_dict(
                   driver, fields=fields)
                   for driver in drivers]
        return {"results": results}

    def get_item(self, id_, params, context=None):
        """Retrieve item with id id\_ from model.

        :param: id\_: The ID of the item to retrieve
        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: context: Key-values providing frame of reference of request

        :returns: The matching item or None if item with id\_ does not exist.
        """
        datasource = context.get('driver_id')
        try:
            driver = self.bus.get_driver_info(datasource)
            schema = self.bus.get_driver_schema(datasource)
        except exception.DriverNotFound as e:
            raise webservice.DataModelException(e.code, str(e),
                                                http_status_code=e.code)

        tables = [api_utils.create_table_dict(table_, schema)
                  for table_ in schema]
        driver['tables'] = tables
        return driver
