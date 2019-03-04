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

""" Generation of JSON from oslo config options (marshalling) """
import collections
import json
import logging

from oslo_config import cfg
from oslo_config import generator
from oslo_config import types

LOG = logging.getLogger(__name__)


class OptionJsonEncoder(json.JSONEncoder):
    """Json encoder used to give a unique representation to namespaces"""

    # pylint: disable=protected-access,method-hidden,too-many-branches
    def default(self, o):
        if isinstance(o, cfg.Opt):
            return {
                'kind': type(o).__name__,
                'deprecated_for_removal': o.deprecated_for_removal,
                'short': o.short,
                'name': o.name,
                'dest': o.dest,
                'deprecated_since': o.deprecated_since,
                'required': o.required,
                'sample_default': o.sample_default,
                'deprecated_opts': o.deprecated_opts,
                'positional': o.positional,
                'default': o.default,
                'secret': o.secret,
                'deprecated_reason': o.deprecated_reason,
                'mutable': o.mutable,
                'type': o.type,
                'metavar': o.metavar,
                'advanced': o.advanced,
                'help': o.help
            }
        elif isinstance(o, (types.ConfigType, types.HostAddress)):
            res = {
                'type': type(o).__name__,
            }

            if isinstance(o, types.Number):
                res['max'] = o.max
                res['min'] = o.min
                # When we build back the type in parsing, we can directly use
                # the list of tuples from choices and it will be in a
                # canonical order (not sorted but the order elements were
                # added)
                if isinstance(o.choices, collections.OrderedDict):
                    res['choices'] = list(o.choices.keys())
                else:
                    res['choices'] = o.choices
            if isinstance(o, types.Range):
                res['max'] = o.max
                res['min'] = o.min
            if isinstance(o, types.String):
                if o.regex and hasattr(o.regex, 'pattern'):
                    res['regex'] = o.regex.pattern
                else:
                    res['regex'] = o.regex
                res['max_length'] = o.max_length
                res['quotes'] = o.quotes
                res['ignore_case'] = o.ignore_case
                if isinstance(o.choices, collections.OrderedDict):
                    res['choices'] = list(o.choices.keys())
                else:
                    res['choices'] = o.choices
            if isinstance(o, types.List):
                res['item_type'] = o.item_type
                res['bounds'] = o.bounds
            if isinstance(o, types.Dict):
                res['value_type'] = o.value_type
                res['bounds'] = o.bounds
            if isinstance(o, types.URI):
                res['schemes'] = o.schemes
                res['max_length'] = o.max_length
            if isinstance(o, types.IPAddress):
                if o.version_checker == o._check_ipv4:
                    res['version'] = 4
                elif o.version_checker == o._check_ipv6:
                    res['version'] = 6

            # Remove unused fields
            remove = [k for k, v in res.items() if not v]
            for k in remove:
                del res[k]

            return res
        elif isinstance(o, cfg.DeprecatedOpt):
            return {
                'name': o.name,
                'group': o.group
            }
        elif isinstance(o, cfg.OptGroup):
            return {
                'title': o.title,
                'help': o.help
            }

        # TODO(vmatt): some options (auth_type, auth_section) from
        # keystoneauth1, loaded by keystonemiddleware.auth,
        # are not defined conventionally (stable/ocata).
        elif isinstance(o, type):
            return {
                'type': 'String'
            }

        else:
            return {
                'type': repr(o)
            }


# pylint: disable=protected-access
def generate_ns_data(namespace):
    """Generate a json string containing the namespace"""
    groups = generator._get_groups(generator._list_opts([namespace]))
    return OptionJsonEncoder(sort_keys=True).encode(groups)
