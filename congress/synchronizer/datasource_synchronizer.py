# Copyright (c) 2016 NEC Corp. All rights reserved.
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

import eventlet
from futurist import periodics
from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_log import log as logging

from congress.db import datasources

LOG = logging.getLogger(__name__)

SYNCHRONIZER_SERVICE_ID = '_datasource_synchronizer'


class DatasourceSynchronizer(object):

    def __init__(self, node):
        self.name = SYNCHRONIZER_SERVICE_ID
        self.sync_thread = None
        self.periodic_tasks = None
        self.node = node

    def start(self):
        callables = [(self.synchronize_all_datasources, None, {}),
                     (self._check_resub_all, None, {})]
        self.periodic_tasks = periodics.PeriodicWorker(callables)
        self.sync_thread = eventlet.spawn_n(self.periodic_tasks.start)
        LOG.info("started datasource synchronizer on node %s",
                 self.node.node_id)

    def stop(self):
        if self.periodic_tasks:
            self.periodic_tasks.stop()
            self.periodic_tasks.wait()
            self.periodic_tasks = None
        if self.sync_thread:
            eventlet.greenthread.kill(self.sync_thread)
            self.sync_thread = None

    @periodics.periodic(spacing=cfg.CONF.dse.time_to_resub)
    def _check_resub_all(self):
        LOG.debug("Running periodic resub on node %s", self.node.node_id)
        for s in self.node.get_services(True):
            s.check_resub_all()

    @lockutils.synchronized('congress_synchronize_datasources')
    def sync_datasource(self, ds_name):
        if not cfg.CONF.datasources:
            LOG.info("sync not supported on non-datasource node")
            return
        datasource = datasources.get_datasource_by_name(ds_name)
        service_obj = self.node.service_object(ds_name)

        if datasource and not service_obj:
            # register service with data node
            service = self.node.create_datasource_service(datasource)
            self.node.register_service(service)
            LOG.debug("service %s registered by synchronizer", ds_name)
            return
        if service_obj and datasource is None:
            # unregister, datasource not present in DB
            self.node.unregister_service(ds_name)
            LOG.debug("service %s unregistered by synchronizer", ds_name)
            return

    @lockutils.synchronized('congress_synchronize_datasources')
    @periodics.periodic(spacing=cfg.CONF.datasource_sync_period)
    def synchronize_all_datasources(self):
        LOG.debug("synchronizing datasources on node %s", self.node.node_id)
        added = 0
        removed = 0
        datasources = self.node.get_datasources(filter_secret=False)
        db_datasources = []
        # Look for datasources in the db, but not in the services.
        for configured_ds in datasources:
            db_datasources.append(configured_ds['id'])
            active_ds = self.node.service_object(uuid_=configured_ds['id'])
            # If datasource is not enabled, unregister the service
            if not configured_ds['enabled']:
                if active_ds:
                    LOG.debug("unregistering %s service, datasource disabled "
                              "in DB.", active_ds.service_id)
                    self.node.unregister_service(active_ds.service_id)
                    removed = removed + 1
                continue
            if active_ds is None:
                # service is not up, create the service
                LOG.debug("registering %s service on node %s",
                          configured_ds['name'], self.node.node_id)
                service = self.node.create_datasource_service(configured_ds)
                self.node.register_service(service)
                added = added + 1

        # Unregister the services which are not in DB
        active_ds_services = [s for s in self.node.get_services(True)
                              if getattr(s, 'type', '') == 'datasource_driver']
        db_datasources_set = set(db_datasources)
        stale_services = [s for s in active_ds_services
                          if s.ds_id not in db_datasources_set]
        for s in stale_services:
            LOG.debug("unregistering %s service, datasource not found in DB ",
                      s.service_id)
            self.node.unregister_service(uuid_=s.ds_id)
            removed = removed + 1

        LOG.info("synchronized datasources, added %d removed %d on node %s",
                 added, removed, self.node.node_id)

        # This might be required once we support update datasource config
        # if not self._config_eq(configured_ds, active_ds):
        #    LOG.debug('configured and active disagree: %s %s',
        #              strutils.mask_password(active_ds),
        #              strutils.mask_password(configured_ds))

        #    LOG.info('Reloading datasource: %s',
        #             strutils.mask_password(configured_ds))
        #    self.delete_datasource(configured_ds['name'],
        #                           update_db=False)
        #    self.add_datasource(configured_ds, update_db=False)

    # def _config_eq(self, db_config, active_config):
    #     return (db_config['name'] == active_config.service_id and
    #             db_config['config'] == active_config.service_info['args'])
