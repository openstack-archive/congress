# Copyright (c) 2013 VMware, Inc. All rights reserved.
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

import congress.tests.helper as helper
import dse.d6cage
import policy.compile as compile
import policy.runtime as runtime
import unittest


class TestDSE(unittest.TestCase):

    def setUp(self):
        pass

    def test_cage(self):
        """Test basic DSE functionality."""
        cage = dse.d6cage.d6Cage()
        # so that we exit once test finishes; all other threads are forced
        #    to be daemons
        cage.daemon = True
        cage.start()
        cage.loadModule("TestDriver",
                        helper.data_module_path("test_driver.py"))
        cage.createservice(name="test1", moduleName="TestDriver",
                           args={'poll_time': 0})
        cage.createservice(name="test2", moduleName="TestDriver",
                           args={'poll_time': 0})
        test1 = cage.service_object('test1')
        test2 = cage.service_object('test2')
        test1.subscribe('test2', 'p', callback=test1.receive_msg)
        test2.publish('p', 42)
        helper.pause()  # give other threads chance to run
        # logging.debug("d6cage:: dataPath = {}; inbox = {}".format(
        #     policy.runtime.iterstr(list(cage.dataPath.queue)),
        #     policy.runtime.iterstr(list(cage.inbox.queue))))
        # logging.debug("test1:: dataPath = {}; inbox = {}".format(
        #     policy.runtime.iterstr(list(test1.dataPath.queue)),
        #     policy.runtime.iterstr(list(test1.inbox.queue))))
        # logging.debug("test2:: dataPath = {}; inbox = {}".format(
        #     policy.runtime.iterstr(list(test2.dataPath.queue)),
        #     policy.runtime.iterstr(list(test2.inbox.queue))))
        self.assertTrue(test1.msg.body, 42)

    def test_policy(self):
        """Test basic DSE functionality with policy engine."""
        cage = dse.d6cage.d6Cage()
        # so that we exit once test finishes; all other threads are forced
        #    to be daemons
        cage.daemon = True
        cage.start()
        cage.loadModule("TestDriver",
                        helper.data_module_path("test_driver.py"))
        cage.loadModule("TestPolicy", helper.policy_module_path())
        cage.createservice(name="data", moduleName="TestDriver")
        cage.createservice(name="policy", moduleName="TestPolicy")
        data = cage.services['data']['object']
        policy = cage.services['policy']['object']
        policy.subscribe('data', 'p', callback=policy.receive_msg)
        data.publish('p', 42)
        helper.pause()  # give other threads chance to run
        self.assertTrue(policy.msg.body, 42)

    def test_policy_data(self):
        """Test policy properly inserts data and processes it normally."""
        cage = dse.d6cage.d6Cage()
        # so that we exit once test finishes; all other threads are forced
        #    to be daemons
        cage.daemon = True
        cage.start()
        cage.loadModule("TestDriver",
                        helper.data_module_path("test_driver.py"))
        cage.loadModule("TestPolicy", helper.policy_module_path())
        cage.createservice(name="data", moduleName="TestDriver")
        cage.createservice(name="policy", moduleName="TestPolicy")
        data = cage.services['data']['object']
        policy = cage.services['policy']['object']
        policy.subscribe('data', 'p', callback=policy.receive_data_update)
        formula = compile.parse1('p(1)')
        # sending a single Insert.  (Default for Event is Insert.)
        data.publish('p', [runtime.Event(formula)])
        helper.pause()  # give other threads chance to run
        e = helper.db_equal(policy.select('data:p(x)'), 'data:p(1)')
        self.assertTrue(e, 'Single insert')

    def test_policy_tables(self):
        """Test basic DSE functionality with policy engine and the API."""
        cage = dse.d6cage.d6Cage()
        # so that we exit once test finishes; all other threads are forced
        #    to be daemons
        cage.daemon = True
        cage.start()
        cage.loadModule("TestDriver",
                        helper.data_module_path("test_driver.py"))
        cage.loadModule("TestPolicy", helper.policy_module_path())
        cage.createservice(name="data", moduleName="TestDriver")
        # using regular testdriver as API for now
        cage.createservice(name="api", moduleName="TestDriver")
        cage.createservice(name="policy", moduleName="TestPolicy")
        data = cage.services['data']['object']
        api = cage.services['api']['object']
        policy = cage.services['policy']['object']
        policy.subscribe('api', 'policy-update',
                         callback=policy.receive_policy_update)
        # simulate API call for insertion of policy statements
        formula = compile.parse1('p(x) :- data:q(x)')
        api.publish('policy-update', [runtime.Event(formula)])
        helper.pause()
        # simulate data source publishing to q
        formula = compile.parse1('q(1)')
        data.publish('q', [runtime.Event(formula)])
        helper.pause()  # give other threads chance to run
        # check that policy did the right thing with data
        e = helper.db_equal(policy.select('data:q(x)'), 'data:q(1)')
        self.assertTrue(e, 'Policy insert 1')
        e = helper.db_equal(policy.select('p(x)'), 'p(1)')
        self.assertTrue(e, 'Policy insert 2')
        #check that publishing into 'p' does not work
        formula = compile.parse1('p(3)')
        data.publish('p', [runtime.Event(formula)])
        helper.pause()
        e = helper.db_equal(policy.select('p(x)'), 'p(1)')
        self.assertTrue(e, 'Policy noninsert')


if __name__ == '__main__':
    unittest.main()
