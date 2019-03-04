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

"""Unmarshaling of options sent by the agent."""
import inspect
import sys

from oslo_config import cfg
from oslo_config import types
from oslo_log import log as logging
from oslo_serialization import jsonutils as json
import six

from congress.cfg_validator import utils

LOG = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class IdentifiedOpt(cfg.Opt):
    """A subclass of option that adds a unique id and a namespace id

    ids are based on hashes
    """
    def __init__(self, id_, ns_id, **kwargs):
        super(IdentifiedOpt, self).__init__(**kwargs)
        self.id_ = id_
        self.ns_id = ns_id


def parse_value(cfgtype, value):
    """Parse and validate a value's type, raising error if check fails.

    :raises: ValueError, TypeError
    """
    return cfgtype(value)


def make_type(type_descr):
    """Declares a new type

    :param type_descr: a type description read from json.
    :return: an oslo config type
    """
    type_name = type_descr['type']
    type_descr = dict(type_descr)
    del type_descr['type']

    if 'item_type' in type_descr:
        item_type = make_type(type_descr['item_type'])
        type_descr['item_type'] = item_type

    if 'value_type' in type_descr:
        value_type = make_type(type_descr['value_type'])
        type_descr['value_type'] = value_type

    try:
        return_obj = getattr(types, type_name)(**type_descr)
    except AttributeError:
        LOG.warning('Custom type %s is not defined in oslo_config.types and '
                    'thus cannot be reconstructed. The type constraints will '
                    'not be enforced.', type_name)
        # give the identity function is the type param to oslo_config.cfg.Opt
        # not enforcing any type constraints
        return_obj = lambda x: x

    return return_obj


# This function must never fail even if the content/metadata
# of the option were weird.
# pylint: disable=broad-except
def make_opt(option, opt_hash, ns_hash):
    """Declares a new group

    :param name: an option retrieved from json.
    :param opt_hash: the option hash
    :param ns_hash: the hash of the namespace defining it.
    :return: an oslo config option representation augmented with the hashes.
    """
    name = option.get('name', None)
    deprecateds = []

    if option.get('deprecated_opts', None):
        for depr_descr in option.get('deprecated_opts', {}):
            depr_name = depr_descr.get('name', None)
            if depr_name is None:
                depr_name = name
            depr_opt = cfg.DeprecatedOpt(depr_name,
                                         depr_descr.get('group', None))
            deprecateds.append(depr_opt)

    if 'type' in option:
        cfgtype = make_type(option['type'])
    else:
        cfgtype = None

    default = option.get('default', None)
    if default and cfgtype:
        try:
            default = cfgtype(default)
        except Exception:
            _, err, _ = sys.exc_info()
            LOG.error('Invalid default value (%s, %s): %s'
                      % (name, default, err))
    try:
        cfgopt = IdentifiedOpt(
            id_=opt_hash,
            ns_id=ns_hash,
            name=name,
            type=cfgtype,
            dest=option.get('dest', None),
            default=default,
            positional=option.get('positional', None),
            help=option.get('help', None),
            secret=option.get('secret', None),
            required=option.get('required', None),
            sample_default=option.get('sample_default', None),
            deprecated_for_removal=option.get('deprecated_for_removal', None),
            deprecated_reason=option.get('deprecated_reason', None),
            deprecated_opts=deprecateds,
            mutable=option.get('mutable', None))
    except Exception:
        cfgopt = None
        _, err, _ = sys.exc_info()
        LOG.error('Invalid option definition (%s in %s): %s'
                  % (name, ns_hash, err))
    return cfgopt


def make_group(name, title, help_msg):
    """Declares a new group

    :param name: group name
    :param title: group title
    :param help_msg: descriptive help message
    :return: an oslo config group representation or None for default.
    """
    if name == 'DEFAULT':
        return None

    return cfg.OptGroup(name=name, title=title, help=help_msg)


def add_namespace(conf, ns_dict, ns_hash):
    """Add options from a kind to an already existing config"""

    for group_name, group in six.iteritems(ns_dict):

        try:
            title = group['object'].get('title', None)
            help_msg = group['object'].get('help', None)
        except AttributeError:
            title = help_msg = None
        cfggroup = make_group(group_name, title, help_msg)

        # Get back the instance already stored or register the group.
        if cfggroup is not None:
            # pylint: disable=protected-access
            cfggroup = conf._get_group(cfggroup, autocreate=True)

        for namespace in group['namespaces']:

            for option in namespace[1]:
                opt_hash = utils.compute_hash(ns_hash, group_name,
                                              option['name'])
                cfgopt = make_opt(option, opt_hash, ns_hash)
                conf.register_opt(cfgopt, cfggroup)


def construct_conf_manager(namespaces):
    """Construct a config manager from a list of namespaces data.

    Register options of given namespaces into a cfg.ConfigOpts object.
    A namespaces dict is typically cfg_validator.generator output. Options are
    provided an hash as an extra field.

    :param namespaces: A list of dict, containing options metadata.
    :return: A cfg.ConfigOpts.
    """
    conf = cfg.ConfigOpts()

    for ns_dict in namespaces:
        ns_hash = utils.compute_hash(json.dumps(ns_dict, sort_keys=True))
        add_namespace(conf, ns_dict, ns_hash)

    return conf


def add_parsed_conf(conf, normalized):
    """Add a normalized values container to a config manager.

    :param conf: A cfg.ConfigOpts object.
    :param normalized: A normalized values container, as introduced by oslo
        cfg._Namespace.
    """
    if conf:
        # pylint: disable=protected-access
        conf._namespace = cfg._Namespace(conf)

        # oslo.config version 6.0.1 added extra arg to _add_parsed_config_file
        # we determine the number of args required to use appropriately
        if six.PY2:
            _add_parsed_config_file_args_len = len(inspect.getargspec(
                conf._namespace._add_parsed_config_file).args) - 1
            # - 1 to not count the first param self
        else:
            _add_parsed_config_file_args_len = len(inspect.signature(
                conf._namespace._add_parsed_config_file).parameters)
        if _add_parsed_config_file_args_len == 3:  # oslo.config>=6.0.1
            conf._namespace._add_parsed_config_file(
                '<memory>', [], normalized[0])
        else:
            conf._namespace._add_parsed_config_file([], normalized[0])


def parse_config_file(namespaces, path):
    """Parse a config file from its pre-loaded namespaces.

    :param namespaces: A list of dict, containing namespaces data.
    :param path: Path to the configuration file to parse.
    :return:
    """
    conf = construct_conf_manager(namespaces)
    # pylint: disable=protected-access
    conf._namespace = cfg._Namespace(conf)
    cfg.ConfigParser._parse_file(path, conf._namespace)

    return conf
