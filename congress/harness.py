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

from congress.dse import d6cage
from congress.openstack.common import log as logging


LOG = logging.getLogger(__name__)


def create(rootdir, statedir, datasource_config):
    """Get Congress up and running when src is installed in rootdir,
    i.e. ROOTDIR=/path/to/congress/congress.
    """
    LOG.debug("Starting Congress with rootdir={}, statedir={}, "
              "datasource_config={}".format(
                  rootdir, statedir, datasource_config))

    # create message bus
    cage = d6cage.d6Cage()
    cage.daemon = True
    cage.start()
    cage.system_service_names.add(cage.name)

    # read in datasource configurations
    cage.config = initialize_config(datasource_config)

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
    return cage


def initialize_config(config_file):
    """Turn config_file into a dictionary of dictionaries, and in so
    doing insulate rest of code from idiosyncracies of ConfigParser.
    """
    config = ConfigParser.ConfigParser()
    config.readfp(open(config_file))
    d = {}
    for section in config.sections():
        e = {}
        for opt in config.options(section):
            e[opt] = config.get(section, opt)
        d[section] = e
    LOG.info("Configuration found for {} services: {}".format(
        len(d.keys()), ";".join(d.keys())))
    return d
