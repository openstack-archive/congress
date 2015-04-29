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
from django.template.defaultfilters import unordered_list
from django.utils.translation import ugettext_lazy as _
from horizon import tables


def get_resource_url(obj):
    return reverse('horizon:admin:datasources:datasource_table_detail',
                   args=(obj['datasource_id'], obj['table_id']))


class DataSourcesTablesTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Table Name"),
                         link=get_resource_url)
    datasource_name = tables.Column("datasource_name",
                                    verbose_name=_("Service"))
    datasource_driver = tables.Column("datasource_driver",
                                      verbose_name=_("Driver"))

    class Meta:
        name = "datasources_tables"
        verbose_name = _("Service Data")
        hidden_title = False


def get_policy_link(datum):
    return reverse('horizon:admin:policies:detail',
                   args=(datum['policy_name'],))


def get_policy_table_link(datum):
    return reverse('horizon:admin:datasources:policy_table_detail',
                   args=(datum['policy_name'], datum['name']))


class PoliciesTablesTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Table Name"),
                         link=get_policy_table_link)
    policy_name = tables.Column("policy_name", verbose_name=_("Policy"),
                                link=get_policy_link)
    policy_owner_id = tables.Column("policy_owner_id",
                                    verbose_name=_("Owner ID"))

    class Meta:
        name = "policies_tables"
        verbose_name = _("Policy Data")
        hidden_title = False


class DataSourceRowsTable(tables.DataTable):
    class Meta:
        name = "datasource_rows"
        verbose_name = _("Rows")
        hidden_title = False


class DataSourceStatusesTable(tables.DataTable):
    datasource_name = tables.Column("service",
                                    verbose_name=_("Service"))
    last_updated = tables.Column("last_updated",
                                 verbose_name=_("Last Updated"))
    subscriptions = tables.Column("subscriptions",
                                  verbose_name=_("Subscriptions"),
                                  wrap_list=True, filters=(unordered_list,))
    last_error = tables.Column("last_error", verbose_name=_("Last Error"))
    subscribers = tables.Column("subscribers", verbose_name=_("Subscribers"),
                                wrap_list=True, filters=(unordered_list,))
    initialized = tables.Column("initialized", verbose_name=_("Initialized"))
    number_of_updates = tables.Column("number_of_updates",
                                      verbose_name=_("Number of Updates"))

    class Meta:
        name = "service_status"
        verbose_name = _("Service Status")
        hidden_title = False
