# Copyright 2014 VMware
#
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

import os

from oslo.config import cfg

from congress.openstack.common.gettextutils import _
from congress.openstack.common import log as logging

LOG = logging.getLogger(__name__)

core_opts = [
    cfg.StrOpt('bind_host', default='0.0.0.0',
               help="The host IP to bind to"),
    cfg.IntOpt('bind_port', default=8080,
               help="The port to bind to"),
    cfg.IntOpt('max_simultaneous_requests', default=1024,
               help="Thread pool size for eventlet."),
    cfg.BoolOpt('tcp_keepalive', default=False,
                help='Set this to true to enable TCP_KEEALIVE socket option '
                     'on connections received by the API server.'),
    cfg.IntOpt('tcp_keepidle',
               default=600,
               help='Sets the value of TCP_KEEPIDLE in seconds for each '
                    'server socket. Only applies if tcp_keepalive is '
                    'true. Not supported on OS X.'),
    cfg.StrOpt('policy_path', default=None,
               help="The path to the latest policy dump"),
    cfg.StrOpt('datasource_file', default=None,
               help="The file containing datasource configuration"),
    cfg.StrOpt('root_path', default=None,
               help="The absolute path to the congress repo"),
    cfg.IntOpt('api_workers', default=1,
               help='The number of worker processes to serve the congress '
                    'API application.'),
    cfg.StrOpt('api_paste_config', default="api-paste.ini",
               help=_("The API paste config file to use")),
    cfg.StrOpt('auth_strategy', default='keystone',
               help=_("The type of authentication to use")),
]

# Register the configuration options
cfg.CONF.register_opts(core_opts)


def init(args, **kwargs):
    cfg.CONF(args=args, project='congress', **kwargs)


def setup_logging():
    """Sets up logging for the congress package."""
    logging.setup('congress')


def find_paste_config():
    config_path = cfg.CONF.find_file(cfg.CONF.api_paste_config)
    if not config_path:
        raise cfg.ConfigFilesNotFoundError(
            config_files=[cfg.CONF.api_paste_config])
    config_path = os.path.abspath(config_path)
    LOG.info(_("Config paste file: %s"), config_path)
    return config_path
