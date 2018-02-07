# Copyright (c) 2017 VMware, Inc. All rights reserved.
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

import json

from oslo_db import exception as oslo_db_exc
import sqlalchemy as sa
from sqlalchemy.orm import exc as db_exc

from congress.db import api as db
from congress.db import model_base
from congress.db import utils as db_utils


class LibraryPolicy(model_base.BASE, model_base.HasId):
    __tablename__ = 'library_policies'

    name = sa.Column(sa.String(255), nullable=False, unique=True)
    abbreviation = sa.Column(sa.String(5), nullable=False)
    description = sa.Column(sa.Text(), nullable=False)
    kind = sa.Column(sa.Text(), nullable=False)
    rules = sa.Column(sa.Text(), nullable=False)

    def to_dict(self, include_rules=True, json_rules=False):
        """From a given library policy, return a policy dict.

        :param: include_rules (bool, optional): include policy rules in return
                dictionary. Defaults to False.
        """
        if not include_rules:
            d = {'id': self.id,
                 'name': self.name,
                 'abbreviation': self.abbreviation,
                 'description': self.description,
                 'kind': self.kind}
        else:
            d = {'id': self.id,
                 'name': self.name,
                 'abbreviation': self.abbreviation,
                 'description': self.description,
                 'kind': self.kind,
                 'rules': (self.rules if json_rules
                           else json.loads(self.rules))}
        return d


@db_utils.retry_on_db_error
def add_policy(policy_dict, session=None):
    session = session or db.get_session()
    try:
        with session.begin(subtransactions=True):
            new_row = LibraryPolicy(
                name=policy_dict['name'],
                abbreviation=policy_dict['abbreviation'],
                description=policy_dict['description'],
                kind=policy_dict['kind'],
                rules=json.dumps(policy_dict['rules']))
            session.add(new_row)
        return new_row
    except oslo_db_exc.DBDuplicateEntry:
        raise KeyError(
            "Policy with name %s already exists" % policy_dict['name'])


@db_utils.retry_on_db_error
def replace_policy(id_, policy_dict, session=None):
    session = session or db.get_session()
    try:
        with session.begin(subtransactions=True):
            new_row = LibraryPolicy(
                id=id_,
                name=policy_dict['name'],
                abbreviation=policy_dict['abbreviation'],
                description=policy_dict['description'],
                kind=policy_dict['kind'],
                rules=json.dumps(policy_dict['rules']))
            session.query(LibraryPolicy).filter(
                LibraryPolicy.id == id_).one().update(
                new_row.to_dict(include_rules=True, json_rules=True))
        return new_row
    except db_exc.NoResultFound:
        raise KeyError('No policy found with policy id %s' % id_)


@db_utils.retry_on_db_error
def delete_policy(id_, session=None):
    session = session or db.get_session()
    return session.query(LibraryPolicy).filter(
        LibraryPolicy.id == id_).delete()


@db_utils.retry_on_db_error
def delete_policies(session=None):
    session = session or db.get_session()
    return session.query(LibraryPolicy).delete()


@db_utils.retry_on_db_error
def get_policy(id_, session=None):
    session = session or db.get_session()
    try:
        return session.query(LibraryPolicy).filter(
            LibraryPolicy.id == id_).one()
    except db_exc.NoResultFound:
        raise KeyError('No policy found with policy id %s' % id_)


@db_utils.retry_on_db_error
def get_policy_by_name(name, session=None):
    session = session or db.get_session()
    try:
        return session.query(LibraryPolicy).filter(
            LibraryPolicy.name == name).one()
    except db_exc.NoResultFound:
        raise KeyError('No policy found with policy name %s' % name)


@db_utils.retry_on_db_error
def get_policies(session=None):
    session = session or db.get_session()
    return (session.query(LibraryPolicy).all())
