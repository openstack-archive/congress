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

import functools
import os
import sys

from oslo_config import cfg

from congress.api import application
from congress.api import router
from congress import harness
from congress.openstack.common import log

LOG = log.getLogger(__name__)


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
    root_path = cfg.CONF.root_path
    if root_path is None:
        root_path = os.path.dirname(__file__)   # drop filename
        root_path = os.path.dirname(root_path)  # drop to congress src dir
    data_path = cfg.CONF.datasource_file
    if data_path is None:
        data_path = os.path.join(root_path, 'etc', 'datasources.conf')

    cage = harness.create(root_path, data_path)

    api_resource_mgr = application.ResourceManager()
    router.APIRouterV1(api_resource_mgr, cage)
    return application.ApiApplication(api_resource_mgr)
