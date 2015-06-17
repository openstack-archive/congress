# Copyright (c) 2015 VMware, Inc. All rights reserved.
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

# The Synchronizer class performs periodic polling of the database to
# keep datasources in the Congress server in sync with the
# configuration in the database.  This is important because there may
# be more than one replica of the Congress server, each of which is
# able to modify the datasource configuration in the database.

import datetime

from oslo.utils import strutils

from congress.dse import d6cage
from congress.dse import deepsix
from congress.managers import datasource as datasource_manager
from congress.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return Synchronizer(name, keys, inbox, datapath, args)


class Synchronizer(deepsix.deepSix):
    def __init__(self, name, keys, inbox, datapath, args):
        super(Synchronizer, self).__init__(name, keys, inbox, datapath)

        LOG.debug("init")
        if 'poll_time' in args:
            self.poll_time = int(args['poll_time'])
        else:
            self.poll_time = 0
        self.last_poll_time = None
        self.last_update = None
        self.datasource_mgr = datasource_manager.DataSourceManager()

    def set_poll_time(self, time):
        self.poll_time = time

    def d6run(self):
        if self.poll_time:
            if self.last_poll_time is None:
                self.synchronize()
                self.last_poll_time = datetime.datetime.now()
            else:
                now = datetime.datetime.now()
                diff = now - self.last_poll_time
                seconds = diff.seconds + diff.days * 24 * 3600
                if seconds > self.poll_time:
                    self.synchronize()
                    self.last_poll_time = datetime.datetime.now()

    def synchronize(self):
        LOG.debug("Synchronizing running datasources")

        cage = d6cage.d6Cage()
        datasources = self.datasource_mgr.get_datasources(filter_secret=False)

        # Look for datasources in the db, but not in the cage.
        for configured_ds in datasources:
            active_ds = cage.service_object(configured_ds['name'])

            if active_ds is not None:
                if not configured_ds['enabled']:
                    LOG.info('Datasource %s now disabled, just delete it.',
                             configured_ds['name'])
                    self.datasource_mgr.delete_datasource(configured_ds['id'],
                                                          update_db=False)
                    continue

                active_config = cage.getservice(name=configured_ds['name'])
                if not self._config_eq(configured_ds, active_config):
                    LOG.debug('configured and active disagree: (%s) %s %s',
                              strutils.mask_password(active_ds),
                              strutils.mask_password(configured_ds),
                              strutils.mask_password(active_config))

                    LOG.info('Reloading datasource: %s',
                             strutils.mask_password(configured_ds))
                    self.datasource_mgr.delete_datasource(configured_ds['id'],
                                                          update_db=False)
                    self.datasource_mgr.add_datasource(
                        configured_ds,
                        update_db=False)
            else:
                if configured_ds['enabled']:
                    LOG.info('Configured datasource is not active, adding: %s',
                             strutils.mask_password(configured_ds))
                    self.datasource_mgr.add_datasource(configured_ds,
                                                       update_db=False)
                else:
                    LOG.info('Configured datasource is not active but ' +
                             'disabled, not adding: %s',
                             strutils.mask_password(configured_ds))

        # Look for datasources in the cage, but not in the db.  This
        # need not compare the configuration, because the above
        # comparison would have already checked the configuration.
        configured_dicts = dict((ds['name'], ds) for ds in datasources)
        LOG.debug("configured dicts: %s",
                  strutils.mask_password(configured_dicts))
        LOG.debug("active services: %s",
                  strutils.mask_password(cage.getservices()))
        for name, service in cage.getservices().items():
            LOG.debug('active datasource: %s', service['name'])
            if (service['type'] == 'datasource_driver' and
                    not configured_dicts.get(service['name'], None)):
                LOG.info('Active datasource is not configured, removing: %s',
                         service['name'])
                cage.deleteservice(service['name'])
                engine = cage.service_object('engine')
                engine.delete_policy(service['name'])

    def _config_eq(self, db_config, active_config):
        return (db_config['name'] == active_config['name'] and
                db_config['config'] == active_config['args'])
