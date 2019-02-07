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

import re

from oslo_serialization import jsonutils as json
import six

from congress.api import base
from congress.api import error_codes
from congress.api import webservice
from congress import exception
from congress.library_service import library_service


class PolicyModel(base.APIModel):
    """Model for handling API requests about Policies."""

    # Note(thread-safety): blocking function
    def get_items(self, params, context=None):
        """Get items in model.

        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: context: Key-values providing frame of reference of request

        :returns: A dict containing at least a 'results' key whose value is
                 a list of items in the model.  Additional keys set in the
                 dict will also be rendered for the user.
        """
        try:
            # Note(thread-safety): blocking call
            return {"results": self.invoke_rpc(base.ENGINE_SERVICE_ID,
                                               'persistent_get_policies',
                                               {})}
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)

    # Note(thread-safety): blocking function
    def get_item(self, id_, params, context=None):
        """Retrieve item with id id\_ from model.

        :param: id\_: The ID of the item to retrieve
        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: context: Key-values providing frame of reference of request

        :returns: The matching item or None if id\_ does not exist.
        """
        try:
            # Note(thread-safety): blocking call
            return self.invoke_rpc(base.ENGINE_SERVICE_ID,
                                   'persistent_get_policy',
                                   {'id_': id_})
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)

    # Note(thread-safety): blocking function
    def add_item(self, item, params, id_=None, context=None):
        """Add item to model.

        :param: item: The item to add to the model
        :param: params: A dict-like object containing parameters
                    from the request query string and body.
        :param: id\_: The ID of the item, or None if an ID should be generated
        :param: context: Key-values providing frame of reference of request

        :returns: Tuple of (ID, newly_created_item)

        :raises KeyError: ID already exists.
        :raises DataModelException: Addition cannot be performed.
        :raises BadRequest: library_policy parameter and request body both
            present
        """

        if id_ is not None:
            (num, desc) = error_codes.get('policy_id_must_not_be_provided')
            raise webservice.DataModelException(num, desc)

        # case 1: parameter gives library policy UUID
        if 'library_policy' in params:
            if item:
                raise exception.BadRequest(
                    'Policy creation request with `library_policy` parameter '
                    'must not have non-empty body.')
            try:
                # Note(thread-safety): blocking call
                library_policy_object = self.invoke_rpc(
                    base.LIBRARY_SERVICE_ID,
                    'get_policy', {'id_': params['library_policy']})

                policy_metadata = self.invoke_rpc(
                    base.ENGINE_SERVICE_ID,
                    'persistent_create_policy_with_rules',
                    {'policy_rules_obj': library_policy_object},
                    timeout=self.dse_long_timeout)
            except exception.CongressException as e:
                raise webservice.DataModelException.create(e)

            return (policy_metadata['id'], policy_metadata)

        # case 2: item contains rules
        if 'rules' in item:
            self._check_create_policy_item(item)
            try:
                library_service.validate_policy_item(item)
                # Note(thread-safety): blocking call
                policy_metadata = self.invoke_rpc(
                    base.ENGINE_SERVICE_ID,
                    'persistent_create_policy_with_rules',
                    {'policy_rules_obj': item}, timeout=self.dse_long_timeout)
            except exception.CongressException as e:
                raise webservice.DataModelException.create(e)

            return (policy_metadata['id'], policy_metadata)

        # case 3: item does not contain rules
        self._check_create_policy_item(item)
        name = item['name']
        try:
            # Note(thread-safety): blocking call
            policy_metadata = self.invoke_rpc(
                base.ENGINE_SERVICE_ID, 'persistent_create_policy',
                {'name': name,
                 'abbr': item.get('abbreviation'),
                 'kind': item.get('kind'),
                 'desc': item.get('description')})
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)

        return (policy_metadata['id'], policy_metadata)

    def _check_create_policy_item(self, item):
        if 'name' not in item:
            (num, desc) = error_codes.get('policy_name_must_be_provided')
            raise webservice.DataModelException(num, desc)
        abbr = item.get('abbreviation')
        if abbr:
            # the length of abbreviation column is 5 chars in policy DB table,
            # check it in API layer and raise exception if it's too long.
            if not isinstance(abbr, six.string_types) or len(abbr) > 5:
                (num, desc) = error_codes.get('policy_abbreviation_error')
                raise webservice.DataModelException(num, desc)

    # Note(thread-safety): blocking function
    def delete_item(self, id_, params, context=None):
        """Remove item from model.

        :param: id\_: The ID or name of the item to be removed
        :param: params:
        :param: context: Key-values providing frame of reference of request

        :returns: The removed item.

        :raises KeyError: Item with specified id\_ not present.
        """
        # Note(thread-safety): blocking call
        return self.invoke_rpc(base.ENGINE_SERVICE_ID,
                               'persistent_delete_policy',
                               {'name_or_id': id_},
                               timeout=self.dse_long_timeout)

    def _get_boolean_param(self, key, params):
        if key not in params:
            return False
        value = params[key]
        return value.lower() == "true" or value == "1"

    # Note: It's confusing to figure out how this method is called.
    # It is called via user supplied string in the `action` method of
    # api/webservice.py:ElementHandler
    # Note(thread-safety): blocking function
    def simulate_action(self, params, context=None, request=None):
        """Simulate the effects of executing a sequence of updates.

        :returns: the result of a query.
        """
        # grab string arguments
        theory = context.get('policy_id') or params.get('policy')
        if theory is None:
            (num, desc) = error_codes.get('simulate_without_policy')
            raise webservice.DataModelException(num, desc)

        body = json.loads(request.body)
        query = body.get('query')
        sequence = body.get('sequence')
        actions = body.get('action_policy')
        delta = self._get_boolean_param('delta', params)
        trace = self._get_boolean_param('trace', params)
        if query is None or sequence is None or actions is None:
            (num, desc) = error_codes.get('incomplete_simulate_args')
            raise webservice.DataModelException(num, desc)

        try:
            args = {'query': query, 'theory': theory, 'sequence': sequence,
                    'action_theory': actions, 'delta': delta,
                    'trace': trace, 'as_list': True}
            # Note(thread-safety): blocking call
            result = self.invoke_rpc(base.ENGINE_SERVICE_ID, 'simulate',
                                     args, timeout=self.dse_long_timeout)
        except exception.PolicyException as e:
            (num, desc) = error_codes.get('simulate_error')
            raise webservice.DataModelException(num, desc + "::" + str(e))

        # always return dict
        if trace:
            return {'result': result[0],
                    'trace': result[1]}
        return {'result': result}

    # Note(thread-safety): blocking function
    def execute_action(self, params, context=None, request=None):
        """Execute the action."""
        body = json.loads(request.body)
        # e.g. name = 'nova:disconnectNetwork'
        items = re.split(':', body.get('name'))
        if len(items) != 2:
            (num, desc) = error_codes.get('service_action_syntax')
            raise webservice.DataModelException(num, desc)
        service = items[0].strip()
        action = items[1].strip()
        action_args = body.get('args', {})
        if (not isinstance(action_args, dict)):
            (num, desc) = error_codes.get('execute_action_args_syntax')
            raise webservice.DataModelException(num, desc)

        try:
            args = {'service_name': service,
                    'action': action,
                    'action_args': action_args}
            # Note(thread-safety): blocking call
            self.invoke_rpc(base.ENGINE_SERVICE_ID, 'execute_action', args,
                            timeout=self.action_retry_timeout)
        except exception.PolicyException as e:
            (num, desc) = error_codes.get('execute_error')
            raise webservice.DataModelException(num, desc + "::" + str(e))

        return {}
