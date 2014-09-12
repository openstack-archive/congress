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

import os
import unittest

from congress.openstack.common import log as logging
from congress.policy import runtime
from congress.tests import helper

LOG = logging.getLogger(__name__)

NREC_THEORY = 'non-recursive theory'


class TestRuntime(unittest.TestCase):
    """Tests for Runtime that are not specific to any theory."""

    def setUp(self):
        pass

    def check_equal(self, actual_string, correct_string, msg):
        self.assertTrue(helper.datalog_equal(
            actual_string, correct_string, msg))

    def test_theory_inclusion(self):
        """Test evaluation routines when one theory includes another."""
        # spread out across inclusions
        th1 = runtime.NonrecursiveRuleTheory()
        th2 = runtime.NonrecursiveRuleTheory()
        th3 = runtime.NonrecursiveRuleTheory()
        th1.includes.append(th2)
        th2.includes.append(th3)

        th1.insert(helper.str2form('p(x) :- q(x), r(x), s(2)'))
        th2.insert(helper.str2form('q(1)'))
        th1.insert(helper.str2form('r(1)'))
        th3.insert(helper.str2form('s(2)'))

        self.check_equal(
            helper.pol2str(th1.select(helper.str2form('p(x)'))),
            'p(1)', 'Data spread across inclusions')

        # TODO(thinrichs): add tests with other types of theories,
        # once we get those other theory types cleaned up.

    def test_get_arity(self):
        run = runtime.Runtime()
        run.debug_mode()
        th = runtime.NonrecursiveRuleTheory()
        th.insert(helper.str2form('q(x) :- p(x)'))
        th.insert(helper.str2form('p(x) :- s(x)'))
        self.assertEqual(th.get_arity('p'), 1)
        self.assertEqual(th.get_arity('q'), 1)
        self.assertIsNone(th.get_arity('s'))
        self.assertIsNone(th.get_arity('missing'))

    def test_multi_policy_update(self):
        """Test updates that apply to multiple policies."""
        def check_equal(actual, correct):
            e = helper.datalog_equal(actual, correct)
            self.assertTrue(e)

        run = runtime.Runtime()
        run.theory['th1'] = runtime.NonrecursiveRuleTheory()
        run.theory['th2'] = runtime.NonrecursiveRuleTheory()

        events1 = [runtime.Event(formula=x, insert=True, target='th1')
                   for x in helper.str2pol("p(1) p(2) q(1) q(3)")]
        events2 = [runtime.Event(formula=x, insert=True, target='th2')
                   for x in helper.str2pol("r(1) r(2) t(1) t(4)")]
        run.update(events1 + events2)

        check_equal(run.select('p(x)', 'th1'), 'p(1) p(2)')
        check_equal(run.select('q(x)', 'th1'), 'q(1) q(3)')
        check_equal(run.select('r(x)', 'th2'), 'r(1) r(2)')
        check_equal(run.select('t(x)', 'th2'), 't(1) t(4)')

    def test_initialize(self):
        """Test initialize() functionality of Runtime."""
        run = runtime.Runtime()
        run.insert('p(1) p(2)')
        run.initialize(['p'], ['p(3)', 'p(4)'])
        e = helper.datalog_equal(run.select('p(x)'), 'p(3) p(4)')
        self.assertTrue(e)

    def test_dump_load(self):
        """Test if dumping/loading theories works properly."""
        run = runtime.Runtime()
        run.debug_mode()
        policy = ('p(4,"a","bcdef ghi", 17.1) '
                  'p(5,"a","bcdef ghi", 17.1) '
                  'p(6,"a","bcdef ghi", 17.1)')
        run.insert(policy)

        full_path = os.path.realpath(__file__)
        path = os.path.dirname(full_path)
        path = os.path.join(path, "snapshot")
        run.dump_dir(path)
        run = runtime.Runtime()
        run.load_dir(path)
        e = helper.datalog_equal(str(run.theory[run.DEFAULT_THEORY]),
                                 policy, 'Service theory dump/load')
        self.assertTrue(e)
