# Copyright 2014 VMware.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from congressclient.v1 import client as congress_client
import keystoneclient
from openstack_dashboard.api import base

LOG = logging.getLogger(__name__)


def _set_id_as_name_if_empty(apidict, length=8):
    try:
        if not apidict._apidict.get('name'):
            id = apidict._apidict['id']
            if length:
                id = id[:length]
                apidict._apidict['name'] = '(%s)' % id
            else:
                apidict._apidict['name'] = id
    except KeyError:
        pass


class PolicyAPIDictWrapper(base.APIDictWrapper):
    def set_id_as_name_if_empty(self):
        # Use the full id as the name.
        _set_id_as_name_if_empty(self, length=0)

    def set_id_if_empty(self, id):
        if not self._apidict.get('id'):
            self._apidict['id'] = id

    def set(self, key, value):
        self._apidict[key] = value


class PolicyTable(PolicyAPIDictWrapper):
    """Wrapper for a Congress policy's data table."""
    def set_policy_details(self, policy):
        self._apidict['policy_name'] = policy['name']
        self._apidict['policy_owner_id'] = policy['owner_id']


def congressclient(request):
    """Instantiate Congress client."""
    auth_url = base.url_for(request, 'identity')
    user = request.user
    auth = keystoneclient.auth.identity.v2.Token(auth_url, user.token.id,
                                                 tenant_id=user.tenant_id,
                                                 tenant_name=user.tenant_name)
    session = keystoneclient.session.Session(auth=auth)
    region_name = user.services_region

    kwargs = {
        'session': session,
        'auth': None,
        'interface': 'publicURL',
        'service_type': 'policy',
        'region_name': region_name
    }
    return congress_client.Client(**kwargs)


def policies_list(request):
    """List all policies."""
    client = congressclient(request)
    policies_list = client.list_policy()
    results = policies_list['results']
    return [PolicyAPIDictWrapper(p) for p in results]


def policy_get(request, policy_name):
    """Get a policy by name."""
    # TODO(jwy): Need API in congress_client to retrieve policy by name.
    policies = policies_list(request)
    for p in policies:
        if p['id'] == policy_name:
            return p
    return PolicyAPIDictWrapper({})


def policy_rules_list(request, policy_name):
    """List all rules in a policy, given by name."""
    client = congressclient(request)
    policy_rules_list = client.list_policy_rules(policy_name)
    results = policy_rules_list['results']
    return [PolicyAPIDictWrapper(r) for r in results]


def policy_tables_list(request, policy_name):
    """List all data tables in a policy, given by name."""
    client = congressclient(request)
    policy_tables_list = client.list_policy_tables(policy_name)
    results = policy_tables_list['results']
    return [PolicyTable(t) for t in results]


def policy_table_get(request, policy_name, table_name):
    """Get a policy table in a policy, given by name."""
    # TODO(jwy): Need API in congress_client to retrieve policy table by name.
    policy_tables = policy_tables_list(request, policy_name)
    for pt in policy_tables:
        if pt['id'] == table_name:
            return pt
    return PolicyTable({})


def policy_rows_list(request, policy_name, table_name):
    """List all rows in a policy's data table, given by name."""
    client = congressclient(request)
    policy_rows_list = client.list_policy_rows(policy_name, table_name)
    results = policy_rows_list['results']

    policy_rows = []
    # Policy table rows currently don't have ids. However, the DataTable object
    # requires an id for the table to get rendered properly. Otherwise, the
    # same contents are displayed for every row in the table. Assign the rows
    # ids here.
    id = 0
    for row in results:
        new_row = PolicyAPIDictWrapper(row)
        new_row.set_id_if_empty(id)
        id += 1
        policy_rows.append(new_row)
    return policy_rows


def datasources_list(request):
    client = congressclient(request)
    datasources_list = client.list_datasources()
    datasources = datasources_list['results']
    return [PolicyAPIDictWrapper(t) for t in datasources]


def datasources_tables_list(request, datasource_name):
    client = congressclient(request)
    datasource_table_list = client.list_datasource_tables(datasource_name)
    datasource_table_rows = datasource_table_list['results']

    return [PolicyAPIDictWrapper(t) for t in datasource_table_rows]


def datasources_rows_list(request, datasource_name, table_name):
    client = congressclient(request)
    datasource_rows_list = client.list_datasource_rows(
        datasource_name, table_name)
    results = datasource_rows_list['results']
    datasource_rows = []
    id = 0
    for row in results:
        new_row = PolicyAPIDictWrapper(row)
        new_row.set_id_if_empty(id)
        id += 1
        datasource_rows.append(new_row)
    return datasource_rows
