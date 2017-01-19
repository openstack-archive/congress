#!/usr/bin/python
# Copyright (c) 2017 NTT All rights reserved.
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

# This script outputs pre definded policies and rules in a config file.
# The config file content should look like following:
# {
#   "policies":
#     [
#       {
#         "name": "sample_policy",
#         "rules": [
#                    {
#                      "rule": "p(x):- q(x)",
#                      "name": "rule1"
#                    },
#                    {
#                      "rule": "q(1)"
#                    },
#                    {
#                      "rule": "q('sample-row')"
#                    },
#                    {
#                      "rule": "server_ids(x):- nova:servers(id=x)"
#                    }
#         ]
#       }
#    ]
# }
#
# Config file option:
#    - "name" key in rule object is option
#
# sample config file is located at
# /path/to/congress/scripts/preload-polices/policy-rules.json.sample


import argparse
import json
import sys

OPENSTACK_COMMAND = 'openstack congress'
POLICY_CREATE = 'policy create'
RULE_CREATE = 'policy rule create'
NAME_OPTION = '--name %s'


def load_policies(policy_file):
    with open(args.policy_file, 'r') as f:
        data = f.read()
        policies = json.loads(data)
    return policies


def main(args):
    defined_policies = load_policies(args.policy_file)

    for p in defined_policies['policies']:
        # create defined policy
        sys.stdout.write(' '.join([OPENSTACK_COMMAND, POLICY_CREATE,
                                   p['name'], '\n']))
        # create defined rules
        for r in p['rules']:
            cmd_string = [OPENSTACK_COMMAND, RULE_CREATE]
            if r.get('name'):
                cmd_string.append(NAME_OPTION % r['name'])
            cmd_string.extend([p['name'], '"%s"' % r['rule'], '\n'])
            sys.stdout.write(' '.join(cmd_string))


parser = argparse.ArgumentParser(description='Output pre-defined policy in '
                                             'openstack command style.')
parser.add_argument('policy_file', type=str,
                    help='Path to pre defined policies and rules.')


if __name__ == '__main__':
    args = parser.parse_args()
    main(args)
