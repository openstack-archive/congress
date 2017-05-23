# Copyright 2017 VMware Corporation. All rights reserved.
# All Rights Reserved.
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

from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions

from congress_tempest_tests.tests.scenario import manager_congress


CONF = config.CONF


class TestHeatDriver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def skip_checks(cls):
        super(TestHeatDriver, cls).skip_checks()
        if not getattr(CONF.service_available, 'heat_plugin', False):
            msg = ("%s skipped because heat service is not configured" %
                   cls.__class__.__name__)
            raise cls.skipException(msg)

    # TODO(testing): checks on correctness of data in updates

    @decorators.attr(type='smoke')
    def test_update_no_error(self):
        if not test_utils.call_until_true(
                func=lambda: self.check_datasource_no_error('heat'),
                duration=30, sleep_for=5):
            raise exceptions.TimeoutException('Datasource could not poll '
                                              'without error.')
