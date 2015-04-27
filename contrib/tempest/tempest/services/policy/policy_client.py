# Copyright 2012 OpenStack Foundation
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

from congressclient.v1 import client
from keystoneclient.auth.identity import v2
from keystoneclient import session
from tempest import config

CONF = config.CONF


class PolicyClient(object):
    def __init__(self, auth_provider):
        auth = v2.Password(auth_url=CONF.identity.uri,
                           username=auth_provider.username,
                           password=auth_provider.password,
                           tenant_name=auth_provider.tenant_name)
        sess = session.Session(auth=auth)
        self.congress_client = client.Client(session=sess,
                                             auth=None,
                                             interface='publicURL',
                                             service_type='policy',
                                             region_name=CONF.identity.region)

    def __getattr__(self, name):
        # NOTE(arosen): test reimplements the client for each project. Though
        # for now there isn't any real benefit to doing that for congress so
        # just plum into it directly.
        return getattr(self.congress_client, name)
