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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import time

import eventlet
from oslo_concurrency import lockutils
from oslo_config import cfg
from oslo_log import log as logging
from oslo_messaging import exceptions as messaging_exceptions
from oslo_utils import uuidutils
import six
from six.moves import range

from congress.datalog import base
from congress.datalog import compile
from congress.datalog import database as db
from congress.datalog import materialized
from congress.datalog import nonrecursive
from congress.datalog import unify
from congress.datalog import utility
from congress.db import api as db_api
from congress.db import db_policy_rules
from congress.dse2 import data_service
from congress import exception
from congress.synchronizer import policy_rule_synchronizer
from congress import utils
from congress.z3 import z3theory
from congress.z3 import z3types

LOG = logging.getLogger(__name__)


class ExecutionLogger(object):
    def __init__(self):
        self.messages = []

    def debug(self, msg, *args):
        self.messages.append(msg % args)

    def info(self, msg, *args):
        self.messages.append(msg % args)

    def warn(self, msg, *args):
        self.messages.append(msg % args)

    def error(self, msg, *args):
        self.messages.append(msg % args)

    def critical(self, msg, *args):
        self.messages.append(msg % args)

    def content(self):
        return '\n'.join(self.messages)

    def empty(self):
        self.messages = []


def list_to_database(atoms):
    database = db.Database()
    for atom in atoms:
        if atom.is_atom():
            database.insert(atom)
    return database


def string_to_database(string, theories=None):
    return list_to_database(compile.parse(
        string, theories=theories))


##############################################################################
# Runtime
##############################################################################

class Trigger(object):
    """A chunk of code that should be run when a table's contents changes."""

    def __init__(self, tablename, policy, callback, modal=None):
        self.tablename = tablename
        self.policy = policy
        self.callback = callback
        self.modal = modal

    def __str__(self):
        return "Trigger on table=%s; policy=%s; modal=%s with callback %s." % (
            self.tablename, self.policy, self.modal, self.callback)


class TriggerRegistry(object):
    """A collection of triggers and algorithms to analyze that collection."""

    def __init__(self, dependency_graph):
        # graph containing relationships between tables
        self.dependency_graph = dependency_graph

        # set of triggers that are currently registered
        self.triggers = set()

        # map from table to triggers relevant to changes for that table
        self.index = {}

    def register_table(self, tablename, policy, callback, modal=None):
        """Register CALLBACK to run when TABLENAME changes."""
        # TODO(thinrichs): either fix dependency graph to differentiate
        #   between execute[alice:p] and alice:p or reject rules
        #   in which both occur
        trigger = Trigger(tablename, policy, callback, modal=modal)
        self.triggers.add(trigger)
        self._add_indexes(trigger)
        LOG.info("registered trigger: %s", trigger)
        return trigger

    def unregister(self, trigger):
        """Unregister trigger ID."""
        self.triggers.remove(trigger)
        self._delete_indexes(trigger)

    def update_dependencies(self, dependency_graph_changes=None):
        """Inform registry of changes to the dependency graph.

        Changes are accounted for in self.dependency_graph, but
        by giving the list of changes we can avoid recomputing
        all dependencies from scratch.
        """
        # TODO(thinrichs): instead of destroying the index and
        #   recomputing from scratch, look at the changes and
        #   figure out the delta.
        self.index = {}
        for trigger in self.triggers:
            self._add_indexes(trigger)

    def _add_indexes(self, trigger):
        full_table = compile.Tablename.build_service_table(
            trigger.policy, trigger.tablename)
        deps = self.dependency_graph.dependencies(full_table)
        if deps is None:
            deps = set([full_table])
        for table in deps:
            if table in self.index:
                self.index[table].add(trigger)
            else:
                self.index[table] = set([trigger])

    def _delete_indexes(self, trigger):
        full_table = compile.Tablename.build_service_table(
            trigger.policy, trigger.tablename)
        deps = self.dependency_graph.dependencies(full_table)
        if deps is None:
            deps = set([full_table])
        for table in deps:
            self.index[table].discard(trigger)

    def relevant_triggers(self, events):
        """Return the set of triggers that are relevant to the EVENTS.

        Each EVENT may either be a compile.Event or a tablename.
        """
        table_changes = set()
        for event in events:
            if isinstance(event, compile.Event):
                if compile.is_rule(event.formula):
                    table_changes |= set(
                        [lit.table.global_tablename(event.target)
                         for lit in event.formula.heads])
                else:
                    table_changes.add(
                        event.formula.table.global_tablename(event.target))
            elif isinstance(event, six.string_types):
                table_changes.add(event)
        triggers = set()
        for table in table_changes:
            if table in self.index:
                triggers |= self.index[table]
        return triggers

    def _index_string(self):
        """Build string representation of self.index; useful for debugging."""
        s = '{'
        s += ";".join(["%s -> %s" % (key, ",".join(str(x) for x in value))
                       for key, value in self.index.items()])
        s += '}'
        return s

    @classmethod
    def triggers_by_table(cls, triggers):
        """Return dictionary from tables to triggers."""
        d = {}
        for trigger in triggers:
            table = (trigger.tablename, trigger.policy, trigger.modal)
            if table not in d:
                d[table] = [trigger]
            else:
                d[table].append(trigger)
        return d


