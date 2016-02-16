# Copyright 2012 OpenStack Foundation
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2010 OpenStack Foundation
# All Rights Reserved.
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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import errno
import re
import socket
import ssl
import sys

import eventlet
import eventlet.wsgi
import greenlet
from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import service
from paste import deploy

from congress.dse2 import dse_node
from congress import exception
from congress.tests import helper

LOG = logging.getLogger(__name__)


class EventletFilteringLogger(object):
    # NOTE(morganfainberg): This logger is designed to filter out specific
    # Tracebacks to limit the amount of data that eventlet can log. In the
    # case of broken sockets (EPIPE and ECONNRESET), we are seeing a huge
    # volume of data being written to the logs due to ~14 lines+ per traceback.
    # The traceback in these cases are, at best, useful for limited debugging
    # cases.
    def __init__(self, logger):
        self.logger = logger
        self.level = logger.logger.level
        self.regex = re.compile(r'errno (%d|%d)' %
                                (errno.EPIPE, errno.ECONNRESET), re.IGNORECASE)

    def write(self, msg):
        m = self.regex.search(msg)
        if m:
            self.logger.log(logging.logging.DEBUG,
                            'Error(%s) writing to socket.',
                            m.group(1))
        else:
            self.logger.log(self.level, msg.rstrip())


class APIServer(service.ServiceBase):
    """Server class to Data Service Node with API services.

    This server has All API services in itself.
    """

    def __init__(self, app_conf, name, host=None, port=None, threads=1000,
                 keepalive=False, keepidle=None):
        self.app_conf = app_conf
        self.name = name
        self.application = None
        self.host = host or '0.0.0.0'
        self.port = port or 0
        self.pool = eventlet.GreenPool(threads)
        self.socket_info = {}
        self.greenthread = None
        self.do_ssl = False
        self.cert_required = False
        self.keepalive = keepalive
        self.keepidle = keepidle
        self.socket = None
        self.node = None

        if cfg.CONF.distributed_architecture:
            messaging_config = helper.generate_messaging_config()
            messaging_config.rpc_response_timeout = 10

            self.node = dse_node.DseNode(messaging_config, self.name, [])

    def start(self, key=None, backlog=128):
        """Run a WSGI server with the given application."""

        if self.socket is None:
            self.listen(key=key, backlog=backlog)

        try:
            kwargs = {'global_conf': {'node_obj': [self.node]}}
            self.application = deploy.loadapp('config:%s' % self.app_conf,
                                              name='congress', **kwargs)
        except Exception:
            raise exception.CongressException(
                'Failed to Start initializing %s server' % self.node.node_id)

        self.greenthread = self.pool.spawn(self._run,
                                           self.application,
                                           self.socket)

    def listen(self, key=None, backlog=128):
        """Create and start listening on socket.

        Call before forking worker processes.

        Raises Exception if this has already been called.
        """

        if self.socket is not None:
            raise Exception(_('Server can only listen once.'))

        LOG.info(_('Starting %(arg0)s on %(host)s:%(port)s'),
                 {'arg0': sys.argv[0],
                  'host': self.host,
                  'port': self.port})

        # TODO(dims): eventlet's green dns/socket module does not actually
        # support IPv6 in getaddrinfo(). We need to get around this in the
        # future or monitor upstream for a fix
        info = socket.getaddrinfo(self.host,
                                  self.port,
                                  socket.AF_UNSPEC,
                                  socket.SOCK_STREAM)[0]
        _socket = eventlet.listen(info[-1],
                                  family=info[0],
                                  backlog=backlog)
        if key:
            self.socket_info[key] = _socket.getsockname()
        # SSL is enabled
        if self.do_ssl:
            if self.cert_required:
                cert_reqs = ssl.CERT_REQUIRED
            else:
                cert_reqs = ssl.CERT_NONE
            sslsocket = eventlet.wrap_ssl(_socket, certfile=self.certfile,
                                          keyfile=self.keyfile,
                                          server_side=True,
                                          cert_reqs=cert_reqs,
                                          ca_certs=self.ca_certs)
            _socket = sslsocket

        # Optionally enable keepalive on the wsgi socket.
        if self.keepalive:
            _socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

            # This option isn't available in the OS X version of eventlet
            if hasattr(socket, 'TCP_KEEPIDLE') and self.keepidle is not None:
                _socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE,
                                   self.keepidle)

        self.socket = _socket

    def set_ssl(self, certfile, keyfile=None, ca_certs=None,
                cert_required=True):
        self.certfile = certfile
        self.keyfile = keyfile
        self.ca_certs = ca_certs
        self.cert_required = cert_required
        self.do_ssl = True

    def kill(self):
        if self.greenthread is not None:
            self.greenthread.kill()

    def stop(self):
        self.kill()
        if cfg.CONF.distributed_architecture:
            self.node.stop()

    def reset(self):
        LOG.info("reset() not implemented yet")

    def wait(self):
        """Wait until all servers have completed running."""
        try:
            self.pool.waitall()
        except KeyboardInterrupt:
            pass
        except greenlet.GreenletExit:
            pass

    def _run(self, application, socket):
        """Start a WSGI server in a new green thread."""
        logger = logging.getLogger('eventlet.wsgi.server')
        try:
            eventlet.wsgi.server(socket, application, max_size=1000,
                                 log=EventletFilteringLogger(logger),
                                 debug=False)
        except greenlet.GreenletExit:
            # Wait until all servers have completed running
            pass
        except Exception:
            LOG.exception(_('Server error'))
            raise
