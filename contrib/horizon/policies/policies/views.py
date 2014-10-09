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
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard.api import congress

from openstack_dashboard.dashboards.admin.policies.policies \
    import tabs as policies_tabs


class DetailView(tabs.TabView):
    """Show detailed information about a policy."""
    tab_group_class = policies_tabs.PolicyDetailTabs
    template_name = 'admin/policies/policies/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        data = self.get_data()
        context['policy'] = data['policy']
        return context

    @memoized.memoized_method
    def get_data(self):
        data = {}
        try:
            policy_name = self.kwargs['policy_name']
            data['policy'] = congress.policy_get(self.request, policy_name)
        except Exception:
            redirect = self.get_redirect_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve policy details.'),
                              redirect=redirect)
        return data

    def get_redirect_url(self):
        return reverse('horizon:admin:policies:index')

    def get_tabs(self, request, *args, **kwargs):
        data = self.get_data()
        policy = data['policy']
        return self.tab_group_class(request, policy=policy, **kwargs)
