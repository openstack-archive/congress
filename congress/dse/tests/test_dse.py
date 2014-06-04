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

import dse.d6cage
import logging
import os
import policy.compile as compile
import policy.runtime as runtime
import time
import unittest


class TestDSE(unittest.TestCase):

    def th_equal(self, actual_string, correct_string, msg):
        """Given two strings representing data theories,
        check if they are the same.
        """
        self.open(msg)
        actual = runtime.string_to_database(actual_string)
        correct = runtime.string_to_database(correct_string)
        self.check_db_diffs(actual, correct, msg)
        self.close(msg)

    def check_db_diffs(self, actual, correct, msg):
        extra = actual - correct
        missing = correct - actual
        extra = [e for e in extra if not e[0].startswith("___")]
        missing = [m for m in missing if not m[0].startswith("___")]
        self.output_diffs(extra, missing, msg, actual=actual)

    def output_diffs(self, extra, missing, msg, actual=None):
        if len(extra) > 0:
            logging.debug("Extra tuples")
            logging.debug(", ".join([str(x) for x in extra]))
        if len(missing) > 0:
            logging.debug("Missing tuples")
            logging.debug(", ".join([str(x) for x in missing]))
        if len(extra) > 0 or len(missing) > 0:
            logging.debug("Resulting database: {}".format(str(actual)))
        self.assertTrue(len(extra) == 0 and len(missing) == 0, msg)

    def open(self, msg):
        logging.debug("** Started: {} **".format(msg))

    def close(self, msg):
        logging.debug("** Finished: {} **".format(msg))

    def setUp(self):
        pass

    def test_foo(self):
        "Dummy DSE test"
        self.assertTrue("a" in "abc", "'a' is a substring of 'abc'")

    def source_path(self):
        x = os.path.realpath(__file__)
        x, y = os.path.split(x)  # drop "test_dse.py"
        x, y = os.path.split(x)  # drop "tests"
        x, y = os.path.split(x)  # drop "dse"
        return x

    def module_path(self, file):
        """Return path to dataservice module with given FILEname."""
        path = self.source_path()
        path = os.path.join(path, "datasources")
        path = os.path.join(path, file)
        return path

    def policy_module_path(self):
        """Return path to policy engine module."""
        path = self.source_path()
        path = os.path.join(path, "policy")
        path = os.path.join(path, "dsepolicy.py")
        return path

    def test_cage(self):
        """Test basic DSE functionality."""
        cage = dse.d6cage.d6Cage()
        # so that we exit once test finishes; all other threads are forced
        #    to be daemons
        cage.daemon = True
        cage.start()
        cage.loadModule("TestDriver", self.module_path("test_driver.py"))
        cage.createservice(name="test1", moduleName="TestDriver")
        cage.createservice(name="test2", moduleName="TestDriver")
        test1 = cage.services['test1']['object']
        test2 = cage.services['test2']['object']
        test1.subscribe('test2', 'p', callback=test1.receive_msg)
        test2.publish('p', 42)
        time.sleep(1)  # give other threads chance to run
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
        cage.loadModule("TestDriver", self.module_path("test_driver.py"))
        cage.loadModule("TestPolicy", self.policy_module_path())
        cage.createservice(name="data", moduleName="TestDriver")
        cage.createservice(name="policy", moduleName="TestPolicy")
        data = cage.services['data']['object']
        policy = cage.services['policy']['object']
        policy.subscribe('data', 'p', callback=policy.receive_msg)
        data.publish('p', 42)
        time.sleep(1)  # give other threads chance to run
        self.assertTrue(policy.msg.body, 42)

    def test_policy_data(self):
        """Test policy properly inserts data and processes it normally."""
        cage = dse.d6cage.d6Cage()
        # so that we exit once test finishes; all other threads are forced
        #    to be daemons
        cage.daemon = True
        cage.start()
        cage.loadModule("TestDriver", self.module_path("test_driver.py"))
        cage.loadModule("TestPolicy", self.policy_module_path())
        cage.createservice(name="data", moduleName="TestDriver")
        cage.createservice(name="policy", moduleName="TestPolicy")
        data = cage.services['data']['object']
        policy = cage.services['policy']['object']
        policy.subscribe('data', 'p', callback=policy.receive_data_update)
        formula = compile.parse1('p(1)')
        # sending a single Insert.  (Default for Event is Insert.)
        data.publish('p', [runtime.Event(formula)])
        time.sleep(1)  # give other threads chance to run
        self.th_equal(policy.select('data:p(x)'), 'data:p(1)', 'Single insert')

    def test_policy_tables(self):
        """Test basic DSE functionality with policy engine and the API."""
        cage = dse.d6cage.d6Cage()
        # so that we exit once test finishes; all other threads are forced
        #    to be daemons
        cage.daemon = True
        cage.start()
        cage.loadModule("TestDriver", self.module_path("test_driver.py"))
        cage.loadModule("TestPolicy", self.policy_module_path())
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
        time.sleep(1)
        # simulate data source publishing to q
        formula = compile.parse1('q(1)')
        data.publish('q', [runtime.Event(formula)])
        time.sleep(1)  # give other threads chance to run
        # check that policy did the right thing with data
        self.th_equal(policy.select('data:q(x)'), 'data:q(1)',
                      'Policy insert 1')
        self.th_equal(policy.select('p(x)'), 'p(1)',
                      'Policy insert 2')
        #check that publishing into 'p' does not work
        formula = compile.parse1('p(3)')
        data.publish('p', [runtime.Event(formula)])
        time.sleep(1)
        self.th_equal(policy.select('p(x)'), 'p(1)',
                      'Policy noninsert')


if __name__ == '__main__':
    unittest.main()
