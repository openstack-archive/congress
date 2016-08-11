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
from django.utils.translation import ungettext_lazy
from horizon import exceptions
from horizon import messages
from horizon import tables
from openstack_dashboard import policy

from congress_dashboard.api import congress


LOG = logging.getLogger(__name__)


def get_policy_link(datum):
    return reverse('horizon:admin:policies:detail', args=(datum['name'],))


class CreatePolicy(tables.LinkAction):
    name = 'create_policy'
    verbose_name = _('Create Policy')
    url = 'horizon:admin:policies:create'
    classes = ('ajax-modal',)
    icon = 'plus'


class DeletePolicy(policy.PolicyTargetMixin, tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u'Delete Policy',
            u'Delete Policies',
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u'Deleted policy',
            u'Deleted policies',
            count
        )

    redirect_url = 'horizon:admin:policies:index'

    def delete(self, request, obj_id):
        LOG.info('User %s deleting policy "%s" in tenant %s',
                 request.user.username, obj_id, request.user.tenant_name)
        try:
            congress.policy_delete(request, obj_id)
            LOG.info('Deleted policy "%s"', obj_id)
        except Exception as e:
            msg_args = {'policy_id': obj_id, 'error': str(e)}
            msg = _('Failed to delete policy "%(policy_id)s": '
                    '%(error)s') % msg_args
            LOG.error(msg)
            messages.error(request, msg)
            redirect = reverse(self.redirect_url)
            raise exceptions.Http302(redirect)

    def allowed(self, request, policy=None):
        # Only user policies can be deleted.
        if policy:
            return policy['owner_id'] == 'user'
        return True


class PoliciesTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"), link=get_policy_link)
    description = tables.Column("description", verbose_name=_("Description"))
    kind = tables.Column("kind", verbose_name=_("Kind"))
    owner_id = tables.Column("owner_id", verbose_name=_("Owner ID"))

    class Meta(object):
        name = "policies"
        verbose_name = _("Policies")
        table_actions = (CreatePolicy, DeletePolicy)
        row_actions = (DeletePolicy,)
