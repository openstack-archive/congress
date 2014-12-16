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
from horizon import messages
from horizon import tables
from openstack_dashboard.api import congress
from openstack_dashboard.dashboards.admin.policies \
    import tables as policies_tables


class IndexView(tables.DataTableView):
    """List policies."""
    table_class = policies_tables.PoliciesTable
    template_name = 'admin/policies/index.html'

    def get_data(self):
        try:
            policies = congress.policies_list(self.request)
        except Exception as e:
            msg = _('Unable to get policies list: %s') % e.message
            messages.error(self.request, msg)
            return []

        for p in policies:
            p.set_id_as_name_if_empty()
        return policies


class DetailView(tables.DataTableView):
    """List details about and rules in a policy."""
    table_class = policies_tables.PolicyRulesTable
    template_name = 'admin/policies/detail.html'

    def get_data(self):
        policy_name = self.kwargs['policy_name']
        try:
            policy_rules = congress.policy_rules_list(self.request,
                                                      policy_name)
        except Exception as e:
            msg_args = {'policy_name': policy_name, 'error': e.message}
            msg = _('Unable to get rules in policy "%(policy_name)s": '
                    '%(error)s') % msg_args
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
            msg_args = {'policy_name': policy_name, 'error': e.message}
            msg = _('Unable to get policy "%(policy_name)s": '
                    '%(error)s') % msg_args
            messages.error(self.request, msg)
            redirect = reverse('horizon:admin:policies:index')
            raise exceptions.Http302(redirect)

        policy.set_id_as_name_if_empty()
        context['policy'] = policy
        return context
