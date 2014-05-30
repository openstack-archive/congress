#!/usr/bin/env python
# Copyright (c) 2013 VMware, Inc. All rights reserved.
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
#

import argparse
import sys
import time

import eventlet
eventlet.patcher.monkey_patch()

import ovs.daemon
import ovs.vlog
vlog = ovs.vlog.Vlog(__name__)

from ad_sync import UserGroupDataModel
from api.webservice import ApiApplication
from api.webservice import CollectionHandler
from api.webservice import ElementHandler
from api.webservice import PolicyDataModel
from api.webservice import RowCollectionHandler
from api.webservice import RowElementHandler
from api.webservice import SimpleDataModel
from api.wsgi import Server


DEFAULT_HTTP_ADDR = '0.0.0.0'
DEFAULT_HTTP_PORT = 8080


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http_listen_port", default=DEFAULT_HTTP_PORT)
    parser.add_argument("--http_listen_addr", default=DEFAULT_HTTP_ADDR)
    ovs.vlog.add_args(parser)
    ovs.daemon.add_args(parser)

    args = parser.parse_args()
    ovs.vlog.handle_args(args)
    ovs.daemon.handle_args(args)

    wsgi_server = Server("API Broker")
    api = ApiApplication()

    tables_model = SimpleDataModel()
    table_collection_handler = CollectionHandler('/tables', tables_model)
    api.register_handler(table_collection_handler)
    table_element_handler = ElementHandler('/tables/([^/]+)', tables_model,
                                           table_collection_handler)
    api.register_handler(table_element_handler)

    rows_model = SimpleDataModel()
    #TODO(pjb): scope model per table
    rows_collection_handler = RowCollectionHandler('/tables/([^/]+)/rows',
                                                   rows_model)
    api.register_handler(rows_collection_handler)
    rows_element_handler = RowElementHandler(
        '/tables/([^/]+)/rows/([^/]+)', rows_model,
        rows_collection_handler)
    api.register_handler(rows_element_handler)

    policy_model = PolicyDataModel()
    policy_element_handler = ElementHandler('/policy', policy_model)
    api.register_handler(policy_element_handler)

    ad_model = UserGroupDataModel()

    def ad_update_thread():
        while True:
            ad_model.update_from_ad()  # XXX: blocks eventlet
            time.sleep(3)

    wsgi_server.pool.spawn_n(ad_update_thread)

    ad_row_handler = CollectionHandler('/tables/ad-groups/rows', ad_model)
    api.register_handler(ad_row_handler, 0)
    # Add static tables to model
    tables_model.add_item({'sample': 'schema', 'id': 'ad-groups'}, 'ad-groups')

    vlog.info("Starting congress server")
    wsgi_server.start(api, args.http_listen_port,
                      args.http_listen_addr)
    wsgi_server.wait()

    #TODO(pjb): trigger watcher for policy outputs


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        vlog.exception("traceback")
        sys.exit(ovs.daemon.RESTART_EXIT_CODE)
