# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import functools
import json
import sys

from oslo_log import log as logging

from congress.api import application
from congress import harness

LOG = logging.getLogger(__name__)


def fail_gracefully(f):
    """Logs exceptions and aborts."""
    @functools.wraps(f)
    def wrapper(*args, **kw):
        try:
            return f(*args, **kw)
        except Exception:
            LOG.exception("Fatal Exception:")
            sys.exit(1)

    return wrapper


@fail_gracefully
def congress_app_factory(global_conf, **local_conf):
    # global_conf only accepts an iteratable value as its dict value
    flags_dict = json.loads(global_conf['flags'])
    services = harness.create2(
        node_id=global_conf['node_id'],
        bus_id=global_conf['bus_id'],
        policy_engine=flags_dict['policy_engine'],
        api=flags_dict['api'],
        datasources=flags_dict['datasources'])
    return application.ApiApplication(services['api_service'])
