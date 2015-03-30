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

from django.template.defaultfilters import linebreaksbr
from django.utils.translation import ugettext_lazy as _
from horizon import tables
from openstack_dashboard.api import congress


def _format_rule(rule):
    """Make rule's text more human readable."""
    head_body = rule.split(congress.RULE_SEPARATOR)
    if len(head_body) < 2:
        return rule
    head = head_body[0]
    body = head_body[1]

    # Add newline after each literal in the body.
    body_literals = body.split(congress.LITERALS_SEPARATOR)
    literals_break = congress.LITERALS_SEPARATOR + '\n'
    new_body = literals_break.join(body_literals)

    # Add newline after the head.
    rules_break = congress.RULE_SEPARATOR + '\n'
    return rules_break.join([head, new_body])


class PolicyRulesTable(tables.DataTable):
    name = tables.Column("name", verbose_name=_("Name"))
    comment = tables.Column("comment", verbose_name=_("Comment"))
    rule = tables.Column("rule", verbose_name=_("Rule"),
                         filters=(_format_rule, linebreaksbr,))

    class Meta(object):
        name = "policy_rules"
        verbose_name = _("Rules")
        hidden_title = False
