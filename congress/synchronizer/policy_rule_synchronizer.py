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

from congress.datalog import base
from congress.datalog import compile
from congress.db import datasources
from congress.db import db_policy_rules

LOG = logging.getLogger(__name__)

SYNCHRONIZER_SERVICE_ID = '_policy_rule_synchronizer'


class PolicyRuleSynchronizer(object):

    def __init__(self, service_obj, node):
        self.name = SYNCHRONIZER_SERVICE_ID
        self.engine = service_obj
        self.sync_thread = None
        self.periodic_tasks = None
        self.node = node

    def start(self):
        callables = [(self.synchronize_all_policies, None, {}),
                     (self.synchronize_rules, None, {})]
        self.periodic_tasks = periodics.PeriodicWorker(callables)
        self.sync_thread = eventlet.spawn_n(self.periodic_tasks.start)
        LOG.info("started policy-rule synchronizer on node %s",
                 self.node.node_id)

    def stop(self):
        if self.periodic_tasks:
            self.periodic_tasks.stop()
            self.periodic_tasks.wait()
            self.periodic_tasks = None
        if self.sync_thread is not None:
            eventlet.greenthread.kill(self.sync_thread)
            self.sync_thread = None

    def _register_datasource_with_pe(self, ds_name):
        """create datasource policy in PE for newly created datasource."""
        if not self.node.is_valid_service(ds_name):
            # datasource service not up, nothing to register
            return
        # Get the datasource schema to sync the schema with PE
        schema = self.node.invoke_service_rpc(ds_name, 'get_datasource_schema',
                                              {'source_id': ds_name})
        self.engine.initialize_datasource(ds_name, schema)
        LOG.debug("registered datasource '%s' with PE on node %s", ds_name,
                  self.node.node_id)

    def _sync_datasource_policies(self):
        added = 0
        removed = 0
        db_datasources = [ds['name'] for ds in self.node.get_datasources()]
        ds_policies = [p['name'] for p in
                       self._get_engine_policies(datasource=True)]

        for ds in db_datasources:
            # check if ds is registered with PE
            if ds not in ds_policies:
                self._register_datasource_with_pe(ds)
                added = added + 1

        # get the policies registered with PE , but not in database
        remove_policies = list(set(ds_policies) - set(db_datasources))
        for p in remove_policies:
            self.engine.delete_policy(p)
            removed = removed+1

        LOG.debug("datasource policies synchronized, added %d removed %d ",
                  added, removed)

    def _get_engine_policies(self, datasource=False):
        all_policies = [self.engine.policy_object(n) for n in
                        self.engine.policy_names()]
        dpolicies = [p for p in all_policies
                     if p.kind == base.DATASOURCE_POLICY_TYPE]
        epolicies = list(set(all_policies) - set(dpolicies))
        policies = dpolicies if datasource else epolicies
        active_policies = []
        for policy in policies:
            active_policies.append({'id': policy.id,
                                    'name': policy.name,
                                    'abbreviation': policy.abbr,
                                    'description': policy.desc,
                                    'owner_id': policy.owner,
                                    'kind': policy.kind})

        return active_policies

    @lockutils.synchronized('congress_synchronize_policies')
    def sync_one_policy(self, name, datasource=True, db_session=None):
        return self.sync_one_policy_nonlocking(
            name, datasource=datasource, db_session=db_session)

    def sync_one_policy_nonlocking(
            self, name, datasource=True, db_session=None):
        """Synchronize single policy with DB.

        :param: name: policy name to be synchronized
        :param: datasource: True, to sync a datasource policy

        """
        LOG.info("sync %s policy with DB", name)

        if datasource:
            policy_object = datasources.get_datasource_by_name(
                name, session=db_session)
            if policy_object is not None:
                if name not in self.engine.policy_names():
                    self._register_datasource_with_pe(name)
                return

        policy_object = db_policy_rules.get_policy_by_name(
            name, session=db_session)
        if policy_object is None:
            if name in self.engine.policy_names():
                self.engine.delete_policy(name)
                LOG.info("policy %s deleted by synchronizer", name)
            return

        p = policy_object.to_dict()
        if name not in self.engine.policy_names():
            self.engine.create_policy(
                p['name'], id_=p['id'], abbr=p['abbreviation'],
                kind=p['kind'], desc=p['description'],
                owner=p['owner_id'])
            LOG.debug("policy %s added by synchronizer", name)

        elif p['id'] != self.engine.policy_object(name).id:
            # if same name but not identical attributes
            # replace by new policy obj according to DB
            self.engine.delete_policy(name)
            self.engine.create_policy(
                p['name'], id_=p['id'], abbr=p['abbreviation'],
                kind=p['kind'], desc=p['description'],
                owner=p['owner_id'])
            LOG.debug("synchronizer, policy replaced %s", name)

    @periodics.periodic(spacing=cfg.CONF.datasource_sync_period)
    @lockutils.synchronized('congress_synchronize_policies')
    def synchronize_all_policies(self):
        """Function to synchronize im-mem policies with DB"""
        added = 0
        removed = 0
        try:
            db_policies = [p.to_dict() for p in db_policy_rules.get_policies()]
            active_policies = self._get_engine_policies()
            # Delete engine policies which are not in DB
            for p in active_policies:
                if p not in db_policies:
                    LOG.debug("removing policy %s", str(p))
                    self.engine.delete_policy(p['id'])
                    removed = removed + 1
            # Add policies to PE, which are in DB
            for p in db_policies:
                if p not in active_policies:
                    LOG.debug("adding policy %s", str(p))
                    self.engine.create_policy(p['name'], id_=p['id'],
                                              abbr=p['abbreviation'],
                                              kind=p['kind'],
                                              desc=p['description'],
                                              owner=p['owner_id'])
                    added = added + 1
            LOG.info("engine policies synchronized, added %d removed %d ",
                     added, removed)
            # synchronize datasource policies
            self._sync_datasource_policies()
            LOG.info("completed synchronization of policies")
        except Exception:
            LOG.exception("Exception occurred in policy synchronizer periodic"
                          "task on node %s", self.node.node_id)
            return

    @periodics.periodic(spacing=cfg.CONF.datasource_sync_period)
    @lockutils.synchronized('congress_synchronize_rules')
    def synchronize_rules(self, db_session=None):
        self.synchronize_rules_nonlocking(db_session=db_session)

    def synchronize_rules_nonlocking(self, db_session=None):
        LOG.debug("Synchronizing rules on node %s", self.node.node_id)
        try:
            # Read rules from DB.
            configured_rules = []
            configured_facts = []
            for r in db_policy_rules.get_policy_rules(session=db_session):
                if ':-' in r.rule:  # if rule has body
                    configured_rules.append({'rule': r.rule,
                                             'id': r.id,
                                             'comment': r.comment,
                                             'name': r.name,
                                             'policy_name': r.policy_name})
                else:  # head-only rule, ie., fact
                    configured_facts.append(
                        {'rule': self.engine.parse1(r.rule).pretty_str(),
                         # note:parse to remove effect of extraneous formatting
                         'policy_name': r.policy_name})

            # Read rules from engine
            policies = {n: self.engine.policy_object(n) for n in
                        self.engine.policy_names()}
            active_policy_rules = []
            active_policy_facts = []
            for policy_name, policy in policies.items():
                if policy.kind != base.DATASOURCE_POLICY_TYPE:
                    for active_rule in policy.content():
                        # FIXME: This assumes r.original_str is None iff
                        # r is a head-only rule (fact). This works in
                        # non-recursive policy but not in recursive policies
                        if active_rule.original_str is None:
                            active_policy_facts.append(
                                {'rule': str(active_rule.head),
                                 'policy_name': policy_name})
                        else:
                            active_policy_rules.append(
                                {'rule': active_rule.original_str,
                                 'id': active_rule.id,
                                 'comment': active_rule.comment,
                                 'name': active_rule.name,
                                 'policy_name': policy_name})

            # ALEX: the Rule object does not have fields like the rule-string
            # or id or comment.  We can add those fields to the Rule object,
            # as long as we don't add them to the Fact because there are many
            # fact instances.  If a user tries to create a lot of Rules, they
            # are probably doing something wrong and should use a datasource
            # driver instead.

            changes = []

            # add configured rules
            for r in configured_rules:
                if r not in active_policy_rules:
                    LOG.debug("adding rule %s", str(r))
                    parsed_rule = self.engine.parse1(r['rule'])
                    parsed_rule.set_id(r['id'])
                    parsed_rule.set_name(r['name'])
                    parsed_rule.set_comment(r['comment'])
                    parsed_rule.set_original_str(r['rule'])

                    event = compile.Event(formula=parsed_rule,
                                          insert=True,
                                          target=r['policy_name'])
                    changes.append(event)

            # add configured facts
            for r in configured_facts:
                if r not in active_policy_facts:
                    LOG.debug("adding rule %s", str(r))
                    parsed_rule = self.engine.parse1(r['rule'])
                    event = compile.Event(formula=parsed_rule,
                                          insert=True,
                                          target=r['policy_name'])
                    changes.append(event)

            # remove active rules not configured
            for r in active_policy_rules:
                if r not in configured_rules:
                    LOG.debug("removing rule %s", str(r))
                    parsed_rule = self.engine.parse1(r['rule'])
                    parsed_rule.set_id(r['id'])
                    parsed_rule.set_name(r['name'])
                    parsed_rule.set_comment(r['comment'])
                    parsed_rule.set_original_str(r['rule'])

                    event = compile.Event(formula=parsed_rule,
                                          insert=False,
                                          target=r['policy_name'])
                    changes.append(event)

            # remove active facts not configured
            for r in active_policy_facts:
                if r not in configured_facts:
                    LOG.debug("removing rule %s", str(r))
                    parsed_rule = self.engine.parse1(r['rule'])
                    event = compile.Event(formula=parsed_rule,
                                          insert=False,
                                          target=r['policy_name'])
                    changes.append(event)

            permitted, changes = self.engine.process_policy_update(changes)
            LOG.info("synchronize_rules, permitted %d, made %d changes on "
                     "node %s", permitted, len(changes), self.node.node_id)
        except Exception:
            LOG.exception("synchronizing rules failed")
