# Copyright (c) 2014 VMware, Inc. All rights reserved.
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

import ConfigParser
import os
import os.path
import re
import sys

from congress.datasources.datasource_driver import DataSourceConfigException
from congress.dse import d6cage
from congress.openstack.common import log as logging


LOG = logging.getLogger(__name__)


def create(rootdir, statedir, config_file, config_override=None):
    """Get Congress up and running when src is installed in rootdir,
    i.e. ROOTDIR=/path/to/congress/congress.
    CONFIG_OVERRIDE is a dictionary of dictionaries with configuration
    values that overrides those provided in CONFIG_FILE.  The top-level
    dictionary has keys for the CONFIG_FILE sections, and the second-level
    dictionaries store values for that section.
    """
    LOG.debug("Starting Congress with rootdir={}, statedir={}, "
              "datasource_config={}, config_override={}".format(
                  rootdir, statedir, config_file, config_override))

    # create message bus
    cage = d6cage.d6Cage()
    cage.daemon = True
    cage.start()
    cage.system_service_names.add(cage.name)

    # read in datasource configurations
    cage.config = initialize_config(config_file, config_override)

    # add policy engine
    engine_path = os.path.join(rootdir, "policy/dsepolicy.py")
    LOG.info("main::start() engine_path: " + str(engine_path))
    cage.loadModule("PolicyEngine", engine_path)
    cage.createservice(
        name="engine",
        moduleName="PolicyEngine",
        description="Policy Engine (DseRuntime instance)",
        args={'d6cage': cage, 'rootdir': rootdir})
    engine = cage.service_object('engine')
    if statedir is not None:
        engine.load_dir(statedir)
    engine.initialize_table_subscriptions()
    cage.system_service_names.add(engine.name)
    engine.debug_mode()  # should take this out for production

    # add policy api
    # TODO(thinrichs): change to real API path.
    api_path = os.path.join(rootdir, "api/policy_model.py")
    LOG.info("main::start() api_path: " + str(api_path))
    cage.loadModule("API-policy", api_path)
    cage.createservice(
        name="api-policy",
        moduleName="API-policy",
        description="API-policy DSE instance",
        args={'policy_engine': engine})
    cage.system_service_names.add('api-policy')

    # add rule api
    api_path = os.path.join(rootdir, "api/rule_model.py")
    LOG.info("main::start() api_path: " + str(api_path))
    cage.loadModule("API-rule", api_path)
    cage.createservice(
        name="api-rule",
        moduleName="API-rule",
        description="API-rule DSE instance",
        args={'policy_engine': engine})
    cage.system_service_names.add('api-rule')

    # add table api
    api_path = os.path.join(rootdir, "api/table_model.py")
    LOG.info("main::start() api_path: " + str(api_path))
    cage.loadModule("API-table", api_path)
    cage.createservice(
        name="api-table",
        moduleName="API-table",
        description="API-table DSE instance",
        args={'policy_engine': engine})
    cage.system_service_names.add('api-table')

    # add row api
    api_path = os.path.join(rootdir, "api/row_model.py")
    LOG.info("main::start() api_path: " + str(api_path))
    cage.loadModule("API-row", api_path)
    cage.createservice(
        name="api-row",
        moduleName="API-row",
        description="API-row DSE instance",
        args={'policy_engine': engine})
    cage.system_service_names.add('api-row')

    # add datasource api
    api_path = os.path.join(rootdir, "api/datasource_model.py")
    LOG.info("main::start() api_path: " + str(api_path))
    cage.loadModule("API-datasource", api_path)
    cage.createservice(
        name="api-datasource",
        moduleName="API-datasource",
        description="API-datasource DSE instance",
        args={'policy_engine': engine})
    cage.system_service_names.add('api-datasource')

    # have policy-engine subscribe to api calls
    # TODO(thinrichs): either have API publish everything to DSE bus and
    #   have policy engine subscribe to all those messages
    #   OR have API interact with individual components directly
    #   and change all tests so that the policy engine does not need to be
    #   subscribed to 'policy-update'
    engine.subscribe('api-rule', 'policy-update',
                     callback=engine.receive_policy_update)

    # spin up all the configured services, if we have configured them
    if cage.config:
        for name in cage.config:
            if 'module' in cage.config[name]:
                load_data_service(name, cage.config[name], cage, rootdir)
        return cage


def load_data_service(service_name, config, cage, rootdir):
    """Load a service if not already loaded.  Also loads its
    module if the module is not already loaded.  Returns None.
    SERVICE_NAME: name of service
    CONFIG: dictionary of configuration values
    CAGE: instance to load service into
    ROOTDIR: dir for start of module paths
    """
    if service_name in cage.services:
        return
    if service_name not in cage.config:
        raise DataSourceConfigException(
            "Service %s used in rule but not configured; "
            "tables will be empty" % service_name)
    if 'module' not in config:
        raise DataSourceConfigException(
            "Service %s config missing 'module' entry" % service_name)
    module_path = config['module']
    module_name = re.sub('[^a-zA-Z0-9_]', '_', module_path)
    if not os.path.isabs(module_path) and rootdir is not None:
        module_path = os.path.join(rootdir, module_path)
    if module_name not in sys.modules:
        LOG.info("Trying to create module {} from {}".format(
            module_name, module_path))
        cage.loadModule(module_name, module_path)
    LOG.info("Trying to create service {} with module {}".format(
        service_name, module_name))
    cage.createservice(name=service_name, moduleName=module_name,
                       args=config)


def initialize_config(config_file, config_override):
    """Turn config_file into a dictionary of dictionaries, and in so
    doing insulate rest of code from idiosyncracies of ConfigParser.
    """
    if config_override is None:
        config_override = {}
    if config_file is None:
        LOG.info("Starting with override configuration: %s",
                 str(config_override))
        return config_override
    config = ConfigParser.ConfigParser()
    # If we can't process the config file, we should die
    config.readfp(open(config_file))
    d = {}
    # turn the config into a dictionary of dictionaries,
    #  taking the config_override values into account.
    for section in config.sections():
        if section in config_override:
            override = config_override[section]
        else:
            override = {}
        e = {}
        for opt in config.options(section):
            e[opt] = config.get(section, opt)
        # union e and override, with conflicts decided by override
        e = dict(e, **override)
        d[section] = e
    LOG.info("Starting with configuration: %s", str(d))
    return d
