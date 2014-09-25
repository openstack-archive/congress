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

from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs

from openstack_dashboard.api import congress

from openstack_dashboard.dashboards.admin.policies.policies.policy_rules \
    import tables as policy_rules_tables
from openstack_dashboard.dashboards.admin.policies.policies.policy_tables \
    import tables as policy_tables_tables


class PolicyRulesTab(tabs.TableTab):
    table_classes = (policy_rules_tables.PolicyRulesTable,)
    name = _("Rules")
    slug = "policy_rules_tab"
    template_name = "admin/policies/policies/policy_rules/table.html"

    def get_policy_rules_data(self):
        policy_name = self.tab_group.kwargs['policy_name']
        try:
            policy_rules = congress.policy_rules_list(self.request,
                                                      policy_name)
        except Exception:
            msg = _('Unable to get policy rules.')
            exceptions.handle(self.request, msg)
            policy_rules = []

        for r in policy_rules:
            r.set_id_as_name_if_empty()
        return policy_rules


class PolicyTablesTab(tabs.TableTab):
    """Like tabs.TableTab, except displays multiple tables in the tab."""
    table_classes = (policy_tables_tables.PolicyTablesTable,)
    name = _("Tables")
    slug = "policy_tables_tab"
    template_name = "admin/policies/policies/policy_tables/tables.html"

    def __init__(self, tab_group, request):
        super(PolicyTablesTab, self).__init__(tab_group, request)
        policy_name = self.tab_group.kwargs['policy_name']
        try:
            policy_tables = congress.policy_tables_list(self.request,
                                                        policy_name)
        except Exception:
            msg = _('Unable to get policy tables.')
            exceptions.handle(self.request, msg)
            policy_tables = []
        for t in policy_tables:
            t.set_id_as_name_if_empty()

        # Instantiate our table classes but don't assign data yet.
        table_instances = [(table['name'],
                            policy_tables_tables.PolicyTablesTable(
                                request, **tab_group.kwargs))
                           for table in policy_tables]
        self._tables = SortedDict(table_instances)
        self._table_data_loaded = False

    def get_policy_rows_data(self, table_name):
        policy_name = self.tab_group.kwargs['policy_name']
        try:
            policy_rows = congress.policy_rows_list(self.request, policy_name,
                                                    table_name)
        except Exception:
            msg = _('Unable to get policy table rows.')
            exceptions.handle(self.request, msg)
            policy_rows = []
        return policy_rows

    def load_table_data(self):
        # We only want the data to be loaded once, so we track if we have...
        if not self._table_data_loaded:
            for table_name, table in self._tables.items():
                # Load the data.
                table.data = self.get_policy_rows_data(table_name)
                table._meta.has_prev_data = self.has_prev_data(table)
                table._meta.has_more_data = self.has_more_data(table)
                # TODO(jwy): Find a way to override the table's name and
                # verbose name so table.render will take care of displaying the
                # table id and header for us in the template.
            # Mark our data as loaded so we don't run the loaders again.
            self._table_data_loaded = True

    def get_context_data(self, request, **kwargs):
        context = super(PolicyTablesTab, self).get_context_data(request,
                                                                **kwargs)
        # If the data hasn't been manually loaded before now,
        # make certain it's loaded before setting the context.
        self.load_table_data()
        context["policy_tables"] = {}
        for table_name, table in self._tables.items():
            context["policy_tables"][table_name] = table
        return context


class PolicyDetailTabs(tabs.TabGroup):
    slug = "policy_detail_tabs"
    tabs = (PolicyRulesTab, PolicyTablesTab)
    sticky = True
