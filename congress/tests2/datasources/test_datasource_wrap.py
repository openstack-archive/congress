# Copyright (c) 2016 Styra, Inc. All rights reserved.
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

import eventlet
import mock
from oslo_config import cfg
cfg.CONF.distributed_architecture = True

from congress.datasources import datasource_driver
from congress.tests import base
from congress.tests.datasources import test_datasource_driver
from congress.tests.datasources import test_driver


class TestDS(test_datasource_driver.TestDatasourceDriver):
    pass


class TestPollingDataSourceDriver(base.TestCase):
    class TestDriver(datasource_driver.PollingDataSourceDriver):
        def __init__(self):
            super(TestPollingDataSourceDriver.TestDriver, self).__init__(
                '', '', None, None, None)
            self.node = 'node'
            self._rpc_server = mock.MagicMock()
            self._init_end_start_poll()

    def setUp(self):
        super(TestPollingDataSourceDriver, self).setUp()

    @mock.patch.object(eventlet, 'spawn')
    def test_init_consistence(self, mock_spawn):
        test_driver = TestPollingDataSourceDriver.TestDriver()
        mock_spawn.assert_not_called()
        self.assertIsNone(test_driver.worker_greenthread)
        test_driver.start()
        mock_spawn.assert_called_once_with(test_driver.poll_loop,
                                           test_driver.poll_time)
        self.assertTrue(test_driver.initialized)
        self.assertIsNotNone(test_driver.worker_greenthread)

    @mock.patch.object(eventlet.greenthread, 'kill')
    @mock.patch.object(eventlet, 'spawn')
    def test_cleanup(self, mock_spawn, mock_kill):
        dummy_thread = dict()
        mock_spawn.return_value = dummy_thread

        test_driver = TestPollingDataSourceDriver.TestDriver()
        test_driver.start()

        self.assertEqual(test_driver.worker_greenthread, dummy_thread)

        test_driver.stop()

        mock_kill.assert_called_once_with(dummy_thread)
        self.assertIsNone(test_driver.worker_greenthread)


class TestExecution(test_datasource_driver.TestExecutionDriver):
    pass


class TestDriver(test_driver.TestDriver):
    pass
