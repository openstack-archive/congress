# Copyright (c) 2014 VMware, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from oslo_utils import uuidutils

from congress.db import db_policy_rules
from congress.tests import base


class TestPolicyRulesDb(base.SqlTestCase):

    def test_add_policy_rule(self):
        id = uuidutils.generate_uuid()
        rule_str = "p(x) :- q(x)"
        policy_name = "classification"
        comment = "None"
        rule = db_policy_rules.add_policy_rule(id=id,
                                               policy_name=policy_name,
                                               rule=rule_str,
                                               comment=comment)
        self.assertEqual(id, rule.id)
        self.assertEqual(policy_name, rule.policy_name)
        self.assertEqual(rule_str, rule.rule)
        self.assertEqual(comment, rule.comment)

    def test_add_policy_rule_with_name(self):
        id = uuidutils.generate_uuid()
        rule_str = "p(x) :- q(x)"
        policy_name = "classification"
        comment = "None"
        rule_name = "classification_rule"
        rule = db_policy_rules.add_policy_rule(id=id,
                                               policy_name=policy_name,
                                               rule=rule_str,
                                               comment=comment,
                                               rule_name=rule_name)
        self.assertEqual(id, rule.id)
        self.assertEqual(policy_name, rule.policy_name)
        self.assertEqual(rule_str, rule.rule)
        self.assertEqual(comment, rule.comment)
        self.assertEqual(rule_name, rule.name)

    def test_add_get_policy_rule(self):
        id = uuidutils.generate_uuid()
        rule_str = "p(x) :- q(x)"
        policy_name = "classification"
        comment = "None"
        db_policy_rules.add_policy_rule(id=id,
                                        policy_name=policy_name,
                                        rule=rule_str,
                                        comment=comment)
        rule = db_policy_rules.get_policy_rule(id, policy_name)
        self.assertEqual(id, rule.id)
        self.assertEqual(policy_name, rule.policy_name)
        self.assertEqual(rule_str, rule.rule)
        self.assertEqual(comment, rule.comment)

    def test_add_delete_get_policy_rule(self):
        id = uuidutils.generate_uuid()
        rule_str = "p(x) :- q(x)"
        policy_name = "classification"
        comment = "None"
        db_policy_rules.add_policy_rule(id=id,
                                        policy_name=policy_name,
                                        rule=rule_str,
                                        comment=comment)
        db_policy_rules.delete_policy_rule(id)
        rule = db_policy_rules.get_policy_rule(id, policy_name)
        self.assertEqual(rule, None)

    def test_add_delete_get_deleted_policy_rule(self):
        id = uuidutils.generate_uuid()
        rule_str = "p(x) :- q(x)"
        policy_name = "classification"
        comment = "None"
        rule1 = db_policy_rules.add_policy_rule(id=id,
                                                policy_name=policy_name,
                                                rule=rule_str,
                                                comment=comment)
        db_policy_rules.delete_policy_rule(id)
        rule2 = db_policy_rules.get_policy_rule(id, policy_name, deleted=True)
        self.assertEqual(rule1.id, rule2.id)
        self.assertNotEqual(rule1.deleted, rule2.deleted)

    def test_add_two_rules_and_get(self):
        id1 = uuidutils.generate_uuid()
        rule1_str = "p(x) :- q(x)"
        id2 = uuidutils.generate_uuid()
        rule2_str = "z(x) :- q(x)"
        policy_name = "classification"
        comment = "None"
        db_policy_rules.add_policy_rule(id=id1,
                                        policy_name=policy_name,
                                        rule=rule1_str,
                                        comment=comment)

        db_policy_rules.add_policy_rule(id=id2,
                                        policy_name=policy_name,
                                        rule=rule2_str,
                                        comment=comment)

        rules = db_policy_rules.get_policy_rules(policy_name)
        self.assertEqual(len(rules), 2)
        self.assertEqual(id1, rules[0].id)
        self.assertEqual(policy_name, rules[0].policy_name)
        self.assertEqual(rule1_str, rules[0].rule)
        self.assertEqual(comment, rules[0].comment)
        self.assertEqual(id2, rules[1].id)
        self.assertEqual(policy_name, rules[1].policy_name)
        self.assertEqual(rule2_str, rules[1].rule)
        self.assertEqual(comment, rules[1].comment)
        self.assertEqual(len(db_policy_rules.get_policy_rules()), 2)

    def test_is_soft_deleted_not_deleted(self):
        uuid = uuidutils.generate_uuid()
        self.assertEqual('', db_policy_rules.is_soft_deleted(uuid, False))

    def test_is_soft_deleted_is_deleted(self):
        uuid = uuidutils.generate_uuid()
        self.assertEqual(uuid, db_policy_rules.is_soft_deleted(uuid, True))
