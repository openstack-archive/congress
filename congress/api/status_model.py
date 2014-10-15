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
    return StatusModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class StatusModel(deepsix.deepSix):
    """Model for handling API requests about Statuses."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(StatusModel, self).__init__(name, keys, inbox=inbox,
                                          dataPath=dataPath)
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
        if 'ds_id' not in context:
            raise Exception(
                "The only element that currently has a status is datasource "
                "but ds-id does not exist in context: " + str(context))
        service_name = context['ds_id']
        service_obj = self.engine.d6cage.service_object(service_name)
        if service_obj is None:
            return
        status = service_obj.get_status()
        if id_ not in status:
            raise KeyError("Status '{}' for datasource '{}' does not "
                           "exist ".format(id_, service_name))
        return status[id_]

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
        if 'ds_id' not in context:
            raise Exception(
                "The only element that currently has a status is datasource "
                "but ds-id does not exist in context: " + str(context))
        service_name = context['ds_id']
        service_obj = self.engine.d6cage.service_object(service_name)
        if service_obj is None:
            return
        status = service_obj.get_status()
        d = [{'key': key, 'value': value}
             for key, value in status.iteritems()]
        return {'results': d}
