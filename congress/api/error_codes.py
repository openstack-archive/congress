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

errors = {}
errors['add_item_id'] = (1001, "Add item does not support user-chosen ID")
errors['rule_syntax'] = (1002, "Syntax error for rule")
errors['multiple_rules'] = (
    1003, "Received string representing more than 1 rule")
errors['incomplete_simulate_args'] = (
    1004, "Simulate requires parameters: query, sequence, action_policy")
errors['simulate_without_policy'] = (
    1005, "Simulate must be told which policy evaluate the query on")
errors['sequence_syntax'] = (
    1006, "Syntax error in sequence")
errors['simulate_error'] = (
    1007, "Error in simulate procedure")
errors['rule_already_exists'] = (
    1008, "Rule already exists")
errors['schema_get_item_id'] = (
    1009, "Get item for schema does not support user-chosen ID")
errors['policy_name_must_be_provided'] = (
    1010, "A name must be provided when creating a policy")
errors['policy_name_must_be_id'] = (
    1011, "A policy name must be a valid tablename")
errors['no_policy_update_owner'] = (
    1012, "The policy owner_id cannot be updated")
errors['no_policy_update_kind'] = (
    1013, "The policy kind cannot be updated")
errors['failed_to_create_policy'] = (
    1014, "A new policy could not be created")
errors['policy_id_must_not_be_provided'] = (
    1015, "An ID may not be provided when creating a policy")


def get(name):
    if name not in errors:
        return (1000, "Unknown error")
    return errors[name]
