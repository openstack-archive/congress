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
from congress import exception


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return StatusModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class StatusModel(deepsix.deepSix):
    """Model for handling API requests about Statuses."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None, datasource_mgr=None):
        super(StatusModel, self).__init__(name, keys, inbox=inbox,
                                          dataPath=dataPath)
        self.datasource_mgr = datasource_mgr
        self.engine = policy_engine

    def rpc(self, caller, name, *args, **kwargs):
        func = getattr(caller, name, None)
        if func:
            return func(*args, **kwargs)
        raise exception.CongressException('method: %s is not defined in %s' %
                                          (name, caller.__name__))

    def datasource_rpc(self, name, datasource_id, *args, **kwargs):
        driver = self.engine.d6cage.getservice(id_=datasource_id,
                                               type_='datasource_driver')
        if not driver:
            raise exception.NotFound('Could not find datasource %s' %
                                     datasource_id)
        return self.rpc(driver['object'], name)

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

        try:
            if caller is self.engine:
                status = self.rpc(caller, 'get_status', source_id, context)
            else:
                status = self.datasource_rpc('get_status', source_id)
        except exception.CongressException as e:
            raise webservice.DataModelException(
                exception.NotFound.code, str(e),
                http_status_code=exception.NotFound.code)

        return status