class Runtime (object):
    """Runtime for the Congress policy language.

    Only have one instantiation in practice, but using a
    class is natural and useful for testing.
    """

    DEFAULT_THEORY = 'classification'
    ACTION_THEORY = 'action'

    def __init__(self):
        # tracer object
        self.tracer = base.Tracer()
        # record execution
        self.logger = ExecutionLogger()
        # collection of theories
        self.theory = {}
        # collection of builtin theories
        self.builtin_policy_names = set()
        # dependency graph for all theories
        self.global_dependency_graph = (
            compile.RuleDependencyGraph())
        # triggers
        self.trigger_registry = TriggerRegistry(self.global_dependency_graph)
        # execution triggers
        self.execution_triggers = {}
        # disabled rules
        self.disabled_events = []
        # rules with errors (because of schema inconsistencies)
        self.error_events = []
        self.synchronizer = None

    ###############################################
    # Persistence layer
    ###############################################
    # Note(thread-safety): blocking function
    def persistent_create_policy_with_rules(self, policy_rules_obj):
        rules, policy_metadata = self.persistent_insert_rules(
            policy_name=policy_rules_obj['name'],
            rules=policy_rules_obj['rules'],
            create_policy=True,
            abbr=policy_rules_obj.get('abbreviation'),
            kind=policy_rules_obj.get('kind'),
            desc=policy_rules_obj.get('description'))

        # remove the rule IDs
        for rule in rules:
            del rule['id']

        policy_metadata['rules'] = rules
        return policy_metadata

    # Note(thread-safety): blocking function
    def persistent_create_policy(self, name, id_=None, abbr=None, kind=None,
                                 desc=None, db_session=None):
        # validation for name
        if not compile.string_is_servicename(name):
            raise exception.PolicyException(
                "Policy name %s is not a valid tablename" % name)

        # Create policy object, but don't add to runtime yet, sync later
        if id_ is None:
            id_ = str(uuidutils.generate_uuid())
        policy_obj = self.construct_policy_obj(
            name=name, abbr=abbr, kind=kind, id_=id_, desc=desc, owner='user')

        # save policy to database
        if desc is None:
            desc = ''
        obj = {'id': policy_obj.id,
               'name': policy_obj.name,
               'owner_id': 'user',
               'description': desc,
               'abbreviation': policy_obj.abbr,
               'kind': policy_obj.kind}
        try:
            # Note(thread-safety): blocking function
            db_policy_rules.add_policy(obj['id'],
                                       obj['name'],
                                       obj['abbreviation'],
                                       obj['description'],
                                       obj['owner_id'],
                                       obj['kind'],
                                       session=db_session)
        except KeyError:
            raise
        except Exception:
            policy_name = policy_obj.name
            msg = ("Unexpected error while adding policy %s into DB."
                   % policy_name)
            LOG.exception(msg)
            raise exception.PolicyException(msg)
        if db_session:
            # stay in current transaction, previous write may not be
            # readable by synchronizer
            self.add_policy_obj_to_runtime(policy_obj)
        else:
            self.synchronizer.sync_one_policy(obj['name'],
                                              db_session=db_session)
        return obj

    # Note(thread-safety): blocking function
    def persistent_delete_policy(self, name_or_id):
        # Note(thread-safety): blocking call
        db_object = db_policy_rules.get_policy(name_or_id)
        if db_object['name'] in [self.DEFAULT_THEORY, self.ACTION_THEORY]:
            raise KeyError("Cannot delete system-maintained policy %s" %
                           db_object['name'])
        # delete policy from memory and from database
        db_policy_rules.delete_policy(db_object['id'])
        self.synchronizer.sync_one_policy(db_object['name'])
        return db_object.to_dict()

    # Note(thread-safety): blocking function
    def persistent_get_policies(self):
        return [p.to_dict() for p in db_policy_rules.get_policies()]

    # Note(thread-safety): blocking function
    def persistent_get_policy(self, id_):
        # Note(thread-safety): blocking call
        try:
            policy = db_policy_rules.get_policy(id_)
            return policy.to_dict()
        except KeyError:
            raise exception.NotFound(
                'No policy found with name or id %s' % id_)

    # Note(thread-safety): blocking function
    def persistent_get_rule(self, id_, policy_name):
        """Return data for rule with id\_ in policy_name."""
        # Check if policy exists, else raise error
        self.assert_policy_exists(policy_name)
        # Note(thread-safety): blocking call
        rule = db_policy_rules.get_policy_rule(id_, policy_name)
        if rule is None:
            return
        return rule.to_dict()

    # Note(thread-safety): blocking function
    def persistent_get_rules(self, policy_name):
        """Return data for all rules in policy_name."""
        # Check if policy exists, else raise error
        self.assert_policy_exists(policy_name)
        # Note(thread-safety): blocking call
        rules = db_policy_rules.get_policy_rules(policy_name)
        return [rule.to_dict() for rule in rules]

    def persistent_insert_rule(self, policy_name, str_rule, rule_name,
                               comment):
        rule_data = {'rule': str_rule, 'name': rule_name,
                     'comment': comment}
        return_data, _ = self.persistent_insert_rules(policy_name, [rule_data])
        return (return_data[0]['id'], return_data[0])

    # Note(thread-safety): blocking function
    # acquire lock to avoid periodic sync from undoing insert before persisted
    # IMPORTANT: Be very careful to avoid deadlock when
    # acquiring locks sequentially. In this case, we will acquire lock A
    # then attempt to acquire lock B. We have to make sure no thread will hold
    # lock B and attempt to acquire lock A, causing a deadlock
    @lockutils.synchronized('congress_synchronize_policies')
    @lockutils.synchronized('congress_synchronize_rules')
    def persistent_insert_rules(self, policy_name, rules, create_policy=False,
                                id_=None, abbr=None, kind=None, desc=None):
        """Insert and persists rule into policy_name."""

        def uninsert_rules(rules_inserted):
            for d in rules_inserted:
                self._safe_process_policy_update(
                    [d['input_rule_str']], policy_name, insert=False)

        success = False  # used to rollback DB if not set to success
        try:
            rules_to_persist = []
            return_data = []
            # get session
            db_session = db_api.get_locking_session()

            # lock policy_rules table to prevent conflicting rules
            # insertion (say causing unsupported recursion)
            # policies and datasources tables locked because
            # it's a requirement of MySQL backend to lock all accessed tables
            db_api.lock_tables(session=db_session,
                               tables=['policy_rules', 'policies',
                                       'datasources'])

            if cfg.CONF.replicated_policy_engine:
                # synchronize policy rules to get latest state, locked state
                # non-locking version because lock already acquired,
                # avoid deadlock
                self.synchronizer.synchronize_rules_nonlocking(
                    db_session=db_session)

            # Note: it's important that this create policy is run after locking
            # the policy_rules table, so as to prevent other nodes from
            # inserting rules into this policy, which may be removed by an
            # undo (delete the policy) later in this method
            policy_metadata = None
            if create_policy:
                policy_metadata = self.persistent_create_policy(
                    id_=id_, name=policy_name, abbr=abbr, kind=kind,
                    desc=desc, db_session=db_session)
            else:
                # Reject rules inserted into non-persisted policies
                # (i.e. datasource policies)

                # Note(thread-safety): blocking call
                policy_name = db_policy_rules.policy_name(
                    policy_name, session=db_session)
                # call synchronizer to make sure policy is sync'ed in memory
                self.synchronizer.sync_one_policy_nonlocking(
                    policy_name, db_session=db_session)
                # Note(thread-safety): blocking call
                policies = db_policy_rules.get_policies(session=db_session)
                persisted_policies = set([p.name for p in policies])
                if policy_name not in persisted_policies:
                    if policy_name in self.theory:
                        LOG.debug(
                            "insert_persisted_rule error: rule not permitted "
                            "for policy %s", policy_name)
                        raise exception.PolicyRuntimeException(
                            name='rule_not_permitted')

            rules_to_insert = []
            for rule_data in rules:
                str_rule = rule_data['rule']
                rule_name = rule_data.get('name')
                comment = rule_data.get('comment')

                id_ = uuidutils.generate_uuid()
                try:
                    rule = self.parse(str_rule)
                except exception.PolicyException as e:
                    # TODO(thinrichs): change compiler to provide these
                    # error_code names directly.
                    raise exception.PolicyException(
                        str(e), name='rule_syntax')

                if len(rule) == 0:
                    msg = ("Empty string passed. Not a valid rule")
                    raise exception.PolicyException(
                        msg, name='rule_syntax')
                elif len(rule) == 1:
                    rule = rule[0]
                else:
                    msg = ("Received multiple rules: " +
                           "; ".join(str(x) for x in rule))
                    raise exception.PolicyRuntimeException(
                        msg, name='multiple_rules')

                rule.set_id(id_)
                rule.set_name(rule_name)
                rule.set_comment(comment or "")
                rule.set_original_str(str_rule)
                rules_to_insert.append(rule)
            changes = self._safe_process_policy_update(
                rules_to_insert, policy_name, persistent=True)

            if len(changes) > 0:
                # remember the rule for possible undo
                rules_inserted = [
                    change_event.formula for change_event in changes]

                # remember the rule for insert into DB
                rules_to_persist = [{
                    'original_str': change_event.formula.original_str,
                    'id': str(change_event.formula.id),
                    'comment': change_event.formula.comment,
                    'name': change_event.formula.name}
                    for change_event in changes]

                # prepare return data based on rules inserted
                return_data = [{
                    'rule': utils.pretty_rule(
                        change_event.formula.original_str),
                    'id': str(change_event.formula.id),
                    'comment': change_event.formula.comment,
                    'name': change_event.formula.name}
                    for change_event in changes]

            # save rule to database if change actually happened.
            # Note: change produced may not be equivalent to original rule
            #   because of column-reference elimination.
            if len(rules_to_persist) == 0 and len(rules) > 0:
                # change not accepted means it was already there
                raise exception.PolicyRuntimeException(
                    name='rule_already_exists')
            try:
                for d in rules_to_persist:
                    # Note(thread-safety): blocking call
                    db_policy_rules.add_policy_rule(
                        d['id'], policy_name, d['original_str'],
                        d['comment'], rule_name=d['name'], session=db_session)
                    # do not begin to avoid implicitly releasing table
                    # lock due to starting new transaction
                success = True
                return return_data, policy_metadata
            except Exception as db_exception:
                try:
                    # un-insert all rules from engine unless all db inserts
                    # succeeded
                    # Note limitation: if an unexpected DB error is encountered
                    # the rule insertions into policy engine are undone, but
                    # may have already had effects on actions and query results
                    uninsert_rules(rules_inserted)
                    raise exception.PolicyRuntimeException(
                        "Error while writing to DB: %s."
                        % str(db_exception))
                except Exception as change_exception:
                    raise exception.PolicyRuntimeException(
                        "Error thrown during recovery from DB error. "
                        "Inconsistent state.  DB error: %s.  "
                        "New error: %s." % (str(db_exception),
                                            str(change_exception)))
        finally:
            # commit/rollback, unlock, and close db_session
            if db_session:
                if success:
                    db_api.commit_unlock_tables(session=db_session)
                else:
                    db_api.rollback_unlock_tables(session=db_session)
                    if create_policy:
                        # sync the potentially rolled back policy creation
                        self.synchronizer.sync_one_policy_nonlocking(
                            policy_name)
                db_session.close()

    # Note(thread-safety): blocking function
    def persistent_delete_rule(self, id_, policy_name_or_id):
        # Note(thread-safety): blocking call
        policy_name = db_policy_rules.policy_name(policy_name_or_id)
        # Note(thread-safety): blocking call
        item = self.persistent_get_rule(id_, policy_name)
        if item is None:
            raise exception.PolicyRuntimeException(
                name='rule_not_exists',
                data='ID: %s, policy_name: %s' % (id_, policy_name))
        rule = self.parse1(item['rule'])
        self._safe_process_policy_update([rule], policy_name, insert=False)
        # Note(thread-safety): blocking call
        db_policy_rules.delete_policy_rule(id_)
        return item

    def persistent_load_policies(self):
        """Load policies from database."""
        return self.synchronizer.synchronize_all_policies()

    # Note(thread-safety): blocking function
    def persistent_load_rules(self):
        """Load all rules from the database."""
        # Note(thread-safety): blocking call
        rules = db_policy_rules.get_policy_rules()
        for rule in rules:
            parsed_rule = self.parse1(rule.rule)
            parsed_rule.set_id(rule.id)
            parsed_rule.set_name(rule.name)
            parsed_rule.set_comment(rule.comment)
            parsed_rule.set_original_str(rule.rule)
            self._safe_process_policy_update(
                [parsed_rule],
                rule.policy_name)

    def _safe_process_policy_update(self, parsed_rules, policy_name,
                                    insert=True, persistent=False):
        if policy_name not in self.theory:
            raise exception.PolicyRuntimeException(
                'Policy ID %s does not exist' % policy_name,
                name='policy_not_exist')
        events = [compile.Event(
            formula=parsed_rule, insert=insert, target=policy_name)
            for parsed_rule in parsed_rules]
        (permitted, changes) = self.process_policy_update(
            events, persistent=persistent)
        if not permitted:
            raise exception.PolicyException(
                ";".join([str(x) for x in changes]),
                name='rule_syntax')
        return changes

    def process_policy_update(self, events, persistent=False):
        LOG.debug("process_policy_update %s" % events)
        # body_only so that we don't subscribe to tables in the head
        result = self.update(events, persistent=persistent)
        return result

    ##########################
    # Non-persistence layer
    ##########################

    def construct_policy_obj(self, name, abbr=None, kind=None, id_=None,
                             desc=None, owner=None):
        """Construct policy obj"""
        if not isinstance(name, six.string_types):
            raise KeyError("Policy name %s must be a string" % name)
        if not isinstance(abbr, six.string_types):
            abbr = name[0:5]
        LOG.debug("Creating policy <%s> with abbr <%s> and kind <%s>",
                  name, abbr, kind)
        if kind is None:
            kind = base.NONRECURSIVE_POLICY_TYPE
        else:
            kind = kind.lower()
        if kind == base.NONRECURSIVE_POLICY_TYPE:
            PolicyClass = nonrecursive.NonrecursiveRuleTheory
        elif kind == base.ACTION_POLICY_TYPE:
            PolicyClass = nonrecursive.ActionTheory
        elif kind == base.DATABASE_POLICY_TYPE:
            PolicyClass = db.Database
        elif kind == base.MATERIALIZED_POLICY_TYPE:
            PolicyClass = materialized.MaterializedViewTheory
        elif kind == base.DATASOURCE_POLICY_TYPE:
            PolicyClass = nonrecursive.DatasourcePolicyTheory
        elif kind == base.Z3_POLICY_TYPE:
            if z3types.Z3_AVAILABLE:
                PolicyClass = z3theory.Z3Theory
            else:
                raise exception.PolicyException(
                    "Z3 not available. Please install it")
        else:
            raise exception.PolicyException(
                "Unknown kind of policy: %s" % kind)
        policy_obj = PolicyClass(name=name, abbr=abbr, theories=self.theory,
                                 desc=desc, owner=owner)
        policy_obj.set_id(id_)
        policy_obj.set_tracer(self.tracer)
        return policy_obj

    def add_policy_obj_to_runtime(self, policy_obj):
        """Add policy obj to runtime"""
        name = policy_obj.name
        if name in self.theory:
            raise KeyError("Policy with name %s already exists" % name)
        self.theory[name] = policy_obj
        LOG.debug("Added to runtime policy <%s> with abbr <%s> and kind <%s>",
                  policy_obj.name, policy_obj.abbr, policy_obj.kind)

    def create_policy(self, name, abbr=None, kind=None, id_=None,
                      desc=None, owner=None):
        """Create a new policy and add it to the runtime.

        ABBR is a shortened version of NAME that appears in
        traces.  KIND is the name of the datastructure used to
        represent a policy.
        """
        policy_obj = self.construct_policy_obj(
            name, abbr, kind, id_, desc, owner)
        self.add_policy_obj_to_runtime(policy_obj)
        return policy_obj

    def initialize_datasource(self, name, schema):
        """Initializes datasource by creating policy and setting schema. """
        try:
            self.create_policy(name, kind=base.DATASOURCE_POLICY_TYPE)
        except KeyError:
            raise exception.DatasourceNameInUse(value=name)
        try:
            self.set_schema(name, schema)
        except Exception:
            self.delete_policy(name)
            raise exception.DatasourceCreationError(value=name)

    def delete_policy(self, name_or_id, disallow_dangling_refs=False):
        """Deletes policy with name NAME or throws KeyError or DanglingRefs."""
        LOG.info("Deleting policy named %s", name_or_id)
        name = self._find_policy_name(name_or_id)
        if disallow_dangling_refs:
            refs = self._references_to_policy(name)
            if refs:
                refmsg = ";".join("%s: %s" % (policy, rule)
                                  for policy, rule in refs)
                raise exception.DanglingReference(
                    "Cannot delete %s because it would leave dangling "
                    "references: %s" % (name, refmsg))
        # delete the rules explicitly so cross-theory state is properly
        #   updated
        events = [compile.Event(formula=rule, insert=False, target=name)
                  for rule in self.theory[name].content()]
        permitted, errs = self.update(events)
        if not permitted:
            # This shouldn't happen
            msg = ";".join(str(x) for x in errs)
            LOG.exception("agnostic:: failed to empty theory %s: %s",
                          name_or_id, msg)
            raise exception.PolicyException("Policy %s could not be deleted "
                                            "since rules could not all be "
                                            "deleted: %s" % (name, msg))
        # delete disabled rules
        self.disabled_events = [event for event in self.disabled_events
                                if event.target != name]
        # explicit destructor could be part of the generic Theory interface.
        if isinstance(self.theory.get(name, None), z3theory.Z3Theory):
            self.theory[name].drop()
        # actually delete the theory
        del self.theory[name]

    def rename_policy(self, oldname, newname):
        """Renames policy OLDNAME to NEWNAME or raises KeyError."""
        if newname in self.theory:
            raise KeyError('Cannot rename %s to %s: %s already exists' %
                           (oldname, newname, newname))
        try:
            self.theory[newname] = self.theory[oldname]
            del self.theory[oldname]
        except KeyError:
            raise KeyError('Cannot rename %s to %s: %s does not exist' %
                           (oldname, newname, oldname))

    # TODO(thinrichs): make Runtime act like a dictionary so that we
    #   can iterate over policy names (keys), check if a policy exists, etc.
    def assert_policy_exists(self, policy_name):
        """Checks if policy exists or not.

        :param: policy_name: policy name
        :returns: True, if policy exists
        :raises: PolicyRuntimeException, if policy doesn't exist.
        """
        if policy_name not in self.theory:
            raise exception.PolicyRuntimeException(
                'Policy ID %s does not exist' % policy_name,
                name='policy_not_exist')
        return True

    def policy_names(self):
        """Returns list of policy names."""
        return list(self.theory.keys())

    def policy_object(self, name=None, id=None):
        """Return policy by given name.  Raises KeyError if does not exist."""
        assert name or id
        if name:
            try:
                if not id or str(self.theory[name].id) == str(id):
                    return self.theory[name]
            except KeyError:
                raise KeyError("Policy with name %s and id %s does not "
                               "exist" % (name, str(id)))
        elif id:
            for n in self.policy_names():
                if str(self.theory[n].id) == str(id):
                    return self.theory[n]
            raise KeyError("Policy with name %s and id %s does not "
                           "exist" % (name, str(id)))

    def policy_type(self, name):
        """Return type of policy NAME.  Throws KeyError if does not exist."""
        return self.policy_object(name).kind

    def set_schema(self, name, schema, complete=False):
        """Set the schema for module NAME to be SCHEMA."""
        # TODO(thinrichs): handle the case of a schema being UPDATED,
        #   not just being set for the first time
        if name not in self.theory:
            raise exception.CongressException(
                "Cannot set policy for %s because it has not been created" %
                name)
        if self.theory[name].schema and len(self.theory[name].schema) > 0:
            raise exception.CongressException(
                "Schema for %s already set" % name)
        self.theory[name].schema = compile.Schema(schema, complete=complete)
        enabled, disabled, errs = self._process_limbo_events(
            self.disabled_events)
        self.disabled_events = disabled
        self.error_events.extend(errs)
        for event in enabled:
            permitted, errors = self._update_obj_datalog([event])
            if not permitted:
                self.error_events.append((event, errors))

    def _create_status_dict(self, target, keys):
        result = {}

        for k in keys:
            attr = getattr(target, k, None)
            if attr is not None:
                result[k] = attr

        return result

    def get_status(self, source_id, params):
        try:
            if source_id in self.policy_names():
                target = self.policy_object(name=source_id)
            else:
                target = self.policy_object(id=source_id)

            keys = ['name', 'id']

            if 'rule_id' in params:
                target = target.get_rule(str(params['rule_id']))
                keys.extend(['comment', 'original_str'])

        except KeyError:
            msg = ("policy with name or id '%s' doesn't exist" % source_id)
            LOG.debug(msg)
            raise exception.NotFound(msg)

        return self._create_status_dict(target, keys)

    def select(self, query, target=None, trace=False):
        """Event handler for arbitrary queries.

        Returns the set of all instantiated QUERY that are true.
        """
        if isinstance(query, six.string_types):
            return self._select_string(query, self.get_target(target), trace)
        elif isinstance(query, tuple):
            return self._select_tuple(query, self.get_target(target), trace)
        else:
            return self._select_obj(query, self.get_target(target), trace)

    def initialize_tables(self, tablenames, facts, target=None):
        """Event handler for (re)initializing a collection of tables

        @facts must be an iterable containing compile.Fact objects.
        """
        target_theory = self.get_target(target)
        alltables = set([compile.Tablename.build_service_table(
                         target_theory.name, x)
                         for x in tablenames])
        triggers = self.trigger_registry.relevant_triggers(alltables)
        LOG.info("relevant triggers (init): %s",
                 ";".join(str(x) for x in triggers))
        # run queries on relevant triggers *before* applying changes
        table_triggers = self.trigger_registry.triggers_by_table(triggers)
        table_data_old = self._compute_table_contents(table_triggers)
        # actually apply the updates
        target_theory.initialize_tables(tablenames, facts)
        # rerun the trigger queries to check for changes
        table_data_new = self._compute_table_contents(table_triggers)
        # run triggers if tables changed
        for table, triggers in table_triggers.items():
            if table_data_old[table] != table_data_new[table]:
                for trigger in triggers:
                    trigger.callback(table,
                                     table_data_old[table],
                                     table_data_new[table])

    def insert(self, formula, target=None):
        """Event handler for arbitrary insertion (rules and facts)."""
        if isinstance(formula, six.string_types):
            return self._insert_string(formula, target)
        elif isinstance(formula, tuple):
            return self._insert_tuple(formula, target)
        else:
            return self._insert_obj(formula, target)

    def delete(self, formula, target=None):
        """Event handler for arbitrary deletion (rules and facts)."""
        if isinstance(formula, six.string_types):
            return self._delete_string(formula, target)
        elif isinstance(formula, tuple):
            return self._delete_tuple(formula, target)
        else:
            return self._delete_obj(formula, target)

    def update(self, sequence, target=None, persistent=False):
        """Event handler for applying an arbitrary sequence of insert/deletes.

        If TARGET is supplied, it overrides the targets in SEQUENCE.
        """
        if isinstance(sequence, six.string_types):
            return self._update_string(sequence, target, persistent)
        else:
            return self._update_obj(sequence, target, persistent)

    def policy(self, target=None):
        """Event handler for querying policy."""
        target = self.get_target(target)
        if target is None:
            return ""
        return " ".join(str(p) for p in target.policy())

    def content(self, target=None):
        """Event handler for querying content()."""
        target = self.get_target(target)
        if target is None:
            return ""
        return " ".join(str(p) for p in target.content())

    def simulate(self, query, theory, sequence, action_theory, delta=False,
                 trace=False, as_list=False):
        """Event handler for simulation.

        :param: query is a string/object to query after
        :param: theory is the policy to query
        :param: sequence is a string/iter of updates to state/policy or actions
        :param: action_theory is the policy that contains action descriptions
        :param: delta indicates whether to return *changes* to query caused by
               sequence
        :param: trace indicates whether to include a string description of the
               implementation.  When True causes the return value to be the
               tuple (result, trace).
        :param: as_list controls whether the result is forced to be a list of
               answers

        Returns a list of instances of query.  If query/sequence are strings
        the query instance list is a single string (unless as_list is True
        in which case the query instance list is a list of strings).  If
        query/sequence are objects then the query instance list is a list
        of objects.

        The computation of a query given an action sequence. That sequence
        can include updates to atoms, updates to rules, and action
        invocations.  Returns a collection of Literals (as a string if the
        query and sequence are strings or as a Python collection otherwise).
        If delta is True, the return is a collection of Literals where
        each tablename ends with either + or - to indicate whether
        that fact was added or deleted.
        Example atom update: q+(1) or q-(1)
        Example rule update: p+(x) :- q(x) or p-(x) :- q(x)
        Example action invocation::

           create_network(17), options:value(17, "name", "net1") :- true
        """
        assert self.get_target(theory) is not None, "Theory must be known"
        assert self.get_target(action_theory) is not None, (
            "Action theory must be known")
        if (isinstance(query, six.string_types) and
                isinstance(sequence, six.string_types)):
            return self._simulate_string(query, theory, sequence,
                                         action_theory, delta, trace, as_list)
        else:
            return self._simulate_obj(query, theory, sequence, action_theory,
                                      delta, trace)

    def get_tablename(self, source_id, table_id):
        tables = self.get_tablenames(source_id)
        # when the policy doesn't have any rule 'tables' is set([])
        # when the policy doesn't exist 'tables' is None
        if tables and table_id in tables:
            return table_id

    def get_tablenames(self, source_id):
        if source_id in self.theory.keys():
            return self.tablenames(theory_name=source_id, include_modal=False)

    def get_row_data(self, table_id, source_id, trace=False):
        # source_id is the policy name.  But it needs to stay 'source_id'
        #  since RPC calls invoke by the name of the argument, and we're
        #  currently assuming the implementations of get_row_data in
        #  the policy engine, datasources, and datasource manager all
        #  use the same argument names.
        policy_name = source_id
        tablename = self.get_tablename(policy_name, table_id)
        if not tablename:
            raise exception.NotFound("table '%s' doesn't exist" % table_id)

        queries = self.table_contents_queries(tablename, policy_name)
        if queries is None:
            m = "Known table but unknown arity for '%s' in policy '%s'" % (
                tablename, policy_name)
            LOG.error(m)
            raise exception.CongressException(m)

        gen_trace = None
        query = self.parse1(queries[0])
        # LOG.debug("query: %s", query)
        result = self.select(query, target=policy_name,
                             trace=trace)
        if trace:
            literals = result[0]
            gen_trace = result[1]
        else:
            literals = result
        # should NOT need to convert to set -- see bug 1344466
        literals = frozenset(literals)
        # LOG.info("results: %s", '\n'.join(str(x) for x in literals))
        results = []
        for lit in literals:
            d = {}
            d['data'] = [arg.name for arg in lit.arguments]
            results.append(d)

        if trace:
            return results, gen_trace
        else:
            return results

    def tablenames(self, body_only=False, include_builtin=False,
                   theory_name=None, include_modal=True):
        """Return tablenames occurring in some theory."""
        tables = set()

        if theory_name:
            th = self.theory.get(theory_name, None)
            if th:
                tables |= set(th.tablenames(body_only=body_only,
                                            include_builtin=include_builtin,
                                            include_modal=include_modal,
                                            include_facts=True))
            return tables

        for th in self.theory.values():
            tables |= set(th.tablenames(body_only=body_only,
                                        include_builtin=include_builtin,
                                        include_modal=include_modal,
                                        include_facts=True))
        return tables

    def reserved_tablename(self, name):
        return name.startswith('___')

    def table_contents_queries(self, tablename, policy, modal=None):
        """Return list of queries yielding contents of TABLENAME in POLICY."""
        # TODO(thinrichs): Handle case of multiple arities.  Connect to API.
        arity = self.arity(tablename, policy, modal)
        if arity is None:
            return
        args = ["x" + str(i) for i in range(0, arity)]
        atom = tablename + "(" + ",".join(args) + ")"
        if modal is None:
            return [atom]
        else:
            return [modal + "[" + atom + "]"]

    def register_trigger(self, tablename, callback, policy=None, modal=None):
        """Register CALLBACK to run when table TABLENAME changes."""
        # calling self.get_target_name to check if policy actually exists
        #   and to resolve None to a policy name
        return self.trigger_registry.register_table(
            tablename, self.get_target_name(policy), callback, modal=modal)

    def unregister_trigger(self, trigger):
        """Unregister CALLBACK for table TABLENAME."""
        return self.trigger_registry.unregister(trigger)

    def arity(self, table, theory, modal=None):
        """Return number of columns for TABLE in THEORY.

        TABLE can include the policy name. <policy>:<table>
        THEORY is the name of the theory we are asking.
        MODAL is the value of the modal, if any.
        """
        arity = self.get_target(theory).arity(table, modal)
        if arity is not None:
            return arity
        policy, tablename = compile.Tablename.parse_service_table(table)
        if policy not in self.theory:
            return
        return self.theory[policy].arity(tablename, modal)

    def find_subpolicy(self, required_tables, prohibited_tables,
                       output_tables, target=None):
        """Return a subset of rules in @theory.

        @required_tables is the set of tablenames that a rule must depend on.
        @prohibited_tables is the set of tablenames that a rule must
        NOT depend on.
        @output_tables is the set of tablenames that all rules must support.
        """
        target = self.get_target(target)
        if target is None:
            return
        subpolicy = compile.find_subpolicy(
            target.content(),
            required_tables,
            prohibited_tables,
            output_tables)
        return " ".join(str(p) for p in subpolicy)

    ##########################################
    # Implementation of Non-persistence layer
    ##########################################
    # Arguments that are strings are suffixed with _string.
    # All other arguments are instances of Theory, Literal, etc.

    ###################################
    # Implementation: updates

    # insert: convenience wrapper around Update
    def _insert_string(self, policy_string, theory_string):
        policy = self.parse(policy_string)
        return self._update_obj(
            [compile.Event(formula=x, insert=True, target=theory_string)
             for x in policy],
            theory_string)

    def _insert_tuple(self, iter, theory_string):
        return self._insert_obj(compile.Literal.create_from_iter(iter),
                                theory_string)

    def _insert_obj(self, formula, theory_string):
        return self._update_obj([compile.Event(formula=formula, insert=True,
                                               target=theory_string)],
                                theory_string)

    # delete: convenience wrapper around Update
    def _delete_string(self, policy_string, theory_string):
        policy = self.parse(policy_string)
        return self._update_obj(
            [compile.Event(formula=x, insert=False, target=theory_string)
             for x in policy],
            theory_string)

    def _delete_tuple(self, iter, theory_string):
        return self._delete_obj(compile.Literal.create_from_iter(iter),
                                theory_string)

    def _delete_obj(self, formula, theory_string):
        return self._update_obj([compile.Event(formula=formula, insert=False,
                                               target=theory_string)],
                                theory_string)

    # update
    def _update_string(self, events_string, theory_string, persistent=False):
        assert False, "Not yet implemented--need parser to read events"

    def _update_obj(self, events, theory_string, persistent=False):
        """Apply events.

        Checks if applying EVENTS is permitted and if not
        returns a list of errors.  If it is permitted, it
        applies it and then returns a list of changes.
        In both cases, the return is a 2-tuple (if-permitted, list).
        Note: All event.target fields are the NAMES of theories, not
        theory objects.  theory_string is the default theory.
        """
        errors = []
        # resolve event targets and check that they actually exist
        for event in events:
            if event.target is None:
                event.target = theory_string
            try:
                event.target = self.get_target_name(event.target)
            except exception.PolicyException as e:
                errors.append(e)
        if len(errors) > 0:
            return (False, errors)
        # eliminate column refs where possible
        enabled, disabled, errs = self._process_limbo_events(
            events, persistent)
        for err in errs:
            errors.extend(err[1])
        if len(errors) > 0:
            return (False, errors)
        # continue updating and if successful disable the rest
        permitted, extra = self._update_obj_datalog(enabled)
        if not permitted:
            return permitted, extra
        self._disable_events(disabled)
        return (True, extra)

    def _disable_events(self, events):
        """Take collection of insert events and disable them.

        Assume that events.theory is an object.
        """
        self.disabled_events.extend(events)

    def _process_limbo_events(self, events, persistent=False):
        """Assume that events.theory is an object.

        Return (<enabled>, <disabled>, <errors>)
        where <errors> is a list of (event, err-list).
        """
        disabled = []
        enabled = []
        errors = []
        for event in events:
            try:
                oldformula = event.formula
                event.formula = \
                    oldformula.eliminate_column_references_and_pad_positional(
                        self.theory, default_theory=event.target)
                # doesn't copy over ID since it creates a new one
                event.formula.set_id(oldformula.id)
                enabled.append(event)

                errs = compile.check_schema_consistency(
                    event.formula, self.theory, event.target)
                if len(errs) > 0:
                    errors.append((event, errs))
                    continue
            except exception.IncompleteSchemaException as e:
                if persistent:
                    # FIXME(ekcs): inconsistent behavior?
                    # persistent_insert with 'unknown:p(x)' allowed but
                    # 'unknown:p(colname=x)' disallowed
                    raise exception.PolicyException(str(e), name='rule_syntax')
                else:
                    disabled.append(event)
            except exception.PolicyException as e:
                errors.append((event, [e]))
        return enabled, disabled, errors

    def _update_obj_datalog(self, events):
        """Do the updating.

        Checks if applying EVENTS is permitted and if not
        returns a list of errors.  If it is permitted, it
        applies it and then returns a list of changes.
        In both cases, the return is a 2-tuple (if-permitted, list).
        Note: All event.target fields are the NAMES of theories, not
        theory objects, and all event.formula fields have
        had all column references removed.
        """
        # TODO(thinrichs): look into whether we can move the bulk of the
        # trigger code into Theory, esp. so that MaterializedViewTheory
        # can implement it more efficiently.
        self.table_log(None, "Updating with %s", utility.iterstr(events))
        errors = []
        # eliminate noop events
        events = self._actual_events(events)
        if not len(events):
            return (True, [])
        # check that the updates would not cause an error
        by_theory = self._group_events_by_target(events)
        for th, th_events in by_theory.items():
            th_obj = self.get_target(th)
            errors.extend(th_obj.update_would_cause_errors(th_events))
        if len(errors) > 0:
            return (False, errors)
        # update dependency graph (and undo it if errors)
        graph_changes = self.global_dependency_graph.formula_update(
            events, include_atoms=False)
        if graph_changes:
            if (self.global_dependency_graph.has_cycle() and
                (not z3types.Z3_AVAILABLE or
                 z3theory.cycle_not_contained_in_z3(
                     self.theory,
                     self.global_dependency_graph.cycles()))):
                # TODO(thinrichs): include path
                errors.append(exception.PolicyException(
                    "Rules are recursive"))
                self.global_dependency_graph.undo_changes(graph_changes)
        if len(errors) > 0:
            return (False, errors)
        # modify execution triggers
        self._maintain_triggers()
        # figure out relevant triggers
        triggers = self.trigger_registry.relevant_triggers(events)
        LOG.info("relevant triggers (update): %s",
                 ";".join(str(x) for x in triggers))
        # signal trigger registry about graph updates
        self.trigger_registry.update_dependencies(graph_changes)

        # run queries on relevant triggers *before* applying changes
        table_triggers = self.trigger_registry.triggers_by_table(triggers)
        table_data_old = self._compute_table_contents(table_triggers)
        # actually apply the updates
        changes = []
        for th, th_events in by_theory.items():
            changes.extend(self.get_target(th).update(events))
        # rerun the trigger queries to check for changes
        table_data_new = self._compute_table_contents(table_triggers)
        # run triggers if tables changed
        for table, triggers in table_triggers.items():
            if table_data_old[table] != table_data_new[table]:
                for trigger in triggers:
                    trigger.callback(table,
                                     table_data_old[table],
                                     table_data_new[table])
        # return non-error and the list of changes
        return (True, changes)

    def _maintain_triggers(self):
        pass

    def _actual_events(self, events):
        actual = []
        for event in events:
            th_obj = self.get_target(event.target)
            actual.extend(th_obj.actual_events([event]))
        return actual

    def _compute_table_contents(self, table_policy_pairs):
        data = {}   # dict from (table, policy) to set of query results
        for table, policy, modal in table_policy_pairs:
            th = self.get_target(policy)
            queries = self.table_contents_queries(table, policy, modal) or []
            data[(table, policy, modal)] = set()
            for query in queries:
                ans = set(self._select_obj(self.parse1(query), th, False))
                data[(table, policy, modal)] |= ans
        return data

    def _group_events_by_target(self, events):
        """Return mapping of targets and events.

        Return a dictionary mapping event.target to the list of events
        with that target.  Assumes each event.target is a string.
        Returns a dictionary from event.target to <list of events>.
        """
        by_target = {}
        for event in events:
            if event.target not in by_target:
                by_target[event.target] = [event]
            else:
                by_target[event.target].append(event)
        return by_target

    def _reroute_events(self, events):
        """Events re-routing.

        Given list of events with different event.target values,
        change each event.target so that the events are routed to the
        proper place.
        """
        by_target = self._group_events_by_target(events)
        for target, target_events in by_target.items():
            newth = self._compute_route(target_events, target)
            for event in target_events:
                event.target = newth

    def _references_to_policy(self, name):
        refs = []
        name = name + ":"
        for th_obj in self.theory.values():
            for rule in th_obj.policy():
                if any(table.startswith(name) for table in rule.tablenames()):
                    refs.append((name, rule))
        return refs

    ##########################
    # Implementation: queries

    # select
    def _select_string(self, policy_string, theory, trace):
        policy = self.parse(policy_string)
        assert (len(policy) == 1), (
            "Queries can have only 1 statement: {}".format(
                [str(x) for x in policy]))
        results = self._select_obj(policy[0], theory, trace)
        if trace:
            return (compile.formulas_to_string(results[0]), results[1])
        else:
            return compile.formulas_to_string(results)

    def _select_tuple(self, tuple, theory, trace):
        return self._select_obj(compile.Literal.create_from_iter(tuple),
                                theory, trace)

    def _select_obj(self, query, theory, trace):
        if trace:
            old_tracer = self.get_tracer()
            tracer = base.StringTracer()  # still LOG.debugs trace
            tracer.trace('*')     # trace everything
            self.set_tracer(tracer)
            value = set(theory.select(query))
            self.set_tracer(old_tracer)
            return (value, tracer.get_value())
        return set(theory.select(query))

    # simulate
    def _simulate_string(self, query, theory, sequence, action_theory, delta,
                         trace, as_list):
        query = self.parse(query)
        if len(query) > 1:
            raise exception.PolicyException(
                "Query %s contained more than 1 rule" % query)
        query = query[0]
        sequence = self.parse(sequence)
        result = self._simulate_obj(query, theory, sequence, action_theory,
                                    delta, trace)
        if trace:
            actual_result = result[0]
        else:
            actual_result = result
        strresult = [str(x) for x in actual_result]
        if not as_list:
            strresult = " ".join(strresult)
        if trace:
            return (strresult, result[1])
        else:
            return strresult

    def _simulate_obj(self, query, theory, sequence, action_theory, delta,
                      trace):
        """Simulate objects.

        Both THEORY and ACTION_THEORY are names of theories.
        Both QUERY and SEQUENCE are parsed.
        """
        assert compile.is_datalog(query), "Query must be formula"
        # Each action is represented as a rule with the actual action
        #    in the head and its supporting data (e.g. options) in the body
        assert all(compile.is_extended_datalog(x) for x in sequence), (
            "Sequence must be an iterable of Rules")
        th_object = self.get_target(theory)

        if trace:
            old_tracer = self.get_tracer()
            tracer = base.StringTracer()  # still LOG.debugs trace
            tracer.trace('*')     # trace everything
            self.set_tracer(tracer)

        # if computing delta, query the current state
        if delta:
            self.table_log(query.tablename(),
                           "** Simulate: Querying %s", query)
            oldresult = th_object.select(query)
            self.table_log(query.tablename(),
                           "Original result of %s is %s",
                           query, utility.iterstr(oldresult))

        # apply SEQUENCE
        self.table_log(query.tablename(), "** Simulate: Applying sequence %s",
                       utility.iterstr(sequence))
        undo = self.project(sequence, theory, action_theory)

        # query the resulting state
        self.table_log(query.tablename(), "** Simulate: Querying %s", query)
        result = set(th_object.select(query))
        self.table_log(query.tablename(), "Result of %s is %s", query,
                       utility.iterstr(result))
        # rollback the changes
        self.table_log(query.tablename(), "** Simulate: Rolling back")
        self.project(undo, theory, action_theory)

        # if computing the delta, do it
        if delta:
            result = set(result)
            oldresult = set(oldresult)
            pos = result - oldresult
            neg = oldresult - result
            pos = [formula.make_update(is_insert=True) for formula in pos]
            neg = [formula.make_update(is_insert=False) for formula in neg]
            result = pos + neg
        if trace:
            self.set_tracer(old_tracer)
            return (result, tracer.get_value())
        return result

    # Helpers

    def _react_to_changes(self, changes):
        """Filters changes and executes actions contained therein."""
        # LOG.debug("react to: %s", iterstr(changes))
        actions = self.get_action_names()
        formulas = [change.formula for change in changes
                    if (isinstance(change, compile.Event)
                        and change.is_insert()
                        and change.formula.is_atom()
                        and change.tablename() in actions)]
        # LOG.debug("going to execute: %s", iterstr(formulas))
        self.execute(formulas)

    def _data_listeners(self):
        return [self.theory[self.ENFORCEMENT_THEORY]]

    def _compute_route(self, events, theory):
        """Compute rerouting.

        When a formula is inserted/deleted (in OPERATION) into a THEORY,
        it may need to be rerouted to another theory.  This function
        computes that rerouting.  Returns a Theory object.
        """
        self.table_log(None, "Computing route for theory %s and events %s",
                       theory.name, utility.iterstr(events))
        # Since Enforcement includes Classify and Classify includes Database,
        #   any operation on data needs to be funneled into Enforcement.
        #   Enforcement pushes it down to the others and then
        #   reacts to the results.  That is, we really have one big theory
        #   Enforcement + Classify + Database as far as the data is concerned
        #   but formulas can be inserted/deleted into each policy individually.
        if all([compile.is_atom(event.formula) for event in events]):
            if (theory is self.theory[self.CLASSIFY_THEORY] or
                    theory is self.theory[self.DATABASE]):
                return self.theory[self.ENFORCEMENT_THEORY]
        return theory

    def project(self, sequence, policy_theory, action_theory):
        """Apply the list of updates SEQUENCE.

        Apply the list of updates SEQUENCE, where actions are described
        in ACTION_THEORY. Return an update sequence that will undo the
        projection.

        SEQUENCE can include atom insert/deletes, rule insert/deletes,
        and action invocations.  Projecting an action only
        simulates that action's invocation using the action's description;
        the results are therefore only an approximation of executing
        actions directly.  Elements of SEQUENCE are just formulas
        applied to the given THEORY.  They are NOT Event()s.

        SEQUENCE is really a program in a mini-programming
        language--enabling results of one action to be passed to another.
        Hence, even ignoring actions, this functionality cannot be achieved
        by simply inserting/deleting.
        """
        actth = self.theory[action_theory]
        policyth = self.theory[policy_theory]
        # apply changes to the state
        newth = nonrecursive.NonrecursiveRuleTheory(abbr="Temp")
        newth.tracer.trace('*')
        actth.includes.append(newth)
        # TODO(thinrichs): turn 'includes' into an object that guarantees
        #   there are no cycles through inclusion.  Otherwise we get
        #   infinite loops
        if actth is not policyth:
            actth.includes.append(policyth)
        actions = self.get_action_names(action_theory)
        self.table_log(None, "Actions: %s", utility.iterstr(actions))
        undos = []         # a list of updates that will undo SEQUENCE
        self.table_log(None, "Project: %s", sequence)
        last_results = []
        for formula in sequence:
            self.table_log(None, "** Updating with %s", formula)
            self.table_log(None, "Actions: %s", utility.iterstr(actions))
            self.table_log(None, "Last_results: %s",
                           utility.iterstr(last_results))
            tablename = formula.tablename()
            if tablename not in actions:
                if not formula.is_update():
                    raise exception.PolicyException(
                        "Sequence contained non-action, non-update: " +
                        str(formula))
                updates = [formula]
            else:
                self.table_log(tablename, "Projecting %s", formula)
                # define extension of current Actions theory
                if formula.is_atom():
                    assert formula.is_ground(), (
                        "Projection atomic updates must be ground")
                    assert not formula.is_negated(), (
                        "Projection atomic updates must be positive")
                    newth.define([formula])
                else:
                    # instantiate action using prior results
                    newth.define(last_results)
                    self.table_log(tablename, "newth (with prior results) %s",
                                   utility.iterstr(newth.content()))
                    bindings = actth.top_down_evaluation(
                        formula.variables(), formula.body, find_all=False)
                    if len(bindings) == 0:
                        continue
                    grounds = formula.plug_heads(bindings[0])
                    grounds = [act for act in grounds if act.is_ground()]
                    assert all(not lit.is_negated() for lit in grounds)
                    newth.define(grounds)
                self.table_log(tablename,
                               "newth contents (after action insertion): %s",
                               utility.iterstr(newth.content()))
                # self.table_log(tablename, "action contents: %s",
                #     iterstr(actth.content()))
                # self.table_log(tablename, "action.includes[1] contents: %s",
                #     iterstr(actth.includes[1].content()))
                # self.table_log(tablename, "newth contents: %s",
                #     iterstr(newth.content()))
                # compute updates caused by action
                updates = actth.consequences(compile.is_update)
                updates = self.resolve_conflicts(updates)
                updates = unify.skolemize(updates)
                self.table_log(tablename, "Computed updates: %s",
                               utility.iterstr(updates))
                # compute results for next time
                for update in updates:
                    newth.insert(update)
                last_results = actth.consequences(compile.is_result)
                last_results = set([atom for atom in last_results
                                    if atom.is_ground()])
            # apply updates
            for update in updates:
                undo = self.project_updates(update, policy_theory)
                if undo is not None:
                    undos.append(undo)
        undos.reverse()
        if actth is not policyth:
            actth.includes.remove(policyth)
        actth.includes.remove(newth)
        return undos

    def project_updates(self, delta, theory):
        """Project atom/delta rule insertion/deletion.

        Takes an atom/rule DELTA with update head table
        (i.e. ending in + or -) and inserts/deletes, respectively,
        that atom/rule into THEORY after stripping
        the +/-. Returns None if DELTA had no effect on the
        current state.
        """
        theory = delta.theory_name() or theory

        self.table_log(None, "Applying update %s to %s", delta, theory)
        th_obj = self.theory[theory]
        insert = delta.tablename().endswith('+')
        newdelta = delta.drop_update().drop_theory()
        changed = th_obj.update([compile.Event(formula=newdelta,
                                               insert=insert)])
        if changed:
            return delta.invert_update()
        else:
            return None

    def resolve_conflicts(self, atoms):
        """If p+(args) and p-(args) are present, removes the p-(args)."""
        neg = set()
        result = set()
        # split atoms into NEG and RESULT
        for atom in atoms:
            if atom.table.table.endswith('+'):
                result.add(atom)
            elif atom.table.table.endswith('-'):
                neg.add(atom)
            else:
                result.add(atom)
        # add elems from NEG only if their inverted version not in RESULT
        for atom in neg:
            if atom.invert_update() not in result:  # slow: copying ATOM here
                result.add(atom)
        return result

    def parse(self, string):
        return compile.parse(string, theories=self.theory)

    def parse1(self, string):
        return compile.parse1(string, theories=self.theory)

    ##########################
    # Helper functions
    ##########################

    def get_target(self, name):
        if name is None:
            if len(self.theory) == 1:
                name = next(iter(self.theory))
            elif len(self.theory) == 0:
                raise exception.PolicyException("No policies exist.")
            else:
                raise exception.PolicyException(
                    "Must choose a policy to operate on")
        if name not in self.theory:
            raise exception.PolicyException("Unknown policy " + str(name))
        return self.theory[name]

    def _find_policy_name(self, name_or_id):
        """Given name or ID, return the name of the policy or KeyError."""
        if name_or_id in self.theory:
            return name_or_id
        for th in self.theory.values():
            if th.id == name_or_id:
                return th.name
        raise KeyError("Policy %s could not be found" % name_or_id)

    def get_target_name(self, name):
        """Resolve NAME to the name of a proper policy (even if it is None).

        Raises PolicyException there is no such policy.
        """
        return self.get_target(name).name

    def get_action_names(self, target):
        """Return a list of the names of action tables."""
        if target not in self.theory:
            return []
        actionth = self.theory[target]
        actions = actionth.select(self.parse1('action(x)'))
        return [action.arguments[0].name for action in actions]

    def table_log(self, table, msg, *args):
        self.tracer.log(table, "RT    : %s" % msg, *args)

    def set_tracer(self, tracer):
        if isinstance(tracer, base.Tracer):
            self.tracer = tracer
            for th in self.theory:
                self.theory[th].set_tracer(tracer)
        else:
            self.tracer = tracer[0]
            for th, tracr in tracer[1].items():
                if th in self.theory:
                    self.theory[th].set_tracer(tracr)

    def get_tracer(self):
        """Return (Runtime's tracer, dict of tracers for each theory).

        Useful so we can temporarily change tracing.
        """
        d = {}
        for th in self.theory:
            d[th] = self.theory[th].get_tracer()
        return (self.tracer, d)

    def debug_mode(self):
        tracer = base.Tracer()
        tracer.trace('*')
        self.set_tracer(tracer)

    def production_mode(self):
        tracer = base.Tracer()
        self.set_tracer(tracer)


