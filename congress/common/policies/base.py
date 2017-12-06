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

from oslo_policy import policy


rules = [
    policy.RuleDefault(
        name='context_is_admin',
        check_str='role:admin'
    ),
    policy.RuleDefault(
        name='admin_only',
        check_str='rule:context_is_admin'
    ),
    policy.RuleDefault(
        name='regular_user',
        check_str='',
        description='The policy rule defining who is a regular user. This '
                    'rule can be overridden by, for example, a role check.'
    ),
    policy.RuleDefault(
        name='default',
        check_str='rule:admin_only',
        description='The default policy rule to apply when enforcing API '
                    'permissions. By default, all APIs are admin only. '
                    'This rule can be overridden (say by rule:regular_user) '
                    'to allow non-admins to access Congress APIs.'
    )
]


def list_rules():
    return rules
