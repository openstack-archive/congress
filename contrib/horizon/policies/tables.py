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
from horizon import tables


def get_policy_link(datum):
    return reverse('horizon:admin:policies:detail', args=(datum['name'],))


class CreatePolicy(tables.LinkAction):
    name = 'create_policy'
    verbose_name = _('Create Policy')
    url = 'horizon:admin:policies:create'
    classes = ('ajax-modal',)
    icon = 'plus'


class PoliciesTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"), link=get_policy_link)
    description = tables.Column("description", verbose_name=_("Description"))
    kind = tables.Column("kind", verbose_name=_("Kind"))
    owner_id = tables.Column("owner_id", verbose_name=_("Owner ID"))

    class Meta(object):
        name = "policies"
        verbose_name = _("Policies")
        table_actions = (CreatePolicy,)
