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
try:
    # For Python 3
    import http.client as httplib
except ImportError:
    import httplib

import uuid

from congress.api import error_codes
from congress.api import webservice
from congress.db import db_policy_rules
from congress.dse import deepsix
from congress.exception import PolicyException
from congress.openstack.common import log as logging
from congress.policy_engines import agnostic


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return RuleModel(name, keys, inbox=inbox, dataPath=datapath, **args)


class RuleModel(deepsix.deepSix):
    """Model for handling API requests about policy Rules."""
    def __init__(self, name, keys, inbox=None, dataPath=None,
                 policy_engine=None):
        super(RuleModel, self).__init__(name, keys, inbox=inbox,
                                        dataPath=dataPath)
        assert policy_engine is not None
        self.engine = policy_engine

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
        policy_name = self.policy_name(context)
        rule = db_policy_rules.get_policy_rule(id_, policy_name)
        if rule is None:
            return
        d = {'rule': rule.rule,
             'id': rule.id,
             'comment': rule.comment,
             'name': rule.name}
        return d

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
        policy_name = self.policy_name(context)
        rules = db_policy_rules.get_policy_rules(policy_name)
        results = []
        for rule in rules:
            d = {'rule': rule.rule,
                 'id': rule.id,
                 'comment': rule.comment,
                 'name': rule.name}
            results.append(d)
        return {'results': results}

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
        # Reject rules inserted into non-persisted policies
        # (i.e. datasource policies)
        policy_name = self.policy_name(context)
        policies = db_policy_rules.get_policies()
        persisted_policies = set([p.name for p in policies])
        if policy_name not in persisted_policies:
            if policy_name in self.engine.theory:
                LOG.debug("add_item error: rule not permitted for policy %s",
                          policy_name)
                raise webservice.DataModelException(
                    *error_codes.get('rule_not_permitted'),
                    http_status_code=httplib.FORBIDDEN)
            else:
                LOG.debug("add_item error: policy %s not exist", policy_name)
                raise webservice.DataModelException(
                    *error_codes.get('policy_not_exist'),
                    http_status_code=httplib.NOT_FOUND)

        str_rule = item['rule']
        id = uuid.uuid4()
        try:
            rule = self.engine.parse(str_rule)
            if len(rule) == 1:
                rule = rule[0]
            else:
                (num, desc) = error_codes.get('multiple_rules')
                raise webservice.DataModelException(
                    num, desc + ":: Received multiple rules: " +
                    "; ".join(str(x) for x in rule))
            rule.set_id(id)
            rule.set_name(item.get('name'))
            rule.set_comment(None)
            rule.set_original_str(str_rule)
            changes = self.change_rule(rule, context)
        except PolicyException as e:
            LOG.debug("add_item error: invalid rule syntax")
            (num, desc) = error_codes.get('rule_syntax')
            raise webservice.DataModelException(num, desc + "::" + str(e))

        for change in changes:
            if change.formula == rule:
                d = {'rule': rule.pretty_str(),
                     'id': str(id),
                     'comment': rule.comment,
                     'name': item.get('name')}
                try:
                    db_policy_rules.add_policy_rule(
                        d['id'], policy_name, str_rule, d['comment'],
                        rule_name=d['name'])
                    return (d['id'], d)
                except Exception as db_exception:
                    try:
                        self.change_rule(rule, context, insert=False)
                    except Exception as change_exception:
                        raise Exception(
                            "Error thrown during recovery from DB error. "
                            "Inconsistent state.  DB error: %s.  "
                            "New error: %s.", str(db_exception),
                            str(change_exception))

        num, desc = error_codes.get('rule_already_exists')
        raise webservice.DataModelException(
            num, desc, http_status_code=httplib.CONFLICT)

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
        item = self.get_item(id_, params, context)
        if item is None:
            raise KeyError('ID %s does not exist', id_)
        rule = self.engine.parse1(item['rule'])
        self.change_rule(rule, context, insert=False)
        db_policy_rules.delete_policy_rule(id_)
        return item

    def change_rule(self, parsed_rule, context, insert=True):
        policy_name = self.policy_name(context)
        if policy_name not in self.engine.theory:
            raise KeyError("Policy with ID '%s' does not exist", policy_name)
        event = agnostic.Event(
            formula=parsed_rule,
            insert=insert,
            target=policy_name)
        (permitted, changes) = self.engine.process_policy_update([event])
        if not permitted:
            raise PolicyException(
                "Errors: " + ";".join((str(x) for x in changes)))
        return changes
