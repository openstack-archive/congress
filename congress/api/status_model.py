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
from congress.dse import d6cage
from congress.dse import deepsix
from congress.exception import NotFound


def d6service(name, keys, inbox, datapath, args):
    return StatusModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class StatusModel(deepsix.deepSix):
    """Model for handling API requests about Statuses."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(StatusModel, self).__init__(name, keys, inbox=inbox,
                                          dataPath=dataPath)
        self.cage = d6cage.d6Cage()

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
        # FIXME(arosen): we need better API validation in congress
        if 'ds_id' not in context:
            raise Exception(
                "The only element that currently has a status is datasource "
                "but ds-id does not exist in context: " + str(context))

        service = self.cage.getservice(id_=context['ds_id'],
                                       type_='datasource_driver')
        if service:
            return service['object'].get_status()

        raise webservice.DataModelException(NotFound.code,
                                            'Could not find service %s' % id_,
                                            http_status_code=NotFound.code)
