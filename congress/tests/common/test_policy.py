# Copyright 2011 Piston Cloud Computing, Inc.
# All Rights Reserved.

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

"""Test of Policy Engine For Congress."""

import os.path

import mock
from oslo_config import cfg
from oslo_policy import policy as oslo_policy

from congress.common import config
from congress.common import policy
from congress import context
from congress import exception
from congress.tests import base
from congress.tests import policy_fixture
from congress import utils


CONF = cfg.CONF


class PolicyFileTestCase(base.TestCase):
    def setUp(self):
        super(PolicyFileTestCase, self).setUp()
        config.setup_logging()
        self.context = context.RequestContext('fake', 'fake')
        self.target = {}

    def test_modified_policy_reloads(self):
        with utils.tempdir() as tmpdir:
            tmpfilename = os.path.join(tmpdir, 'policy')

            CONF.set_override('policy_file', tmpfilename, 'oslo_policy')

            # NOTE(uni): context construction invokes policy check to determin
            # is_admin or not. As a side-effect, policy reset is needed here
            # to flush existing policy cache.
            policy.reset()

            action = "example:test"
            with open(tmpfilename, "w") as policyfile:
                policyfile.write('{"example:test": ""}')
            policy.enforce(self.context, action, self.target)
            with open(tmpfilename, "w") as policyfile:
                policyfile.write('{"example:test": "!"}')
            policy._ENFORCER.load_rules(True)
            self.assertRaises(exception.PolicyNotAuthorized, policy.enforce,
                              self.context, action, self.target)


class PolicyTestCase(base.TestCase):
    def setUp(self):
        super(PolicyTestCase, self).setUp()
        rules = oslo_policy.Rules.from_dict({
            "true": '@',
            "example:allowed": '@',
            "example:denied": "!",
            "example:get_http": "http://www.example.com",
            "example:my_file": "role:compute_admin or "
                               "project_id:%(project_id)s",
            "example:early_and_fail": "! and @",
            "example:early_or_success": "@ or !",
            "example:lowercase_admin": "role:admin or role:sysadmin",
            "example:uppercase_admin": "role:ADMIN or role:sysadmin",
        })
        policy.reset()
        policy.init()
        policy.set_rules(rules)
        self.context = context.RequestContext('fake', 'fake', roles=['member'])
        self.target = {}

    def test_enforce_nonexistent_action_throws(self):
        action = "example:noexist"
        self.assertRaises(exception.PolicyNotAuthorized, policy.enforce,
                          self.context, action, self.target)

    def test_enforce_bad_action_throws(self):
        action = "example:denied"
        self.assertRaises(exception.PolicyNotAuthorized, policy.enforce,
                          self.context, action, self.target)

    def test_enforce_bad_action_noraise(self):
        action = "example:denied"
        result = policy.enforce(self.context, action, self.target, False)
        self.assertEqual(result, False)

    def test_enforce_good_action(self):
        action = "example:allowed"
        result = policy.enforce(self.context, action, self.target)
        self.assertEqual(result, True)

    @mock.patch.object(oslo_policy._checks.HttpCheck, '__call__',
                       return_value=True)
    def test_enforce_http_true(self, mock_httpcheck):
        action = "example:get_http"
        target = {}
        result = policy.enforce(self.context, action, target)
        self.assertTrue(result)

    @mock.patch.object(oslo_policy._checks.HttpCheck, '__call__',
                       return_value=False)
    def test_enforce_http_false(self, mock_httpcheck):
        action = "example:get_http"
        target = {}
        self.assertRaises(exception.PolicyNotAuthorized,
                          policy.enforce, self.context,
                          action, target)

    def test_templatized_enforcement(self):
        target_mine = {'project_id': 'fake'}
        target_not_mine = {'project_id': 'another'}
        action = "example:my_file"
        policy.enforce(self.context, action, target_mine)
        self.assertRaises(exception.PolicyNotAuthorized, policy.enforce,
                          self.context, action, target_not_mine)

    def test_early_AND_enforcement(self):
        action = "example:early_and_fail"
        self.assertRaises(exception.PolicyNotAuthorized, policy.enforce,
                          self.context, action, self.target)

    def test_early_OR_enforcement(self):
        action = "example:early_or_success"
        policy.enforce(self.context, action, self.target)

    def test_ignore_case_role_check(self):
        lowercase_action = "example:lowercase_admin"
        uppercase_action = "example:uppercase_admin"
        # NOTE(dprince) we mix case in the Admin role here to ensure
        # case is ignored
        admin_context = context.RequestContext('admin',
                                               'fake',
                                               roles=['AdMiN'])
        policy.enforce(admin_context, lowercase_action, self.target)
        policy.enforce(admin_context, uppercase_action, self.target)


class DefaultPolicyTestCase(base.TestCase):

    def setUp(self):
        super(DefaultPolicyTestCase, self).setUp()

        self.rules = oslo_policy.Rules.from_dict({
            "default": '',
            "example:exist": "!",
        })

        self._set_rules('default')

        self.context = context.RequestContext('fake', 'fake')

    def _set_rules(self, default_rule):
        policy.reset()
        policy.init(rules=self.rules, default_rule=default_rule,
                    use_conf=False)

    def test_policy_called(self):
        self.assertRaises(exception.PolicyNotAuthorized, policy.enforce,
                          self.context, "example:exist", {})

    def test_not_found_policy_calls_default(self):
        policy.enforce(self.context, "example:noexist", {})

    def test_default_not_found(self):
        self._set_rules("default_noexist")
        self.assertRaises(exception.PolicyNotAuthorized, policy.enforce,
                          self.context, "example:noexist", {})


class IsAdminCheckTestCase(base.TestCase):
    def setUp(self):
        super(IsAdminCheckTestCase, self).setUp()
        policy.init()

    def test_init_true(self):
        check = policy.IsAdminCheck('is_admin', 'True')

        self.assertEqual(check.kind, 'is_admin')
        self.assertEqual(check.match, 'True')
        self.assertEqual(check.expected, True)

    def test_init_false(self):
        check = policy.IsAdminCheck('is_admin', 'nottrue')

        self.assertEqual(check.kind, 'is_admin')
        self.assertEqual(check.match, 'False')
        self.assertEqual(check.expected, False)

    def test_call_true(self):
        check = policy.IsAdminCheck('is_admin', 'True')

        self.assertEqual(check('target', dict(is_admin=True),
                               policy._ENFORCER), True)
        self.assertEqual(check('target', dict(is_admin=False),
                               policy._ENFORCER), False)

    def test_call_false(self):
        check = policy.IsAdminCheck('is_admin', 'False')

        self.assertEqual(check('target', dict(is_admin=True),
                               policy._ENFORCER), False)
        self.assertEqual(check('target', dict(is_admin=False),
                               policy._ENFORCER), True)


class AdminRolePolicyTestCase(base.TestCase):
    def setUp(self):
        super(AdminRolePolicyTestCase, self).setUp()
        config.setup_logging()
        self.policy = self.useFixture(policy_fixture.RoleBasedPolicyFixture())
        self.context = context.RequestContext('fake', 'fake', roles=['member'])
        self.actions = policy.get_rules().keys()
        self.target = {}

    def test_enforce_admin_actions_with_nonadmin_context_throws(self):
        """test for non-admin context

        Check if non-admin context passed to admin actions throws
        Policy not authorized exception
        """
        for action in self.actions:
            self.assertRaises(exception.PolicyNotAuthorized, policy.enforce,
                              self.context, action, self.target)
