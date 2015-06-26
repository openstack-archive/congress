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

import time

import eventlet
from oslo_log import log as logging
from oslo_utils import strutils

from congress.dse import d6cage
from congress.dse import deepsix
from congress.managers import datasource as datasource_manager

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    return Synchronizer(name, keys, inbox, datapath, args)


class Synchronizer(deepsix.deepSix):
    def __init__(self, name, keys, inbox, datapath, args):
        super(Synchronizer, self).__init__(name, keys, inbox, datapath)

        LOG.debug("init")

        if 'poll_time' in args:
            poll_time = int(args['poll_time'])
        else:
            poll_time = 0

        self.last_poll_time = None
        self.last_update = None
        self.datasource_mgr = datasource_manager.DataSourceManager()
        self.poller_greenthread = eventlet.spawn(self.poll_loop, poll_time)
        # unfortunately LifoQueue(maxsize=1) blocks writers if the queue is
        # full (or raises Full exception for non-blocking writers) so we use
        # a normal queue here and drain it to ensure we always get the latest
        # *poll_time* value
        self.timer_update_queue = eventlet.Queue()

    def set_poll_time(self, time):
        self.timer_update_queue.put(time)

    def poll_loop(self, poll_time):
        """Entrypoint for the synchronizer's poller greenthread.

        Triggers polling every *poll_time* seconds. If *poll_time* evaluates to
        False the thread will block waiting for a message to be sent via
        *set_poll_time*.

        :param poll_time: is the amount of time (in seconds) to wait between
        successful polling rounds.
        """
        while self.running:
            if poll_time:
                if self.last_poll_time is None:
                    self.do_poll()
                else:
                    try:
                        with eventlet.Timeout(poll_time):
                            poll_time = self.block_and_maybe_poll()
                    except eventlet.Timeout:
                        self.do_poll()
            else:
                poll_time = self.block_and_maybe_poll()

    def block_and_maybe_poll(self):
        poll_time = self.drain_timer_update_queue_blocking()
        if not poll_time:
            return
        time_since_last_poll = time.time() - self.last_poll_time
        if time_since_last_poll > poll_time:
            self.do_poll()
        return poll_time

    def drain_timer_update_queue_blocking(self):
        poll_time = self.timer_update_queue.get()
        while not self.timer_update_queue.empty():
            poll_time = self.timer_update_queue.get_nowait()
        return poll_time

    def do_poll(self):
        self.synchronize()
        self.last_poll_time = time.time()

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
