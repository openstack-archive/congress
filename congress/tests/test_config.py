# Copyright (c) 2014 VMware
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from oslo_config import cfg
import testtools


class ConfigurationTest(testtools.TestCase):

    def test_defaults(self):
        self.assertEqual('0.0.0.0', cfg.CONF.bind_host)
        self.assertEqual(1789, cfg.CONF.bind_port)
        self.assertEqual(False, cfg.CONF.tcp_keepalive)
        self.assertEqual(600, cfg.CONF.tcp_keepidle)
        self.assertEqual(1, cfg.CONF.api_workers)
        self.assertEqual('api-paste.ini', cfg.CONF.api_paste_config)
        self.assertEqual('keystone', cfg.CONF.auth_strategy)
