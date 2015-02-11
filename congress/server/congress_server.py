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

import os.path
import socket
import sys

import eventlet
eventlet.monkey_patch()
from oslo.config import cfg
from paste import deploy

from congress.common import config
from congress.common import eventlet_server
from congress import harness
from congress.openstack.common import log as logging
from congress.openstack.common import service
from congress.openstack.common import systemd


LOG = logging.getLogger(__name__)


class ServerWrapper(object):
    """Wraps an eventlet_server with some launching info & capabilities."""

    def __init__(self, server, workers):
        self.server = server
        self.workers = workers

    def launch_with(self, launcher):
        self.server.listen()
        if self.workers > 1:
            # Use multi-process launcher
            launcher.launch_service(self.server, self.workers)
        else:
            # Use single process launcher
            launcher.launch_service(self.server)


def create_api_server(conf, name, host, port, workers):
    app = deploy.loadapp('config:%s' % conf, name=name)
    congress_api_server = eventlet_server.Server(
        app, host=host, port=port,
        keepalive=cfg.CONF.tcp_keepalive,
        keepidle=cfg.CONF.tcp_keepidle)

    return name, ServerWrapper(congress_api_server, workers)


def serve(*servers):
    if max([server[1].workers for server in servers]) > 1:
        # TODO(arosen) - need to provide way to communicate with DSE services
        launcher = service.ProcessLauncher()
    else:
        launcher = service.ServiceLauncher()

    for name, server in servers:
        try:
            server.launch_with(launcher)
        except socket.error:
            LOG.exception(_('Failed to start the %s server'), name)
            raise

    # notify calling process we are ready to serve
    systemd.notify_once()

    for name, server in servers:
        launcher.wait()


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

    def __init__(self, pool_size, module_dir=None, policy_path=None):
        """Init EventLoop with a given eventlet pool_size and module_dir."""
        if module_dir is None:
            fpath = os.path.dirname(os.path.realpath(__file__))
            module_dir = os.path.dirname(fpath)
        self.module_dir = module_dir
        self.cage = harness.create(self.module_dir, policy_path)
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

    # API resource runtime encapsulation:
    #   event loop -> wsgi server -> webapp -> resource manager

    paste_config = config.find_paste_config()
    servers = []
    servers.append(create_api_server(paste_config,
                                     "congress",
                                     cfg.CONF.bind_host,
                                     cfg.CONF.bind_port,
                                     cfg.CONF.api_workers))
    serve(*servers)


if __name__ == '__main__':
    main()
