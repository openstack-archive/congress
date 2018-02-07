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

import json

import sqlalchemy as sa
from sqlalchemy.orm import exc as db_exc

from congress.db import api as db
from congress.db import db_ds_table_data as table_data
from congress.db import model_base
from congress.db import utils as db_utils
from congress import encryption


class Datasource(model_base.BASE, model_base.HasId):
    __tablename__ = 'datasources'

    name = sa.Column(sa.String(255), unique=True)
    driver = sa.Column(sa.String(255))
    config = sa.Column(sa.Text(), nullable=False)
    description = sa.Column(sa.Text(), nullable=True)
    enabled = sa.Column(sa.Boolean, default=True)

    def __init__(self, id_, name, driver, config, description,
                 enabled=True):
        self.id = id_
        self.name = name
        self.driver = driver
        self.config = json.dumps(config)
        self.description = description
        self.enabled = enabled


def _encrypt_secret_config_fields(ds_db_obj, secret_config_fields):
    '''encrypt secret config fields'''
    config = json.loads(ds_db_obj.config)
    if config is None:  # nothing to encrypt
        return ds_db_obj  # return original obj
    if '__encrypted_fields' in config:
        raise Exception('Attempting to encrypt already encrypted datasource '
                        'DB object. This should not occer.')
    for field in secret_config_fields:
        config[field] = encryption.encrypt(config[field])
    config['__encrypted_fields'] = secret_config_fields
    ds_db_obj.config = json.dumps(config)
    return ds_db_obj


def _decrypt_secret_config_fields(ds_db_obj):
    '''de-encrypt previously encrypted secret config fields'''
    config = json.loads(ds_db_obj.config)
    if config is None:
        return ds_db_obj  # return original object
    if '__encrypted_fields' not in config:  # not previously encrypted
        return ds_db_obj  # return original object
    else:
        for field in config['__encrypted_fields']:
            config[field] = encryption.decrypt(config[field])
        del config['__encrypted_fields']
        ds_db_obj.config = json.dumps(config)
        return ds_db_obj


@db_utils.retry_on_db_error
def add_datasource(id_, name, driver, config, description,
                   enabled, session=None, secret_config_fields=None):
    secret_config_fields = secret_config_fields or []
    session = session or db.get_session()
    with session.begin(subtransactions=True):
        datasource = Datasource(
            id_=id_,
            name=name,
            driver=driver,
            config=config,
            description=description,
            enabled=enabled)
        _encrypt_secret_config_fields(datasource, secret_config_fields)
        session.add(datasource)
    return datasource


@db_utils.retry_on_db_error
def delete_datasource(id_, session=None):
    session = session or db.get_session()
    return session.query(Datasource).filter(
        Datasource.id == id_).delete()


@db_utils.retry_on_db_error
def delete_datasource_with_data(id_, session=None):
    session = session or db.get_session()
    with session.begin(subtransactions=True):
        deleted = delete_datasource(id_, session)
        table_data.delete_ds_table_data(id_, session=session)
    return deleted


@db_utils.retry_on_db_error
def get_datasource_name(name_or_id, session=None):
    session = session or db.get_session()
    datasource_obj = get_datasource(name_or_id, session)
    if datasource_obj is not None:
        return datasource_obj.name
    return name_or_id


def get_datasource(name_or_id, session=None):
    db_object = (get_datasource_by_name(name_or_id, session) or
                 get_datasource_by_id(name_or_id, session))

    return db_object


@db_utils.retry_on_db_error
def get_datasource_by_id(id_, session=None):
    session = session or db.get_session()
    try:
        return _decrypt_secret_config_fields(session.query(Datasource).
                                             filter(Datasource.id == id_).
                                             one())
    except db_exc.NoResultFound:
        pass


@db_utils.retry_on_db_error
def get_datasource_by_name(name, session=None):
    session = session or db.get_session()
    try:
        return _decrypt_secret_config_fields(session.query(Datasource).
                                             filter(Datasource.name == name).
                                             one())
    except db_exc.NoResultFound:
        pass


@db_utils.retry_on_db_error
def get_datasources(session=None, deleted=False):
    session = session or db.get_session()
    return [_decrypt_secret_config_fields(ds_obj)
            for ds_obj in session.query(Datasource).all()]
