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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
import socket
import sys

import eventlet
eventlet.monkey_patch()
from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service
from paste import deploy

from congress.common import config
from congress.common import eventlet_server

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
        launcher = service.ProcessLauncher(cfg.CONF)
    else:
        launcher = service.ServiceLauncher(cfg.CONF)

    for name, server in servers:
        try:
            server.launch_with(launcher)
        except socket.error:
            LOG.exception(_('Failed to start the %s server'), name)
            raise

    try:
        launcher.wait()
    except KeyboardInterrupt:
        LOG.info("Congress server stopped by interrupt.")


def main():
    config.init(sys.argv[1:])
    if not cfg.CONF.config_file:
        sys.exit("ERROR: Unable to find configuration file via default "
                 "search paths ~/.congress/, ~/, /etc/congress/, /etc/) and "
                 "the '--config-file' option!")
    config.setup_logging()
    LOG.info("Starting congress server on port %d", cfg.CONF.bind_port)

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
