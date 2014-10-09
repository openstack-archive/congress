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

"""
Admin views for managing policy rules, policy tables, and data sources.
"""

from horizon import tabs

from openstack_dashboard.dashboards.admin.policies \
    import tabs as policies_tabs


class IndexView(tabs.TabbedTableView):
    """Show tabs with policy related information."""
    tab_group_class = policies_tabs.PoliciesGroupTabs
    template_name = 'admin/policies/index.html'
