# Copyright 2015 Huawei.
# All Rights Reserved.
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

import copy
import json
import os

from six.moves import http_client
import webob
import webob.dec

from congress.api import webservice


VERSIONS = {
    "v1": {
        "id": "v1",
        "status": "CURRENT",
        "updated": "2013-08-12T17:42:13Z",
        "links": [
            {
                "rel": "describedby",
                "type": "text/html",
                "href": "http://congress.readthedocs.org/",
            },
        ],
    },
}


def _get_view_builder(request):
    base_url = request.application_url
    return ViewBuilder(base_url)


class ViewBuilder(object):

    def __init__(self, base_url):
        """:param base_url: url of the root wsgi application."""
        self.base_url = base_url

    def build_choices(self, versions, request):
        version_objs = []
        for version in sorted(versions.keys()):
            version = versions[version]
            version_objs.append({
                "id": version['id'],
                "status": version['status'],
                "updated": version['updated'],
                "links": self._build_links(version, request.path),
                })

        return dict(choices=version_objs)

    def build_versions(self, versions):
        version_objs = []
        for version in sorted(versions.keys()):
            version = versions[version]
            version_objs.append({
                "id": version['id'],
                "status": version['status'],
                "updated": version['updated'],
                "links": self._build_links(version),
            })

        return dict(versions=version_objs)

    def build_version(self, version):
        reval = copy.deepcopy(version)
        reval['links'].insert(0, {
            "rel": "self",
            "href": self.base_url.rstrip('/') + '/',
        })
        return dict(version=reval)

    def _build_links(self, version_data, path=None):
        """Generate a container of links that refer to the provided version."""
        href = self._generate_href(version_data['id'], path)

        links = [
            {
                "rel": "self",
                "href": href,
            },
        ]

        return links

    def _generate_href(self, version, path=None):
        """Create an url that refers to a specific version."""
        if path:
            path = path.strip('/')
            return os.path.join(self.base_url, version, path)
        else:
            return os.path.join(self.base_url, version) + '/'


class Versions(object):

    @classmethod
    def factory(cls, global_config, **local_config):
        return cls()

    @webob.dec.wsgify(RequestClass=webob.Request)
    def __call__(self, request):
        """Respond to a request for all Congress API versions."""

        builder = _get_view_builder(request)
        if request.path == '/':
            body = builder.build_versions(VERSIONS)
            status = http_client.OK
        else:
            body = builder.build_choices(VERSIONS, request)
            status = http_client.MULTIPLE_CHOICES

        return webob.Response(body="%s\n" % json.dumps(body),
                              status=status,
                              content_type='application/json')


class VersionV1Handler(webservice.AbstractApiHandler):

    def handle_request(self, request):
        builder = _get_view_builder(request)
        body = builder.build_version(VERSIONS['v1'])
        return webob.Response(body="%s\n" % json.dumps(body),
                              status=http_client.OK,
                              content_type='application/json')
