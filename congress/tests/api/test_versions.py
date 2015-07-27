# Copyright (c) 2015 Huawei, Inc. All rights reserved.
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

import httplib
import json

import webob

from congress.tests import base
from congress.tests import fake_wsgi


class TestVersions(base.TestCase):

    def setUp(self):
        super(TestVersions, self).setUp()

    def test_versions_list(self):
        req = webob.Request.blank('/')
        req.accept = "application/json"
        res = req.get_response(fake_wsgi.wsgi_app())
        self.assertEqual(httplib.OK, res.status_int)
        self.assertEqual("application/json", res.content_type)
        versions = json.loads(res.body)
        expected = {
            "versions": [{
                "status": "CURRENT",
                "updated": "2013-08-12T17:42:13Z",
                "id": "v1",
                "links": [{
                    "href": "http://localhost/v1/",
                    "rel": "self"
                }]
            }]
        }
        self.assertEqual(expected, versions)

    def test_versions_choices(self):
        req = webob.Request.blank('/fake')
        req.accept = "application/json"
        res = req.get_response(fake_wsgi.wsgi_app())
        self.assertEqual(httplib.MULTIPLE_CHOICES, res.status_int)
        self.assertEqual("application/json", res.content_type)
        versions = json.loads(res.body)
        expected = {
            "choices": [{
                "status": "CURRENT",
                "updated": "2013-08-12T17:42:13Z",
                "id": "v1",
                "links": [{
                    "href": "http://localhost/v1/fake",
                    "rel": "self"
                }]
            }]
        }
        self.assertEqual(expected, versions)

    def test_version_v1_show(self):
        req = webob.Request.blank('/v1')
        req.accept = "application/json"
        res = req.get_response(fake_wsgi.wsgi_app())
        self.assertEqual(httplib.OK, res.status_int)
        self.assertEqual("application/json", res.content_type)
        versions = json.loads(res.body)
        expected = {
            "version": {
                "status": "CURRENT",
                "updated": "2013-08-12T17:42:13Z",
                "id": "v1",
                "links": [{
                    "href": "http://localhost/v1/",
                    "rel": "self"
                }, {
                    "rel": "describedby",
                    "type": "text/html",
                    "href": "http://congress.readthedocs.org/",
                }]
            }
        }
        self.assertEqual(expected, versions)

    def test_version_v1_multiple_path(self):
        req = webob.Request.blank('/v1')
        req.accept = "application/json"
        res = req.get_response(fake_wsgi.wsgi_app())
        self.assertEqual(httplib.OK, res.status_int)
        self.assertEqual("application/json", res.content_type)

        req_ = webob.Request.blank('/v1/')
        req_.accept = "application/json"
        res_ = req_.get_response(fake_wsgi.wsgi_app())
        self.assertEqual(httplib.OK, res_.status_int)
        self.assertEqual("application/json", res_.content_type)

        self.assertEqual(json.loads(res.body), json.loads(res_.body))

    def test_version_v1_not_found(self):
        req = webob.Request.blank('/v1/fake')
        req.accept = "application/json"
        res = req.get_response(fake_wsgi.wsgi_app())
        self.assertEqual(httplib.NOT_FOUND, res.status_int)
        self.assertEqual("application/json", res.content_type)
