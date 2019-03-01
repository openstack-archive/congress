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

import sys

from oslo_config import cfg
from oslo_log import log as logging

from congress.api import action_model
from congress.api import application
from congress.api import base as api_base
from congress.api import datasource_model
from congress.api import library_policy_model
from congress.api import policy_model
from congress.api import router
from congress.api import row_model
from congress.api import rule_model
from congress.api import schema_model
from congress.api import status_model
from congress.api.system import driver_model
from congress.api import table_model
from congress.api import webhook_model
from congress.datasources.json_ingester import exec_api
from congress.datasources.json_ingester import json_ingester
from congress.db import datasources as db_datasources
from congress.dse2 import datasource_manager as ds_manager
from congress.dse2 import dse_node
from congress import exception
from congress.library_service import library_service
from congress.policy_engines import agnostic
from congress import utils

LOG = logging.getLogger(__name__)


def create2(node_id=None, bus_id=None, existing_node=None,
            policy_engine=True, datasources=True, api=True):
    """Get Congress up.

    Creates a DseNode if one is not provided and adds policy_engine,
    datasources, api to that node.

    :param: node_id is node_id of DseNode to be created
    :param: bus_id is partition_id of DseNode to be created
    :param: existing_node is a DseNode (optional; in lieu of previous 2 params)
    :param: policy_engine controls whether policy_engine is included
    :param: datasources controls whether datasources are included
    :param: api controls whether API is included
    :returns: DseNode
    """
    # create DseNode if existing_node not given
    if existing_node is None:
        assert (not (node_id is None or bus_id is None)),\
            'params node_id and bus_id required.'
        node = dse_node.DseNode(cfg.CONF, node_id, [], partition_id=bus_id)
    else:
        assert (node_id is None and bus_id is None),\
            'params node_id and bus_id must be None when existing_node given.'
        node = existing_node

    # create services as required
    services = {}

    # Load all configured drivers
    dse_node.DseNode.load_drivers()

    if datasources:
        LOG.info("Registering congress datasource services on node %s",
                 node.node_id)
        services['datasources'] = create_datasources(node)
        services['ds_manager'] = ds_manager.DSManagerService(
            api_base.DS_MANAGER_SERVICE_ID)
        node.register_service(services['ds_manager'])

    if policy_engine:
        LOG.info("Registering congress PolicyEngine service on node %s",
                 node.node_id)
        engine = create_policy_engine()
        services[api_base.ENGINE_SERVICE_ID] = engine
        node.register_service(engine)
        initialize_policy_engine(engine)

        # NOTE(ekcs): library service does not depend on policy engine,
        # it is placed on the same nodes as policy engine for convenience only
        LOG.info("Registering congress policy library service on node %s",
                 node.node_id)
        library = create_policy_library_service()
        services[api_base.LIBRARY_SERVICE_ID] = library
        node.register_service(library)

    if api:
        LOG.info("Registering congress API service on node %s", node.node_id)
        services['api'], services['api_service'] = create_api()
        node.register_service(services['api_service'])

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
    res['api-library-policy'] = library_policy_model.LibraryPolicyModel(
        'api-library-policy', bus=bus)
    res['api-policy'] = policy_model.PolicyModel('api-policy', bus=bus)
    res['api-rule'] = rule_model.RuleModel('api-rule', bus=bus)
    res['api-row'] = row_model.RowModel('api-row', bus=bus)
    res['api-datasource'] = datasource_model.DatasourceModel(
        'api-datasource', bus=bus)
    res['api-schema'] = schema_model.SchemaModel('api-schema', bus=bus)
    res['api-table'] = table_model.TableModel('api-table', bus=bus)
    res['api-webhook'] = webhook_model.WebhookModel('api-webhook', bus=bus)
    res['api-status'] = status_model.StatusModel('api-status', bus=bus)
    res['api-action'] = action_model.ActionsModel('api-action', bus=bus)
    res['api-system'] = driver_model.DatasourceDriverModel(
        'api-system', bus=bus)
    return res


def create_policy_engine():
    """Create policy engine and initialize it using the api models."""
    engine = agnostic.DseRuntime(api_base.ENGINE_SERVICE_ID)
    engine.debug_mode()  # should take this out for production
    return engine


def initialize_policy_engine(engine):
    """Initialize the policy engine using the API."""
    # Load policies from database
    engine.persistent_load_policies()
    engine.create_default_policies()
    engine.persistent_load_rules()


def create_policy_library_service():
    """Create policy library service."""
    library = library_service.LibraryService(api_base.LIBRARY_SERVICE_ID)
    # load library policies from file if none present in DB
    if len(library.get_policies(include_rules=False)) == 0:
        library.load_policies_from_files()
    return library


def create_json_ingester_datasources(bus):
    ds_configs = utils.YamlConfigs(
        cfg.CONF.json_ingester.config_path, 'name',
        cfg.CONF.json_ingester.config_reusables_path)
    ds_configs.load_from_files()
    exec_manager = exec_api.ExecApiManager(
        ds_configs.loaded_structures.values())

    datasources = []
    for name in ds_configs.loaded_structures:
        LOG.debug('creating datasource  %s', name)
        datasource_config = ds_configs.loaded_structures[name]
        try:
            service = json_ingester.JsonIngester(
                name, datasource_config, exec_manager)
            if service:
                # config w/o table used to define exec_api endpoint
                # no service created in that case
                bus.register_service(service)
                datasources.append(service)
        except Exception:
            LOG.exception(
                "Failed to create JsonIngester service {}.".format(name))
    return datasources


def create_datasources(bus):
    """Create and register datasource services ."""
    if cfg.CONF.delete_missing_driver_datasources:
        # congress server started with --delete-missing-driver-datasources
        bus.delete_missing_driver_datasources()

    # create regular (table) data sources
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
                          "--delete-missing-driver-datasources option to "
                          "clean up stale datasources in DB.")
            sys.exit(1)
        except Exception:
            LOG.exception("datasource %s creation failed. %s service may not "
                          "be running.", ds.name, ds.driver)

    # create json_ingester data sources
    if cfg.CONF.json_ingester.enable:
        create_json_ingester_datasources(bus)

    return services
