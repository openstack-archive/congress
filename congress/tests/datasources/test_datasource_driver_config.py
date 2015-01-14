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

from congress import exception
from congress.tests import helper


class TestDataSourceDriverConfig(object):
    """Test that driver throws an error when improperly configured."""

    def test_config_missing_username(self):
        args = helper.datasource_openstack_args()
        del args['username']
        self.assertRaises(exception.DataSourceConfigException,
                          self.driver_obj, args=args)

    def test_config_missing_password(self):
        args = helper.datasource_openstack_args()
        del args['password']
        self.assertRaises(exception.DataSourceConfigException,
                          self.driver_obj, args=args)

    def test_config_missing_auth_url(self):
        args = helper.datasource_openstack_args()
        del args['auth_url']
        self.assertRaises(exception.DataSourceConfigException,
                          self.driver_obj, args=args)

    def test_config_missing_tenant_name(self):
        args = helper.datasource_openstack_args()
        del args['tenant_name']
        self.assertRaises(exception.DataSourceConfigException,
                          self.driver_obj, args=args)
