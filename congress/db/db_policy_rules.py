# Copyright (c) 2012 OpenStack Foundation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import sqlalchemy as sa
from sqlalchemy.orm import exc as db_exc

from congress.db import api as db
from congress.db import model_base


class PolicyRule(model_base.BASE, model_base.HasId, model_base.HasAudit):

    __tablename__ = "policy_rules"

    rule = sa.Column(sa.Text(), nullable=False)
    policy_name = sa.Column(sa.String(255), nullable=False, primary_key=True)
    comment = sa.Column(sa.String(255), nullable=False, primary_key=True)

    def __init__(self, id, policy_name, rule, comment, deleted=False):
        self.id = id
        self.policy_name = policy_name
        self.rule = rule
        # FIXME(arosen) we should not be passing None for comment here.
        self.comment = comment or ""
        self.deleted = is_soft_deleted(id, deleted)


def add_policy_rule(id, policy_name, rule, comment, deleted=False,
                    session=None):
    session = session or db.get_session()
    with session.begin(subtransactions=True):
        policy_rule = PolicyRule(id, policy_name, rule, comment, deleted)
        session.add(policy_rule)
    return policy_rule


def delete_policy_rule(id, session=None):
    session = session or db.get_session()
    return session.query(PolicyRule).filter_by(id=id).soft_delete()


def get_policy_rule(id, policy_name, session=None, deleted=False):
    session = session or db.get_session()
    rule_query = (session.query(PolicyRule).
                  filter(PolicyRule.id == id).
                  filter(PolicyRule.deleted == is_soft_deleted(id, deleted)))
    if policy_name:
        rule_query = (rule_query.
                      filter(PolicyRule.policy_name == policy_name))
    try:
        return rule_query.one()
    except db_exc.NoResultFound:
        pass


def get_policy_rules(policy_name=None, session=None, deleted=False):
    session = session or db.get_session()
    rule_query = session.query(PolicyRule)
    if not deleted:
        rule_query = rule_query.filter(PolicyRule.deleted == '')
    else:
        rule_query = rule_query.filter(PolicyRule.deleted != '')
    if policy_name:
        rule_query = rule_query.filter(policy_name == policy_name)
    return rule_query.all()


def is_soft_deleted(uuid, deleted):
    return '' if deleted is False else uuid
