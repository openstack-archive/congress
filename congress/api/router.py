# Copyright (c) 2015 OpenStack Foundation
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

from congress.api.webservice import CollectionHandler
from congress.api.webservice import ElementHandler


class APIRouterV1(object):

    def __init__(self, resource_mgr, cage):
        """Bootstrap data models and handlers for the API definition."""
        policies = cage.service_object('api-policy')
        resource_mgr.register_model('policies', policies)

        policy_collection_handler = CollectionHandler(r'/v1/policies',
                                                      policies)
        resource_mgr.register_handler(policy_collection_handler)
        policy_path = r'/v1/policies/(?P<policy_id>[^/]+)'
        policy_element_handler = ElementHandler(policy_path, policies,
                                                policy_collection_handler,
                                                allow_update=False,
                                                allow_replace=False)
        resource_mgr.register_handler(policy_element_handler)

        policy_rules = cage.service_object('api-rule')
        resource_mgr.register_model('rules', policy_rules)
        rule_collection_handler = CollectionHandler(
            r'/v1/policies/(?P<policy_id>[^/]+)/rules',
            policy_rules,
            "{policy_id}")
        resource_mgr.register_handler(rule_collection_handler)
        rule_path = (r'/v1/policies/(?P<policy_id>[^/]+)' +
                     r'/rules/(?P<rule_id>[^/]+)')
        rule_element_handler = ElementHandler(rule_path, policy_rules,
                                              "{policy_id}")
        resource_mgr.register_handler(rule_element_handler)

        # Setup /v1/data-sources
        data_sources = cage.service_object('api-datasource')
        resource_mgr.register_model('data_sources', data_sources)
        ds_collection_handler = CollectionHandler(r'/v1/data-sources',
                                                  data_sources)
        resource_mgr.register_handler(ds_collection_handler)

        # Setup /v1/data-sources/<ds_id>
        ds_path = r'/v1/data-sources/(?P<ds_id>[^/]+)'
        ds_element_handler = ElementHandler(ds_path, data_sources)
        resource_mgr.register_handler(ds_element_handler)

        # Setup /v1/data-sources/<ds_id>/schema
        schema = cage.service_object('api-schema')
        schema_path = "%s/schema" % ds_path
        schema_element_handler = ElementHandler(schema_path, schema)
        resource_mgr.register_handler(schema_element_handler)

        # Setup /v1/data-sources/<ds_id>/tables/<table_id>/spec
        table_schema_path = "%s/tables/(?P<table_id>[^/]+)/spec" % ds_path
        table_schema_element_handler = ElementHandler(table_schema_path,
                                                      schema)
        resource_mgr.register_handler(table_schema_element_handler)

        # Setup status handlers
        statuses = cage.service_object('api-status')
        ds_status_path = "%s/status" % ds_path
        ds_status_element_handler = ElementHandler(ds_status_path, statuses)
        resource_mgr.register_handler(ds_status_element_handler)
        policy_status_path = "%s/status" % policy_path
        policy_status_element_handler = ElementHandler(policy_status_path,
                                                       statuses)
        resource_mgr.register_handler(policy_status_element_handler)
        rule_status_path = "%s/status" % rule_path
        rule_status_element_handler = ElementHandler(rule_status_path,
                                                     statuses)
        resource_mgr.register_handler(rule_status_element_handler)

        tables = cage.service_object('api-table')
        resource_mgr.register_model('tables', tables)
        tables_path = "(%s|%s)/tables" % (ds_path, policy_path)
        table_collection_handler = CollectionHandler(tables_path, tables)
        resource_mgr.register_handler(table_collection_handler)
        table_path = "%s/(?P<table_id>[^/]+)" % tables_path
        table_element_handler = ElementHandler(table_path, tables)
        resource_mgr.register_handler(table_element_handler)

        table_rows = cage.service_object('api-row')
        resource_mgr.register_model('table_rows', table_rows)
        rows_path = "%s/rows" % table_path
        row_collection_handler = CollectionHandler(rows_path, table_rows)
        resource_mgr.register_handler(row_collection_handler)
        row_path = "%s/(?P<row_id>[^/]+)" % rows_path
        row_element_handler = ElementHandler(row_path, table_rows)
        resource_mgr.register_handler(row_element_handler)

        # Setup /v1/system/datasource-drivers
        system = cage.service_object('api-system')
        resource_mgr.register_model('system', system)
        # NOTE(arosen): start url out with datasource-drivers since we don't
        # yet implement /v1/system/ yet.
        system_collection_handler = CollectionHandler(r'/v1/system/drivers',
                                                      system)
        resource_mgr.register_handler(system_collection_handler)

        # Setup /v1/system/datasource-drivers/<driver_id>
        driver_path = r'/v1/system/drivers/(?P<driver_id>[^/]+)'
        driver_element_handler = ElementHandler(driver_path, system)
        resource_mgr.register_handler(driver_element_handler)
