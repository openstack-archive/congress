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
from congress.api import error_codes
from congress.api import webservice
from congress.dse import deepsix
from congress.policy import compile


def d6service(name, keys, inbox, datapath, args):
    return PolicyModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class PolicyModel(deepsix.deepSix):
    """Model for handling API requests about Policies."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(PolicyModel, self).__init__(name, keys, inbox=inbox,
                                          dataPath=dataPath)
        self.engine = policy_engine

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
        results = [self.get_item(x, params, context)
                   for x in self.engine.theory.keys()]
        return {"results": results}

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
        if id_ not in self.engine.theory:
            return None
        # TODO(thinrichs): Add meta-data to policies
        d = {'id': id_,
             'owner_id': 'system'}
        return d

    def _get_boolean_param(self, key, params):
        if key not in params:
            return False
        value = params[key]
        return value.lower() == "true" or value == "1"

    def simulate_action(self, params, context=None, request=None):
        """Simulate the effects of executing a sequence of updates and
        return the result of a query.
        """
        # grab string arguments
        theory = context.get('policy_id') or params.get('policy')
        if theory is None:
            (num, desc) = error_codes.get('simulate_without_policy')
            raise webservice.DataModelException(num, desc)

        query = params.get('query')
        sequence = params.get('sequence')
        actions = params.get('action_policy')
        delta = self._get_boolean_param('delta', params)
        trace = self._get_boolean_param('trace', params)
        if query is None or sequence is None or actions is None:
            (num, desc) = error_codes.get('incomplete_simulate_args')
            raise webservice.DataModelException(num, desc)

        # parse arguments so that result of simulate is an object
        query = self._parse_rule(query)
        sequence = self._parse_rules(sequence)

        try:
            result = self.engine.simulate(
                query, theory, sequence, actions, delta, trace)
        except compile.CongressException as e:
            (num, desc) = error_codes.get('simulate_error')
            raise webservice.DataModelException(num, desc + "::" + str(e))

        # always return dict
        if trace:
            return {'result': [str(x) for x in result[0]],
                    'trace': result[1]}
        return {'result': [str(x) for x in result]}


    def _parse_rules(self, string, errmsg=''):
        if errmsg:
            errmsg = errmsg + ":: "
        # basic parsing
        try:
            return compile.parse(string)
        except compile.CongressException as e:
            (num, desc) = error_codes.get('rule_syntax')
            raise webservice.DataModelException(
                num, desc + ":: " + errmsg + str(e))

    def _parse_rule(self, string, errmsg=''):
        rules = self._parse_rules(string, errmsg)
        if len(rules) == 1:
            return rules[0]
        if errmsg:
            errmsg = errmsg + ":: "
        (num, desc) = error_codes.get('multiple_rules')
        raise webservice.DataModelException(
            num, desc + ":: " + errmsg + string + " parses to " +
            "; ".join(str(x) for x in rules))



    # TODO(thinrichs): Add ability to create multiple policies,
    #   to support multi-tenancy
    # def add_item(self, item, id_=None, context=None):
    #     """Add item to model.

    #     Args:
    #         item: The item to add to the model
    #         id_: The ID of the item, or None if an ID should be generated
    #         context: Key-values providing frame of reference of request

    #     Returns:
    #          Tuple of (ID, newly_created_item)

    #     Raises:
    #         KeyError: ID already exists.
    #     """

    # TODO(thinrichs): Once we have a multi-tenant runtime,
    #   add ability to update policy metadata.
    # def update_item(self, id_, item, context=None):
    #     """Update item with id_ with new data.

    #     Args:
    #         id_: The ID of the item to be updated
    #         item: The new item
    #         context: Key-values providing frame of reference of request

    #     Returns:
    #          The updated item.

    #     Raises:
    #         KeyError: Item with specified id_ not present.
    #     """
    #     # currently a noop since the owner_id cannot be changed
    #     if id_ not in self.items:
    #         raise KeyError("Cannot update item with ID '%s': "
    #                        "ID does not exist")
    #     return item

    # TODO(thinrichs): Once we have a multi-tenant runtime,
    #   add ability to delete policies.
    # def delete_item(self, id_, context=None):
        # """Remove item from model.

        # Args:
        #     id_: The ID of the item to be removed
        #     context: Key-values providing frame of reference of request

        # Returns:
        #      The removed item.

        # Raises:
        #     KeyError: Item with specified id_ not present.
        # """
