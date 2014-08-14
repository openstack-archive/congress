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
from congress.policy import compile
from congress.policy import runtime


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

    def get_item(self, id_, context=None):
        """Retrieve item with id id_ from model.

        Args:
            id_: The ID of the item to retrieve
            context: Key-values providing frame of reference of request

        Returns:
             The matching item or None if item with id_ does not exist.
        """
        policy_name = self.policy_name(context)
        if policy_name not in self.engine.theory:
            raise KeyError("Policy with ID '%s' does not exist",
                           policy_name)
        rule = self.engine.theory[policy_name].get_rule(id_)
        if rule is None:
            return
        # TODO(thinrichs): add comment property to rule
        d = {'rule': str(rule),
             'id': rule.id,
             'comment': 'None'}
        return d

    def get_items(self, context=None):
        """Get items in model.

        Args:
            context: Key-values providing frame of reference of request

        Returns: A dict containing at least a 'results' key whose value is
                 a list of items in the model.  Additional keys set in the
                 dict will also be rendered for the user.
        """
        policy_name = self.policy_name(context)
        if policy_name not in self.engine.theory:
            return []
        results = []
        for rule in self.engine.theory[policy_name].policy():
            # TODO(thinrichs): add comment property to rule
            d = {'rule': str(rule),
                 'id': rule.id,
                 'comment': 'None'}
            results.append(d)
        return {'results': results}

    def add_item(self, item, id_=None, context=None):
        """Add item to model.

        Args:
            item: The item to add to the model
            id_: The ID of the item, or None if an ID should be generated
            context: Key-values providing frame of reference of request

        Returns:
             Tuple of (ID, newly_created_item)

        Raises:
            KeyError: ID already exists.
        """
        # TODO(thinrichs): add comment property to rule
        if id_ is not None:
            raise NotImplemented
        str_rule = item['rule']
        rule = compile.parse1(str_rule)
        changes = self.change_rule(rule, context)
        for change in changes:
            if change.formula == rule:
                d = {'rule': str(rule),
                     'id': rule.id,
                     'comment': None}
                return (rule.id, d)
        # rule already existed
        policy_name = self.policy_name(context)
        for p in self.engine.theory[policy_name].policy():
            if p == rule:
                d = {'rule': str(rule),
                     'id': rule.id,
                     'comment': 'None'}
                return (rule.id, d)
        raise Exception("add_item added a rule but then could not find it.")

    def delete_item(self, id_, context=None):
        """Remove item from model.

        Args:
            id_: The ID of the item to be removed
            context: Key-values providing frame of reference of request

        Returns:
             The removed item.

        Raises:
            KeyError: Item with specified id_ not present.
        """
        item = self.get_item(id_, context)
        if item is None:
            raise KeyError('ID %s does not exist', id_)
        rule = compile.parse1(item['rule'])
        self.change_rule(rule, context, insert=False)
        return item

    def change_rule(self, parsed_rule, context, insert=True):
        policy_name = self.policy_name(context)
        if policy_name not in self.engine.theory:
            raise KeyError("Policy with ID '%s' does not exist", policy_name)
        event = runtime.Event(
            formula=parsed_rule,
            insert=insert,
            target=policy_name)
        (permitted, changes) = self.engine.process_policy_update([event])
        if not permitted:
            raise Exception("Errors: " + ";".join((str(x) for x in changes)))
        return changes
