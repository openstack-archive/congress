#
# Copyright (c) 2016 VMware, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
test_congress_haht
----------------------------------

Replicated policy engine high availability tests for `congress` module.
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import shutil
import subprocess
import sys
import tempfile
import time

from oslo_log import log as logging
import requests
import tenacity

from congress.db import api as db
from congress.db import db_policy_rules
from congress.tests import base
from congress.tests import helper


LOG = logging.getLogger(__name__)


class TestCongressHAHT(base.SqlTestCase):

    class client(object):
        version = '/v1'

        def __init__(self, port, host='0.0.0.0'):
            self.host = host
            self.port = port
            self.base_url = 'http://' + host + ':%d' % port

        def url(self, suffix=None):
            if suffix is None:
                return self.base_url
            else:
                return self.base_url + self.version + '/' + suffix

        def get(self, suffix=None):
            return requests.get(self.url(suffix))

        def delete(self, suffix=None):
            return requests.delete(self.url(suffix))

        def post(self, suffix=None, json=None):
            x = requests.post(self.url(suffix), json=json)
            # print("status: %s, text: %s" % (x.status_code, x.text))
            return x

    def setUp(self):
        super(TestCongressHAHT, self).setUp()
        assert sys.executable is not None,\
            'test cannot proceed when sys.executable is None'

        # establish clean starting DB
        self.clean_db()
        shutil.copy(helper.test_path('haht/test.db.clean'),
                    helper.test_path('haht/test.db'))

        self.clients = []
        self.procs = []
        self.outfiles = {}
        self.errfiles = {}

        self.pe1 = self.start_pe(1, 4001)
        self.pe2 = self.start_pe(2, 4002)

    def dump_nodes_logs(self):
        LOG.error('PE1 process output:\n%s' %
                  self.read_output_file(self.outfiles[1]))
        LOG.error('PE2 process output:\n%s' %
                  self.read_output_file(self.outfiles[2]))

    def clean_db(self):
        session = db.get_session()
        with session.begin(subtransactions=True):
            session.query(db_policy_rules.Policy).delete()
            session.query(db_policy_rules.PolicyRule).delete()

    def start_pe(self, num, port):
        self.outfiles[num] = tempfile.NamedTemporaryFile(
            mode='a+', suffix='.out',
            prefix='congress-pe%d-%d-' % (num, port),
            dir='/tmp')

        self.errfiles[num] = tempfile.NamedTemporaryFile(
            mode='a+', suffix='.err',
            prefix='congress-pe%d-%d-' % (num, port),
            dir='/tmp')

        args = [sys.executable,
                'bin/congress-server',
                '--node-id',
                'node_%d' % num,
                '--api',
                '--policy-engine',
                '--config-file',
                'congress/tests/etc/congress.conf.test.ha_pe%d' % num]
        pe = subprocess.Popen(args,
                              stdout=self.outfiles[num],
                              stderr=self.outfiles[num],
                              cwd=helper.root_path())
        self.addCleanup(pe.kill)
        pe = self.client(port)
        try:
            helper.retry_check_function_return_value(
                lambda: pe.get().status_code, 200)
        except tenacity.RetryError:
            out = self.read_output_file(self.outfiles[num])
            LOG.error('PE%d failed to start. Process output:\n%s' % (num, out))
            raise
        return pe

    def read_output_file(self, file):
        file.flush()
        file.seek(0)
        return ''.join(file.readlines())

    def tail(self, thing, length=20):
        lines = thing.split('\n')
        return '\n'.join(lines[-length:])

    def test_policy_create_delete(self):
        # create policy alice in PE1
        self.assertEqual(self.pe1.post(
            suffix='policies', json={'name': 'alice'}).status_code, 201)
        # check policy alice in PE1
        self.assertEqual(self.pe1.get('policies/alice').status_code, 200)
        # check policy alice in PE2
        helper.retry_check_function_return_value(
            lambda: self.pe2.get('policies/alice').status_code, 200)
        # create policy bob in PE2
        self.assertEqual(self.pe2.post(
            suffix='policies', json={'name': 'bob'}).status_code, 201)
        # check policy bob in PE2
        self.assertEqual(self.pe2.get('policies/bob').status_code, 200)
        # check policy bob in PE1
        helper.retry_check_function_return_value(
            lambda: self.pe1.get('policies/bob').status_code, 200)

        # check policy listings
        self.assertEqual(len(self.pe1.get('policies').json()['results']), 4)
        self.assertEqual(len(self.pe2.get('policies').json()['results']), 4)

        # delete policy alice in PE2, and check deleted on both PE
        self.assertEqual(self.pe2.delete('policies/alice').status_code, 200)
        self.assertEqual(self.pe2.get('policies/alice').status_code, 404)
        helper.retry_check_function_return_value(
            lambda: self.pe1.get('policies/alice').status_code, 404)

        # delete policy bob in PE2, and check deleted on both PE
        self.assertEqual(self.pe2.delete('policies/bob').status_code, 200)
        self.assertEqual(self.pe2.get('policies/bob').status_code, 404)
        helper.retry_check_function_return_value(
            lambda: self.pe1.get('policies/bob').status_code, 404)

    def test_policy_rule_crud(self):
        try:
            # create policy alice in PE1
            self.assertEqual(self.pe1.post(
                suffix='policies', json={'name': 'alice'}).status_code, 201)
            # add rule to PE1
            j = {'rule': 'p(x) :- q(x)', 'name': 'rule1'}
            self.assertEqual(self.pe1.post(
                suffix='policies/alice/rules', json=j).status_code, 201)
            self.assertEqual(
                self.pe1.get('policies/alice/rules').status_code, 200)
            self.assertEqual(
                len(self.pe1.get('policies/alice/rules').
                    json()['results']), 1)
            # retry necessary because of synchronization
            helper.retry_check_function_return_value(
                lambda: len(self.pe2.get('policies/alice/rules').
                            json()['results']), 1)
            # add rule to PE2
            j = {'rule': 'q(1)', 'name': 'rule2'}
            self.assertEqual(self.pe2.post(
                suffix='policies/alice/rules', json=j).status_code, 201)
            # check 2 rule in each pe
            self.assertEqual(len(
                self.pe2.get('policies/alice/rules').json()['results']), 2)
            self.assertEqual(len(
                self.pe1.get('policies/alice/rules').json()['results']), 2)

            # grab rule IDs
            rules = self.pe2.get('policies/alice/rules').json()['results']
            id1 = next(x['id'] for x in rules if x['name'] == 'rule1')
            id2 = next(x['id'] for x in rules if x['name'] == 'rule2')

            # show rules by id
            self.assertEqual(
                self.pe1.get('policies/alice/rules/%s' % id1).status_code, 200)
            self.assertEqual(
                self.pe2.get('policies/alice/rules/%s' % id1).status_code, 200)
            self.assertEqual(
                self.pe1.get('policies/alice/rules/%s' % id2).status_code, 200)
            self.assertEqual(
                self.pe2.get('policies/alice/rules/%s' % id2).status_code, 200)

            # list tables
            self.assertEqual(len(
                self.pe1.get('policies/alice/tables').json()['results']), 2)
            self.assertEqual(len(
                self.pe2.get('policies/alice/tables').json()['results']), 2)

            # show tables
            self.assertEqual(
                self.pe1.get('policies/alice/tables/p').status_code, 200)
            self.assertEqual(
                self.pe2.get('policies/alice/tables/p').status_code, 200)
            self.assertEqual(
                self.pe1.get('policies/alice/tables/q').status_code, 200)
            self.assertEqual(
                self.pe2.get('policies/alice/tables/q').status_code, 200)

            # delete from PE1 and check both have 1 rule left
            self.assertEqual(self.pe1.delete(
                suffix='policies/alice/rules/%s' % id1).status_code, 200)
            self.assertEqual(
                len(self.pe1.get('policies/alice/rules').
                    json()['results']), 1)
            self.assertEqual(
                len(self.pe2.get('policies/alice/rules').
                    json()['results']), 1)
            # delete from PE2 and check both have 0 rules left
            self.assertEqual(self.pe2.delete(
                suffix='policies/alice/rules/%s' % id2).status_code, 200)
            self.assertEqual(
                len(self.pe1.get('policies/alice/rules').
                    json()['results']), 0)
            self.assertEqual(
                len(self.pe2.get('policies/alice/rules').
                    json()['results']), 0)
        except Exception:
            self.dump_nodes_logs()
            raise

    def test_conflicting_policy_create_delete(self):
        try:
            # create policy alice in PE1
            self.assertEqual(self.pe1.post(
                suffix='policies', json={'name': 'alice'}).status_code, 201)
            self.assertEqual(self.pe2.post(
                suffix='policies', json={'name': 'alice'}).status_code, 409)

            # create policy bob in PE1
            self.assertEqual(self.pe1.post(
                suffix='policies', json={'name': 'bob'}).status_code, 201)
            self.assertEqual(self.pe2.delete(
                suffix='policies/bob').status_code, 200)
            self.assertEqual(self.pe1.post(
                suffix='policies', json={'name': 'bob'}).status_code, 201)
        except Exception:
            LOG.error('PE1 process output:\n%s' %
                      self.read_output_file(self.outfiles[1]))
            LOG.error('PE2 process output:\n%s' %
                      self.read_output_file(self.outfiles[2]))
            raise

    def test_policy_rule_create_delete(self):
        try:
            # create policy alice in PE1
            self.assertEqual(self.pe1.post(
                suffix='policies', json={'name': 'alice'}).status_code, 201)
            # add rule to PE1 (retry since 500 on first attempt)
            j = {'rule': 'p(x) :- q(x)', 'name': 'rule1'}
            self.assertEqual(self.pe1.post(
                suffix='policies/alice/rules', json=j).status_code, 201)
            self.assertEqual(
                self.pe1.get('policies/alice/rules').status_code, 200)
            self.assertEqual(
                len(self.pe1.get('policies/alice/rules').
                    json()['results']), 1)
            time.sleep(10)  # wait for sync before reading from PE2
            self.assertEqual(
                len(self.pe2.get('policies/alice/rules').
                    json()['results']), 1)
            # add rule to PE2
            j = {'rule': 'q(1)', 'name': 'rule2'}
            self.assertEqual(self.pe2.post(
                suffix='policies/alice/rules', json=j).status_code, 201)
            # check 2 rule in each pe
            self.assertEqual(len(
                self.pe2.get('policies/alice/rules').json()['results']), 2)
            self.assertEqual(len(
                self.pe1.get('policies/alice/rules').json()['results']), 2)
            # grab rule IDs
            rules = self.pe2.get('policies/alice/rules').json()['results']
            id1 = next(x['id'] for x in rules if x['name'] == 'rule1')
            id2 = next(x['id'] for x in rules if x['name'] == 'rule2')
            # delete from PE1 and check both have 1 rule left
            self.assertEqual(self.pe1.delete(
                suffix='policies/alice/rules/%s' % id1).status_code, 200)
            self.assertEqual(
                len(self.pe1.get('policies/alice/rules').
                    json()['results']), 1)
            self.assertEqual(
                len(self.pe2.get('policies/alice/rules').
                    json()['results']), 1)
            # delete from PE2 and check both have 0 rules left
            self.assertEqual(self.pe2.delete(
                suffix='policies/alice/rules/%s' % id2).status_code, 200)
            self.assertEqual(
                len(self.pe1.get('policies/alice/rules').
                    json()['results']), 0)
            self.assertEqual(
                len(self.pe2.get('policies/alice/rules').
                    json()['results']), 0)
        except Exception:
            self.dump_nodes_logs()
            raise

    def test_policy_rule_create_delete_interference(self):
        try:
            # create policy alice in PE1
            self.assertEqual(self.pe1.post(
                suffix='policies', json={'name': 'alice'}).status_code, 201)
            j = {'rule': 'p(x) :- q(x)', 'name': 'rule1'}

            rule_create_res = self.pe2.post(
                suffix='policies/alice/rules', json=j)
            self.assertEqual(rule_create_res.status_code, 201)
            rule_id = rule_create_res.json()['id']
            self.assertEqual(self.pe1.delete(
                suffix='policies/alice/rules/%s' % rule_id).status_code, 200)

            self.assertEqual(self.pe2.post(
                suffix='policies/alice/rules', json=j).status_code, 201)

        except Exception:
            self.dump_nodes_logs()
            raise

    def test_policy_rule_duplicate(self):
        try:
            # create policy alice in PE1
            self.assertEqual(self.pe1.post(
                suffix='policies', json={'name': 'alice'}).status_code, 201)
            j = {'rule': 'p(x) :- q(x)', 'name': 'rule1'}

            self.assertEqual(self.pe2.post(
                suffix='policies/alice/rules', json=j).status_code, 201)

            self.assertEqual(self.pe1.post(
                suffix='policies/alice/rules', json=j).status_code, 409)

            self.assertEqual(self.pe2.post(
                suffix='policies/alice/rules', json=j).status_code, 409)

            self.assertEqual(
                self.pe1.get('policies/alice/rules').status_code, 200)
            self.assertLessEqual(
                len(self.pe1.get('policies/alice/rules').json()['results']),
                1)
            self.assertEqual(
                len(self.pe2.get('policies/alice/rules').
                    json()['results']), 1)
        except Exception:
            self.dump_nodes_logs()
            raise

    def test_policy_rule_recursion(self):
        try:
            # create policy alice in PE1
            self.assertEqual(self.pe1.post(
                suffix='policies', json={'name': 'alice'}).status_code, 201)
            r1 = {'rule': 'p(x) :- q(x)', 'name': 'rule1'}
            r2 = {'rule': 'q(x) :- p(x)', 'name': 'rule2'}

            self.assertEqual(self.pe2.post(
                suffix='policies/alice/rules', json=r1).status_code, 201)

            self.assertEqual(self.pe1.post(
                suffix='policies/alice/rules', json=r2).status_code, 400)

            self.assertEqual(self.pe2.post(
                suffix='policies/alice/rules', json=r2).status_code, 400)

            self.assertEqual(
                self.pe1.get('policies/alice/rules').status_code, 200)
            self.assertLessEqual(
                len(self.pe1.get('policies/alice/rules').json()['results']),
                1)
            self.assertEqual(
                len(self.pe2.get('policies/alice/rules').
                    json()['results']), 1)
        except Exception:
            self.dump_nodes_logs()
            raise

    def test_policy_rule_schema_mismatch(self):
        try:
            # create policy alice in PE1
            self.assertEqual(self.pe1.post(
                suffix='policies', json={'name': 'alice'}).status_code, 201)
            r1 = {'rule': 'p(x) :- q(x)', 'name': 'rule1'}
            r2 = {'rule': 'p(x) :- q(x, x)', 'name': 'rule2'}

            self.assertEqual(self.pe2.post(
                suffix='policies/alice/rules', json=r1).status_code, 201)

            self.assertEqual(self.pe1.post(
                suffix='policies/alice/rules', json=r2).status_code, 400)

            self.assertEqual(self.pe2.post(
                suffix='policies/alice/rules', json=r2).status_code, 400)

            self.assertEqual(
                self.pe1.get('policies/alice/rules').status_code, 200)
            self.assertLessEqual(
                len(self.pe1.get('policies/alice/rules').json()['results']),
                1)
            self.assertEqual(
                self.pe2.get('policies/alice/rules').status_code, 200)
            self.assertEqual(
                len(self.pe2.get('policies/alice/rules').
                    json()['results']), 1)
        except Exception:
            self.dump_nodes_logs()
            raise

    def test_policy_rule_evaluation(self):
        try:
            # create policy alice in PE1
            self.assertEqual(self.pe1.post(
                suffix='policies', json={'name': 'alice'}).status_code, 201)
            # add rule to PE1
            j = {'rule': 'p(x) :- q(x)', 'name': 'rule0'}
            res = self.pe1.post(
                suffix='policies/alice/rules', json=j)
            self.assertEqual(res.status_code, 201)
            r_id = res.json()['id']

            # add data to PE1
            j = {'rule': '  q(   1   )   ', 'name': 'rule1'}
            res = self.pe1.post(
                suffix='policies/alice/rules', json=j)
            self.assertEqual(res.status_code, 201)
            q1_id = res.json()['id']

            # # add data to PE2
            j = {'rule': '  q   (     2  )   ', 'name': 'rule2'}
            self.assertEqual(self.pe2.post(
                suffix='policies/alice/rules', json=j).status_code, 201)

            # eval on PE1
            helper.retry_check_function_return_value_table(
                lambda: [x['data'] for x in
                         self.pe1.get('policies/alice/tables/p/rows').json()[
                             'results']],
                [[1], [2]])

            # eval on PE2
            helper.retry_check_function_return_value_table(
                lambda: [x['data'] for x in
                         self.pe2.get('policies/alice/tables/p/rows').json()[
                             'results']],
                [[1], [2]])

            self.assertEqual(self.pe1.delete(
                suffix='policies/alice/rules/%s' % q1_id).status_code, 200)

            # eval on PE1
            helper.retry_check_function_return_value_table(
                lambda: [x['data'] for x in
                         self.pe1.get('policies/alice/tables/p/rows').json()[
                             'results']],
                [[2]])

            # eval on PE2
            helper.retry_check_function_return_value_table(
                lambda: [x['data'] for x in
                         self.pe2.get('policies/alice/tables/p/rows').json()[
                             'results']],
                [[2]])

            self.assertEqual(self.pe2.delete(
                suffix='policies/alice/rules/%s' % r_id).status_code, 200)
            helper.retry_check_function_return_value(lambda: self.pe1.get(
                'policies/alice/tables/p/rows').status_code, 404)
            helper.retry_check_function_return_value(lambda: self.pe2.get(
                'policies/alice/tables/p/rows').status_code, 404)

        except Exception:
            self.dump_nodes_logs()
            raise
