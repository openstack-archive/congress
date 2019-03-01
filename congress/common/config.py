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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import socket

from oslo_config import cfg
from oslo_db import options as db_options
from oslo_log import log as logging
from oslo_middleware import cors

from congress import version

LOG = logging.getLogger(__name__)

core_opts = [
    cfg.HostAddressOpt('bind_host', default='0.0.0.0',
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
    cfg.IntOpt('api_workers', default=1,
               help='The number of worker processes to serve the congress '
                    'API application.'),
    cfg.StrOpt('api_paste_config', default='api-paste.ini',
               help=_('The API paste config file to use')),
    cfg.StrOpt('auth_strategy', default='keystone',
               help=_('The type of authentication to use')),
    cfg.ListOpt('drivers',
                default=[],
                deprecated_for_removal=True,
                deprecated_reason='automatically loads all configured drivers',
                help=_('List of driver class paths to import.')),
    cfg.ListOpt('disabled_drivers',
                default=[],
                help=_('List of driver names to be disabled. For example, '
                       'disabled_drivers=nova, plexxi')),
    cfg.ListOpt('custom_driver_endpoints',
                default=[],
                help=_("List of third party endpoints to be loaded seperated "
                       "by comma. For example custom_driver_endpoints = "
                       "'test=congress.datasources.test_driver:TestDriver',")),
    cfg.IntOpt('datasource_sync_period', default=60,
               help='The number of seconds to wait between synchronizing '
                    'datasource config from the database'),
    cfg.BoolOpt('enable_execute_action', default=True,
                help='Set the flag to False if you don\'t want Congress '
                     'to execute actions.'),
    cfg.BoolOpt('replicated_policy_engine', default=False,
                help='Set the flag to use congress with replicated policy '
                     'engines.'),
    cfg.StrOpt('policy_library_path', default='/etc/congress/library',
               help=_('The directory containing library policy files.')),
    cfg.StrOpt('encryption_key_path', default='/etc/congress/keys',
               help=_('The directory containing encryption keys.')),
]

# Register the configuration options
cfg.CONF.register_opts(core_opts)

dse_opts = [
    cfg.StrOpt('bus_id', default='bus',
               help='Unique ID of this DSE bus'),
    cfg.IntOpt('ping_timeout', default=5,
               help='RPC short timeout in seconds; used to ping destination'),
    cfg.IntOpt('long_timeout', default=120,
               help='RPC long timeout in seconds; used on potentially long '
                    'running requests such as datasource action and PE row '
                    'query'),
    cfg.IntOpt('time_to_resub', default=10,
               help='Time in seconds which a subscriber will wait for missing '
                    'update before attempting to resubscribe from publisher'),
    cfg.BoolOpt('execute_action_retry', default=False,
                help='Set the flag to True to make Congress retry execute '
                     'actions; may cause duplicate executions.'),
    cfg.IntOpt('execute_action_retry_timeout', default=600,
               help='The number of seconds to retry execute action before '
                    'giving up. Zero or negative value means never give up.'),
]

# Register dse opts
cfg.CONF.register_opts(dse_opts, group='dse')

# json ingester opts
json_opts = [
    cfg.BoolOpt('enable', default=False,
                help='Set the flag to True to enable the experimental JSON'
                     'ingester feature.'),
    cfg.StrOpt('config_path', default='/etc/congress/json_ingesters',
               help=_('The directory for JSON ingester config files.')),
    cfg.StrOpt('config_reusables_path',
               default='/etc/congress/config_reusables.yaml',
               help=_('The path to reusables YAML file for JSON '
                      'ingesters config.')),
    cfg.StrOpt('db_connection',
               help='The PostgreSQL connection string to use to connect to '
                    'the database.',
               secret=True),
]

# Register dse opts
cfg.CONF.register_opts(json_opts, group='json_ingester')

logging.register_options(cfg.CONF)

_SQL_CONNECTION_DEFAULT = 'sqlite://'
# Update the default QueuePool parameters. These can be tweaked by the
# configuration variables - max_pool_size, max_overflow and pool_timeout
db_options.set_defaults(cfg.CONF,
                        connection=_SQL_CONNECTION_DEFAULT,
                        max_pool_size=10, max_overflow=20, pool_timeout=10)

# Command line options
cli_opts = [
    cfg.BoolOpt('datasources', default=False,
                help='Use this option to deploy the datasources.'),
    cfg.BoolOpt('api', default=False,
                help='Use this option to deploy API service'),
    cfg.BoolOpt('policy-engine', default=False,
                help='Use this option to deploy policy engine service.'),
    cfg.StrOpt('node-id', default=socket.gethostname(),
               help='A unique ID for this node.  Must be unique across all '
                    'nodes with the same bus_id.'),
    cfg.BoolOpt('delete-missing-driver-datasources', default=False,
                help='Use this option to delete datasources with missing '
                     'drivers from DB')
]
cfg.CONF.register_cli_opts(cli_opts)


def init(args, **kwargs):
    cfg.CONF(args=args, project='congress',
             version='%%(prog)s %s' % version.version_info.release_string(),
             **kwargs)


def setup_logging():
    """Sets up logging for the congress package."""
    logging.setup(cfg.CONF, 'congress')


def find_paste_config():
    config_path = cfg.CONF.find_file(cfg.CONF.api_paste_config)

    if not config_path:
        raise cfg.ConfigFilesNotFoundError(
            config_files=[cfg.CONF.api_paste_config])
    config_path = os.path.abspath(config_path)
    LOG.info(("Config paste file: %s"), config_path)
    return config_path


def set_config_defaults():
    """This method updates all configuration default values."""
    cors.set_defaults(
        allow_headers=['X-Auth-Token',
                       'X-OpenStack-Request-ID',
                       'X-Identity-Status',
                       'X-Roles',
                       'X-Service-Catalog',
                       'X-User-Id',
                       'X-Tenant-Id'],
        expose_headers=['X-Auth-Token',
                        'X-OpenStack-Request-ID',
                        'X-Subject-Token',
                        'X-Service-Token'],
        allow_methods=['GET',
                       'PUT',
                       'POST',
                       'DELETE',
                       'PATCH']
    )
