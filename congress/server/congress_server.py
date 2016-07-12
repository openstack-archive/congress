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

from congress.common import config
# FIXME It has to initialize distributed_architecture flag basing on the
# config file before the python interpreter imports python file which has
# if-statement for deepsix. Since the default value of the flag is False
# in current implementation, so it will import dse.deepsix as deepsix
# even if you set it to True in congress.conf.
# After changing the default to True, remove following one line.
# This appears in main() too.  Removing either instance breaks something.
config.init(sys.argv[1:])
from congress.common import eventlet_server

from congress import harness

LOG = logging.getLogger(__name__)


class ServerWrapper(object):
    """Wraps an eventlet_server with some launching info & capabilities."""

    def __init__(self, server, workers):
        self.server = server
        self.workers = workers

    def launch_with(self, launcher):
        if hasattr(self.server, 'listen'):
            self.server.listen()
        if self.workers > 1:
            # Use multi-process launcher
            launcher.launch_service(self.server, self.workers)
        else:
            # Use single process launcher
            launcher.launch_service(self.server)


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


def create_api_server(conf_path, node_id, host, port, workers, policy_engine,
                      datasources):
    congress_api_server = eventlet_server.APIServer(
        conf_path, node_id, host=host, port=port,
        keepalive=cfg.CONF.tcp_keepalive,
        keepidle=cfg.CONF.tcp_keepidle,
        policy_engine=policy_engine,
        api=True,
        datasources=datasources,
        bus_id=cfg.CONF.bus_id)
    # TODO(thinrichs): there's some sort of magic happening for the api
    #   server.  We call eventlet_server, which on start() calls
    #   service.congress_app_factory, which uses harness to create the
    #   API service, which the magic seems to need to do the right thing.
    #   That's why we're not just calling harness.create2 here; instead,
    #   it's buried inside the congress_app_factory.
    return node_id, ServerWrapper(congress_api_server, workers)


def create_nonapi_server(node_id, policy_engine, datasources, workers):
    congress_server = eventlet_server.Server(node_id, bus_id=cfg.CONF.bus_id)
    harness.create2(node=congress_server.node, api=False,
                    policy_engine=policy_engine,
                    datasources=datasources)
    return node_id, ServerWrapper(congress_server, workers)


def launch_servers(node_id, api, policy, data):
    servers = []
    if api:
        LOG.info("Starting congress API server on port %d", cfg.CONF.bind_port)
        # API resource runtime encapsulation:
        # event loop -> wsgi server -> webapp -> resource manager
        paste_config = config.find_paste_config()
        config.set_config_defaults()
        servers.append(create_api_server(paste_config,
                                         node_id,
                                         cfg.CONF.bind_host,
                                         cfg.CONF.bind_port,
                                         cfg.CONF.api_workers,
                                         policy_engine=policy,
                                         datasources=data))
    else:
        LOG.info("Starting congress server on node %s", node_id)
        servers.append(create_nonapi_server(node_id, policy, data,
                                            cfg.CONF.api_workers))

    return servers


def main():
    args = sys.argv[1:]

    # TODO(thinrichs): find the right way to do deployment configuration.
    # For some reason we need to config.init(args) in 2 places; here and
    # at the top of the file.  Remove either one, and things break.
    # Note: config.init() will delete the deploy args, so grab them before.
    config.init(args)
    if not cfg.CONF.config_file:
        sys.exit("ERROR: Unable to find configuration file via default "
                 "search paths ~/.congress/, ~/, /etc/congress/, /etc/) and "
                 "the '--config-file' option!")
    config.setup_logging()

    # grab deployment options from command line
    deploy_api = cfg.CONF.api
    deploy_policy = cfg.CONF.policy_engine
    deploy_datasources = cfg.CONF.datasources

    if deploy_api or deploy_policy or deploy_datasources:
        if not cfg.CONF.distributed_architecture:
            sys.exit("ERROR: can only be used with distributed arch")
        if (cfg.CONF.node_id is None and
           not (deploy_api and deploy_policy and deploy_datasources)):
            sys.exit("ERROR: must supply unique node_id")

    else:
        # Start all services
        deploy_api = True
        deploy_policy = True
        deploy_datasources = True

    # Construct requested deployment
    servers = launch_servers(cfg.CONF.node_id, deploy_api, deploy_policy,
                             deploy_datasources)

    serve(*servers)


if __name__ == '__main__':
    main()
