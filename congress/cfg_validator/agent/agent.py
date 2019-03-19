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

"""Agent is the main entry point for the configuration validator agent.

The agent is executed on the different nodes of the cloud and sends back
configuration values and metadata to the configuration validator datasource
driver.
"""

import json
import os
import sys

from oslo_config import cfg
from oslo_config import generator
from oslo_log import log as logging
from oslo_service import service
import six

from congress.common import config

from congress.cfg_validator.agent import generator as validator_generator
from congress.cfg_validator.agent import opts as validator_opts
from congress.cfg_validator.agent import rpc
from congress.cfg_validator import parsing
from congress.cfg_validator import utils


LOG = logging.getLogger(__name__)


class Config(object):
    """Encapsulates a configuration file and its meta-data.

    Attributes:
        :ivar path: Path to the configuration on the local file system.
        :ivar template: A Template object to use for parsing the configuration.
        :ivar data: The normalized Namespace loaded by oslo-config, contains
            the parsed values.
        :ivar hash: Hash of the configuration file, salted with the hostname
            and the template hash
        :ivar service_name: The associated service name
    """

    # pylint: disable=protected-access

    def __init__(self, path, template, service_name):
        self.path = path
        self.template = template
        self.data = None
        self.hash = None
        self.service = service_name

    def parse(self, host):
        """Parses the config at the path given. Updates data and hash.

        host: the name of the host where the config is. Used for building a
        unique hash.
        """
        namespaces_data = [ns.data for ns in self.template.namespaces]
        conf = parsing.parse_config_file(namespaces_data, self.path)

        Config.sanitize_config(conf)
        self.data = conf._namespace._normalized

        self.hash = utils.compute_hash(host, self.template.hash,
                                       json.dumps(self.data, sort_keys=True))

    @staticmethod
    def sanitize_config(conf):
        """Sanitizes some cfg.ConfigOpts values, given its options meta-data.

        :param conf: A cfg.ConfigOpts object, pre-loaded with its options
            meta-data and with its configurations values.
        """
        normalized = getattr(conf._namespace,
                             '_normalized', None)
        if not normalized:
            return

        normalized = normalized[0]

        # Obfuscate values of options declared secret
        def _sanitize(opt, group_name='DEFAULT'):
            if not opt.secret:
                return
            if group_name not in normalized:
                return
            if opt.name in normalized[group_name]:
                normalized[group_name][opt.name] = ['*' * 4]

        for option in six.itervalues(conf._opts):
            _sanitize(option['opt'])

        for group_name, group in six.iteritems(conf._groups):
            for option in six.itervalues(group._opts):
                _sanitize(option['opt'], group_name)

    def get_info(self):
        """Information on the configuration file.

        :return: a quadruple made of:
          * the hash of the template,
          * the path to the file,
          * the content
          * the service name.
        """
        return {'template': self.template.hash, 'path': self.path,
                'data': self.data, 'service': self.service}


class Namespace(object):
    """Encapsulates a namespace, as defined by oslo-config-generator.

    It contains the actual meta-data of the options. The data is loaded from
    the service source code, by means of oslo-config-generator.

    Attributes:
        name: The name, as used by oslo-config-generator.
        data: The meta-data of the configuration options.
        hash: Hash of the namespace.
    """

    def __init__(self, name):
        self.name = name
        self.data = None
        self.hash = None

    @staticmethod
    def load(name):
        """Loads a namespace from disk

        :param name: the name of namespace to load.
        :return: a fully configured namespace.
        """

        namespace = Namespace(name)

        saved_conf = cfg.CONF
        cfg.CONF = cfg.ConfigOpts()

        try:
            json_data = validator_generator.generate_ns_data(name)
        finally:
            cfg.CONF = saved_conf

        namespace.hash = utils.compute_hash(json_data)
        namespace.data = json.loads(json_data)

        return namespace

    def get_info(self):
        """Information on the namespace

        :return: a tuple containing
         * data: the content of the namespace
         * name: the name of the namespace
        """
        return {'data': self.data, 'name': self.name}


class Template(object):
    """Describes a template, as defined by oslo-config-generator.

    Attributes:
        :ivar name: The name, as used by oslo-config-generator.
        :ivar path: The path to the template configuration file, as defined by
            oslo-config-generator, on the local file system.
        :ivar output_file: The default output path for this template.
        :ivar namespaces: A set of Namespace objects, which make up this
            template.
    """

    # pylint: disable=protected-access

    def __init__(self, path, output_file):
        self.path = path
        self.output_file = output_file
        self.namespaces = []
        self.hash = None

        name = os.path.basename(output_file)
        self.name = os.path.splitext(name)[0] if name.endswith('.sample') \
            else name

    @staticmethod
    def _parse_template_conf(template_path):
        """Parses a template configuration file"""
        conf = cfg.ConfigOpts()

        conf.register_opts(generator._generator_opts)
        conf(['--config-file', template_path])

        return conf.namespace, conf.output_file

    @staticmethod
    def load(template_path):
        """Loads a template configuration file

        :param template_path: path to the template
        :return: a fully configured Template object.
        """
        namespaces, output_file = Template._parse_template_conf(template_path)

        template = Template(template_path, output_file)

        for namespace in namespaces:
            template.namespaces.append(Namespace.load(namespace))

        template.hash = utils.compute_hash(
            sorted([ns.hash for ns in template.namespaces]))

        return template

    def get_info(self):
        """Info on the template

        :return: a quadruple made of:
            * path: the path to the template path
            * name: the name of the template
            * output_fle:
            * namespaces: an array of namespace hashes.
        """
        return {'path': self.path, 'name': self.name,
                'output_file': self.output_file,
                'namespaces': [ns.hash for ns in self.namespaces]}


