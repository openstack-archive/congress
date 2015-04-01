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

from congress.api import error_codes
from congress.api import webservice
from congress.db import db_policy_rules
from congress.dse import deepsix
from congress.exception import PolicyException
from congress.openstack.common import log as logging
from congress.openstack.common import uuidutils


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
        # non-datasource policies (i.e. those persisted to disk)
        policies = db_policy_rules.get_policies()
        LOG.debug("persisted policies: %s", policies)
        persisted_policies = set([p.name for p in policies])
        persisted = [self._db_item_to_dict(p) for p in policies]

        # datasource policies (i.e. those not persisted)
        nonpersisted = [self._theory_item_to_dict(self.engine.theory[p])
                        for p in self.engine.theory
                        if p not in persisted_policies]

        return {"results": persisted + nonpersisted}

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
        policy = db_policy_rules.get_policy(id_)
        if policy is None:
            return
        return self._db_item_to_dict(policy)

    def _theory_item_to_dict(self, theory_item):
        """From a given Runtime.Theory, return a policy dict."""
        d = {'id': 'None',
             'name': theory_item.name,
             'abbreviation': theory_item.abbr,
             'description': 'Datasource store',
             'owner_id': 'system',
             'kind': theory_item.kind}
        return d

    def _db_item_to_dict(self, db_item):
        """From a given database policy, return a policy dict."""
        d = {'id': db_item.id,
             'name': db_item.name,
             'abbreviation': db_item.abbreviation,
             'description': db_item.description,
             'owner_id': db_item.owner,
             'kind': db_item.kind}
        return d

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
        # validation
        if id_ is None:
            id_ = str(uuidutils.generate_uuid())
        else:
            (num, desc) = error_codes.get('policy_id_must_not_be_provided')
            raise webservice.DataModelException(num, desc)
        if 'name' not in item:
            (num, desc) = error_codes.get('policy_name_must_be_provided')
            raise webservice.DataModelException(num, desc)
        name = item['name']
        try:
            self.engine.parse("%s() :- true()" % name)
        except PolicyException:
            (num, desc) = error_codes.get('policy_name_must_be_id')
            raise webservice.DataModelException(
                num, desc + ": " + str(name))

        # create policy in policy engine
        try:
            policy_obj = self.engine.create_policy(
                name, abbr=item.get('abbreviation'), kind=item.get('kind'))
        except PolicyException as e:
            (num, desc) = error_codes.get('failed_to_create_policy')
            raise webservice.DataModelException(
                num, desc + ": " + str(e))

        # save policy to database
        desc = item.get('description', '')
        if desc is None:
            desc = ''
        obj = {'id': id_,
               'name': name,
               'owner_id': 'user',
               'description': desc,
               'abbreviation': policy_obj.abbr,
               'kind': self.engine.policy_type(name)}
        # TODO(thinrichs): add rollback of policy engine if this fails
        db_policy_rules.add_policy(obj['id'],
                                   obj['name'],
                                   obj['abbreviation'],
                                   obj['description'],
                                   obj['owner_id'],
                                   obj['kind'])
        return (id_, obj)

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
        # check that policy exists
        db_object = self.get_item(id_, context)
        if db_object is None:
            raise KeyError("Cannot delete policy with ID '%s': "
                           "ID '%s' does not exist",
                           id_, id_)
        if db_object['name'] in ['classification', 'action']:
            raise KeyError("Cannot delete system-maintained policy %s",
                           db_object['name'])
        # delete policy from memory and from database
        self.engine.delete_policy(db_object['name'])
        db_policy_rules.delete_policy(id_)
        return db_object

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

        # parse arguments so that result of simulate is an object
        query = self._parse_rule(query)
        sequence = self._parse_rules(sequence)

        try:
            result = self.engine.simulate(
                query, theory, sequence, actions, delta, trace)
        except PolicyException as e:
            (num, desc) = error_codes.get('simulate_error')
            raise webservice.DataModelException(num, desc + "::" + str(e))

        # always return dict
        if trace:
            return {'result': [str(x) for x in result[0]],
                    'trace': result[1]}
        return {'result': [str(x) for x in result]}

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
        action_args = body.get('args')
        if (not isinstance(action_args, dict)):
            (num, desc) = error_codes.get('execute_action_args_syntax')
            raise webservice.DataModelException(num, desc)

        try:
            self.engine.execute_action(service, action, action_args)
        except PolicyException as e:
            (num, desc) = error_codes.get('execute_error')
            raise webservice.DataModelException(num, desc + "::" + str(e))

        return {}

    def _parse_rules(self, string, errmsg=''):
        if errmsg:
            errmsg = errmsg + ":: "
        # basic parsing
        try:
            return self.engine.parse(string)
        except PolicyException as e:
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
