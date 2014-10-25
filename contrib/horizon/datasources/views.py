# Copyright 2014 VMware.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tables

from openstack_dashboard.api import congress

from openstack_dashboard.dashboards.admin.datasources \
    import tables as datasources_tables


class IndexView(tables.MultiTableView):
    """List plugin and policy defined data."""
    table_classes = (datasources_tables.DataSourcesTablesTable,
                     datasources_tables.PoliciesTablesTable,)
    template_name = 'admin/datasources/index.html'

    def get_datasources_tables_data(self):
        # TODO(jwy): Return list of data sources.
        return []

    def get_policies_tables_data(self):
        policies = congress.policies_list(self.request)
        policies_tables = []

        for policy in policies:
            policy.set_id_as_name_if_empty()
            policy_name = policy['name']
            policy_tables = congress.policy_tables_list(self.request,
                                                        policy_name)
            for pt in policy_tables:
                pt.set_id_as_name_if_empty()
                pt.set_policy_details(policy)
            policies_tables.extend(policy_tables)

        # Group by policy name.
        return sorted(policies_tables,
                      cmp=lambda x, y: cmp(x['policy_name'], y['policy_name']))


class DetailView(tables.DataTableView):
    """List details about and rows from a data source (plugin or policy)."""
    table_class = datasources_tables.DataSourceTableRowsTable
    template_name = 'admin/datasources/detail.html'

    def get_data(self):
        datasource_name = self.kwargs['datasource_name']
        table_name = self.kwargs.get('policy_table_name')
        if table_name:
            try:
                rows = congress.policy_rows_list(self.request, datasource_name,
                                                 table_name)
            except Exception:
                redirect = reverse('horizon:admin:datasources:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve policy table rows.'),
                                  redirect=redirect)
        else:
            table_name = self.kwargs['datasource_table_name']
            # TODO(jwy): Get rows for plugin data source table.
            rows = []
        return rows

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        datasource_name = kwargs['datasource_name']
        table_name = kwargs.get('policy_table_name')
        if table_name:
            try:
                datasource_table = congress.policy_table_get(
                    self.request, datasource_name, table_name)
            except Exception:
                redirect = reverse('horizon:admin:policies:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve policy table.'),
                                  redirect=redirect)
        else:
            table_name = kwargs['datasource_table_name']
            # TODO(jwy): Get table for plugin data source.
            datasource_table = None
        datasource_table.set_id_as_name_if_empty()
        context['datasource_table'] = datasource_table
        return context
