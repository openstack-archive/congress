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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

# The Synchronizer class performs periodic polling of the database to
# keep datasources in the Congress server in sync with the
# configuration in the database.  This is important because there may
# be more than one replica of the Congress server, each of which is
# able to modify the datasource configuration in the database.

import time

import eventlet
from oslo_log import log as logging
from oslo_utils import strutils

from congress.datalog import base
from congress.datalog import compile
from congress.db import db_policy_rules
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
        while self._running:
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
        try:
            self.synchronize_datasources()
        except Exception:
            LOG.exception("synchronize_datasources failed")

        try:
            self.synchronize_policies()
        except Exception:
            LOG.exception("synchronize_policies failed")

        try:
            self.synchronize_rules()
        except Exception:
            LOG.exception("synchronize_rules failed")

        self.last_poll_time = time.time()

    def synchronize_datasources(self):
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

    def synchronize_policies(self):
        LOG.debug("Synchronizing policies")
        # Read policies from DB.
        cage = d6cage.d6Cage()
        configured_policies = [{'id': p.id,
                                'name': p.name,
                                'abbr': p.abbreviation,
                                'desc': p.description,
                                'owner': p.owner,
                                'kind': p.kind}
                               for p in db_policy_rules.get_policies()]

        # Read policies from engine
        engine = cage.service_object('engine')
        policies = [engine.policy_object(n) for n in engine.policy_names()]
        active_policies = []
        for policy in policies:
            active_policies.append({'id': policy.id,
                                    'name': policy.name,
                                    'abbr': policy.abbr,
                                    'desc': policy.desc,
                                    'owner': policy.owner,
                                    'kind': policy.kind})

        added = 0
        removed = 0
        for p in active_policies:
            if (p['kind'] != base.DATASOURCE_POLICY_TYPE and
                    p not in configured_policies):
                LOG.debug("removing policy %s", str(p))
                engine.delete_policy(p['id'])
                removed = removed + 1

        for p in configured_policies:
            if p not in active_policies:
                LOG.debug("adding policy %s", str(p))
                engine.create_policy(p['name'], id_=p['id'], abbr=p['abbr'],
                                     kind=p['kind'], desc=p['desc'],
                                     owner=p['owner'])
                added = added + 1

        LOG.debug("synchronize_policies, added %d removed %d",
                  added, removed)

    def synchronize_rules(self):
        LOG.debug("Synchronizing rules")

        # Read rules from DB.
        cage = d6cage.d6Cage()
        configured_rules = [{'rule': r.rule,
                             'id': r.id,
                             'comment': r.comment,
                             'name': r.name,
                             'policy_name': r.policy_name}
                            for r in db_policy_rules.get_policy_rules()]

        # Read rules from engine
        engine = cage.service_object('engine')
        policies = {n: engine.policy_object(n) for n in engine.policy_names()}
        active_policy_rules = []
        for policy_name, policy in policies.items():
            if policy.kind != base.DATASOURCE_POLICY_TYPE:
                for active_rule in policy.content():
                    active_policy_rules.append(
                        {'rule': active_rule.original_str,
                         'id': active_rule.id,
                         'comment': active_rule.comment,
                         'name': active_rule.name,
                         'policy_name': policy_name})

        # ALEX: the Rule object does not have fields like the rule-string or
        # id or comment.  We can add those fields to the Rule object, as long
        # as we don't add them to the Fact because there are many fact
        # instances.  If a user tries to create a lot of Rules, they are
        # probably doing something wrong and should use a datasource driver
        # instead.

        changes = []
        for r in configured_rules:
            if r not in active_policy_rules:
                LOG.debug("adding rule %s", str(r))
                parsed_rule = engine.parse1(r['rule'])
                parsed_rule.set_id(r['id'])
                parsed_rule.set_name(r['name'])
                parsed_rule.set_comment(r['comment'])
                parsed_rule.set_original_str(r['rule'])

                event = compile.Event(formula=parsed_rule,
                                      insert=True,
                                      target=r['policy_name'])
                changes.append(event)

        for r in active_policy_rules:
            if r not in configured_rules:
                LOG.debug("removing rule %s", str(r))
                parsed_rule = engine.parse1(r['rule'])
                parsed_rule.set_id(r['id'])
                parsed_rule.set_name(r['name'])
                parsed_rule.set_comment(r['comment'])
                parsed_rule.set_original_str(r['rule'])

                event = compile.Event(formula=parsed_rule,
                                      insert=False,
                                      target=r['policy_name'])
                changes.append(event)
        permitted, changes = engine.process_policy_update(changes)
        LOG.debug("synchronize_rules, permitted %d, made %d changes",
                  permitted, len(changes))
