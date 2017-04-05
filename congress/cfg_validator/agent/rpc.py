#
# Copyright (c) 2017 Orange.
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

"""Handling of RPC

Communication with the datasource driver on the config validator agent
"""

from oslo_config import cfg
import oslo_messaging as messaging
from oslo_service import service

from congress.dse2 import dse_node as dse

DRIVER_TOPIC = (dse.DseNode.SERVICE_TOPIC_PREFIX + 'config' + '-'
                + cfg.CONF.dse.bus_id)


class AgentService(service.Service):
    """Definition of the agent service implemented as an RPC endpoint."""
    def __init__(self, topic, endpoints, conf=None):
        super(AgentService, self).__init__()
        self.conf = conf or cfg.CONF

        self.host = self.conf.agent.host
        self.topic = topic
        self.endpoints = endpoints
        self.transport = messaging.get_transport(self.conf)
        self.target = messaging.Target(exchange=dse.DseNode.EXCHANGE,
                                       topic=self.topic,
                                       version=dse.DseNode.RPC_VERSION,
                                       server=self.host)
        self.server = messaging.get_rpc_server(self.transport,
                                               self.target,
                                               self.endpoints,
                                               executor='eventlet')

    def start(self):
        super(AgentService, self).start()
        self.server.start()

    def stop(self, graceful=False):
        self.server.stop()
        super(AgentService, self).stop(graceful)


class ValidatorDriverClient(object):
    """RPC Proxy used by the agent to access the driver."""
    def __init__(self, topic=DRIVER_TOPIC):
        transport = messaging.get_transport(cfg.CONF)
        target = messaging.Target(exchange=dse.DseNode.EXCHANGE,
                                  topic=topic,
                                  version=dse.DseNode.RPC_VERSION)
        self.client = messaging.RPCClient(transport, target)

    # block calling thread
    def process_templates_hashes(self, context, hashes, host):
        """Sends a list of template hashes to the driver for processing

        :param hashes: the array of hashes
        :param host: the host they come from.
        """
        cctx = self.client.prepare()
        return cctx.call(context, 'process_templates_hashes', hashes=hashes,
                         host=host)

    # block calling thread
    def process_configs_hashes(self, context, hashes, host):
        """Sends a list of config files hashes to the driver for processing

        :param hashes: the array of hashes
        :param host: the host they come from.
        """
        cctx = self.client.prepare()
        return cctx.call(context, 'process_configs_hashes',
                         hashes=hashes, host=host)
