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

"""Options for the config validator agent"""
from oslo_config import cfg
from oslo_config import types
from oslo_log import log as logging

GROUP = cfg.OptGroup(
    name='agent',
    title='Congress agent options for config datasource')

AGT_OPTS = [
    cfg.StrOpt('host', required=True),
    cfg.StrOpt('version', required=True, help='OpenStack version'),
    cfg.IntOpt('max_delay', default=10, help='The maximum delay an agent will '
                                             'wait before sending his files. '
                                             'The smaller the value, the more '
                                             'likely congestion is to happen'
                                             '.'),

    cfg.Opt(
        'services',
        help='Services activated on this node and configuration files',
        default={},
        sample_default=(
            'nova: { /etc/nova/nova.conf:/path1.conf }, '
            'neutron: { /etc/nova/neutron.conf:/path2.conf },'),
        type=types.Dict(
            bounds=False,
            value_type=types.Dict(bounds=True, value_type=types.String()))),

]


def register_validator_agent_opts(conf):
    """Register the options of the agent in the config object"""
    conf.register_group(GROUP)
    conf.register_opts(AGT_OPTS, group=GROUP)
    logging.register_options(conf)


def list_opts():
    """List agent options"""
    return [(GROUP, AGT_OPTS)]
