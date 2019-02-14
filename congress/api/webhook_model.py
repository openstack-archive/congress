# Copyright (c) 2018 VMware, Inc. All rights reserved.
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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from congress.api import api_utils
from congress.api import base
from congress.api import webservice
from congress import exception


class WebhookModel(base.APIModel):
    """Model for handling webhook notifications."""

    def add_item(self, item, params, id_=None, context=None):
        """POST webhook notification.

        :param item: The webhook payload
        :param params: A dict-like object containing parameters
            from the request query string and body.
        :param id_: not used in this case; should be None
        :param context: Key-values providing frame of reference of request
        """
        caller, source_id = api_utils.get_id_from_context(context)
        table_name = context.get('table_name')

        try:
            if table_name:  # json ingester case
                args = {'table_name': table_name,
                        'body': item}
                # Note(thread-safety): blocking call
                self.invoke_rpc(base.JSON_DS_SERVICE_PREFIX + caller,
                                'json_ingester_webhook_handler', args)
            else:
                args = {'payload': item}
                # Note(thread-safety): blocking call
                self.invoke_rpc(caller, 'process_webhook_notification', args)
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)
