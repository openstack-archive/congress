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
import re

import six

from django.core.urlresolvers import reverse
from django import template
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from horizon import forms
from horizon import workflows
from openstack_dashboard.api import congress


COLUMN_FORMAT = '<datasource>%s<table> <column>' % congress.TABLE_SEPARATOR
COLUMN_PATTERN = r'\s*[\w.]+%s[\w.]+\s+[\w.]+\s*$' % congress.TABLE_SEPARATOR
COLUMN_PATTERN_ERROR = 'Column name must be in "%s" format' % COLUMN_FORMAT

TABLE_FORMAT = '<datasource>%s<table>' % congress.TABLE_SEPARATOR
TABLE_PATTERN = r'\s*[\w.]+%s[\w.]+\s*$' % congress.TABLE_SEPARATOR
TABLE_PATTERN_ERROR = 'Table name must be in "%s" format' % TABLE_FORMAT

LOG = logging.getLogger(__name__)


class CreateOutputAction(workflows.Action):
    policy_name = forms.CharField(widget=forms.HiddenInput(), required=False)
    rule_name = forms.CharField(label=_('Rule Name'), max_length=255,
                                initial='', required=False)
    comment = forms.CharField(label=_('Rule Comment'), initial='',
                              required=False)
    policy_table = forms.CharField(label=_("Policy Table Name"), initial='',
                                   max_length=255)
    policy_columns = forms.CharField(
        label=_('Policy Table Columns'), initial='',
        help_text=_('Name the columns in the output table, one per textbox.'))
    failure_url = 'horizon:admin:policies:detail'

    def __init__(self, request, context, *args, **kwargs):
        super(CreateOutputAction, self).__init__(request, context, *args,
                                                 **kwargs)
        self.fields['policy_name'].initial = context['policy_name']

    class Meta(object):
        name = _('Output')


class CreateOutput(workflows.Step):
    action_class = CreateOutputAction
    contributes = ('policy_name', 'rule_name', 'comment', 'policy_table',
                   'policy_columns')
    template_name = 'admin/policies/rules/_create_output.html'
    help_text = _('Information about the rule and the policy table '
                  'being created.')

    def render(self):
        # Overriding parent method to add extra template context variables.
        step_template = template.loader.get_template(self.template_name)
        extra_context = {"form": self.action,
                         "step": self}
        context = template.RequestContext(self.workflow.request, extra_context)

        # Data needed to re-create policy column inputs after an error occurs.
        policy_columns = self.workflow.request.POST.get('policy_columns', '')
        columns_list = policy_columns.split(', ')
        context['policy_columns_list'] = columns_list
        context['policy_columns_count'] = len(columns_list)
        return step_template.render(context)


class CreateConditionsAction(workflows.Action):
    mappings = forms.CharField(label=_('Policy table columns:'), initial='')

    class Meta(object):
        name = _('Conditions')


class CreateConditions(workflows.Step):
    action_class = CreateConditionsAction
    contributes = ('mappings',)
    template_name = 'admin/policies/rules/_create_conditions.html'
    help_text = _('Sources from which the output policy table will get its '
                  'data, plus any constraints.')

    def _compare_mapping_columns(self, x, y):
        # x = "mapping_column_<int>", y = "mapping_column_<int>"
        return cmp(int(x.split('_')[-1]), int(y.split('_')[-1]))

    def render(self):
        # Overriding parent method to add extra template context variables.
        step_template = template.loader.get_template(self.template_name)
        extra_context = {"form": self.action,
                         "step": self}
        context = template.RequestContext(self.workflow.request, extra_context)

        # Data needed to re-create mapping column inputs after an error occurs.
        post = self.workflow.request.POST
        mappings = []
        policy_columns = post.get('policy_columns')
        policy_columns_list = []
        # Policy column to data source mappings.
        if policy_columns:
            policy_columns_list = policy_columns.split(', ')
            mapping_columns = []
            for param, value in post.items():
                if (param.startswith('mapping_column_') and
                        param != 'mapping_column_0'):
                    mapping_columns.append(param)

            # Mapping columns should be in the same order as the policy columns
            # above to which they match.
            sorted_mapping_columns = sorted(mapping_columns,
                                            cmp=self._compare_mapping_columns)
            mapping_columns_list = [post.get(c)
                                    for c in sorted_mapping_columns]
            mappings = zip(policy_columns_list, mapping_columns_list)
        context['mappings'] = mappings
        # Add one for the hidden template row.
        context['mappings_count'] = len(mappings) + 1

        # Data needed to re-create join, negation, and alias inputs.
        joins = []
        negations = []
        aliases = []
        for param, value in post.items():
            if param.startswith('join_left_') and value:
                join_num = param.split('_')[-1]
                other_value = post.get('join_right_%s' % join_num)
                join_op = post.get('join_op_%s' % join_num)
                if other_value and join_op is not None:
                    joins.append((value, join_op, other_value))
            elif param.startswith('negation_value_') and value:
                negation_num = param.split('_')[-1]
                negation_column = post.get('negation_column_%s' %
                                           negation_num)
                if negation_column:
                    negations.append((value, negation_column))
            elif param.startswith('alias_column_') and value:
                alias_num = param.split('_')[-1]
                alias_name = post.get('alias_name_%s' % alias_num)
                if alias_name:
                    aliases.append((value, alias_name))

        # Make sure there's at least one empty row.
        context['joins'] = joins or [('', '')]
        context['joins_count'] = len(joins) or 1
        context['negations'] = negations or [('', '')]
        context['negations_count'] = len(negations) or 1
        context['aliases'] = aliases or [('', '')]
        context['aliases_count'] = len(aliases) or 1

        # Input validation attributes.
        context['column_pattern'] = COLUMN_PATTERN
        context['column_pattern_error'] = COLUMN_PATTERN_ERROR
        context['table_pattern'] = TABLE_PATTERN
        context['table_pattern_error'] = TABLE_PATTERN_ERROR
        return step_template.render(context)


