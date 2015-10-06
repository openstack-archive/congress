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


# name of unknown error
UNKNOWN = 'unknown'


# dict mapping error name to (<error id>, <description>, <http error code>)
errors = {}
errors[UNKNOWN] = (
    1000, "Unknown error", httplib.BAD_REQUEST)
errors['add_item_id'] = (
    1001, "Add item does not support user-chosen ID", httplib.BAD_REQUEST)
errors['rule_syntax'] = (
    1002, "Syntax error for rule", httplib.BAD_REQUEST)
errors['multiple_rules'] = (
    1003, "Received string representing more than 1 rule", httplib.BAD_REQUEST)
errors['incomplete_simulate_args'] = (
    1004, "Simulate requires parameters: query, sequence, action_policy",
    httplib.BAD_REQUEST)
errors['simulate_without_policy'] = (
    1005, "Simulate must be told which policy evaluate the query on",
    httplib.BAD_REQUEST)
errors['sequence_syntax'] = (
    1006, "Syntax error in sequence", httplib.BAD_REQUEST)
errors['simulate_error'] = (
    1007, "Error in simulate procedure", httplib.INTERNAL_SERVER_ERROR)
errors['rule_already_exists'] = (
    1008, "Rule already exists", httplib.CONFLICT)
errors['schema_get_item_id'] = (
    1009, "Get item for schema does not support user-chosen ID",
    httplib.BAD_REQUEST)
errors['policy_name_must_be_provided'] = (
    1010, "A name must be provided when creating a policy",
    httplib.BAD_REQUEST)
errors['no_policy_update_owner'] = (
    1012, "The policy owner_id cannot be updated",
    httplib.BAD_REQUEST)
errors['no_policy_update_kind'] = (
    1013, "The policy kind cannot be updated",
    httplib.BAD_REQUEST)
errors['failed_to_create_policy'] = (
    1014, "A new policy could not be created",
    httplib.INTERNAL_SERVER_ERROR)
errors['policy_id_must_not_be_provided'] = (
    1015, "An ID may not be provided when creating a policy",
    httplib.BAD_REQUEST)
errors['execute_error'] = (
    1016, "Error in execution procedure", httplib.INTERNAL_SERVER_ERROR)
errors['service_action_syntax'] = (
    1017, "Incorrect action syntax. Requires: <service>:<action>",
    httplib.BAD_REQUEST)
errors['execute_action_args_syntax'] = (
    1018, "Incorrect argument syntax"
    "Requires: {'positional': [<args>], 'named': {<key>:<value>,}}",
    httplib.BAD_REQUEST)
errors['rule_not_permitted'] = (
    1019, "Rules not permitted on non persisted policies",
    httplib.BAD_REQUEST)
errors['policy_not_exist'] = (
    1020, "The specified policy does not exist", httplib.BAD_REQUEST)
errors['policy_rule_insertion_failure'] = (
    1021, "The policy rule could not be inserted", httplib.BAD_REQUEST)
errors['policy_abbreviation_error'] = (
    1022, "The policy abbreviation must be a string and the length of the "
          "string must be equal to or less than 5 characters",
    httplib.BAD_REQUEST)


def get(name):
    if name not in errors:
        name = UNKNOWN
    return errors[name][:2]


def get_num(name):
    if name not in errors:
        name = UNKNOWN
    return errors[name][0]


def get_desc(name):
    if name not in errors:
        name = UNKNOWN
    return errors[name][1]


def get_http(name):
    if name not in errors:
        name = UNKNOWN
    return errors[name][2]
