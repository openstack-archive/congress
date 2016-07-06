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
from congress.datalog import base
from congress.db import datasources as db_datasources
from congress.dse import d6cage
from congress import exception
from congress.managers import datasource as datasource_manager
from congress.policy_engines.agnostic import Dse2Runtime
from congress import utils


LOG = logging.getLogger(__name__)
ENGINE_SERVICE_NAME = 'engine'


def create(rootdir, config_override=None):
    """Get Congress up and running when src is installed in rootdir.

    i.e. ROOTDIR=/path/to/congress/congress.
    CONFIG_OVERRIDE is a dictionary of dictionaries with configuration
    values that overrides those provided in CONFIG_FILE.  The top-level
    dictionary has keys for the CONFIG_FILE sections, and the second-level
    dictionaries store values for that section.
    """
    LOG.debug("Starting Congress with rootdir=%s, config_override=%s",
              rootdir, config_override)

    # create message bus
    cage = d6cage.d6Cage()

    # read in datasource configurations
    cage.config = config_override or {}

    # path to congress source dir
    src_path = os.path.join(rootdir, "congress")

    datasource_mgr = datasource_manager.DataSourceManager()
    datasource_mgr.validate_configured_drivers()

    # add policy engine
    engine_path = os.path.join(src_path, "policy_engines/agnostic.py")
    LOG.info("main::start() engine_path: %s", engine_path)
    cage.loadModule("PolicyEngine", engine_path)
    cage.createservice(
        name="engine",
        moduleName="PolicyEngine",
        description="Policy Engine (DseRuntime instance)",
        args={'d6cage': cage, 'rootdir': src_path,
              'log_actions_only': cfg.CONF.enable_execute_action})
    engine = cage.service_object('engine')
    engine.initialize_table_subscriptions()
    engine.debug_mode()  # should take this out for production

    # add policy api
    api_path = os.path.join(src_path, "api/policy_model.py")
    LOG.info("main::start() api_path: %s", api_path)
    cage.loadModule("API-policy", api_path)
    cage.createservice(
        name="api-policy",
        moduleName="API-policy",
        description="API-policy DSE instance",
        args={'policy_engine': engine})

    # add rule api
    api_path = os.path.join(src_path, "api/rule_model.py")
    LOG.info("main::start() api_path: %s", api_path)
    cage.loadModule("API-rule", api_path)
    cage.createservice(
        name="api-rule",
        moduleName="API-rule",
        description="API-rule DSE instance",
        args={'policy_engine': engine})

    # add table api
    api_path = os.path.join(src_path, "api/table_model.py")
    LOG.info("main::start() api_path: %s", api_path)
    cage.loadModule("API-table", api_path)
    cage.createservice(
        name="api-table",
        moduleName="API-table",
        description="API-table DSE instance",
        args={'policy_engine': engine,
              'datasource_mgr': datasource_mgr})

    # add row api
    api_path = os.path.join(src_path, "api/row_model.py")
    LOG.info("main::start() api_path: %s", api_path)
    cage.loadModule("API-row", api_path)
    cage.createservice(
        name="api-row",
        moduleName="API-row",
        description="API-row DSE instance",
        args={'policy_engine': engine,
              'datasource_mgr': datasource_mgr})

    # add status api
    api_path = os.path.join(src_path, "api/status_model.py")
    LOG.info("main::start() api_path: %s", api_path)
    cage.loadModule("API-status", api_path)
    cage.createservice(
        name="api-status",
        moduleName="API-status",
        description="API-status DSE instance",
        args={'policy_engine': engine,
              'datasource_mgr': datasource_mgr})

    # add action api
    api_path = os.path.join(src_path, "api/action_model.py")
    LOG.info("main::start() api_path: %s", api_path)
    cage.loadModule("API-action", api_path)
    cage.createservice(
        name="api-action",
        moduleName="API-action",
        description="API-action DSE instance",
        args={'policy_engine': engine,
              'datasource_mgr': datasource_mgr})

    # add schema api
    api_path = os.path.join(src_path, "api/schema_model.py")
    LOG.info("main::start() api_path: %s", api_path)
    cage.loadModule("API-schema", api_path)
    cage.createservice(
        name="api-schema",
        moduleName="API-schema",
        description="API-schema DSE instance",
        args={'datasource_mgr': datasource_mgr})

    # add path for system/datasource-drivers
    api_path = os.path.join(src_path, "api/system/driver_model.py")
    LOG.info("main::start() api_path: %s", api_path)
    cage.loadModule("API-system", api_path)
    cage.createservice(
        name="api-system",
        moduleName="API-system",
        description="API-system DSE instance",
        args={'datasource_mgr': datasource_mgr})

    # Load policies from database
    engine.persistent_load_policies()

    # if this is the first time we are running Congress, need
    #   to create the default theories (which cannot be deleted)
    api_policy = cage.service_object('api-policy')

    engine.DEFAULT_THEORY = 'classification'
    engine.builtin_policy_names.add(engine.DEFAULT_THEORY)
    try:
        api_policy.add_item({'name': engine.DEFAULT_THEORY,
                             'description': 'default policy'}, {})
    except KeyError:
        pass

    engine.ACTION_THEORY = 'action'
    engine.builtin_policy_names.add(engine.ACTION_THEORY)
    try:
        api_policy.add_item({'kind': base.ACTION_POLICY_TYPE,
                             'name': engine.ACTION_THEORY,
                             'description': 'default action policy'},
                            {})
    except KeyError:
        pass

    # have policy-engine subscribe to api calls
    # TODO(thinrichs): either have API publish everything to DSE bus and
    #   have policy engine subscribe to all those messages
    #   OR have API interact with individual components directly
    #   and change all tests so that the policy engine does not need to be
    #   subscribed to 'policy-update'
    engine.subscribe('api-rule', 'policy-update',
                     callback=engine.receive_policy_update)

    # spin up all the configured services, if we have configured them

    drivers = datasource_mgr.get_datasources()
    # Setup cage.config as it previously done when it was loaded
    # from disk. FIXME(arosen) later!
    for driver in drivers:
        if not driver['enabled']:
            LOG.info("module %s not enabled, skip loading", driver['name'])
            continue
        driver_info = datasource_mgr.get_driver_info(driver['driver'])
        engine.create_policy(driver['name'], kind=base.DATASOURCE_POLICY_TYPE)
        try:
            cage.createservice(name=driver['name'],
                               moduleName=driver_info['module'],
                               args=driver['config'],
                               module_driver=True,
                               type_='datasource_driver',
                               id_=driver['id'])
        except d6cage.DataServiceError:
            # FIXME(arosen): If createservice raises congress-server
            # dies here. So we catch this exception so the server does
            # not die. We need to refactor the dse code so it just
            # keeps retrying the driver gracefully...
            continue
        service = cage.service_object(driver['name'])
        engine.set_schema(driver['name'], service.get_schema())

    # Insert rules.  Needs to be done after datasources are loaded
    #  so that we can compile away column references at read time.
    #  If datasources loaded after this, we don't have schemas.
    engine.persistent_load_rules()

    # Start datasource synchronizer after explicitly starting the
    # datasources, because the explicit call to create a datasource
    # will crash if the synchronizer creates the datasource first.
    synchronizer_path = os.path.join(src_path, "synchronizer.py")
    LOG.info("main::start() synchronizer: %s", synchronizer_path)
    cage.loadModule("Synchronizer", synchronizer_path)
    cage.createservice(
        name="synchronizer",
        moduleName="Synchronizer",
        description="DB synchronizer instance",
        args={'poll_time': cfg.CONF.datasource_sync_period})
    synchronizer = cage.service_object('synchronizer')
    engine.set_synchronizer(synchronizer)

    # add datasource api
    api_path = os.path.join(src_path, "api/datasource_model.py")
    LOG.info("main::start() api_path: %s", api_path)
    cage.loadModule("API-datasource", api_path)
    cage.createservice(
        name="api-datasource",
        moduleName="API-datasource",
        description="API-datasource DSE instance",
        args={'policy_engine': engine,
              'datasource_mgr': datasource_mgr,
              'synchronizer': synchronizer})

    return cage


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
        for ds in services['datasources']:
            try:
                utils.create_datasource_policy(ds, ds.name,
                                               ENGINE_SERVICE_NAME)
            except (exception.BadConfig,
                    exception.DatasourceNameInUse,
                    exception.DriverNotFound,
                    exception.DatasourceCreationError) as e:
                LOG.exception("Datasource %s creation failed. %s" % (ds, e))
                node.unregister_service(ds)

    # TODO(dse2): Figure out what to do about the synchronizer
    # # Start datasource synchronizer after explicitly starting the
    # # datasources, because the explicit call to create a datasource
    # # will crash if the synchronizer creates the datasource first.
    # synchronizer_path = os.path.join(src_path, "synchronizer.py")
    # LOG.info("main::start() synchronizer: %s", synchronizer_path)
    # cage.loadModule("Synchronizer", synchronizer_path)
    # cage.createservice(
    #     name="synchronizer",
    #     moduleName="Synchronizer",
    #     description="DB synchronizer instance",
    #     args={'poll_time': cfg.CONF.datasource_sync_period})
    # synchronizer = cage.service_object('synchronizer')
    # engine.set_synchronizer(synchronizer)

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
    """Create datasource services and return datasources."""
    datasources = db_datasources.get_datasources()
    services = []
    for ds in datasources:
        ds_dict = bus.make_datasource_dict(ds)
        if not ds['enabled']:
            LOG.info("module %s not enabled, skip loading", ds_dict['name'])
            continue

        LOG.info("create configured datasource service %s." % ds_dict['name'])
        try:
            driver_info = bus.get_driver_info(ds_dict['driver'])
            service = bus.create_service(
                class_path=driver_info['module'],
                kwargs={'name': ds_dict['name'], 'args': ds_dict['config']})
            bus.register_service(service)
            services.append(service)
        except Exception:
            LOG.exception("datasource %s creation failed." % ds_dict['name'])

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
