# Copyright 2011 VMware, Inc.
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

from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import session
from oslo_log import log as logging

from congress import exception as congress_exc

LOG = logging.getLogger(__name__)

_FACADE = None


def _create_facade_lazily():
    global _FACADE

    if _FACADE is None:
        _FACADE = session.EngineFacade.from_config(cfg.CONF, sqlite_fk=True)

    return _FACADE


def get_engine():
    """Helper method to grab engine."""
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(autocommit=True, expire_on_commit=False, make_new=False):
    """Helper method to grab session."""
    if make_new:  # do not reuse existing facade
        facade = session.EngineFacade.from_config(cfg.CONF, sqlite_fk=True)
    else:
        facade = _create_facade_lazily()
    return facade.get_session(autocommit=autocommit,
                              expire_on_commit=expire_on_commit)


def get_locking_session():
    """Obtain db_session that works with table locking

    supported backends: MySQL and PostgreSQL
    return default session if backend not supported (eg. sqlite)
    """
    if is_mysql() or is_postgres():
        db_session = get_session(
            autocommit=False,
            # to prevent implicit new transactions,
            # which UNLOCKS in MySQL
            expire_on_commit=False,  # need to UNLOCK after commit
            make_new=True)  # brand new facade avoids interference

    else:  # unsupported backend for locking (eg sqlite), return default
        db_session = get_session()

    return db_session


def lock_tables(session, tables):
    """Write-lock tables for supported backends: MySQL and PostgreSQL"""
    session.begin(subtransactions=True)
    if is_mysql():  # Explicitly LOCK TABLES for MySQL
        session.execute('SET autocommit=0')
        session.execute('LOCK TABLES {}'.format(
            ','.join([table + ' WRITE' for table in tables])))
    elif is_postgres():  # Explicitly LOCK TABLE for Postgres
        session.execute('BEGIN TRANSACTION')
        for table in tables:
            session.execute('LOCK TABLE {} IN EXCLUSIVE MODE'.format(table))


def commit_unlock_tables(session):
    """Commit and unlock tables for supported backends: MySQL and PostgreSQL"""
    try:
        session.execute('COMMIT')  # execute COMMIT on DB backend
        session.commit()
        # because sqlalchemy session does not guarantee
        # exact boundary correspondence to DB backend transactions
        # We must guarantee DB commits transaction before UNLOCK

        # unlock
        if is_mysql():
            session.execute('UNLOCK TABLES')
        # postgres automatically releases lock at transaction end
    except db_exc.DBDataError as exc:
        LOG.exception('Database backend experienced data error.')
        raise congress_exc.DatabaseDataError(data=exc)


def rollback_unlock_tables(session):
    """Rollback and unlock tables

    supported backends: MySQL and PostgreSQL
    """
    # unlock
    if is_mysql():
        session.execute('UNLOCK TABLES')

    # postgres automatically releases lock at transaction end

    session.rollback()


def is_mysql():
    """Return true if and only if database backend is mysql"""
    return (cfg.CONF.database.connection is not None and
            (cfg.CONF.database.connection.split(':/')[0] == 'mysql' or
             cfg.CONF.database.connection.split('+')[0] == 'mysql'))


def is_postgres():
    """Return true if and only if database backend is postgres"""
    return (cfg.CONF.database.connection is not None and
            (cfg.CONF.database.connection.split(':/')[0] == 'postgresql' or
             cfg.CONF.database.connection.split('+')[0] == 'postgresql'))


def is_sqlite():
    """Return true if and only if database backend is sqlite"""
    return (cfg.CONF.database.connection is not None and
            (cfg.CONF.database.connection.split(':/')[0] == 'sqlite' or
             cfg.CONF.database.connection.split('+')[0] == 'sqlite'))
