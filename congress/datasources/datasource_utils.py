# Copyright (c) 2013,2014 VMware, Inc. All rights reserved.
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

import functools

from congress.datasources import constants


def get_openstack_required_config():
    return {'auth_url': constants.REQUIRED,
            'endpoint': constants.OPTIONAL,
            'region': constants.OPTIONAL,
            'username': constants.REQUIRED,
            'password': constants.REQUIRED,
            'tenant_name': constants.REQUIRED,
            'poll_time': constants.OPTIONAL}


def check_raw_data_changed(raw_data_name):
    """Decorator to check raw data before retranslating.

    If raw data is same with cached self.raw_state,
    don't translate data, return empty list directly.
    """

    def outer(f):
        @functools.wraps(f)
        def inner(self, raw_data, *args, **kw):
            if (raw_data_name not in self.raw_state or
                    raw_data != self.raw_state[raw_data_name]):
                result = f(self, raw_data, *args, **kw)
                self.raw_state[raw_data_name] = raw_data
            else:
                result = []
            return result
        return inner
    return outer
