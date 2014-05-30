# Copyright (c) 2013 VMware, Inc. All rights reserved.
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

import errno
import socket
import sys
import time


import eventlet.wsgi
eventlet.patcher.monkey_patch(all=False, socket=True)

import ovs.vlog
vlog = ovs.vlog.Vlog(__name__)
# Number of seconds to keep retrying to listen
RETRY_UNTIL_WINDOW = 30

# Sets the value of TCP_KEEPIDLE in seconds for each server socket.
TCP_KEEPIDLE = 600

# Number of backlog requests to configure the socket with
BACKLOG = 4096


class Server(object):
    """Server class to manage multiple WSGI sockets and applications."""

    def __init__(self, name, threads=1000):
        self.pool = eventlet.GreenPool(threads)
        self.name = name

    def _get_socket(self, host, port, backlog):
        bind_addr = (host, port)
        # TODO(dims): eventlet's green dns/socket module does not actually
        # support IPv6 in getaddrinfo(). We need to get around this in the
        # future or monitor upstream for a fix
        try:
            info = socket.getaddrinfo(bind_addr[0],
                                      bind_addr[1],
                                      socket.AF_UNSPEC,
                                      socket.SOCK_STREAM)[0]
            family = info[0]
            bind_addr = info[-1]
        except Exception:
            vlog.exception(("Unable to listen on %(host)s:%(port)s") %
                           {'host': host, 'port': port})
            sys.exit(1)

        sock = None
        retry_until = time.time() + RETRY_UNTIL_WINDOW
        while not sock and time.time() < retry_until:
            try:
                sock = eventlet.listen(bind_addr,
                                       backlog=backlog,
                                       family=family)
            except socket.error as err:
                if err.errno != errno.EADDRINUSE:
                    raise
                eventlet.sleep(0.1)
        if not sock:
            raise RuntimeError(("Could not bind to %(host)s:%(port)s "
                               "after trying for %(time)d seconds") %
                               {'host': host,
                                'port': port,
                                'time': RETRY_UNTIL_WINDOW})
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sockets can hang around forever without keepalive
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

        if hasattr(socket, 'TCP_KEEPIDLE'):
            sock.setsockopt(socket.IPPROTO_TCP,
                            socket.TCP_KEEPIDLE,
                            TCP_KEEPIDLE)

        return sock

    def start(self, application, port, host='0.0.0.0'):
        """Run a WSGI server with the given application."""
        self._host = host
        self._port = port
        backlog = BACKLOG

        self._socket = self._get_socket(self._host,
                                        self._port,
                                        backlog=backlog)
        self._server = self.pool.spawn(self._run, application, self._socket)

    @property
    def host(self):
        return self._socket.getsockname()[0] if self._socket else self._host

    @property
    def port(self):
        return self._socket.getsockname()[1] if self._socket else self._port

    def stop(self):
        self._server.kill()

    def wait(self):
        """Wait until all servers have completed running."""
        try:
            self.pool.waitall()
        except KeyboardInterrupt:
            pass

    def _run(self, application, socket):
        """Start a WSGI server in a new green thread."""
        eventlet.wsgi.server(socket, application, custom_pool=self.pool)
