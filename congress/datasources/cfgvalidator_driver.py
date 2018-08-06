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

"""Datasource for configuration options"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from collections import OrderedDict
import datetime
import os
import six

from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_config import types
from oslo_log import log as logging
import oslo_messaging as messaging

from congress.cfg_validator import parsing
from congress.cfg_validator import utils
from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.dse2 import dse_node as dse


LOG = logging.getLogger(__name__)

FILE = u'file'
VALUE = u'binding'
OPTION = u'option'
OPTION_INFO = u'option_info'
INT_TYPE = u'int_type'
FLOAT_TYPE = u'float_type'
STR_TYPE = u'string_type'
LIST_TYPE = u'list_type'
RANGE_TYPE = u'range_type'
URI_TYPE = u'uri_type'
IPADDR_TYPE = u'ipaddr_type'
SERVICE = u'service'
HOST = u'host'
MODULE = u'module'
TEMPLATE = u'template'
TEMPLATE_NS = u'template_ns'
NAMESPACE = u'namespace'


class ValidatorDriver(datasource_driver.PollingDataSourceDriver):
    """Driver for the Configuration validation datasource"""

    # pylint: disable=too-many-instance-attributes

    DS_NAME = u'config'

    def __init__(self, name=None, args=None):
        super(ValidatorDriver, self).__init__(self.DS_NAME, args)

        # { template_hash -> {name, namespaces} }
        self.known_templates = {}
        # { namespace_hash -> namespace_name }
        self.known_namespaces = {}
        # set(config_hash)
        self.known_configs = set()
        # { template_hash -> (conf_hash, conf)[] }
        self.templates_awaited_by_config = {}

        self.agent_api = ValidatorAgentClient()

        self.rule_added = False

        if hasattr(self, 'add_rpc_endpoint'):
            self.add_rpc_endpoint(ValidatorDriverEndpoints(self))
        self._init_end_start_poll()

    # pylint: disable=no-self-use
    def get_context(self):
        """context for RPC. To define"""
        return {}

    @staticmethod
    def get_datasource_info():
        """Gives back a standardized description of the datasource"""
        result = {}
        result['id'] = 'config'
        result['description'] = (
            'Datasource driver that allows OS configs retrieval.')
        result['config'] = {
            'poll_time': constants.OPTIONAL,
            'lazy_tables': constants.OPTIONAL}
        return result

    @classmethod
    def get_schema(cls):
        sch = {
            # option value
            VALUE: [
                {'name': 'option_id', 'desc': 'The represented option'},
                {'name': 'file_id',
                 'desc': 'The file containing the assignement'},
                {'name': 'val', 'desc': 'Actual value'}],
            OPTION: [
                {'name': 'id', 'desc': 'Id'},
                {'name': 'namespace', 'desc': ''},
                {'name': 'group', 'desc': ''},
                {'name': 'name', 'desc': ''}, ],
            # options metadata, omitted : dest
            OPTION_INFO: [
                {'name': 'option_id', 'desc': 'Option id'},
                {'name': 'type', 'desc': ''},
                {'name': 'default', 'desc': ''},
                {'name': 'deprecated', 'desc': ''},
                {'name': 'deprecated_reason', 'desc': ''},
                {'name': 'mutable', 'desc': ''},
                {'name': 'positional', 'desc': ''},
                {'name': 'required', 'desc': ''},
                {'name': 'sample_default', 'desc': ''},
                {'name': 'secret', 'desc': ''},
                {'name': 'help', 'desc': ''}],
            HOST: [
                {'name': 'id', 'desc': 'Id'},
                {'name': 'name', 'desc': 'Arbitraty host name'}],
            FILE: [
                {'name': 'id', 'desc': 'Id'},
                {'name': 'host_id', 'desc': 'File\'s host'},
                {'name': 'template',
                 'desc': 'Template specifying the content of the file'},
                {'name': 'name', 'desc': ''}],
            MODULE: [
                {'name': 'id', 'desc': 'Id'},
                {'name': 'base_dir', 'desc': ''},
                {'name': 'module', 'desc': ''}],
            SERVICE: [
                {'name': 'service', 'desc': ''},
                {'name': 'host', 'desc': ''},
                {'name': 'version', 'desc': ''}],
            TEMPLATE: [
                {'name': 'id', 'desc': ''},
                {'name': 'name', 'desc': ''}, ],
            TEMPLATE_NS: [
                {'name': 'template', 'desc': 'hash'},
                {'name': 'namespace', 'desc': 'hash'}],
            NAMESPACE: [
                {'name': 'id', 'desc': ''},
                {'name': 'name', 'desc': ''}],
            INT_TYPE: [
                {'name': 'option_id', 'desc': ''},
                {'name': 'min', 'desc': ''},
                {'name': 'max', 'desc': ''},
                {'name': 'choices', 'desc': ''}, ],
            FLOAT_TYPE: [
                {'name': 'option_id', 'desc': ''},
                {'name': 'min', 'desc': ''},
                {'name': 'max', 'desc': ''}, ],
            STR_TYPE: [
                {'name': 'option_id', 'desc': ''},
                {'name': 'regex', 'desc': ''},
                {'name': 'max_length', 'desc': ''},
                {'name': 'quotes', 'desc': ''},
                {'name': 'ignore_case', 'desc': ''},
                {'name': 'choices', 'desc': ''}, ],
            LIST_TYPE: [
                {'name': 'option_id', 'desc': ''},
                {'name': 'item_type', 'desc': ''},
                {'name': 'bounds', 'desc': ''}, ],
            IPADDR_TYPE: [
                {'name': 'option_id', 'desc': ''},
                {'name': 'version', 'desc': ''}, ],
            URI_TYPE: [
                {'name': 'option_id', 'desc': ''},
                {'name': 'max_length', 'desc': ''},
                {'name': 'schemes', 'desc': ''}, ],
            RANGE_TYPE: [
                {'name': 'option_id', 'desc': ''},
                {'name': 'min', 'desc': ''},
                {'name': 'max', 'desc': ''}, ],
        }

        return sch

    def poll(self):
        LOG.info("%s:: polling", self.name)
        # Initialize published state to a sensible empty state.
        # Avoids races with queries.
        if self.number_of_updates == 0:
            for tablename in set(self.get_schema()):
                self.state[tablename] = set()
                self.publish(tablename, self.state[tablename],
                             use_snapshot=False)
        self.agent_api.publish_templates_hashes(self.get_context())
        self.agent_api.publish_configs_hashes(self.get_context())
        self.last_updated_time = datetime.datetime.now()
        self.number_of_updates += 1

    def process_config_hashes(self, hashes, host):
        """Handles a list of config files hashes and their retrieval.

        If the driver can process the parsing and translation of the config,
        it registers the configs to the driver.

        :param hashes: A list of config files hashes
        :param host: Name of the node hosting theses config files
        """
        LOG.debug('Received configs list from %s' % host)

        for cfg_hash in set(hashes) - self.known_configs:
            config = self.agent_api.get_config(self.get_context(),
                                               cfg_hash, host)
            if self.process_config(cfg_hash, config, host):
                self.known_configs.add(cfg_hash)
                LOG.debug('Config %s from %s registered' % (cfg_hash, host))

    @lockutils.synchronized('validator_process_template_hashes')
    def process_template_hashes(self, hashes, host):
        """Handles a list of template hashes and their retrieval.

        Uses lock to avoid multiple sending of the same data.
        :param hashes: A list of templates hashes
        :param host: Name of the node hosting theses config files
        """

        LOG.debug('Process template hashes from %s' % host)

        for t_h in set(hashes) - set(self.known_templates):
            LOG.debug('Treating template hash %s' % t_h)
            template = self.agent_api.get_template(self.get_context(), t_h,
                                                   host)

            ns_hashes = template['namespaces']

            for ns_hash in set(ns_hashes) - set(self.known_namespaces):
                namespace = self.agent_api.get_namespace(
                    self.get_context(), ns_hash, host)
                self.known_namespaces[ns_hash] = namespace

            self.known_templates[t_h] = template
            for (c_h, config) in self.templates_awaited_by_config.pop(t_h, []):
                if self.process_config(c_h, config, host):
                    self.known_configs.add(c_h)
                    LOG.debug('Config %s from %s registered (late)' %
                              (c_h, host))
        return True

    def translate_service(self, host_id, service, version):
        """Translates a service infos to SERVICE table.

        :param host_id: Host ID, should reference HOST.ID
        :param service: A service name
        :param version: A version name, can be None
        """
        if not host_id or not service:
            return

        service_row = tuple(
            map(utils.cfg_value_to_congress, (service, host_id, version)))
        self.state[SERVICE].add(service_row)

    def translate_host(self, host_id, host_name):
        """Translates a host infos to HOST table.

        :param host_id: Host ID
        :param host_name: A host name
        """
        if not host_id:
            return

        host_row = tuple(
            map(utils.cfg_value_to_congress, (host_id, host_name)))
        self.state[HOST].add(host_row)

    def translate_file(self, file_id, host_id, template_id, file_name):
        """Translates a file infos to FILE table.

        :param file_id: File ID
        :param host_id: Host ID, should reference HOST.ID
        :param template_id: Template ID, should reference TEMPLATE.ID
        """
        if not file_id or not host_id:
            return

        file_row = tuple(
            map(utils.cfg_value_to_congress,
                (file_id, host_id, template_id, file_name)))
        self.state[FILE].add(file_row)

    def translate_template_namespace(self, template_id, name, ns_ids):
        """Translates a template infos and its namespaces infos.

        Modifies tables : TEMPLATE, NAMESPACE and TEMPLATE_NS

        :param template_id: Template ID
        :param name: A template name
        :param ns_ids: List of namespace IDs, defining this template, should
            reference NAMESPACE.ID
        """

        if not template_id:
            return

        template_row = tuple(
            map(utils.cfg_value_to_congress, (template_id, name)))
        self.state[TEMPLATE].add(template_row)

        for ns_h, ns_name in six.iteritems(ns_ids):
            if not ns_h:
                continue

            namespace_row = tuple(map(utils.cfg_value_to_congress,
                                      (ns_h, ns_name)))
            self.state[NAMESPACE].add(namespace_row)

            tpl_ns_row = tuple(
                map(utils.cfg_value_to_congress, (template_id, ns_h)))
            self.state[TEMPLATE_NS].add(tpl_ns_row)

    # pylint: disable=protected-access,too-many-branches
    def translate_type(self, opt_id, cfg_type):
        """Translates a type to the appropriate type table.

        :param opt_id: Option ID, should reference OPTION.ID
        :param cfg_type: An oslo ConfigType for the referenced option
        """

        if not opt_id:
            return

        if isinstance(cfg_type, types.String):
            tablename = STR_TYPE
            # oslo.config 5.2 begins to use a different representation of
            # choices (OrderedDict). We first convert back to simple list to
            # have consistent output regardless of oslo.config version
            if isinstance(cfg_type.choices, OrderedDict):
                choices = list(map(lambda item: item[0],
                                   cfg_type.choices.items()))
            else:
                choices = cfg_type.choices
            row = (cfg_type.regex, cfg_type.max_length, cfg_type.quotes,
                   cfg_type.ignore_case, choices)

        elif isinstance(cfg_type, types.Integer):
            tablename = INT_TYPE
            # oslo.config 5.2 begins to use a different representation of
            # choices (OrderedDict). We first convert back to simple list to
            # have consistent output regardless of oslo.config version
            if isinstance(cfg_type.choices, OrderedDict):
                choices = list(map(lambda item: item[0],
                                   cfg_type.choices.items()))
            else:
                choices = cfg_type.choices
            row = (cfg_type.min, cfg_type.max, choices)

        elif isinstance(cfg_type, types.Float):
            tablename = FLOAT_TYPE
            row = (cfg_type.min, cfg_type.max)

        elif isinstance(cfg_type, types.List):
            tablename = LIST_TYPE
            row = (type(cfg_type.item_type).__name__, cfg_type.bounds)

        elif isinstance(cfg_type, types.IPAddress):
            tablename = IPADDR_TYPE
            if cfg_type.version_checker == cfg_type._check_ipv4:
                version = 4
            elif cfg_type.version_checker == cfg_type._check_ipv6:
                version = 6
            else:
                version = None
            row = (version,)

        elif isinstance(cfg_type, types.URI):
            tablename = URI_TYPE
            row = (cfg_type.max_length, cfg_type.schemes)

        elif isinstance(cfg_type, types.Range):
            tablename = RANGE_TYPE
            row = (cfg_type.min, cfg_type.max)

        else:
            return

        row = (opt_id,) + row

        if isinstance(cfg_type, types.List):
            self.translate_type(opt_id, cfg_type.item_type)

        self.state[tablename].add(
            tuple(map(utils.cfg_value_to_congress, row)))

    def translate_value(self, file_id, option_id, value):
        """Translates a value to the VALUE table.

        If value is a list, a table entry is added for every list item.
        If value is a dict, a table entry is added for every key-value.
        :param file_id: File ID, should reference FILE.ID
        :param option_id: Option ID, should reference OPTION.ID
        :param value: A value, can be None
        """
        if not file_id:
            return

        if not option_id:
            return

        if isinstance(value, list):
            for v_item in value:
                value_row = tuple(
                    map(utils.cfg_value_to_congress,
                        (option_id, file_id, v_item)))
                self.state[VALUE].add(value_row)
        elif isinstance(value, dict):
            for v_key, v_item in six.iteritems(value):
                value_row = tuple(
                    map(utils.cfg_value_to_congress,
                        (option_id, file_id, '%s:%s' % (v_key, v_item))))
                self.state[VALUE].add(value_row)
        else:
            value_row = tuple(
                map(utils.cfg_value_to_congress,
                    (option_id, file_id, value)))
            self.state[VALUE].add(value_row)

    def translate_option(self, option, group_name):
        """Translates an option metadata to datasource tables.

        Modifies tables : OPTION, OPTION_INFO
        :param option: An IdentifiedOpt object
        :param group_name: Associated section name
        """

        if option is None:
            return

        if not group_name:
            return

        option_row = tuple(map(utils.cfg_value_to_congress, (
            option.id_, option.ns_id, group_name, option.name)))

        self.state[OPTION].add(option_row)

        option_info_row = tuple(
            map(utils.cfg_value_to_congress, (
                option.id_,
                type(option.type).__name__,
                option.default,
                option.deprecated_for_removal,
                option.deprecated_reason,
                option.mutable,
                option.positional,
                option.required,
                option.sample_default,
                option.secret,
                option.help)))

        self.state[OPTION_INFO].add(option_info_row)

    def translate_conf(self, conf, file_id):
        """Translates a config manager to the datasource state.

        :param conf: A config manager ConfigOpts, containing the parsed values
         and the options metadata to read them
        :param file_id: Id of the file, which contains the parsed values
        """

        cfg_ns = conf._namespace

        def _do_translation(option, group_name='DEFAULT'):
            option = option['opt']
            # skip options that do not have the required attributes
            # avoids processing built-in options included by oslo.config, which
            # don't have all the needed IdentifiedOpt attributes.
            # see: https://github.com/openstack/oslo.config/commit/5ad89d40210bf5922de62e30b096634cac36da6c#diff-768b817a50237989cacd1a8064b4a8af  # noqa
            for attribute in ['id_', 'name', 'type', 'ns_id']:
                if not hasattr(option, attribute):
                    return

            self.translate_option(option, group_name)

            try:
                value = option._get_from_namespace(cfg_ns, group_name)
                if hasattr(cfg, 'LocationInfo'):
                    value = value[0]
            except KeyError:
                # No value parsed for this option
                return

            self.translate_type(option.id_, option.type)

            try:
                value = parsing.parse_value(option.type, value)
            except (ValueError, TypeError):
                LOG.warning('Value for option %s is not valid : %s' % (
                    option.name, value))

            self.translate_value(file_id, option.id_, value)

        for _, option in six.iteritems(conf._opts):
            _do_translation(option)

        for group_name, identified_group in six.iteritems(conf._groups):
            for _, option in six.iteritems(identified_group._opts):
                _do_translation(option, group_name)

    def process_config(self, file_hash, config, host):
        """Manages all translations related to a config file.

        Publish tables to PE.
        :param file_hash: Hash of the configuration file
        :param config: object representing the configuration
        :param host: Remote host name
        :return: True if config was processed
        """
        try:
            LOG.debug("process_config hash=%s" % file_hash)
            template_hash = config['template']
            template = self.known_templates.get(template_hash, None)
            if template is None:
                waiting = (
                    self.templates_awaited_by_config.get(template_hash, []))
                waiting.append((file_hash, config))
                self.templates_awaited_by_config[template_hash] = waiting
                LOG.debug('Template %s not yet registered' % template_hash)
                return False

            host_id = utils.compute_hash(host)

            namespaces = [self.known_namespaces.get(h, None).get('data', None)
                          for h in template['namespaces']]

            conf = parsing.construct_conf_manager(namespaces)
            parsing.add_parsed_conf(conf, config['data'])

            for tablename in set(self.get_schema()) - set(self.state):
                self.state[tablename] = set()
                self.publish(tablename, self.state[tablename],
                             use_snapshot=False)

            self.translate_conf(conf, file_hash)

            self.translate_host(host_id, host)

            self.translate_service(
                host_id, config['service'], config['version'])

            file_name = os.path.basename(config['path'])
            self.translate_file(file_hash, host_id, template_hash, file_name)

            ns_hashes = {h: self.known_namespaces[h]['name']
                         for h in template['namespaces']}
            self.translate_template_namespace(template_hash, template['name'],
                                              ns_hashes)

            for tablename in self.state:
                self.publish(tablename, self.state[tablename],
                             use_snapshot=True)
            return True
        except KeyError:
            LOG.error('Config %s from %s NOT registered'
                      % (file_hash, host))
            return False


class ValidatorAgentClient(object):
    """RPC Proxy to access the agent from the datasource."""

    def __init__(self, topic=utils.AGENT_TOPIC):
        transport = messaging.get_transport(cfg.CONF)
        target = messaging.Target(exchange=dse.DseNode.EXCHANGE,
                                  topic=topic,
                                  version=dse.DseNode.RPC_VERSION)
        self.client = messaging.RPCClient(transport, target)

    def publish_configs_hashes(self, context):
        """Asks for config hashes"""
        cctx = self.client.prepare(fanout=True)
        return cctx.cast(context, 'publish_configs_hashes')

    def publish_templates_hashes(self, context):
        """Asks for template hashes"""
        cctx = self.client.prepare(fanout=True)
        return cctx.cast(context, 'publish_templates_hashes')

    # block calling thread
    def get_namespace(self, context, ns_hash, server):
        """Retrieves an explicit namespace from a server given a hash. """
        cctx = self.client.prepare(server=server)
        return cctx.call(context, 'get_namespace', ns_hash=ns_hash)

    # block calling thread
    def get_template(self, context, tpl_hash, server):
        """Retrieves an explicit template from a server given a hash"""
        cctx = self.client.prepare(server=server)
        return cctx.call(context, 'get_template', tpl_hash=tpl_hash)

    # block calling thread
    def get_config(self, context, cfg_hash, server):
        """Retrieves a config from a server given a hash"""
        cctx = self.client.prepare(server=server)
        return cctx.call(context, 'get_config', cfg_hash=cfg_hash)


class ValidatorDriverEndpoints(object):
    """RPC endpoint on the datasource driver for use by the agents"""

    def __init__(self, driver):
        self.driver = driver

    # pylint: disable=unused-argument
    def process_templates_hashes(self, context, **kwargs):
        """Process the template hashes received from a server"""
        LOG.debug(
            'Received template hashes from host %s' % kwargs.get('host', ''))

        self.driver.process_template_hashes(**kwargs)

    # pylint: disable=unused-argument
    def process_configs_hashes(self, context, **kwargs):
        """Process the config hashes received from a server"""
        LOG.debug(
            'Received config hashes from host %s' % kwargs.get('host', ''))

        self.driver.process_config_hashes(**kwargs)
