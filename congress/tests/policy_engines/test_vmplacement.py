# Copyright (c) 2015 VMware, Inc. All rights reserved.
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

from congress.dse import d6cage
from congress import harness
from congress.openstack.common import log as logging
from congress.policy_engines.vm_placement import ComputePlacementEngine
from congress.tests import base
from congress.tests import helper

LOG = logging.getLogger(__name__)

NREC_THEORY = 'non-recursive theory'


class TestEngine(base.TestCase):

    def test_parse(self):
        engine = ComputePlacementEngine()
        engine.debug_mode()
        f = engine.parse1('nova:q(1)')
        self.assertTrue(f.table, 'nova:q')
        self.assertIsNone(f.theory)

        f = engine.parse1('p(x) :- q(x)')
        self.assertEqual(f.head.table, 'p')
        self.assertEqual(f.body[0].table, 'q')

    def test_select(self):
        engine = ComputePlacementEngine()
        engine.debug_mode()
        engine.insert('p(x) :- q(x)')
        engine.insert('q(1)')
        ans = engine.select('p(x)')
        self.assertTrue(helper.datalog_equal(ans, 'p(1)'))

    def test_theory_in_head(self):
        engine = ComputePlacementEngine()
        engine.debug_mode()
        engine.policy.insert(engine.parse1('p(x) :- nova:q(x)'))
        engine.policy.insert(engine.parse1('nova:q(1)'))
        ans = engine.policy.select(engine.parse1('p(x)'))
        ans = " ".join(str(x) for x in ans)
        self.assertTrue(helper.datalog_equal(ans, 'p(1)'))


class TestSetPolicy(base.TestCase):
    """Tests for setting policy."""

    def setUp(self):
        # create DSE and add vm-placement engine and fake datasource
        super(TestSetPolicy, self).setUp()
        self.cage = d6cage.d6Cage()
        config = {'vmplace':
                  {'module': "congress/policy_engines/vm_placement.py"},
                  'fake':
                  {'poll_time': 0,
                   'module': "congress/tests/fake_datasource.py"}}

        harness.load_data_service("vmplace", config['vmplace'],
                                  self.cage, helper.root_path(), 1)
        harness.load_data_service("fake", config['fake'],
                                  self.cage, helper.root_path(), 2)

        self.vmplace = self.cage.service_object('vmplace')
        self.vmplace.debug_mode()
        self.fake = self.cage.service_object('fake')

    def test_set_policy_subscriptions(self):
        self.vmplace.set_policy('p(x) :- fake:q(x)')
        helper.retry_check_subscriptions(
            self.vmplace, [(self.fake.name, 'q')])
        helper.retry_check_subscribers(
            self.fake, [(self.vmplace.name, 'q')])

    def test_set_policy(self):
        LOG.info("set_policy")
        self.vmplace.set_policy('p(x) :- fake:q(x)')
        self.fake.state = {'q': set([tuple([1]), tuple([2])])}
        self.fake.poll()
        ans = ('p(1) p(2)')
        helper.retry_check_db_equal(self.vmplace, 'p(x)', ans)

    # TODO(thinrichs): add tests for data update
    #   Annoying since poll() saves self.state, invokes
    #   update_from_datasource (which updates self.state),
    #   computes deltas, and publishes.  No easy way to inject
    #   a new value for self.state and get it to send non-empty
    #   deltas over the message bus.  Probably want to extend
    #   fake_datasource to include a client (default to None), make
    #   update_from_datasource use that client to set self.state,
    #   and then mock out the client.

    # TODO(thinrichs): add tests for setting policy to something that
    #   requires tables to be unsubscribed from

    # TODO(thinrichs): test production_mode()
