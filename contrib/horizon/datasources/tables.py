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


def get_resource_url(obj):
        return reverse('horizon:admin:datasources:datasource_table_detail',
                       args=(obj['datasource'], obj['id']))


class DataSourcesTablesTable(tables.DataTable):
    datasource_name = tables.Column("datasource",
                                    verbose_name=_("Data Source"))
    name = tables.Column("name", verbose_name=_("Table Name"),
                         link=get_resource_url)
    owner_id = tables.Column("owner_id", verbose_name=_("Owner ID"))

    class Meta:
        name = "datasources_tables"
        verbose_name = _("Plugin Data")


def get_policy_link(datum):
    return reverse('horizon:admin:policies:detail',
                   args=(datum['policy_name'],))


def get_policy_table_link(datum):
    return reverse('horizon:admin:datasources:policy_table_detail',
                   args=(datum['policy_name'], datum['name']))


class PoliciesTablesTable(tables.DataTable):
    policy_name = tables.Column("policy_name", verbose_name=_("Policy"),
                                link=get_policy_link)
    name = tables.Column("name", verbose_name=_("Table Name"),
                         link=get_policy_table_link)
    policy_owner_id = tables.Column("policy_owner_id",
                                    verbose_name=_("Owner ID"))

    class Meta:
        name = "policies_tables"
        verbose_name = _("Policy Data")


class DataSourcesRowsTable(tables.DataTable):
    data = tables.Column("data", verbose_name=_("Data"))

    class Meta:
        name = "datasource_rows"
        verbose_name = _("Rows")
