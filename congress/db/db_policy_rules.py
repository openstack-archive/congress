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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


from oslo_log import log as logging
import sqlalchemy as sa
from sqlalchemy.orm import exc as db_exc

from congress.db import api as db
from congress.db import model_base


LOG = logging.getLogger(__name__)


class Policy(model_base.BASE, model_base.HasId, model_base.HasAudit):
    __tablename__ = 'policies'

    # name is a human-readable string, so it can be referenced in policy
    name = sa.Column(sa.Text(), nullable=False)
    abbreviation = sa.Column(sa.String(5), nullable=False)
    description = sa.Column(sa.Text(), nullable=False)
    owner = sa.Column(sa.Text(), nullable=False)
    kind = sa.Column(sa.Text(), nullable=False)

    def __init__(self, id_, name, abbreviation, description, owner, kind,
                 deleted=False):
        self.id = id_
        self.name = name
        self.abbreviation = abbreviation
        self.description = description
        self.owner = owner
        self.kind = kind
        self.deleted = is_soft_deleted(id_, deleted)

    def to_dict(self):
        """From a given database policy, return a policy dict."""
        d = {'id': self.id,
             'name': self.name,
             'abbreviation': self.abbreviation,
             'description': self.description,
             'owner_id': self.owner,
             'kind': self.kind}
        return d


def add_policy(id_, name, abbreviation, description, owner, kind,
               deleted=False, session=None):
    session = session or db.get_session()
    with session.begin(subtransactions=True):
        policy = Policy(id_, name, abbreviation, description, owner,
                        kind, deleted)
        session.add(policy)
    return policy


def delete_policy(id_, session=None):
    session = session or db.get_session()
    with session.begin(subtransactions=True):
        # delete all rules for that policy from database
        policy = get_policy_by_id(id_, session=session)
        for rule in get_policy_rules(policy.name, session=session):
            delete_policy_rule(rule.id, session=session)
        # delete the policy
        return (session.query(Policy).
                filter(Policy.id == id_).
                soft_delete())


def get_policy_by_id(id_, session=None, deleted=False):
    session = session or db.get_session()
    try:
        return (session.query(Policy).
                filter(Policy.id == id_).
                filter(Policy.deleted == is_soft_deleted(id_, deleted)).
                one())
    except db_exc.NoResultFound:
        pass


def get_policy_by_name(name, session=None, deleted=False):
    session = session or db.get_session()
    try:
        return (session.query(Policy).
                filter(Policy.name == name).
                filter(Policy.deleted == is_soft_deleted(name, deleted)).
                one())
    except db_exc.NoResultFound:
        pass


def get_policy(name_or_id, session=None, deleted=False):
    # Try to retrieve policy either by id or name
    db_object = (get_policy_by_id(name_or_id, session, deleted) or
                 get_policy_by_name(name_or_id, session, deleted))
    if not db_object:
        raise KeyError("Policy Name or ID '%s' does not exist" % (name_or_id))
    return db_object


def get_policies(session=None, deleted=False):
    session = session or db.get_session()
    return (session.query(Policy).
            filter(Policy.deleted == '').
            all())


def policy_name(name_or_id, session=None):
    session = session or db.get_session()
    try:
        ans = (session.query(Policy).
               filter(Policy.deleted == '').
               filter(Policy.id == name_or_id).
               one())
    except db_exc.NoResultFound:
        return name_or_id
    return ans.name


class PolicyRule(model_base.BASE, model_base.HasId, model_base.HasAudit):

    __tablename__ = "policy_rules"

    # TODO(thinrichs): change this so instead of storing the policy name
    #   we store the policy's ID.  Nontrivial since we often have the
    #   policy's name but not the ID; looking up the ID from the name
    #   outside of this class leads to race conditions, which means
    #   this class ought to be modified so that add/delete/etc. supports
    #   either name or ID as input.
    rule = sa.Column(sa.Text(), nullable=False)
    policy_name = sa.Column(sa.Text(), nullable=False)
    comment = sa.Column(sa.String(255), nullable=False)
    name = sa.Column(sa.String(255))

    def __init__(self, id, policy_name, rule, comment, deleted=False,
                 rule_name=""):
        self.id = id
        self.policy_name = policy_name
        self.rule = rule
        # FIXME(arosen) we should not be passing None for comment here.
        self.comment = comment or ""
        self.deleted = is_soft_deleted(id, deleted)
        self.name = rule_name

    def to_dict(self):
        d = {'rule': self.rule,
             'id': self.id,
             'comment': self.comment,
             'name': self.name}
        return d


def add_policy_rule(id, policy_name, rule, comment, deleted=False,
                    rule_name="", session=None):
    session = session or db.get_session()
    with session.begin(subtransactions=True):
        policy_rule = PolicyRule(id, policy_name, rule, comment,
                                 deleted, rule_name=rule_name)
        session.add(policy_rule)
    return policy_rule


def delete_policy_rule(id, session=None):
    """Specify either the ID or the NAME, and that policy is deleted."""
    session = session or db.get_session()
    return session.query(PolicyRule).filter(PolicyRule.id == id).soft_delete()


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


def get_policy_rules(policy_name=None, session=None,
                     deleted=False):
    session = session or db.get_session()
    rule_query = session.query(PolicyRule)
    if not deleted:
        rule_query = rule_query.filter(PolicyRule.deleted == '')
    else:
        rule_query = rule_query.filter(PolicyRule.deleted != '')
    if policy_name:
        rule_query = rule_query.filter(PolicyRule.policy_name == policy_name)
    return rule_query.all()


def is_soft_deleted(uuid, deleted):
    return '' if deleted is False else uuid
