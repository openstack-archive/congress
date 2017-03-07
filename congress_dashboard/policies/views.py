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

import json
import logging

from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.template.defaultfilters import dictsort
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon import tables

from congress_dashboard.api import congress
import congress_dashboard.datasources.utils as ds_utils
from congress_dashboard.policies import forms as policies_forms
from congress_dashboard.policies.rules import tables as rules_tables
from congress_dashboard.policies import tables as policies_tables


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    """List policies."""
    table_class = policies_tables.PoliciesTable
    template_name = 'admin/policies/index.html'

    def get_data(self):
        try:
            policies = congress.policies_list(self.request)
        except Exception as e:
            msg = _('Unable to get policies list: %s') % str(e)
            LOG.error(msg)
            messages.error(self.request, msg)
            return []
        return policies


class CreateView(forms.ModalFormView):
    form_class = policies_forms.CreatePolicy
    template_name = 'admin/policies/create.html'
    success_url = reverse_lazy('horizon:admin:policies:index')


class DetailView(tables.MultiTableView):
    """List details about and rules in a policy."""
    table_classes = (rules_tables.PolicyRulesTable,
                     rules_tables.PoliciesTablesTable,)
    template_name = 'admin/policies/detail.html'

    def get_policies_tables_data(self):
        policy_name = self.kwargs['policy_name']
        try:
            policy_tables = congress.policy_tables_list(self.request,
                                                        policy_name)
        except Exception as e:
            msg_args = {'policy_name': policy_name, 'error': str(e)}
            msg = _('Unable to get tables list for policy '
                    '"%(policy_name)s": %(error)s') % msg_args
            messages.error(self.request, msg)
            return []

        for pt in policy_tables:
            pt.set_id_as_name_if_empty()
            pt.set_value('policy_name', policy_name)
            # Object ids within a Horizon table must be unique. Otherwise,
            # Horizon will cache the column values for the object by id and
            # use the same column values for all rows with the same id.
            pt.set_value('table_id', pt['id'])
            pt.set_value('id', '%s-%s' % (policy_name, pt['table_id']))

        return policy_tables

    def get_policy_rules_data(self):
        policy_name = self.kwargs['policy_name']
        try:
            policy_rules = congress.policy_rules_list(self.request,
                                                      policy_name)
        except Exception as e:
            msg_args = {'policy_name': policy_name, 'error': str(e)}
            msg = _('Unable to get rules in policy "%(policy_name)s": '
                    '%(error)s') % msg_args
            LOG.error(msg)
            messages.error(self.request, msg)
            redirect = reverse('horizon:admin:policies:index')
            raise exceptions.Http302(redirect)

        for r in policy_rules:
            r.set_id_as_name_if_empty()
        return policy_rules

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        policy_name = kwargs['policy_name']
        try:
            policy = congress.policy_get(self.request, policy_name)
        except Exception as e:
            msg_args = {'policy_name': policy_name, 'error': str(e)}
            msg = _('Unable to get policy "%(policy_name)s": '
                    '%(error)s') % msg_args
            LOG.error(msg)
            messages.error(self.request, msg)
            redirect = reverse('horizon:admin:policies:index')
            raise exceptions.Http302(redirect)
        context['policy'] = policy

        # Alphabetize and convert list of data source tables and columns into
        # JSON formatted string consumable by JavaScript. Do this here instead
        # of in the Create Rule form so that the tables and columns lists
        # appear in the HTML document before the JavaScript that uses them.
        all_tables = ds_utils.get_datasource_tables(self.request)
        sorted_datasources = dictsort(all_tables, 'datasource')
        tables = []
        for ds in sorted_datasources:
            datasource_tables = ds['tables']
            datasource_tables.sort()
            for table in ds['tables']:
                tables.append('%s%s%s' % (ds['datasource'],
                                          congress.TABLE_SEPARATOR, table))
        context['tables'] = json.dumps(tables)

        datasource_columns = ds_utils.get_datasource_columns(self.request)
        sorted_datasources = dictsort(datasource_columns, 'datasource')
        columns = []
        for ds in sorted_datasources:
            sorted_tables = dictsort(ds['tables'], 'table')
            for tbl in sorted_tables:
                # Ignore service-derived tables, which are already included.
                if congress.TABLE_SEPARATOR in tbl['table']:
                    continue
                table_columns = tbl['columns']
                if table_columns:
                    table_columns.sort()
                else:
                    # Placeholder name for column when the table has none.
                    table_columns = ['_']

                for column in table_columns:
                    columns.append('%s%s%s %s' % (ds['datasource'],
                                                  congress.TABLE_SEPARATOR,
                                                  tbl['table'], column))
        context['columns'] = json.dumps(columns)
        return context
