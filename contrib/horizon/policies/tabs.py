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

from django.utils.translation import ugettext_lazy as _

from horizon import tabs

from openstack_dashboard.api import congress

from openstack_dashboard.dashboards.admin.policies.datasources \
    import tables as datasources_tables
from openstack_dashboard.dashboards.admin.policies.policies \
    import tables as policies_tables


class PoliciesTab(tabs.TableTab):
    table_classes = (policies_tables.PoliciesTable,)
    name = _("Policies")
    slug = "policies_tab"
    template_name = "admin/policies/policies/table.html"

    def get_policies_data(self):
        policies = congress.policies_list(self.request)
        for p in policies:
            p.set_id_as_name_if_empty()
        return policies


class DatasourcesTab(tabs.TableTab):
    table_classes = (datasources_tables.DatasourcesTable,)
    name = _("Data Sources")
    slug = "datasources_tab"
    template_name = "admin/policies/datasources/table.html"

    def get_datasources_data(self):
        # TODO(jwy): Return list of data sources.
        return []


class PoliciesGroupTabs(tabs.TabGroup):
    slug = "policies_group_tabs"
    # TODO(jwy): Need to implement DatasourcesTab.get_datasources_data().
    # tabs = (PoliciesTab, DatasourcesTab)
    tabs = (PoliciesTab,)
    sticky = True
