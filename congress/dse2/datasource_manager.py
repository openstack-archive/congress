# Copyright (c) 2016 . All rights reserved.
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
from oslo_db import exception as db_exc
from oslo_log import log as logging

from congress.api import base as api_base
from congress.db import datasources as datasources_db
from congress.dse2 import data_service
from congress import exception
from congress.synchronizer import datasource_synchronizer

LOG = logging.getLogger(__name__)


class DSManagerService(data_service.DataService):
    """A proxy service to datasource managing methods in dse_node."""
    def __init__(self, service_id):
        super(DSManagerService, self).__init__(service_id)
        self.synchronizer = None
        self.add_rpc_endpoint(DSManagerEndpoints(self))

    def register_synchronizer(self):
        self.synchronizer = datasource_synchronizer.DatasourceSynchronizer(
            self.node)
        self.synchronizer.start()

    def start(self):
        super(DSManagerService, self).start()
        self.register_synchronizer()

    def stop(self):
        if self.synchronizer:
            self.synchronizer.stop()
        super(DSManagerService, self).stop()

    # Note(thread-safety): blocking function
    def add_datasource(self, item, deleted=False, update_db=True):
        req = self.make_datasource_dict(item)

        # check the request has valid information
        self.node.validate_create_datasource(req)
        if (len(req['name']) == 0 or req['name'][0] == '_'):
            raise exception.InvalidDatasourceName(value=req['name'])

        new_id = req['id']
        LOG.debug("adding datasource %s", req['name'])
        if update_db:
            LOG.debug("updating db")
            try:
                driver_info = self.node.get_driver_info(req['driver'])
                # Note(thread-safety): blocking call
                datasource = datasources_db.add_datasource(
                    id_=req['id'],
                    name=req['name'],
                    driver=req['driver'],
                    config=req['config'],
                    description=req['description'],
                    enabled=req['enabled'],
                    secret_config_fields=driver_info.get('secret', []))
            except db_exc.DBDuplicateEntry:
                raise exception.DatasourceNameInUse(value=req['name'])
            except db_exc.DBError:
                LOG.exception('Creating a new datasource failed due to '
                              'database backend error.')
                raise exception.DatasourceCreationError(value=req['name'])

        new_id = datasource['id']
        try:
            self.synchronizer.sync_datasource(req['name'])
            # immediate synch policies on local PE if present
            # otherwise wait for regularly scheduled synch
            engine = self.node.service_object(api_base.ENGINE_SERVICE_ID)
            if engine is not None:
                engine.synchronizer.sync_one_policy(req['name'])
            # TODO(dse2): also broadcast to all PE nodes to synch
        except exception.DataServiceError:
            LOG.debug('the datasource service is already '
                      'created in the node')
        except Exception:
            LOG.exception(
                'Unexpected exception encountered while registering '
                'new datasource %s.', req['name'])
            if update_db:
                datasources_db.delete_datasource(req['id'])
            msg = ("Datasource service: %s creation fails." % req['name'])
            raise exception.DatasourceCreationError(message=msg)

        new_item = dict(item)
        new_item['id'] = new_id
        return self.node.make_datasource_dict(new_item)

    # Note(thread-safety): blocking function
    def delete_datasource(self, datasource, update_db=True):
        LOG.debug("Deleting %s datasource ", datasource['name'])
        datasource_id = datasource['id']
        if update_db:
            # Note(thread-safety): blocking call
            result = datasources_db.delete_datasource_with_data(datasource_id)
            if not result:
                raise exception.DatasourceNotFound(id=datasource_id)

        # Note(thread-safety): blocking call
        try:
            self.synchronizer.sync_datasource(datasource['name'])
            # If local PE exists.. sync
            engine = self.node.service_object(api_base.ENGINE_SERVICE_ID)
            if engine:
                engine.synchronizer.sync_one_policy(datasource['name'])
        except Exception:
            msg = ('failed to synchronize_datasource after '
                   'deleting datasource: %s' % datasource_id)
            LOG.exception(msg)
            raise exception.DataServiceError(msg)


class DSManagerEndpoints(object):

    def __init__(self, service):
        self.ds_manager = service

    def add_datasource(self, context, items):
        return self.ds_manager.add_datasource(items)

    def delete_datasource(self, context, datasource):
        return self.ds_manager.delete_datasource(datasource)
