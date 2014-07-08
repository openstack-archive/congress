#! /usr/bin/python
#
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
#

import eventlet
eventlet.monkey_patch()

import os.path
from oslo.config import cfg
import sys

import api.application
import api.wsgi
from congress.common import config
from congress.openstack.common import log as logging
import dse.d6cage


LOG = logging.getLogger(__name__)


class EventLoop(object):
    """Wrapper for eventlet pool and DSE constructs used by services.

    DSE (d6Cage in particular) is used for congress services, but it is
    not (yet) tightly integrated with eventlet.  (DSE/eventlet integration
    is currently done via monkey patching.)  This class provides a common
    container for DSE and eventlet services (e.g. wsgi).

    Attributes:
        module_dir: Path to DSE modules.
        cage: A DSE d6cage instance.
        pool: An eventlet GreenPool instance.
    """

    def __init__(self, pool_size, module_dir=None):
        """Init EventLoop with a given eventlet pool_size and module_dir."""
        if module_dir is None:
            fpath = os.path.dirname(os.path.realpath(__file__))
            module_dir = os.path.dirname(fpath)
        self.module_dir = module_dir
        self.cage = dse.d6cage.d6Cage()

        self.pool = eventlet.GreenPool(pool_size)

    def register_service(self, service_name, module_name, module_path,
                         description):
        """Register a new module with the DSE runtime."""
        module_fullpath = os.path.join(self.module_dir, module_path)
        self.cage.loadModule(module_name, module_fullpath)
        self.cage.createservice(
            name=service_name, moduleName=module_name,
            description=description, args={'d6cage': self.cage})
        return self.cage.services[service_name]['object']

    def wait(self):
        """Wait until all servers have completed running."""
        try:
            self.pool.waitall()
        except KeyboardInterrupt:
            pass


def main():
    config.init(sys.argv[1:])
    if not cfg.CONF.config_file:
        sys.exit("ERROR: Unable to find configuration file via default "
                 "search paths ~/.congress/, ~/, /etc/congress/, /etc/) and "
                 "the '--config-file' option!")
    config.setup_logging()
    LOG.info("Starting congress server")

    loop = EventLoop(cfg.CONF.max_simultaneous_requests)
    # TODO(pballand): Fix the policy enginge registration to work with the
    #                latest policy changes.
    # engine = loop.register_service(
    #    "engine", "PolicyEngine", "policy/dsepolicy.py",
    #    "Policy Engine (DseRuntime instance)")
    # engine.initialize_table_subscriptions()

    # API resource runtime encapsulation:
    #   event loop -> wsgi server -> webapp -> resource manager

    wsgi_server = api.wsgi.Server("Congress API Broker", pool=loop.pool)
    api_resource_mgr = api.application.ResourceManager()
    api.application.initialize_resources(api_resource_mgr)
    api_webapp = api.application.ApiApplication(api_resource_mgr)
    # TODO(pballand): start this inside d6cage(?)
    wsgi_server.start(api_webapp, cfg.CONF.bind_port,
                      cfg.CONF.bind_host)

    loop.wait()


if __name__ == '__main__':
    main()
