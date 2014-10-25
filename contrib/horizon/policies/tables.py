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

from horizon import tables


class PoliciesTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"),
                         link="horizon:admin:policies:detail")
    owner_id = tables.Column("owner_id", verbose_name=_("Owner ID"))

    class Meta:
        name = "policies"
        verbose_name = _("Policies")


class PolicyRulesTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"))
    comment = tables.Column("comment", verbose_name=_("Comment"))
    rule = tables.Column("rule", verbose_name=_("Rule"))

    class Meta:
        name = "policy_rules"
        verbose_name = _("Rules")
