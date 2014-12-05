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
import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import tables
from openstack_dashboard.api import congress
from openstack_dashboard.dashboards.admin.datasources \
    import tables as datasources_tables

logger = logging.getLogger(__name__)


class IndexView(tables.MultiTableView):
    """List plugin and policy defined data."""
    table_classes = (datasources_tables.DataSourcesTablesTable,
                     datasources_tables.PoliciesTablesTable,)
    template_name = 'admin/datasources/index.html'

    def get_datasources_tables_data(self):
        try:
            ds1 = congress.datasources_list(self.request)
        except Exception:
            redirect = reverse('horizon:admin:datasources:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve datasources list.'),
                              redirect=redirect)
        ds_temp = []

        for d1 in ds1:
            s = d1['id']
            owner_id = d1['owner_id']
            try:
                ds = congress.datasources_tables_list(self.request, s)
                for d in ds:
                    d.set('datasource', s)
                    d.set('owner_id', owner_id)
                    d.set_id_as_name_if_empty()
                    ds_temp.append(d)
            except Exception:
                redirect = reverse('horizon:admin:datasources:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve datasource tables,'),
                                  redirect=redirect)
        logger.info("ds_temp %s" % ds_temp)
        return ds_temp

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
    table_class = datasources_tables.DataSourcesRowsTable
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
            table_name = self.kwargs['table_name']
            try:
                rows = congress.datasources_rows_list(self.request,
                                                      datasource_name,
                                                      table_name)
            except Exception:
                redirect = reverse('horizon:admin:datasources:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve policy table rows.'),
                                  redirect=redirect)
        return rows

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        table_name = kwargs.get('policy_table_name')
        if not table_name:
            if 'table_name' in kwargs:
                table_name = kwargs['table_name']
        context['table_name'] = table_name
        return context