##############################################################################
# ExperimentalRuntime
##############################################################################

class ExperimentalRuntime (Runtime):
    def explain(self, query, tablenames=None, find_all=False, target=None):
        """Event handler for explanations.

        Given a ground query and a collection of tablenames
        that we want the explanation in terms of,
        return proof(s) that the query is true. If
        FIND_ALL is True, returns list; otherwise, returns single proof.
        """
        if isinstance(query, six.string_types):
            return self.explain_string(
                query, tablenames, find_all, self.get_target(target))
        elif isinstance(query, tuple):
            return self.explain_tuple(
                query, tablenames, find_all, self.get_target(target))
        else:
            return self.explain_obj(
                query, tablenames, find_all, self.get_target(target))

    def remediate(self, formula):
        """Event handler for remediation."""
        if isinstance(formula, six.string_types):
            return self.remediate_string(formula)
        elif isinstance(formula, tuple):
            return self.remediate_tuple(formula)
        else:
            return self.remediate_obj(formula)

    def execute(self, action_sequence):
        """Event handler for execute:

        Execute a sequence of ground actions in the real world.
        """
        if isinstance(action_sequence, six.string_types):
            return self.execute_string(action_sequence)
        else:
            return self.execute_obj(action_sequence)

    def access_control(self, action, support=''):
        """Event handler for making access_control request.

        ACTION is an atom describing a proposed action instance.
        SUPPORT is any data that should be assumed true when posing
        the query.  Returns True iff access is granted.
        """
        # parse
        if isinstance(action, six.string_types):
            action = self.parse1(action)
            assert compile.is_atom(action), "ACTION must be an atom"
        if isinstance(support, six.string_types):
            support = self.parse(support)
        # add support to theory
        newth = nonrecursive.NonrecursiveRuleTheory(abbr="Temp")
        newth.tracer.trace('*')
        for form in support:
            newth.insert(form)
        acth = self.theory[self.ACCESSCONTROL_THEORY]
        acth.includes.append(newth)
        # check if action is true in theory
        result = len(acth.select(action, find_all=False)) > 0
        # allow new theory to be freed
        acth.includes.remove(newth)
        return result

    # explain
    def explain_string(self, query_string, tablenames, find_all, theory):
        policy = self.parse(query_string)
        assert len(policy) == 1, "Queries can have only 1 statement"
        results = self.explain_obj(policy[0], tablenames, find_all, theory)
        return compile.formulas_to_string(results)

    def explain_tuple(self, tuple, tablenames, find_all, theory):
        self.explain_obj(compile.Literal.create_from_iter(tuple),
                         tablenames, find_all, theory)

    def explain_obj(self, query, tablenames, find_all, theory):
        return theory.explain(query, tablenames, find_all)

    # remediate
    def remediate_string(self, policy_string):
        policy = self.parse(policy_string)
        assert len(policy) == 1, "Queries can have only 1 statement"
        return compile.formulas_to_string(self.remediate_obj(policy[0]))

    def remediate_tuple(self, tuple, theory):
        self.remediate_obj(compile.Literal.create_from_iter(tuple))

    def remediate_obj(self, formula):
        """Find a collection of action invocations

        That if executed result in FORMULA becoming false.
        """
        actionth = self.theory[self.ACTION_THEORY]
        classifyth = self.theory[self.CLASSIFY_THEORY]
        # look at FORMULA
        if compile.is_atom(formula):
            pass  # TODO(tim): clean up unused variable
            # output = formula
        elif compile.is_regular_rule(formula):
            pass  # TODO(tim): clean up unused variable
            # output = formula.head
        else:
            assert False, "Must be a formula"
        # grab a single proof of FORMULA in terms of the base tables
        base_tables = classifyth.base_tables()
        proofs = classifyth.explain(formula, base_tables, False)
        if proofs is None:  # FORMULA already false; nothing to be done
            return []
        # Extract base table literals that make that proof true.
        #   For remediation, we assume it suffices to make any of those false.
        #   (Leaves of proof may not be literals or may not be written in
        #    terms of base tables, despite us asking for base tables--
        #    because of negation.)
        leaves = [leaf for leaf in proofs[0].leaves()
                  if (compile.is_atom(leaf) and
                      leaf.table in base_tables)]
        self.table_log(None, "Leaves: %s", utility.iterstr(leaves))
        # Query action theory for abductions of negated base tables
        actions = self.get_action_names()
        results = []
        for lit in leaves:
            goal = lit.make_positive()
            if lit.is_negated():
                goal.table = goal.table + "+"
            else:
                goal.table = goal.table + "-"
            # return is a list of goal :- act1, act2, ...
            # This is more informative than query :- act1, act2, ...
            for abduction in actionth.abduce(goal, actions, False):
                results.append(abduction)
        return results

    ##########################
    # Execute actions

    def execute_string(self, actions_string):
        self.execute_obj(self.parse(actions_string))

    def execute_obj(self, actions):
        """Executes the list of ACTION instances one at a time.

        For now, our execution is just logging.
        """
        LOG.debug("Executing: %s", utility.iterstr(actions))
        assert all(compile.is_atom(action) and action.is_ground()
                   for action in actions)
        action_names = self.get_action_names()
        assert all(action.table in action_names for action in actions)
        for action in actions:
            if not action.is_ground():
                if self.logger is not None:
                    self.logger.warn("Unground action to execute: %s", action)
                continue
            if self.logger is not None:
                self.logger.info("%s", action)

