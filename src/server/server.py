#!/usr/bin/env python
# Copyright (c) 2013 VMware, Inc. All rights reserved.

import argparse
import sys
import time

import eventlet
eventlet.patcher.monkey_patch()

import ovs.daemon
import ovs.vlog
vlog = ovs.vlog.Vlog(__name__)

from ad_sync import UserGroupDataModel
from webservice import ApiApplication
from webservice import CollectionHandler
from webservice import ElementHandler
from webservice import PolicyDataModel
from webservice import RowCollectionHandler
from webservice import RowElementHandler
from webservice import SimpleDataModel
from wsgi import Server


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
    #TODO: scope model per table
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

    ad_row_handler = CollectionHandler( '/tables/ad-groups/rows', ad_model)
    api.register_handler(ad_row_handler, 0)
    # Add static tables to model
    tables_model.add_item({'sample': 'schema', 'id': 'ad-groups'}, 'ad-groups')


    vlog.info("Starting congress server")
    wsgi_server.start(api, args.http_listen_port,
                      args.http_listen_addr)
    wsgi_server.wait()

    #TODO: trigger watcher for policy outputs


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except:
        vlog.exception("traceback")
        sys.exit(ovs.daemon.RESTART_EXIT_CODE)
