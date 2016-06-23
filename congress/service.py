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
import sys

from oslo_config import cfg
from oslo_log import log as logging

from congress.api import application
from congress.api import router
from congress import harness
from congress import utils

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
    if getattr(cfg.CONF, "distributed_architecture", False):
        # global_conf only accepts an iteratable value as its dict value
        services = harness.create2(
            node=global_conf['node'][0],    # value must be iterables
            policy_engine=global_conf['flags']['policy_engine'],
            api=global_conf['flags']['api'],
            datasources=global_conf['flags']['datasources'])
        return application.ApiApplication(services['api_service'])

    else:
        if cfg.CONF.root_path:
            root_path = cfg.CONF.root_path
        else:
            root_path = utils.get_root_path()
        data_path = cfg.CONF.datasource_file

        cage = harness.create(root_path, data_path)
        api_process_dict = dict([[name, service_obj['object']]
                                 for name, service_obj
                                 in cage.getservices().items()
                                 if 'object' in service_obj])

        api_resource_mgr = application.ResourceManager()
        router.APIRouterV1(api_resource_mgr, api_process_dict)
        return application.ApiApplication(api_resource_mgr)
