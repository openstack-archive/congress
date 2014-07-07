#!/usr/bin/env python
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

import traceback
import webob
import webob.dec

from openstack.common.gettextutils import _

from api.webservice import CollectionHandler
from api.webservice import ElementHandler
from api.webservice import INTERNAL_ERROR_RESPONSE
from api.webservice import NOT_SUPPORTED_RESPONSE
from api.webservice import SimpleDataModel
from congress.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class ApiApplication(object):
    """An API web application that binds REST resources to a wsgi server.

    This indirection between the wsgi server and REST resources facilitates
    binding the same resource tree to multiple endpoints (e.g. HTTP/HTTPS).
    """

    def __init__(self, resource_mgr):
        self.resource_mgr = resource_mgr

    @webob.dec.wsgify(RequestClass=webob.Request)
    def __call__(self, request):
        try:
            handler = self.resource_mgr.get_handler(request)
            if handler:
                msg = _("Handling request '%(meth)s %(path)s' with %(hndlr)s")
                LOG.debug(msg % {"meth": request.method, "path": request.path,
                                 "hndlr": str(handler)})
                response = handler.handle_request(request)
            else:
                response = NOT_SUPPORTED_RESPONSE
        except Exception as e:
            msg = _("Exception caught for request: %s")
            LOG.error(msg % (request))
            LOG.error(traceback.format_exc(e))
            response = INTERNAL_ERROR_RESPONSE
        return response


class ResourceManager(object):
    """A container for REST API resources and underlying data models.

    This container is meant to be called from one or more wsgi servers/ports.

    Attributes:
        handlers: An array of API resource handlers for registered resources.
        models: A dict of {model_id: data_model} for registered data models.
    """

    def __init__(self):
        self.handlers = []
        self.models = {}

    def register_handler(self, handler, search_index=None):
        """Register a new resource handler.

        Args:
            handler: The resource handler to register.
            search_index: Priority of resource handler to resolve cases where
                a request matches multiple handlers.
        """
        if search_index is not None:
            self.handlers.insert(search_index, handler)
        else:
            self.handlers.append(handler)
        msg = _("Registered API handler: %s") % (handler)
        LOG.info(msg)

    def get_handler(self, request):
        """Find a handler for a REST request.

        Args:
           request: A webob request object.

        Returns:
            A handler instance or None.
        """
        for h in self.handlers:
            if h.handles_request(request):
                return h
        return None

    def register_model(self, model_id, model):
        """Register a data model.

        Args:
            model_id: A unique ID for the model.
            model: The model to register.
        """
        if model_id in self.models:
            raise KeyError("Model '%s' already registered" % model_id)
        self.models[model_id] = model

    def get_model(self, model_id):
        return self.models.get(model_id)


def initialize_resources(resource_mgr):
    """Bootstrap data models and handlers for the current API definition."""
    policies = SimpleDataModel('policies')
    resource_mgr.register_model('policies', policies)
    #system policy is always present
    policies.add_item({'id': 'system', 'owner': 'system'}, 'system')

    policy_collection_handler = CollectionHandler(
        r'/policies', policies, allow_create=False)
    resource_mgr.register_handler(policy_collection_handler)
    policy_element_handler = ElementHandler(
        r'/policies/(?P<policy_id>[^/]+)', policies, policy_collection_handler,
        allow_replace=False, allow_update=False, allow_delete=False)
    resource_mgr.register_handler(policy_element_handler)

    policy_rules = SimpleDataModel('rules')
    resource_mgr.register_model('rules', policy_rules)
    rule_collection_handler = CollectionHandler(
        r'/policies/(?P<policy_id>[^/]+)/rules', policy_rules, "{policy_id}")
    resource_mgr.register_handler(rule_collection_handler)
    rule_element_handler = ElementHandler(
        r'/policies/(?P<policy_id>[^/]+)/rules/(?P<rule_id>[^/]+)',
        policy_rules, "{policy_id}")
    resource_mgr.register_handler(rule_element_handler)

    data_sources = SimpleDataModel('data_sources')
    resource_mgr.register_model('data_sources', data_sources)
    ds_collection_handler = CollectionHandler(r'/data-sources', data_sources)
    resource_mgr.register_handler(ds_collection_handler)
    ds_path = r'/data-sources/(?P<ds_id>[^/]+)'
    ds_element_handler = ElementHandler(ds_path, data_sources)
    resource_mgr.register_handler(ds_element_handler)

    # TODO(pballand) register models for schema and status
    #schema_path = "%s/schema" % ds_path
    #schema_element_handler = ElementHandler(schema_path, XXX,
    #                                        "schema")
    #resource_mgr.register_handler(schema_element_handler)
    #status_path = "%s/status" % ds_path
    #status_element_handler = ElementHandler(status_path, XXX,
    #                                        "status")
    #resource_mgr.register_handler(status_element_handler)

    tables = SimpleDataModel('tables')
    resource_mgr.register_model('tables', tables)
    tables_path = "%s/tables" % ds_path
    table_collection_handler = CollectionHandler(tables_path, tables)
    resource_mgr.register_handler(table_collection_handler)
    table_path = "%s/(?P<table_id>[^/]+)" % tables_path
    table_element_handler = ElementHandler(table_path, tables)
    resource_mgr.register_handler(table_element_handler)

    table_rows = SimpleDataModel('table_rows')
    resource_mgr.register_model('table_rows', table_rows)
    rows_path = "%s/rows" % table_path
    row_collection_handler = CollectionHandler(rows_path, table_rows)
    resource_mgr.register_handler(row_collection_handler)
    row_path = "%s/(?P<row_id>[^/]+)" % rows_path
    row_element_handler = ElementHandler(row_path, table_rows)
    resource_mgr.register_handler(row_element_handler)