##############################################################################
# Engine that operates on the DSE
##############################################################################


class PolicySubData (object):
    def __init__(self, trigger):
        self.table_trigger = trigger
        self.to_add = ()
        self.to_rem = ()
        self.dataindex = trigger.policy + ":" + trigger.tablename

    def trigger(self):
        return self.table_trigger

    def changes(self):
        result = []
        for row in self.to_add:
            event = compile.Event(formula=row, insert=True)
            result.append(event)
        for row in self.to_rem:
            event = compile.Event(formula=row, insert=False)
            result.append(event)
        return result


class DseRuntime (Runtime, data_service.DataService):
    def __init__(self, name):
        Runtime.__init__(self)
        data_service.DataService.__init__(self, name)
        self.name = name
        self.msg = None
        self.last_policy_change = None
        self.policySubData = {}
        self.log_actions_only = cfg.CONF.enable_execute_action
        self.add_rpc_endpoint(DseRuntimeEndpoints(self))

    def set_synchronizer(self):
        obj = policy_rule_synchronizer.PolicyRuleSynchronizer(self, self.node)
        self.synchronizer = obj

    def start(self):
        super(DseRuntime, self).start()
        self.set_synchronizer()
        if self.synchronizer is not None:
            self.synchronizer.start()

    def extend_schema(self, service_name, schema):
        newschema = {}
        for key, value in schema:
            newschema[service_name + ":" + key] = value
        super(DseRuntime, self).extend_schema(self, newschema)

    def receive_policy_update(self, msg):
        LOG.debug("received policy-update msg %s",
                  utility.iterstr(msg.body.data))
        # update the policy and subscriptions to data tables.
        self.last_policy_change = self.process_policy_update(msg.body.data)

    def process_policy_update(self, events, persistent=False):
        LOG.debug("process_policy_update %s" % events)
        # body_only so that we don't subscribe to tables in the head
        oldtables = self.tablenames(body_only=True)
        result = Runtime.process_policy_update(self, events,
                                               persistent=persistent)
        newtables = self.tablenames(body_only=True)
        self.update_table_subscriptions(oldtables, newtables)
        return result

    def initialize_table_subscriptions(self):
        """Initialize table subscription.

        Once policies have all been loaded, this function subscribes to
        all the necessary tables.  See UPDATE_TABLE_SUBSCRIPTIONS as well.
        """
        self.update_table_subscriptions(set(), self.tablenames())

    def update_table_subscriptions(self, oldtables, newtables):
        """Update table subscription.

        Change the subscriptions from OLDTABLES to NEWTABLES, ensuring
        to load all the appropriate services.
        """
        add = newtables - oldtables
        rem = oldtables - newtables
        LOG.debug("Tables:: Old: %s, new: %s, add: %s, rem: %s",
                  oldtables, newtables, add, rem)
        # subscribe to the new tables (loading services as required)
        for table in add:
            if not self.reserved_tablename(table):
                (service, tablename) = compile.Tablename.parse_service_table(
                    table)
                if service is not None:
                    LOG.debug("Subscribing to new (service, table): (%s, %s)",
                              service, tablename)
                    self.subscribe(service, tablename)

        # unsubscribe from the old tables
        for table in rem:
            (service, tablename) = compile.Tablename.parse_service_table(table)
            if service is not None:
                LOG.debug("Unsubscribing to new (service, table): (%s, %s)",
                          service, tablename)
                self.unsubscribe(service, tablename)

    # Note(thread-safety): blocking function
    def execute_action(self, service_name, action, action_args):
        """Event handler for action execution.

        :param service_name: openstack service to perform the action on,
            e.g. 'nova', 'neutron'
        :param action: action to perform on service, e.g. an API call
        :param action_args: positional-args and named-args in format:
            {'positional': ['p_arg1', 'p_arg2'],
            'named': {'name1': 'n_arg1', 'name2': 'n_arg2'}}.
        """
        if not self.log_actions_only:
            LOG.info("action %s is called with args %s on %s, but "
                     "current configuration doesn't allow Congress to "
                     "execute any action.", action, action_args, service_name)
            return

        # Log the execution
        LOG.info("%s:: executing: %s:%s on %s",
                 self.name, service_name, action, action_args)
        if self.logger is not None:
            pos_args = ''
            if 'positional' in action_args:
                pos_args = ", ".join(str(x) for x in action_args['positional'])
            named_args = ''
            if 'named' in action_args:
                named_args = ", ".join(
                    "%s=%s" % (key, val)
                    for key, val in action_args['named'].items())
            delimit = ''
            if pos_args and named_args:
                delimit = ', '
            self.logger.info(
                "Executing %s:%s(%s%s%s)",
                service_name, action, pos_args, delimit, named_args)

        # execute the action on a service in the DSE
        if not self.service_exists(service_name):
            raise exception.PolicyException(
                "Service %s not found" % service_name)
        if not action:
            raise exception.PolicyException("Action not found")
        LOG.info("Sending request(%s:%s), args = %s",
                 service_name, action, action_args)
        # Note(thread-safety): blocking call
        self._rpc(service_name, action, args=action_args)

    def pub_policy_result(self, table, olddata, newdata):
        """Callback for policy table triggers."""
        LOG.debug("grabbing policySubData[%s]", table)
        policySubData = self.policySubData[table]
        policySubData.to_add = newdata - olddata
        policySubData.to_rem = olddata - newdata
        LOG.debug("Table Data:: Old: %s, new: %s, add: %s, rem: %s",
                  olddata, newdata, policySubData.to_add, policySubData.to_rem)

        # TODO(dse2): checks needed that all literals are facts
        # TODO(dse2): should we support modals and other non-fact literals?
        # convert literals to rows for dse2
        newdata = [lit.argument_names() for lit in newdata]
        self.publish(policySubData.dataindex, newdata)

    def get_snapshot(self, table_name):
        # print("agnostic policy engine get_snapshot(%s); %s" % (
        #     table_name, self.policySubData[table]))
        (policy, tablename) = compile.Tablename.parse_service_table(table_name)
        data = self.get_row_data(tablename, policy, trace=False)
        data = [tuple(record['data']) for record in data]
        return data

    def _maintain_triggers(self):
        # ensure there is a trigger registered to execute actions
        curr_tables = set(self.global_dependency_graph.tables_with_modal(
            'execute'))
        # add new triggers
        for table in curr_tables:
            LOG.debug("%s:: checking for missing trigger table %s",
                      self.name, table)
            if table not in self.execution_triggers:
                (policy, tablename) = compile.Tablename.parse_service_table(
                    table)
                LOG.debug("creating new trigger for policy=%s, table=%s",
                          policy, tablename)
                trig = self.trigger_registry.register_table(
                    tablename, policy,
                    lambda table, old, new: self._execute_table(
                        policy, tablename, old, new),
                    modal='execute')
                self.execution_triggers[table] = trig
        # remove triggers no longer needed
        #    Using copy of execution_trigger keys so we can delete inside loop
        for table in self.execution_triggers.copy().keys():
            LOG.debug("%s:: checking for stale trigger table %s",
                      self.name, table)
            if table not in curr_tables:
                LOG.debug("removing trigger for table %s", table)
                try:
                    self.trigger_registry.unregister(
                        self.execution_triggers[table])
                    del self.execution_triggers[table]
                except KeyError:
                    LOG.exception(
                        "Tried to unregister non-existent trigger: %s", table)

    # Note(thread-safety): blocking function
    def _execute_table(self, theory, table, old, new):
        # LOG.info("execute_table(theory=%s, table=%s, old=%s, new=%s",
        #          theory, table, ";".join(str(x) for x in old),
        #          ";".join(str(x) for x in new))
        service, tablename = compile.Tablename.parse_service_table(table)
        service = service or theory
        for newlit in new - old:
            args = [term.name for term in newlit.arguments]
            LOG.info("%s:: on service %s executing %s on %s",
                     self.name, service, tablename, args)
            try:
                # Note(thread-safety): blocking call
                self.execute_action(service, tablename, {'positional': args})
            except exception.PolicyException as e:
                LOG.error(str(e))

    def stop(self):
        if self.synchronizer:
            self.synchronizer.stop()
        super(DseRuntime, self).stop()

    # eventually we should remove the action theory as a default,
    #   but we need to update the docs and tutorials
    def create_default_policies(self):
        # check the DB before creating policy instead of in-mem
        policy = db_policy_rules.get_policy_by_name(self.DEFAULT_THEORY)
        if policy is None:
            self.persistent_create_policy(name=self.DEFAULT_THEORY,
                                          desc='default policy')

        policy = db_policy_rules.get_policy_by_name(self.ACTION_THEORY)
        if policy is None:
            self.persistent_create_policy(name=self.ACTION_THEORY,
                                          kind=base.ACTION_POLICY_TYPE,
                                          desc='default action policy')

    # Note(thread-safety): blocking function
    def _rpc(self, service_name, action, args):
        """Overloading the DseRuntime version of _rpc so it uses dse2."""
        # TODO(ramineni): This is called only during execute_action, added
        # the same function name for compatibility with old arch

        retry_rpc = cfg.CONF.dse.execute_action_retry
        args = {'action': action, 'action_args': args, 'wait': retry_rpc}

        def execute_once():
            return self.rpc(service_name, 'request_execute', args,
                            timeout=cfg.CONF.dse.long_timeout, retry=0)

        def execute_retry():
            timeout = cfg.CONF.dse.execute_action_retry_timeout
            start_time = time.time()
            end_time = start_time + timeout
            while timeout <= 0 or time.time() < end_time:
                try:
                    return self.rpc(
                        service_name, 'request_execute', args,
                        timeout=cfg.CONF.dse.long_timeout, retry=0)
                except (messaging_exceptions.MessagingTimeout,
                        messaging_exceptions.MessageDeliveryFailure):
                    LOG.warning('DSE failure executing action %s with '
                                'arguments %s. Retrying.',
                                action, args['action_args'])
            LOG.error('Failed to executing action %s with arguments %s',
                      action, args['action_args'])

        # long timeout for action execution because actions can take a while
        if not retry_rpc:
            # Note(thread-safety): blocking call
            #   Only when thread pool at capacity
            eventlet.spawn_n(execute_once)
            eventlet.sleep(0)
        else:
            # Note(thread-safety): blocking call
            #   Only when thread pool at capacity
            eventlet.spawn_n(execute_retry)
            eventlet.sleep(0)

    def service_exists(self, service_name):
        return self.is_valid_service(service_name)

    def receive_data(self, publisher, table, data, is_snapshot=False):
        """Event handler for when a dataservice publishes data.

        That data can either be the full table (as a list of tuples)
        or a delta (a list of Events).
        """
        LOG.debug("received data msg for %s:%s", publisher, table)
        if not is_snapshot:
            to_add = data[0]
            to_del = data[1]
            result = []
            for row in to_del:
                formula = compile.Literal.create_from_table_tuple(
                    table, utils.tuple_to_congress(row))
                event = compile.Event(formula=formula, insert=False)
                result.append(event)
            for row in to_add:
                formula = compile.Literal.create_from_table_tuple(
                    table, utils.tuple_to_congress(row))
                event = compile.Event(formula=formula, insert=True)
                result.append(event)
            self.receive_data_update(publisher, table, result)
            return

        # if empty data, assume it is an init msg, since noop otherwise
        if len(data) == 0:
            self.receive_data_full(publisher, table, data)
        else:
            # grab an item from any iterable
            dataelem = next(iter(data))
            if isinstance(dataelem, compile.Event):
                self.receive_data_update(publisher, table, data)
            else:
                self.receive_data_full(publisher, table, data)

    def receive_data_full(self, publisher, table, data):
        """Handler for when dataservice publishes full table."""
        LOG.debug("received full data msg for %s:%s. %s",
                  publisher, table, utility.iterstr(data))
        # Use a generator to avoid instantiating all these Facts at once.
        facts = (compile.Fact(table, utils.tuple_to_congress(row))
                 for row in data)
        self.initialize_tables([table], facts, target=publisher)

    def receive_data_update(self, publisher, table, data):
        """Handler for when dataservice publishes a delta."""
        LOG.debug("received update data msg for %s:%s: %s",
                  publisher, table, utility.iterstr(data))
        events = data
        for event in events:
            assert compile.is_atom(event.formula), (
                "receive_data_update received non-atom: " +
                str(event.formula))
            # prefix tablename with data source
            event.target = publisher
        (permitted, changes) = self.update(events)
        if not permitted:
            raise exception.CongressException(
                "Update not permitted." + '\n'.join(str(x) for x in changes))
        else:
            LOG.debug("update data msg for %s from %s caused %d "
                      "changes: %s", table, publisher, len(changes),
                      utility.iterstr(changes))
            if table in self.theory[publisher].tablenames():
                rows = self.theory[publisher].content([table])
                LOG.debug("current table: %s", utility.iterstr(rows))

    def on_first_subs(self, tables):
        """handler for policy table subscription

        when a previously non-subscribed table gains a subscriber, register a
        trigger for the tables and publish table results when there is
        updates.
        """
        for table in tables:
            (policy, tablename) = compile.Tablename.parse_service_table(
                table)
            # we only care about policy table subscription
            if policy is None:
                return

            if not (tablename, policy, None) in self.policySubData:
                trig = self.trigger_registry.register_table(
                    tablename,
                    policy,
                    self.pub_policy_result)
                self.policySubData[
                    (tablename, policy, None)] = PolicySubData(trig)

    def on_no_subs(self, tables):
        """Remove triggers when tables have no subscribers."""
        for table in tables:
            (policy, tablename) = compile.Tablename.parse_service_table(table)
            if (tablename, policy, None) in self.policySubData:
                # release resource if no one cares about it any more
                sub = self.policySubData.pop((tablename, policy, None))
                self.trigger_registry.unregister(sub.trigger())
        return True

    def set_schema(self, name, schema, complete=False):
        old_tables = self.tablenames(body_only=True)
        super(DseRuntime, self).set_schema(name, schema, complete)
        new_tables = self.tablenames(body_only=True)
        self.update_table_subscriptions(old_tables, new_tables)


