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

import os
import sys

import functools
from oslo.config import cfg

from congress.api import application
from congress import harness
from congress.openstack.common import log
from congress.server import congress_server

LOG = log.getLogger(__name__)


def fail_gracefully(f):
    """Logs exceptions and aborts."""
    @functools.wraps(f)
    def wrapper(*args, **kw):
        try:
            return f(*args, **kw)
        except Exception as e:
            LOG.debug(e, exc_info=True)

            # exception message is printed to all logs
            LOG.critical(e)
            sys.exit(1)

    return wrapper


@fail_gracefully
def congress_app_factory(global_conf, **local_conf):
    #TODO(arosen): refactor this code so we don't need to rely on paths.
    fpath = os.path.dirname(os.path.realpath(__file__) + "/server")
    src_path = os.path.dirname(fpath)
    src_path = os.path.dirname(fpath)
    policy_path = cfg.CONF.policy_path
    if policy_path is None:
        policy_path = src_path
    data_path = cfg.CONF.datasource_file
    if data_path is None:
        data_path = os.path.dirname(src_path)
        data_path = os.path.join(data_path, 'etc', 'datasources.conf')

    cage = harness.create(src_path, policy_path, data_path)

    api_resource_mgr = application.ResourceManager()
    congress_server.initialize_resources(api_resource_mgr, cage)
    return application.ApiApplication(api_resource_mgr)
