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


from oslo.config import cfg

from congress.openstack.common import log

core_opts = [
    cfg.StrOpt('bind_host', default='0.0.0.0',
               help="The host IP to bind to"),
    cfg.IntOpt('bind_port', default=8080,
               help="The port to bind to"),
    cfg.IntOpt('max_simultaneous_requests', default=1024,
               help="Thread pool size for eventlet."),

]

# Register the configuration options
cfg.CONF.register_opts(core_opts)


def init(args, **kwargs):
    cfg.CONF(args=args, project='congress', **kwargs)


def setup_logging():
    """Sets up logging for the congress package."""
    log.setup('congress')