class DseRuntimeEndpoints(object):
    """RPC endpoints exposed by DseRuntime."""

    def __init__(self, dse):
        self.dse = dse

    # Note(thread-safety): blocking function
    def persistent_create_policy(self, context, name=None, id_=None,
                                 abbr=None, kind=None, desc=None):
        # Note(thread-safety): blocking call
        return self.dse.persistent_create_policy(name, id_, abbr, kind, desc)

    # Note(thread-safety): blocking function
    def persistent_create_policy_with_rules(self, context, policy_rules_obj):
        # Note(thread-safety): blocking call
        return self.dse.persistent_create_policy_with_rules(policy_rules_obj)

    # Note(thread-safety): blocking function
    def persistent_delete_policy(self, context, name_or_id):
        # Note(thread-safety): blocking call
        return self.dse.persistent_delete_policy(name_or_id)

    # Note(thread-safety): blocking function
    def persistent_get_policies(self, context):
        # Note(thread-safety): blocking call
        return self.dse.persistent_get_policies()

    # Note(thread-safety): blocking function
    def persistent_get_policy(self, context, id_):
        # Note(thread-safety): blocking call
        return self.dse.persistent_get_policy(id_)

    # Note(thread-safety): blocking function
    def persistent_get_rule(self, context, id_, policy_name):
        # Note(thread-safety): blocking call
        return self.dse.persistent_get_rule(id_, policy_name)

    # Note(thread-safety): blocking function
    def persistent_get_rules(self, context, policy_name):
        # Note(thread-safety): blocking call
        return self.dse.persistent_get_rules(policy_name)

    # Note(thread-safety): blocking function
    def persistent_insert_rule(self, context, policy_name, str_rule, rule_name,
                               comment):
        # Note(thread-safety): blocking call
        return self.dse.persistent_insert_rule(
            policy_name, str_rule, rule_name, comment)

    # Note(thread-safety): blocking function
    def persistent_delete_rule(self, context, id_, policy_name_or_id):
        # Note(thread-safety): blocking call
        return self.dse.persistent_delete_rule(id_, policy_name_or_id)

    # Note(thread-safety): blocking function
    def persistent_load_policies(self, context):
        # Note(thread-safety): blocking call
        return self.dse.persistent_load_policies()

    def simulate(self, context, query, theory, sequence, action_theory,
                 delta=False, trace=False, as_list=False):
        return self.dse.simulate(query, theory, sequence, action_theory,
                                 delta, trace, as_list)

    def get_tablename(self, context, source_id, table_id):
        return self.dse.get_tablename(source_id, table_id)

    def get_tablenames(self, context, source_id):
        return self.dse.get_tablenames(source_id)

    def get_status(self, context, source_id, params):
        return self.dse.get_status(source_id, params)

    def get_row_data(self, context, table_id, source_id, trace=False):
        return self.dse.get_row_data(table_id, source_id, trace)

    # Note(thread-safety): blocking function
    def execute_action(self, context, service_name, action, action_args):
        # Note(thread-safety): blocking call
        return self.dse.execute_action(service_name, action, action_args)

    def delete_policy(self, context, name, disallow_dangling_refs=False):
        return self.dse.delete_policy(name, disallow_dangling_refs)

    def initialize_datasource(self, context, name, schema):
        return self.dse.initialize_datasource(name, schema)

    def synchronize_policies(self, context):
        return self.dse.synchronizer.synchronize_all_policies()

    def sync_one_policy(self, context, policy_name):
        return self.dse.synchronizer.sync_one_policy(policy_name)
