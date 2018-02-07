# Copyright (c) 2016 VMware, Inc. All rights reserved.
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
from congress.db import model_base
from congress.db import utils as db_utils


class DSTableData(model_base.BASE):
    __tablename__ = 'dstabledata'

    ds_id = sa.Column(sa.String(36), nullable=False, primary_key=True)
    tablename = sa.Column(sa.String(255), nullable=False, primary_key=True)
    # choose long length compatible with MySQL, SQLite, Postgres
    tabledata = sa.Column(sa.Text(), nullable=False)


@db_utils.retry_on_db_error
def store_ds_table_data(ds_id, tablename, tabledata, session=None):
    session = session or db.get_session()
    tabledata = _json_encode_table_data(tabledata)
    with session.begin(subtransactions=True):
        new_row = session.merge(DSTableData(
            ds_id=ds_id,
            tablename=tablename,
            tabledata=tabledata))
    return new_row


@db_utils.retry_on_db_error
def delete_ds_table_data(ds_id, tablename=None, session=None):
    session = session or db.get_session()
    if tablename is None:
        return session.query(DSTableData).filter(
            DSTableData.ds_id == ds_id).delete()
    else:
        return session.query(DSTableData).filter(
            DSTableData.ds_id == ds_id,
            DSTableData.tablename == tablename).delete()


@db_utils.retry_on_db_error
def get_ds_table_data(ds_id, tablename=None, session=None):
    session = session or db.get_session()
    try:
        if tablename is None:
            rows = session.query(DSTableData).filter(
                DSTableData.ds_id == ds_id)
            return_list = []
            for row in rows:
                return_list.append(
                    {'tablename': row.tablename,
                     'tabledata': _json_decode_table_data(row.tabledata)})
            return return_list
        else:
            return _json_decode_table_data(session.query(DSTableData).filter(
                DSTableData.ds_id == ds_id,
                DSTableData.tablename == tablename).one().tabledata)
    except db_exc.NoResultFound:
        pass


def _json_encode_table_data(tabledata):
    tabledata = list(tabledata)
    for i in range(0, len(tabledata)):
        tabledata[i] = list(tabledata[i])
    return json.dumps(tabledata)


def _json_decode_table_data(json_tabledata):
    tabledata = json.loads(json_tabledata)
    for i in range(0, len(tabledata)):
        tabledata[i] = tuple(tabledata[i])
    return set(tabledata)
