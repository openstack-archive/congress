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

from oslo_config import cfg
from oslo_db import options as db_options
from oslo_log import log as logging
from oslo_policy import opts as policy_opts

from congress.managers import datasource as datasource_mgr
from congress import version

LOG = logging.getLogger(__name__)

core_opts = [
    cfg.StrOpt('bind_host', default='0.0.0.0',
               help="The host IP to bind to"),
    cfg.PortOpt('bind_port', default=1789,
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
    cfg.StrOpt('policy_path',
               help="The path to the latest policy dump"),
    cfg.StrOpt('datasource_file',
               help="The file containing datasource configuration"),
    cfg.StrOpt('root_path',
               help="The absolute path to the congress repo"),
    cfg.IntOpt('api_workers', default=1,
               help='The number of worker processes to serve the congress '
                    'API application.'),
    cfg.StrOpt('api_paste_config', default="api-paste.ini",
               help=_("The API paste config file to use")),
    cfg.StrOpt('auth_strategy', default='keystone',
               help=_("The type of authentication to use")),
    cfg.ListOpt('drivers',
                default=[],
                help=_("List of driver class paths to import.")),
    cfg.IntOpt('datasource_sync_period', default=0,
               help='The number of seconds to wait between synchronizing '
                    'datasource config from the database '),
    cfg.BoolOpt('enable_execute_action', default=True,
                help="Sets the flag to False if you don't want the congress "
                "to execute actions."),
    cfg.BoolOpt('distributed_architecture', default=False,
                help="The flag to use congress new distributed architecture."
                "Don't set it to True in L release since the new architecture "
                "is under implementation."),
]

# Register the configuration options
cfg.CONF.register_opts(core_opts)

policy_opts.set_defaults(cfg.CONF, 'policy.json')
logging.register_options(cfg.CONF)

_SQL_CONNECTION_DEFAULT = 'sqlite://'
# Update the default QueuePool parameters. These can be tweaked by the
# configuration variables - max_pool_size, max_overflow and pool_timeout
db_options.set_defaults(cfg.CONF,
                        connection=_SQL_CONNECTION_DEFAULT,
                        sqlite_db='', max_pool_size=10,
                        max_overflow=20, pool_timeout=10)


def init(args, **kwargs):
    cfg.CONF(args=args, project='congress',
             version='%%(prog)s %s' % version.version_info.release_string(),
             **kwargs)
    datasource_mgr.DataSourceManager.validate_configured_drivers()


def setup_logging():
    """Sets up logging for the congress package."""
    logging.setup(cfg.CONF, 'congress')


def find_paste_config():
    config_path = cfg.CONF.find_file(cfg.CONF.api_paste_config)
    if not config_path:
        raise cfg.ConfigFilesNotFoundError(
            config_files=[cfg.CONF.api_paste_config])
    config_path = os.path.abspath(config_path)
    LOG.info(_("Config paste file: %s"), config_path)
    return config_path
