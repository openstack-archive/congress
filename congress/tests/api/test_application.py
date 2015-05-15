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

import json

import mock
from oslo_config import cfg
import webob

from congress.api import application
from congress.api import webservice
from congress.tests import base


class TestApiApplication(base.TestCase):

    def setUp(self):
        super(TestApiApplication, self).setUp()
        cfg.CONF.set_override('auth_strategy', 'noauth')

    def _check_data_model_exc_response(self, method, exc, response):
        self.assertEqual(response.status_code, exc.http_status_code,
                         'Correct %s HTTP error status' % method)
        body = json.loads(response.body)
        self.assertEqual(body['error']['error_code'], exc.error_code,
                         'Correct %s error code in response body' % method)
        self.assertEqual(
            body['error']['message'], exc.description,
            'Correct %s description in response body' % method)
        self.assertEqual(body['error']['error_data'], exc.data,
                         'Correct %s error data in response body' % method)

    def test_data_model_exception(self):
        exc = webservice.DataModelException(1, "error1", [1, {'a': 'b'}], 409)
        model = webservice.SimpleDataModel("test")
        for method in [m for m in dir(model) if "_item" in m]:
            setattr(model, method, mock.Mock(side_effect=exc))

        resource_mgr = application.ResourceManager()
        app = application.ApiApplication(resource_mgr)

        collection_handler = webservice.CollectionHandler(r'/c', model)
        resource_mgr.register_handler(collection_handler)
        for method in ['GET', 'POST']:
            request = webob.Request.blank('/c', body='{}', method=method)
            response = app(request)
            self._check_data_model_exc_response(method, exc, response)

        element_handler = webservice.ElementHandler(r'/e', model)
        resource_mgr.register_handler(element_handler)
        for method in ['GET', 'PUT', 'PATCH', 'DELETE']:
            request = webob.Request.blank('/e', body='{}', method=method)
            response = app(request)
            self._check_data_model_exc_response(method, exc, response)

    def _check_base_exc_response(self, method, response, expected_status):
        self.assertEqual(response.status_code, expected_status,
                         'Correct %s HTTP error status' % method)
        body = json.loads(response.body)
        self.assertEqual(body['error']['error_code'], expected_status,
                         'Correct %s error code in response body' % method)
        if expected_status == 500:
            description = "Internal server error"
        elif expected_status == 404:
            description = "The resouce could not be found."
        else:
            self.fail("Unsupported expected_status value.")

        self.assertEqual(
            body['error']['message'], description,
            'Correct %s description in response body' % method)

    def test__exception(self):
        model = webservice.SimpleDataModel("test")
        for method in [m for m in dir(model) if "_item" in m]:
            setattr(model, method, mock.Mock(side_effect=Exception()))

        resource_mgr = application.ResourceManager()
        app = application.ApiApplication(resource_mgr)

        collection_handler = webservice.CollectionHandler(r'/c', model)
        resource_mgr.register_handler(collection_handler)
        for method in ['GET', 'POST']:
            request = webob.Request.blank('/c', body='{}', method=method)
            response = app(request)
            self._check_base_exc_response(method, response, 500)

        element_handler = webservice.ElementHandler(r'/e', model)
        resource_mgr.register_handler(element_handler)
        for method in ['GET', 'PUT', 'PATCH', 'DELETE']:
            request = webob.Request.blank('/e', body='{}', method=method)
            response = app(request)
            self._check_base_exc_response(method, response, 500)

            # Tests that making a request to an invalid url returns 404.
            request = webob.Request.blank('/invalid', body='{}', method=method)
            response = app(request)
            self._check_base_exc_response(method, response, 404)