def _underscore_slugify(name):
    # Slugify given string, except using undesrscores instead of hyphens.
    return slugify(name).replace('-', '_')


class CreateRule(workflows.Workflow):
    slug = 'create_rule'
    name = _('Create Rule')
    finalize_button_name = _('Create')
    success_message = _('Created rule%(rule_name)s.%(error)s')
    failure_message = _('Unable to create rule%(rule_name)s: %(error)s')
    default_steps = (CreateOutput, CreateConditions)
    wizard = True

    def get_success_url(self):
        policy_name = self.context.get('policy_name')
        return reverse('horizon:admin:policies:detail', args=(policy_name,))

    def get_failure_url(self):
        policy_name = self.context.get('policy_name')
        return reverse('horizon:admin:policies:detail', args=(policy_name,))

    def format_status_message(self, message):
        rule_name = self.context.get('rule_name')
        name_str = ''
        if rule_name:
            name_str = ' "%s"' % rule_name
        else:
            rule_id = self.context.get('rule_id')
            if rule_id:
                name_str = ' %s' % rule_id
        return message % {'rule_name': name_str,
                          'error': self.context.get('error', '')}

    def _get_schema_columns(self, request, table):
        table_parts = table.split(congress.TABLE_SEPARATOR)
        datasource = table_parts[0]
        table_name = table_parts[1]
        try:
            schema = congress.datasource_table_schema_get_by_name(
                request, datasource, table_name)
        except Exception:
            # Maybe it's a policy table, not a service.
            try:
                schema = congress.policy_table_schema_get(
                    request, datasource, table_name)
            except Exception as e:
                # Nope.
                LOG.error('Unable to get schema for table "%s", '
                          'datasource "%s": %s' % (table_name, datasource,
                                                   e.message))
                return e.message
        return schema['columns']

    def handle(self, request, data):
        policy_name = data['policy_name']
        username = request.user.username
        project_name = request.user.tenant_name

        # Output data.
        rule_name = data.get('rule_name')
        comment = data.get('comment')
        policy_table = _underscore_slugify(data['policy_table'])
        if not data['policy_columns']:
            self.context['error'] = 'Missing policy table columns'
            return False
        policy_columns = data['policy_columns'].split(', ')

        # Conditions data.
        if not data['mappings']:
            self.context['error'] = ('Missing data source column mappings for '
                                     'policy table columns')
            return False
        mapping_columns = [c.strip() for c in data['mappings'].split(', ')]
        if len(policy_columns) != len(mapping_columns):
            self.context['error'] = ('Missing data source column mappings for '
                                     'some policy table columns')
            return False
        # Map columns used in rule's head. Every column in the head must also
        # appear in the body.
        head_columns = [_underscore_slugify(c).strip() for c in policy_columns]
        column_variables = dict(zip(mapping_columns, head_columns))

        # All tables needed in the body.
        body_tables = set()
        negation_tables = set()

        # Keep track of the tables from the head that need to be in the body.
        for column in mapping_columns:
            if re.match(COLUMN_PATTERN, column) is None:
                self.context['error'] = '%s: %s' % (COLUMN_PATTERN_ERROR,
                                                    column)
                return False
            table = column.split()[0]
            body_tables.add(table)

        # Make sure columns that are given a significant variable name are
        # unique names by adding name_count as a suffix.
        name_count = 0
        for param, value in request.POST.items():
            if param.startswith('join_left_') and value:
                if re.match(COLUMN_PATTERN, value) is None:
                    self.context['error'] = '%s: %s' % (COLUMN_PATTERN_ERROR,
                                                        value)
                    return False
                value = value.strip()

                # Get operator and other column used in join.
                join_num = param.split('_')[-1]
                join_op = request.POST.get('join_op_%s' % join_num)
                other_value = request.POST.get('join_right_%s' % join_num)
                other_value = other_value.strip()

                if join_op == '=':
                    try:
                        # Check if static value is a number, but keep it as a
                        # string, to be used later.
                        int(other_value)
                        column_variables[value] = other_value
                    except ValueError:
                        # Pass it along as a quoted string.
                        column_variables[value] = '"%s"' % other_value
                else:
                    # Join between two columns.
                    if not other_value:
                        # Ignore incomplete pairing.
                        continue
                    if re.match(COLUMN_PATTERN, other_value) is None:
                        self.context['error'] = ('%s: %s' %
                                                 (COLUMN_PATTERN_ERROR,
                                                  other_value))
                        return False

                    # Tables used in the join need to be in the body.
                    value_parts = value.split()
                    body_tables.add(value_parts[0])
                    body_tables.add(other_value.split()[0])

                    # Arbitrarily name the right column the same as the left.
                    column_name = value_parts[1]
                    # Use existing variable name if there is already one for
                    # either column in this join.
                    if other_value in column_variables:
                        column_variables[value] = column_variables[other_value]
                    elif value in column_variables:
                        column_variables[other_value] = column_variables[value]
                    else:
                        variable = '%s_%s' % (column_name, name_count)
                        name_count += 1
                        column_variables[value] = variable
                        column_variables[other_value] = variable

            elif param.startswith('negation_value_') and value:
                if re.match(COLUMN_PATTERN, value) is None:
                    self.context['error'] = '%s: %s' % (COLUMN_PATTERN_ERROR,
                                                        value)
                    return False
                value = value.strip()

                # Get operator and other column used in negation.
                negation_num = param.split('_')[-1]
                negation_column = request.POST.get('negation_column_%s' %
                                                   negation_num)
                if not negation_column:
                    # Ignore incomplete pairing.
                    continue
                if re.match(COLUMN_PATTERN, negation_column) is None:
                    self.context['error'] = '%s: %s' % (COLUMN_PATTERN_ERROR,
                                                        negation_column)
                    return False
                negation_column = negation_column.strip()

                # Tables for columns referenced by the negation table must
                # appear in the body.
                value_parts = value.split()
                body_tables.add(value_parts[0])

                negation_tables.add(negation_column.split()[0])
                # Use existing variable name if there is already one for either
                # column in this negation.
                if negation_column in column_variables:
                    column_variables[value] = column_variables[negation_column]
                elif value in column_variables:
                    column_variables[negation_column] = column_variables[value]
                else:
                    # Arbitrarily name the negated table's column the same as
                    # the value column.
                    column_name = value_parts[1]
                    variable = '%s_%s' % (column_name, name_count)
                    name_count += 1
                    column_variables[value] = variable
                    column_variables[negation_column] = variable

        LOG.debug('column_variables for rule: %s' % column_variables)

        # Form the literals for all the tables needed in the body. Make sure
        # column that have no relation to any other columns are given a unique
        # variable name, using column_count.
        column_count = 0
        literals = []
        for table in body_tables:
            # Replace column names with variable names that join related
            # columns together.
            columns = self._get_schema_columns(request, table)
            if isinstance(columns, six.string_types):
                self.context['error'] = columns
                return False

            literal_columns = []
            if columns:
                for column in columns:
                    table_column = '%s %s' % (table, column['name'])
                    literal_columns.append(
                        column_variables.get(table_column, 'col_%s' %
                                             column_count))
                    column_count += 1
                literals.append('%s(%s)' % (table, ', '.join(literal_columns)))
            else:
                # Just the table name, such as for classification:true.
                literals.append(table)

        # Form the negated tables.
        for table in negation_tables:
            columns = self._get_schema_columns(request, table)
            if isinstance(columns, six.string_types):
                self.context['error'] = columns
                return False

            literal_columns = []
            num_variables = 0
            for column in columns:
                table_column = '%s %s' % (table, column['name'])
                if table_column in column_variables:
                    literal_columns.append(column_variables[table_column])
                    num_variables += 1
                else:
                    literal_columns.append('col_%s' % column_count)
                    column_count += 1
            literal = 'not %s(%s)' % (table, ', '.join(literal_columns))
            literals.append(literal)

            # Every column in the negated table must appear in a non-negated
            # literal in the body. If there are some variables that have not
            # been used elsewhere, repeat the literal in its non-negated form.
            if num_variables != len(columns) and table not in body_tables:
                literals.append(literal.replace('not ', ''))

        # All together now.
        rule = '%s(%s) %s %s' % (policy_table, ', '.join(head_columns),
                                 congress.RULE_SEPARATOR, ', '.join(literals))
        LOG.info('User %s creating policy "%s" rule "%s" in tenant %s: %s' %
                 (username, policy_name, rule_name, project_name, rule))
        try:
            params = {
                'name': rule_name,
                'comment': comment,
                'rule': rule,
            }
            rule = congress.policy_rule_create(request, policy_name,
                                               body=params)
            LOG.info('Created rule %s' % rule['id'])
            self.context['rule_id'] = rule['id']
        except Exception as e:
            LOG.error('Error creating policy "%s" rule "%s": %s' %
                      (policy_name, rule_name, e.message))
            self.context['error'] = e.message
            return False
        return True
