# Copyright 2015 VMware.
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
from horizon import forms
from horizon import messages

from congress_dashboard.api import congress


LOG = logging.getLogger(__name__)

POLICY_KIND_CHOICES = (
    ('nonrecursive', _('Nonrecursive')),
    ('action', _('Action')),
    ('database', _('Database')),
    ('materialized', _('Materialized')),
)


class CreatePolicy(forms.SelfHandlingForm):
    name = forms.CharField(max_length=255, label=_("Policy Name"))
    kind = forms.ChoiceField(choices=POLICY_KIND_CHOICES, label=_("Kind"),
                             initial='nonrecursive')
    description = forms.CharField(label=_("Description"), required=False,
                                  widget=forms.Textarea(attrs={'rows': 4}))
    failure_url = 'horizon:admin:policies:index'

    def handle(self, request, data):
        policy_name = data['name']
        policy_description = data.get('description')
        policy_kind = data.pop('kind')
        LOG.info('User %s creating policy "%s" of type %s in tenant %s',
                 request.user.username, policy_name, policy_kind,
                 request.user.tenant_name)
        try:
            params = {
                'name': policy_name,
                'description': policy_description,
                'kind': policy_kind,
            }
            policy = congress.policy_create(request, params)
            msg = _('Created policy "%s"') % policy_name
            LOG.info(msg)
            messages.success(request, msg)
        except Exception as e:
            msg_args = {'policy_name': policy_name, 'error': str(e)}
            msg = _('Failed to create policy "%(policy_name)s": '
                    '%(error)s') % msg_args
            LOG.error(msg)
            messages.error(self.request, msg)
            redirect = reverse(self.failure_url)
            raise exceptions.Http302(redirect)
        return policy
