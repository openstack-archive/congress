# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2011 OpenStack Foundation
# Copyright 2013 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from novaclient.tests import fakes
from novaclient.tests.v1_1.fakes import FakeHTTPClient
from novaclient.v1_1 import client


class NovaFakeClient(fakes.FakeClient, client.Client):

    def __init__(self, *args, **kwargs):
        #super.__init__(*args, **kwargs)

        client.Client.__init__(self, 'username', 'password',
                               'project_id', 'auth_url',
                               extensions=kwargs.get('extensions'))
        self.client = NovaFakeHTTPClient(**kwargs)


class NovaFakeHTTPClient(FakeHTTPClient):

    def __init__(self, **kwargs):
        FakeHTTPClient.__init__(self, **kwargs)

    def get_servers(self, **kw):
        return (200, {}, {"servers": [
            {'id': 1234, 'name': 'sample-server'},
            {'id': 5678, 'name': 'sample-server2'}
        ]})

    def get_servers_detail(self, **kw):
        response = {"servers": [
            {
                "id": 1234,
                "name": "sample-server",
                "image": {
                        "id": 2,
                        "name": "sample image",
                },
                "flavor": {
                    "id": 1,
                    "name": "256 MB Server",
                },
                "hostId": "e4d909c290d0fb1ca068ffaddf22cbd0",
                "status": "BUILD",
                "progress": 60,
                "tenant_id": "4ffc664c198e435e9853f2538fbcd7a7",
                "user_id": "4c7057c23b9c46c5ac21-b91bd8b5462b",
                "addresses": {
                    "public": [{
                        "version": 4,
                        "addr": "1.2.3.4",
                    }, {
                        "version": 4,
                        "addr": "5.6.7.8",
                    }],
                    "private": [{
                        "version": 4,
                        "addr": "10.11.12.13",
                    }],
                },
                "metadata": {
                    "Server Label": "Web Head 1",
                    "Image Version": "2.1"
                },
                "OS-EXT-SRV-ATTR:host": "computenode1",
                "security_groups": [{
                    'id': 1, 'name': 'securitygroup1',
                    'description': 'FAKE_SECURITY_GROUP',
                    'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7'
                }],
                "OS-EXT-MOD:some_thing": "mod_some_thing_value",
            },
            {
                "id": 5678,
                "name": "sample-server2",
                "image": {
                    "id": 2,
                    "name": "sample image",
                },
                "flavor": {
                    "id": 1,
                    "name": "256 MB Server",
                },
                "hostId": "9e107d9d372bb6826bd81d3542a419d6",
                "status": "ACTIVE",
                "tenant_id": "4ffc664c198e435e9853f2538fbcd7a7",
                "user_id": "4c7057c23b9c46c5ac21-b91bd8b5462b",
                "addresses": {
                    "public": [{
                        "version": 4,
                        "addr": "4.5.6.7",
                    }, {
                        "version": 4,
                        "addr": "5.6.9.8",
                    }],
                    "private": [{
                        "version": 4,
                        "addr": "10.13.12.13",
                    }],
                },
                "metadata": {
                    "Server Label": "DB 1"
                },
                "OS-EXT-SRV-ATTR:host": "computenode2",
                "security_groups": [{
                    'id': 1, 'name': 'securitygroup1',
                    'description': 'FAKE_SECURITY_GROUP',
                    'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7'
                }, {
                    'id': 2, 'name': 'securitygroup2',
                    'description': 'ANOTHER_FAKE_SECURITY_GROUP',
                    'tenant_id': '4ffc664c198e435e9853f2538fbcd7a7'
                }],
            },
            {
                "id": 9012,
                "name": "sample-server3",
                "image": {
                    "id": 2,
                    "name": "sample image",
                },
                "flavor": {
                    "id": 1,
                    "name": "256 MB Server",
                },
                "hostId": "9e107d9d372bb6826bd81d3542a419d6",
                "status": "ACTIVE",
                "tenant_id": "4ffc664c198e435e9853f2538fbcd7a7",
                "user_id": "4c7057c23b9c46c5ac21-b91bd8b5462b",
                "addresses": {
                    "public": [{
                        "version": 4,
                        "addr": "4.5.6.7",
                    }, {
                        "version": 4,
                        "addr": "5.6.9.8",
                    }],
                    "private": [{
                        "version": 4,
                        "addr": "10.13.12.13",
                    }],
                },
                "metadata": {
                    "Server Label": "DB 1"
                }
            }
        ]}
        return (200, {}, response)

    def get_flavors_detail(self, **kw):
        flavors = {'flavors': [
            {'id': 1, 'name': '256 MB Server', 'ram': 256, 'disk': 10,
             'vcpus': 1, 'OS-FLV-EXT-DATA:ephemeral': 10,
             'os-flavor-access:is_public': True, 'rxtx_factor': 1.0,
             'links': {}},
            {'id': 2, 'name': '512 MB Server', 'ram': 512, 'disk': 20,
             'vcpus': 2, 'OS-FLV-EXT-DATA:ephemeral': 20,
             'os-flavor-access:is_public': False, 'rxtx_factor': 1.0,
             'links': {}},
            {'id': 4, 'name': '1024 MB Server', 'ram': 1024, 'disk': 10,
             'vcpus': 3, 'OS-FLV-EXT-DATA:ephemeral': 10,
             'os-flavor-access:is_public': True, 'rxtx_factor': 2.0,
             'links': {}},
            {'id': 3, 'name': '128 MB Server', 'ram': 128, 'disk': 0,
             'vcpus': 4, 'OS-FLV-EXT-DATA:ephemeral': 0,
             'os-flavor-access:is_public': True, 'rxtx_factor': 3.0,
             'links': {}}
        ]}

        return (200, {}, flavors)

    def get_os_hosts(self, **kw):
        zone = kw.get('zone', 'nova1')
        return (200, {}, {'hosts':
                          [{'host_name': 'host1',
                            'service': 'nova-compute',
                            'zone': zone},
                           {'host_name': 'host2',
                            'service': 'nova-cert',
                            'zone': zone}]})