class ConfigManager(object):
    """Manages the services configuration files on a node and their meta-data.

    Attributes:
        :ivar host: A hostname.
        :ivar configs: A dict mapping config hashes to their associated Config
            object.
        :ivar templates: A dict mapping template hashes to their associated
            Template object.
        :ivar namespaces: A dict mapping namespace hashes to their associated
            Namespace object.
    """

    def __init__(self, host, services_files):
        self.host = host

        self.configs = {}
        self.templates = {}
        self.namespaces = {}

        for service_name, files in six.iteritems(services_files):
            self.register_service(service_name, files)

    def get_template_by_path(self, template_path):
        """Given a path finds the corresponding template if it is registered

        :param template_path: the path of the searched template
        :return: None or the template
        """
        for template in six.itervalues(self.templates):
            if template.path == template_path:
                return template

    def add_template(self, template_path):
        """Adds a new template (loads it from path).

        :param template_path: a valid path to the template file.
        """
        template = Template.load(template_path)

        self.templates[template.hash] = template
        self.namespaces.update({ns.hash: ns for ns in template.namespaces})

        return template

    def register_config(self, config_path, template_path, service_name):
        """Register a configuration file and its associated template.

        Template and config are actually parsed and loaded.

        :param config_path: a valid path to the config file.
        :param template_path: a valid path to the template file.
        """
        template = (self.get_template_by_path(template_path)
                    or self.add_template(template_path))

        conf = Config(config_path, template, service_name)

        conf.parse(self.host)

        self.configs[conf.hash] = conf

        LOG.info('{hash: %s, path:%s}' % (conf.hash, conf.path))

    def register_service(self, service_name, files):
        """Register all configs for an identified service.

        Inaccessible files are ignored and files registration pursues.

        :param service_name: The name of the service
        :param files: A dict, mapping a configuration path to
            its associated template path
        """
        for config_path, template_path in six.iteritems(files):
            try:
                self.register_config(config_path, template_path, service_name)
            except (IOError, cfg.ConfigFilesNotFoundError, BaseException):
                LOG.error(('Error while registering config %s with template'
                           ' %s for service %s') %
                          (config_path, template_path, service_name))


class ValidatorAgentEndpoint(object):
    """Validator Agent.

    It is used as an RPC endpoint.

    Attributes:
        config_manager: ConfigManager object.
        driver_api: RPC client to communicate with the driver.
    """

    # pylint: disable=unused-argument,too-many-instance-attributes

    def __init__(self, conf=None):
        self.conf = conf or cfg.CONF
        validator_conf = self.conf.agent

        self.host = validator_conf.host
        self.version = validator_conf.version
        self.max_delay = validator_conf.max_delay
        self.driver_api = rpc.ValidatorDriverClient()

        self.services = list(validator_conf.services.keys())

        service_files = validator_conf.services
        self.config_manager = ConfigManager(self.host, service_files)

    def publish_configs_hashes(self, context, **kwargs):
        """"Sends back all configuration hashes"""
        LOG.info('Sending config hashes')
        conf = set(self.config_manager.configs)
        self.driver_api.process_configs_hashes({}, conf, self.host)

    def publish_templates_hashes(self, context, **kwargs):
        """"Sends back all template hashes"""
        LOG.info('Sending template hashes')
        tpl = set(self.config_manager.templates)
        self.driver_api.process_templates_hashes({}, tpl, self.host)

    def get_namespace(self, context, **kwargs):
        """"Sends back a namespace

        :param context: the RPC context
        :param hash: the hash of the namespace to send
        :return: the namespace or None if not found
        """
        ns_hash = kwargs['ns_hash']
        LOG.info('Sending namespace %s' % ns_hash)

        namespace = self.config_manager.namespaces.get(ns_hash, None)
        if namespace is None:
            return None
        ret = namespace.get_info()
        ret['version'] = self.version
        return ret

    def get_template(self, context, **kwargs):
        """"Sends back a template

        :param context: the RPC context
        :param hash: the hash of the template to send
        :return: the template or None if not found
        """
        template_hash = kwargs['tpl_hash']

        LOG.info('Sending template %s' % template_hash)

        template = self.config_manager.templates.get(template_hash, None)
        if template is None:
            return None
        ret = template.get_info()
        ret['version'] = self.version
        return ret

    def get_config(self, context, **kwargs):
        """"Sends back a config

        :param context: the RPC context
        :param hash: the hash of the config to send
        :return: the config or None if not found
        """
        config_hash = kwargs['cfg_hash']

        LOG.info('Sending config %s' % config_hash)

        conf = self.config_manager.configs.get(config_hash, None)
        if conf is None:
            return None
        ret = conf.get_info()
        ret['version'] = self.version
        return ret


def main():
    """Agent entry point"""
    validator_opts.register_validator_agent_opts(cfg.CONF)
    config.init(sys.argv[1:])
    config.setup_logging()

    if not cfg.CONF.config_file:
        sys.exit("ERROR: Unable to find configuration file via default "
                 "search paths ~/.congress/, ~/, /etc/congress/, /etc/) and "
                 "the '--config-file' option!")

    agent = ValidatorAgentEndpoint()
    server = rpc.AgentService(utils.AGENT_TOPIC, [agent])
    service.launch(agent.conf, server).wait()


if __name__ == '__main__':
    main()
