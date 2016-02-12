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

from oslo_log import log as logging

from congress.api import base
from congress.api import error_codes
from congress.api import webservice
from congress import exception


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return RuleModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class RuleModel(base.APIModel):
    """Model for handling API requests about policy Rules."""

    def policy_name(self, context):
        if 'ds_id' in context:
            return context['ds_id']
        elif 'policy_id' in context:
            return context['policy_id']

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
        try:
            args = {'id_': id_, 'policy_name': self.policy_name(context)}
            return self.invoke_rpc(self.engine, 'persistent_get_rule', args)
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)

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
        try:
            args = {'policy_name': self.policy_name(context)}
            rules = self.invoke_rpc(self.engine, 'persistent_get_rules', args)
            return {'results': rules}
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)

    def add_item(self, item, params, id_=None, context=None):
        """Add item to model.

        Args:
            item: The item to add to the model
            params: A dict-like object containing parameters
                    from the request query string and body.
            id_: The ID of the item, or None if an ID should be generated
            context: Key-values providing frame of reference of request

        Returns:
             Tuple of (ID, newly_created_item)

        Raises:
            KeyError: ID already exists.
        """
        if id_ is not None:
            raise webservice.DataModelException(
                *error_codes.get('add_item_id'))
        try:
            args = {'policy_name': self.policy_name(context),
                    'str_rule': item.get('rule'),
                    'rule_name': item.get('name'),
                    'comment': item.get('comment')}
            return self.invoke_rpc(self.engine, 'persistent_insert_rule', args)
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)

    def delete_item(self, id_, params, context=None):
        """Remove item from model.

        Args:
            id_: The ID of the item to be removed
            params: A dict-like object containing parameters
                    from the request query string and body.
            context: Key-values providing frame of reference of request

        Returns:
             The removed item.

        Raises:
            KeyError: Item with specified id_ not present.
        """
        try:
            args = {'id_': id_, 'policy_name_or_id': self.policy_name(context)}
            return self.invoke_rpc(self.engine, 'persistent_delete_rule', args)
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)
