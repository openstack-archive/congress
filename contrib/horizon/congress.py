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

LITERALS_SEPARATOR = '), '
RULE_SEPARATOR = ':-'
PLUGIN_TABLE_SEPARATOR = ':'

LOG = logging.getLogger(__name__)


def _set_id_as_name_if_empty(apidict, length=0):
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
        _set_id_as_name_if_empty(self)

    def set_id_if_empty(self, id):
        apidict_id = self._apidict.get('id')
        if not apidict_id or apidict_id == "None":
            self._apidict['id'] = id

    def set_value(self, key, value):
        self._apidict[key] = value

    def delete_by_key(self, key):
        del self._apidict[key]


class PolicyRule(PolicyAPIDictWrapper):
    """Wrapper for a Congress policy's rule."""
    def set_id_as_name_if_empty(self):
        # Shorten UUID.
        _set_id_as_name_if_empty(self, length=8)


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
    policies = []
    for p in results:
        policy = PolicyAPIDictWrapper(p)
        # Policies currently have a name but not necessarily a non-"None" id.
        # Use the name to identify the policy, needed to differentiate them in
        # DataTables.
        policy.set_id_if_empty(policy.get('name'))
        policies.append(policy)
    return policies


def policy_get(request, policy_name):
    """Get a policy by name."""
    # TODO(jwy): Use congress.show_policy() once system policies have unique
    # IDs.
    policies = policies_list(request)
    for p in policies:
        if p['name'] == policy_name:
            return p


def policy_rules_list(request, policy_name):
    """List all rules in a policy, given by name."""
    client = congressclient(request)
    policy_rules_list = client.list_policy_rules(policy_name)
    results = policy_rules_list['results']
    return [PolicyRule(r) for r in results]


def policy_tables_list(request, policy_name):
    """List all data tables in a policy, given by name."""
    client = congressclient(request)
    policy_tables_list = client.list_policy_tables(policy_name)
    results = policy_tables_list['results']
    return [PolicyTable(t) for t in results]


def policy_table_get(request, policy_name, table_name):
    """Get a policy table in a policy, given by name."""
    client = congressclient(request)
    return client.show_policy_table(policy_name, table_name)


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


def policy_table_schema_get(request, policy_name, table_name):
    """Get the schema for a policy table, based on the first matching rule."""
    column_names = []
    rules = policy_rules_list(request, policy_name)
    # There might be multiple rules that use the same name in the head. Pick
    # the first matching one, which is what the policy engine currently does.
    for rule in rules:
        rule_def = rule['rule']
        head, _ = rule_def.split(' %s ' % RULE_SEPARATOR)
        if head.startswith('%s(' % table_name):
            start = head.index('(') + 1
            end = head.index(')')
            column_names = head[start:end].split(', ')
            break

    schema = {'table_id': table_name}
    schema['columns'] = [{'name': name, 'description': None}
                         for name in column_names]
    return schema


def datasources_list(request):
    """List all the data sources."""
    client = congressclient(request)
    datasources_list = client.list_datasources()
    datasources = datasources_list['results']
    return [PolicyAPIDictWrapper(d) for d in datasources]


def datasource_get(request, datasource_id):
    """Get a data source by id."""
    # TODO(jwy): Need API in congress_client to retrieve data source by id.
    datasources = datasources_list(request)
    for d in datasources:
        if d['id'] == datasource_id:
            return d


def datasource_get_by_name(request, datasource_name):
    """Get a data source by name."""
    datasources = datasources_list(request)
    for d in datasources:
        if d['name'] == datasource_name:
            return d


def datasource_tables_list(request, datasource_id):
    """List all data tables in a data source, given by id."""
    client = congressclient(request)
    datasource_tables_list = client.list_datasource_tables(datasource_id)
    results = datasource_tables_list['results']
    return [PolicyAPIDictWrapper(t) for t in results]


def datasource_rows_list(request, datasource_id, table_name):
    """List all rows in a data source's data table, given by id."""
    client = congressclient(request)
    datasource_rows_list = client.list_datasource_rows(datasource_id,
                                                       table_name)
    results = datasource_rows_list['results']
    datasource_rows = []
    id = 0
    for row in results:
        new_row = PolicyAPIDictWrapper(row)
        new_row.set_id_if_empty(id)
        id += 1
        datasource_rows.append(new_row)
    return datasource_rows


def datasource_table_schema_get(request, datasource_id, table_name):
    """Get the schema for a data source table."""
    client = congressclient(request)
    return client.show_datasource_table_schema(datasource_id, table_name)
