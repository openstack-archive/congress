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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import copy
import os
import os.path
import re
import sys

from oslo_config import cfg

from oslo_log import log as logging

from congress.api import action_model
from congress.api import application
from congress.api import datasource_model
from congress.api import policy_model
from congress.api import router
from congress.api import row_model
from congress.api import rule_model
from congress.api import schema_model
from congress.api import status_model
from congress.api.system import driver_model
from congress.api import table_model
from congress.db import datasources as db_datasources
from congress import exception
from congress.policy_engines.agnostic import Dse2Runtime


LOG = logging.getLogger(__name__)
ENGINE_SERVICE_NAME = 'engine'


def create2(node, policy_engine=True, datasources=True, api=True):
    """Get Congress up.

    Creates a DseNode if one is not provided and adds policy_engine,
    datasources, api to that node.

    :param node is a DseNode
    :param policy_engine controls whether policy_engine is included
    :param datasources controls whether datasources are included
    :param api controls whether API is included
    :returns DseNode
    """
    # create services as required
    services = {}
    if api:
        LOG.info("Registering congress API service on node %s", node.node_id)
        services['api'], services['api_service'] = create_api()
        node.register_service(services['api_service'])

    if policy_engine:
        LOG.info("Registering congress PolicyEngine service on node %s",
                 node.node_id)
        services[ENGINE_SERVICE_NAME] = create_policy_engine()
        node.register_service(services[ENGINE_SERVICE_NAME])
        initialize_policy_engine(services[ENGINE_SERVICE_NAME])

    if datasources:
        LOG.info("Registering congress datasource services on node %s",
                 node.node_id)
        services['datasources'] = create_datasources(node)

        # datasource policies would be created by respective PE's synchronizer
        # for ds in services['datasources']:
        #    try:
        #        utils.create_datasource_policy(ds, ds.name,
        #                                       ENGINE_SERVICE_NAME)
        #    except (exception.BadConfig,
        #            exception.DatasourceNameInUse,
        #            exception.DriverNotFound,
        #            exception.DatasourceCreationError) as e:
        #        LOG.exception("Datasource %s creation failed. %s" % (ds, e))
        #        node.unregister_service(ds)

    # start synchronizer
    if policy_engine:
        services[ENGINE_SERVICE_NAME].start_policy_synchronizer()
    if datasources:
        node.start_datasource_synchronizer()
    return services


def create_api():
    """Return service that encapsulates api logic for DSE2."""
    # ResourceManager inherits from DataService
    api_resource_mgr = application.ResourceManager()
    models = create_api_models(api_resource_mgr)
    router.APIRouterV1(api_resource_mgr, models)
    return models, api_resource_mgr


def create_api_models(bus):
    """Create all the API models and return as a dictionary for DSE2."""
    res = {}
    res['api-policy'] = policy_model.PolicyModel('api-policy', bus=bus)
    res['api-rule'] = rule_model.RuleModel('api-rule', bus=bus)
    res['api-row'] = row_model.RowModel('api-row', bus=bus)
    res['api-datasource'] = datasource_model.DatasourceModel(
        'api-datasource', bus=bus)
    res['api-schema'] = schema_model.SchemaModel('api-schema', bus=bus)
    res['api-table'] = table_model.TableModel('api-table', bus=bus)
    res['api-status'] = status_model.StatusModel('api-status', bus=bus)
    res['api-action'] = action_model.ActionsModel('api-action', bus=bus)
    res['api-system'] = driver_model.DatasourceDriverModel(
        'api-system', bus=bus)
    return res


def create_policy_engine():
    """Create policy engine and initialize it using the api models."""
    engine = Dse2Runtime(ENGINE_SERVICE_NAME)
    engine.debug_mode()  # should take this out for production
    return engine


def initialize_policy_engine(engine):
    """Initialize the policy engine using the API."""
    # Load policies from database
    engine.persistent_load_policies()
    engine.create_default_policies()
    engine.persistent_load_rules()


def create_datasources(bus):
    """Create and register datasource services ."""
    if cfg.CONF.delete_missing_driver_datasources:
        # congress server started with --delete_missing_driver_datasources
        bus.delete_missing_driver_datasources()

    datasources = db_datasources.get_datasources()
    services = []
    for ds in datasources:
        LOG.info("create configured datasource service %s.", ds.name)
        try:
            service = bus.create_datasource_service(ds)
            if service:
                bus.register_service(service)
                services.append(service)
        except exception.DriverNotFound:
            LOG.exception("Some datasources could not be loaded, start "
                          "congress server with "
                          "--delete_missing_driver_datasources option to "
                          "clean up stale datasources in DB.")
            sys.exit(1)
        except Exception:
            LOG.exception("datasource %s creation failed.", ds.name)
            raise

    return services


def load_data_service(service_name, config, cage, rootdir, id_):
    """Load service.

    Load a service if not already loaded. Also loads its
    module if the module is not already loaded.  Returns None.
    SERVICE_NAME: name of service
    CONFIG: dictionary of configuration values
    CAGE: instance to load service into
    ROOTDIR: dir for start of module paths
    ID: UUID of the service.
    """
    config = copy.copy(config)
    if service_name in cage.services:
        return
    if 'module' not in config:
        raise exception.DataSourceConfigException(
            "Service %s config missing 'module' entry" % service_name)
    module_path = config['module']
    module_name = re.sub('[^a-zA-Z0-9_]', '_', module_path)
    if not os.path.isabs(module_path) and rootdir is not None:
        module_path = os.path.join(rootdir, module_path)
    if module_name not in sys.modules:
        LOG.info("Trying to create module %s from %s",
                 module_name, module_path)
        cage.loadModule(module_name, module_path)
    LOG.info("Trying to create service %s with module %s",
             service_name, module_name)
    cage.createservice(name=service_name, moduleName=module_name,
                       args=config, type_='datasource_driver', id_=id_)
