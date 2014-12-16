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

import copy
import logging

from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import messages
from horizon import tables
from openstack_dashboard.api import congress
from openstack_dashboard.dashboards.admin.datasources \
    import tables as datasources_tables


logger = logging.getLogger(__name__)


class IndexView(tables.MultiTableView):
    """List plugin and policy defined data."""
    table_classes = (datasources_tables.DataSourcesTablesTable,
                     datasources_tables.PoliciesTablesTable,)
    template_name = 'admin/datasources/index.html'

    def get_datasources_tables_data(self):
        try:
            ds1 = congress.datasources_list(self.request)
        except Exception as e:
            msg = _('Unable to get plugins list: %s') % e.message
            messages.error(self.request, msg)
            return []

        ds_temp = []
        for d1 in ds1:
            s = d1['id']
            owner_id = d1['owner_id']
            try:
                ds = congress.datasource_tables_list(self.request, s)
            except Exception as e:
                msg_args = {'ds_name': s, 'error': e.message}
                msg = _('Unable to get tables list for plugin "%(ds_name)s": '
                        '%(error)s') % msg_args
                messages.error(self.request, msg)
                return []

            for d in ds:
                d.set_value('datasource', s)
                d.set_value('owner_id', owner_id)
                d.set_id_as_name_if_empty()
                ds_temp.append(d)

        logger.info("ds_temp %s" % ds_temp)
        return ds_temp

    def get_policies_tables_data(self):
        try:
            policies = congress.policies_list(self.request)
        except Exception as e:
            msg = _('Unable to get policies list: %s') % e.message
            messages.error(self.request, msg)
            return []

        policies_tables = []
        for policy in policies:
            policy.set_id_as_name_if_empty()
            policy_name = policy['name']
            try:
                policy_tables = congress.policy_tables_list(self.request,
                                                            policy_name)
            except Exception as e:
                msg_args = {'policy_name': policy_name, 'error': e.message}
                msg = _('Unable to get tables list for policy '
                        '"%(policy_name)s": %(error)s') % msg_args
                messages.error(self.request, msg)
                return []

            for pt in policy_tables:
                pt.set_id_as_name_if_empty()
                pt.set_policy_details(policy)
            policies_tables.extend(policy_tables)
        return policies_tables


class DetailView(tables.DataTableView):
    """List details about and rows from a data source (plugin or policy)."""
    table_class = datasources_tables.DataSourceRowsTable
    template_name = 'admin/datasources/detail.html'

    def get_data(self):
        datasource_name = self.kwargs['datasource_name']
        table_name = self.kwargs.get('policy_table_name')
        has_schema = False

        try:
            if table_name:
                # Policy data table.
                rows = congress.policy_rows_list(self.request, datasource_name,
                                                 table_name)
                if congress.PLUGIN_TABLE_SEPARATOR in table_name:
                    table_name_parts = table_name.split(
                        congress.PLUGIN_TABLE_SEPARATOR)
                    maybe_datasource_name = table_name_parts[0]
                    if congress.datasource_get(self.request,
                                               maybe_datasource_name):
                        # Plugin-derived policy data table.
                        has_schema = True
                        datasource_name = maybe_datasource_name
                        table_name = table_name_parts[1]
            else:
                # Plugin data table.
                table_name = self.kwargs['table_name']
                rows = congress.datasource_rows_list(
                    self.request, datasource_name, table_name)
                has_schema = True
        except Exception as e:
            msg_args = {
                'table_name': table_name,
                'ds_name': datasource_name,
                'error': e.message
            }
            msg = _('Unable to get rows in table "%(table_name)s", data '
                    'source "%(ds_name)s": %(error)s') % msg_args
            messages.error(self.request, msg)
            redirect = reverse('horizon:admin:datasources:index')
            raise exceptions.Http302(redirect)

        # Normally, in Horizon, the columns for a table are defined as
        # attributes of the Table class. When the class is instantiated,
        # the columns are processed during the metaclass initialization. To
        # add columns dynamically, re-create the class from the metaclass
        # with the added columns, re-create the Table from the new class,
        # then reassign the Table stored in this View.
        column_names = []
        table_class_attrs = copy.deepcopy(dict(self.table_class.__dict__))
        if has_schema:
            # Get schema from the server.
            try:
                schema = congress.datasource_table_schema_show(
                    self.request, datasource_name, table_name)
            except Exception as e:
                msg_args = {
                    'table_name': table_name,
                    'ds_name': datasource_name,
                    'error': e.message
                }
                msg = _('Unable to get schema for table "%(table_name)s", '
                        'data source "%(ds_name)s": %(error)s') % msg_args
                messages.error(self.request, msg)
                redirect = reverse('horizon:admin:datasources:index')
                raise exceptions.Http302(redirect)

            for col in schema['columns']:
                col_name = col['name']
                # Attribute name for column in the class must be a valid
                # identifier. Slugify it.
                col_slug = slugify(col_name)
                column_names.append(col_slug)
                table_class_attrs[col_slug] = tables.Column(
                    col_slug, verbose_name=col_name)
        elif len(rows):
            # Divide the rows into unnamed columns. Number them for internal
            # reference.
            row_len = len(rows[0].get('data', []))
            for i in xrange(0, row_len):
                col_name = str(i)
                column_names.append(col_name)
                table_class_attrs[col_name] = tables.Column(
                    col_name, verbose_name='')

        # Class and object re-creation, using a new class name, the same base
        # classes, and the new class attributes, which now includes columns.
        columnized_table_class_name = '%s%sRows' % (
            slugify(datasource_name).title(), slugify(table_name).title())
        columnized_table_class = tables.base.DataTableMetaclass(
            str(columnized_table_class_name), self.table_class.__bases__,
            table_class_attrs)

        self.table_class = columnized_table_class
        columnized_table = columnized_table_class(self.request, **self.kwargs)
        self._tables[columnized_table_class._meta.name] = columnized_table

        # Map columns names to row values.
        num_cols = len(column_names)
        for row in rows:
            try:
                row_data = row['data']
                row.delete_by_key('data')
                for i in xrange(0, num_cols):
                    row.set_value(column_names[i], row_data[i])
            except Exception as e:
                msg_args = {
                    'table_name': table_name,
                    'ds_name': datasource_name,
                    'error': e.message
                }
                msg = _('Unable to get data for table "%(table_name)s", data '
                        'source "%(ds_name)s": %(error)s') % msg_args
                messages.error(self.request, msg)
                redirect = reverse('horizon:admin:datasources:index')
                raise exceptions.Http302(redirect)

        return rows

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        if 'policy_table_name' in kwargs:
            table_name = kwargs.get('policy_table_name')
            context['datasource_type'] = _('Policy')
        else:
            table_name = kwargs['table_name']
            context['datasource_type'] = _('Plugin')
        context['table_name'] = table_name
        return context
