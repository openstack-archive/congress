# Copyright (c) 2014 VMware
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import socket

import mock
from oslo_config import cfg
import testtools

from congress.common import eventlet_server


class APIServerTest(testtools.TestCase):

    @mock.patch('paste.deploy.loadapp')
    @mock.patch('eventlet.listen')
    @mock.patch('socket.getaddrinfo')
    def test_keepalive_unset(self, mock_getaddrinfo, mock_listen, mock_app):
        mock_getaddrinfo.return_value = [(1, 2, 3, 4, 5)]
        mock_sock = mock.Mock()
        mock_sock.setsockopt = mock.Mock()
        mock_app.return_value = mock.MagicMock()

        mock_listen.return_value = mock_sock
        server = eventlet_server.APIServer('/path/to/paste', 'api-server',
                                           host=cfg.CONF.bind_host,
                                           port=cfg.CONF.bind_port)
        server.start()
        self.assertTrue(mock_listen.called)
        self.assertTrue(mock_app.called)
        self.assertFalse(mock_sock.setsockopt.called)

    @mock.patch('paste.deploy.loadapp')
    @mock.patch('eventlet.listen')
    @mock.patch('socket.getaddrinfo')
    def test_keepalive_set(self, mock_getaddrinfo, mock_listen, mock_app):
        mock_getaddrinfo.return_value = [(1, 2, 3, 4, 5)]
        mock_sock = mock.Mock()
        mock_sock.setsockopt = mock.Mock()
        mock_app.return_value = mock.MagicMock()

        mock_listen.return_value = mock_sock
        server = eventlet_server.APIServer('/path/to/paste', 'api-server',
                                           host=cfg.CONF.bind_host,
                                           port=cfg.CONF.bind_port,
                                           keepalive=True)
        server.start()
        mock_sock.setsockopt.assert_called_once_with(socket.SOL_SOCKET,
                                                     socket.SO_KEEPALIVE,
                                                     1)
        self.assertTrue(mock_listen.called)
        self.assertTrue(mock_app.called)

    @mock.patch('paste.deploy.loadapp')
    @mock.patch('eventlet.listen')
    @mock.patch('socket.getaddrinfo')
    def test_keepalive_and_keepidle_set(self, mock_getaddrinfo, mock_listen,
                                        mock_app):
        mock_getaddrinfo.return_value = [(1, 2, 3, 4, 5)]
        mock_sock = mock.Mock()
        mock_sock.setsockopt = mock.Mock()
        mock_app.return_value = mock.MagicMock()

        mock_listen.return_value = mock_sock
        server = eventlet_server.APIServer('/path/to/paste', 'api-server',
                                           host=cfg.CONF.bind_host,
                                           port=cfg.CONF.bind_port,
                                           keepalive=True,
                                           keepidle=1)
        server.start()

        # keepidle isn't available in the OS X version of eventlet
        if hasattr(socket, 'TCP_KEEPIDLE'):
            self.assertEqual(mock_sock.setsockopt.call_count, 2)

            # Test the last set of call args i.e. for the keepidle
            mock_sock.setsockopt.assert_called_with(socket.IPPROTO_TCP,
                                                    socket.TCP_KEEPIDLE,
                                                    1)
        else:
            self.assertEqual(mock_sock.setsockopt.call_count, 1)

        self.assertTrue(mock_listen.called)
        self.assertTrue(mock_app.called)
