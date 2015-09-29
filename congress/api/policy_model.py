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
import json
import re

from oslo_log import log as logging
import six

from congress.api import error_codes
from congress.api import webservice
from congress.dse import deepsix
from congress import exception


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return PolicyModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class PolicyModel(deepsix.deepSix):
    """Model for handling API requests about Policies."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(PolicyModel, self).__init__(name, keys, inbox=inbox,
                                          dataPath=dataPath)
        self.engine = policy_engine

    def rpc(self, name, *args, **kwds):
        f = getattr(self.engine, name)
        return f(*args, **kwds)

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
            return {"results": self.rpc('persistent_get_policies')}
        except exception.CongressException as e:
            raise webservice.DataModelException.create(e)

    def get_item(self, id_, params, context=None):
        """Retrieve item with id id_ from model.

        Args:
            id_: The ID of the item to retrieve
            params: A dict-like object containing parameters
                    from the request query string and body.
            context: Key-values providing frame of reference of request

        Returns:
             The matching item or None if id_ does not exist.
        """
        try:
            return self.rpc('persistent_get_policy', id_)
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
            DataModelException: Addition cannot be performed.
        """
        self._check_create_policy(id_, item)
        name = item['name']
        try:
            policy_metadata = self.rpc(
                'persistent_create_policy', name,
                abbr=item.get('abbreviation'), kind=item.get('kind'),
                desc=item.get('description'))
        except exception.CongressException as e:
            (num, desc) = error_codes.get('failed_to_create_policy')
            raise webservice.DataModelException(
                num, desc + ": " + str(e))

        return (policy_metadata['id'], policy_metadata)

    def _check_create_policy(self, id_, item):
        if id_ is not None:
            (num, desc) = error_codes.get('policy_id_must_not_be_provided')
            raise webservice.DataModelException(num, desc)
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

    def delete_item(self, id_, params, context=None):
        """Remove item from model.

        Args:
            id_: The ID or name of the item to be removed
            params:
            context: Key-values providing frame of reference of request

        Returns:
             The removed item.

        Raises:
            KeyError: Item with specified id_ not present.
        """
        return self.rpc('persistent_delete_policy', id_)

    def _get_boolean_param(self, key, params):
        if key not in params:
            return False
        value = params[key]
        return value.lower() == "true" or value == "1"

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
            result = self.rpc(
                'simulate', query, theory, sequence, actions, delta=delta,
                trace=trace, as_list=True)
        except exception.PolicyException as e:
            (num, desc) = error_codes.get('simulate_error')
            raise webservice.DataModelException(num, desc + "::" + str(e))

        # always return dict
        if trace:
            return {'result': result[0],
                    'trace': result[1]}
        return {'result': result}

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
            self.rpc('execute_action', service, action, action_args)
        except exception.PolicyException as e:
            (num, desc) = error_codes.get('execute_error')
            raise webservice.DataModelException(num, desc + "::" + str(e))

        return {}
