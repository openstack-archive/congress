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
#
from oslo_log import log as logging
import retrying

from congress.datalog import base
from congress.datalog import compile
from congress import harness
from congress.policy_engines import agnostic
from congress.tests import base as testbase
from congress.tests import helper

LOG = logging.getLogger(__name__)

NREC_THEORY = 'non-recursive theory'
DB_THEORY = 'database'
ACTION_THEORY = 'action'


class TestRuntimePerformance(testbase.TestCase):
    """Tests for Runtime performance that are not specific to any theory.

    To run one test:
      nosetests -v  \
      congress/tests/policy/test_runtime_performance.py:TestRuntimePerformance.test_foo

    To collect profiling data:
      python -m cProfile -o profile.out `which nosetests` -v \
      congress/tests/policy/test_runtime_performance.py:TestRuntimePerformance.test_foo

    To parse and sort profiling data in different ways:
      import pstats
      pstats.Stats('profile.out').strip_dirs().sort_stats("cum").print_stats()
      pstats.Stats('profile.out').strip_dirs().sort_stats("time").print_stats()
      pstats.Stats('profile.out').strip_dirs().sort_stats("calls").print_stats()

    """

    def setUp(self):
        super(TestRuntimePerformance, self).setUp()

        self._agnostic = agnostic.Runtime()
        self._agnostic.create_policy(NREC_THEORY,
                                     kind=base.NONRECURSIVE_POLICY_TYPE)
        self._agnostic.create_policy(DB_THEORY, kind=base.DATABASE_POLICY_TYPE)
        self._agnostic.debug_mode()
        self._agnostic.insert('', target=NREC_THEORY)

    def _create_event(self, table, tuple_, insert, target):
        return compile.Event(compile.Literal.create_from_table_tuple(table,
                                                                     tuple_),
                             insert=insert, target=target)

    def _create_large_tables(self, n, theory):
        facts = [compile.Fact('p', (i, j, k))
                 for i in range(n) for k in range(n) for j in range(n)]

        facts.extend(compile.Fact('q', (i,)) for i in range(n))
        self._agnostic.initialize_tables(['p', 'q'], facts, theory)

    def test_insert_nonrecursive(self):
        MAX = 100
        th = NREC_THEORY
        for i in range(MAX):
            self._agnostic.insert('r(%d)' % i, th)

    def test_insert_database(self):
        MAX = 100
        th = DB_THEORY
        for i in range(MAX):
            self._agnostic.insert('r(%d)' % i, th)

    def test_update_nonrecursive(self):
        MAX = 10000
        th = NREC_THEORY
        updates = [self._create_event('r', (i,), True, th)
                   for i in range(MAX)]
        self._agnostic.update(updates)

    def test_update_database(self):
        MAX = 1000
        th = DB_THEORY
        updates = [self._create_event('r', (i,), True, th)
                   for i in range(MAX)]
        self._agnostic.update(updates)

    def test_indexing(self):
        MAX = 100
        th = NREC_THEORY

        for table in ('a', 'b', 'c'):
            updates = [self._create_event(table, (i,), True, th)
                       for i in range(MAX)]
            self._agnostic.update(updates)

        # With indexing, this query should take O(n) time where n is MAX.
        # Without indexing, this query will take O(n^3).
        self._agnostic.insert('d(x) :- a(x), b(x), c(x)', th)
        ans = ' '.join(['d(%d)' % i for i in range(MAX)])
        self.assertTrue(helper.datalog_equal(self._agnostic.select('d(x)',
                                                                   th), ans))

    def test_runtime_initialize_tables(self):
        MAX = 700
        longstring = 'a' * 100
        facts = (compile.Fact('p',
                              (1, 2, 'foo', 'bar', i, longstring + str(i)))
                 for i in range(MAX))

        th = NREC_THEORY
        self._agnostic.initialize_tables(['p'], facts, th)

    def test_select_1match(self):
        # with different types of policies (exercise indexing, large sets,
        # many joins, etc)
        MAX = 10
        th = NREC_THEORY

        self._create_large_tables(MAX, th)
        self._agnostic.insert('r(x,y) :- p(x,x,y), q(x)', th)

        for i in range(100):
            # This select returns 1 result
            self._agnostic.select('r(1, 1)', th)

    def test_select_100matches(self):
        # with different types of policies (exercise indexing, large sets,
        # many joins, etc)
        MAX = 10
        th = NREC_THEORY

        self._create_large_tables(MAX, th)
        self._agnostic.insert('r(x,y) :- p(x,x,y), q(x)', th)

        # This takes about 60ms per select
        for i in range(10):
            # This select returns 100 results
            self._agnostic.select('r(x, y)', th)

    def test_simulate_latency(self):
        # We think the cost will be the sum of the simulate call + the cost to
        # do and undo the evaluation, so this test should focus on the cost
        # specific to the simulate call, so the the test should do a minimal
        # amount of evaluation.

        MAX = 10
        th = NREC_THEORY

        self._create_large_tables(MAX, th)
        self._agnostic.create_policy(ACTION_THEORY,
                                     kind=base.ACTION_POLICY_TYPE)

        self._agnostic.insert('q(0)', th)
        self._agnostic.insert('s(x) :- q(x), p(x,0,0)', th)

        # This takes about 13ms per simulate.  The query for s(x) can use
        # indexing, so it should be efficient.
        for _ in range(100):
            self._agnostic.simulate('s(x)', th, 'p-(0,0,0)',
                                    ACTION_THEORY, delta=True)

    def test_simulate_throughput(self):
        # up to 250 requests per second
        pass

    def test_update_rate(self):
        pass

    def test_concurrency(self):
        pass


class TestDsePerformance(testbase.SqlTestCase):

    def setUp(self):
        super(TestDsePerformance, self).setUp()
        self.cage = harness.create(helper.root_path(), config_override={})
        self.api = {'policy': self.cage.service_object('api-policy'),
                    'rule': self.cage.service_object('api-rule'),
                    'table': self.cage.service_object('api-table'),
                    'row': self.cage.service_object('api-row'),
                    'datasource': self.cage.service_object('api-datasource'),
                    'status': self.cage.service_object('api-status'),
                    'schema': self.cage.service_object('api-schema')}
        self.engine = self.cage.service_object('engine')

    @retrying.retry(wait_fixed=100)
    def wait_til_query_nonempty(self, query, policy):
        if len(self.engine.select(query, target=policy)) == 0:
            raise Exception("Query %s is not empty" % query)

    def test_initialize_tables_dse(self):
        """Test performance of initializing data with DSE and Engine.

        This test populates the tables exported by a datasource driver,
        and then invokes the poll() method to send that data to the
        policy engine.  It tests the amount of time to send tables
        across the DSE and load them into the policy engine.
        """
        MAX_TUPLES = 700
        # install datasource driver we can control
        self.cage.loadModule(
            "TestDriver",
            helper.data_module_path(
                "../tests/datasources/test_driver.py"))
        self.cage.createservice(
            name="data",
            moduleName="TestDriver",
            args=helper.datasource_openstack_args())
        driver = self.cage.service_object('data')
        driver.poll_time = 0
        self.engine.create_policy('data')

        # set return value for datasource driver
        facts = [(1, 2.3, 'foo', 'bar', i, 'a'*100 + str(i))
                 for i in range(MAX_TUPLES)]
        driver.state = {'p': facts}

        # Send formula to engine (so engine subscribes to data:p)
        policy = self.engine.DEFAULT_THEORY
        formula = compile.parse1(
            'q(1) :- data:p(1, 2.3, "foo", "bar", 1, %s)' % ('a'*100 + '1'))
        self.api['rule'].publish(
            'policy-update', [compile.Event(formula, target=policy)])

        # Poll data and wait til it arrives at engine
        driver.poll()
        self.wait_til_query_nonempty('q(1)', policy)

    def test_initialize_tables_full(self):
        """Test performance of initializing data with Datasource, DSE, Engine.

        This test gives a datasource driver the Python data that would
        have resulted from making an API call and parsing it into Python
        and then polls that datasource, waiting until the data arrives
        in the policy engine.  It tests the amount of time required to
        translate Python data into tables, send those tables over the DSE,
        and load them into the policy engine.
        """
        MAX_TUPLES = 700
        # install datasource driver we can control
        self.cage.loadModule(
            "PerformanceTestDriver",
            helper.data_module_path(
                "../tests/datasources/performance_datasource_driver.py"))
        self.cage.createservice(
            name="data",
            moduleName="PerformanceTestDriver",
            args=helper.datasource_openstack_args())
        driver = self.cage.service_object('data')
        driver.poll_time = 0
        self.engine.create_policy('data')

        # set return value for datasource driver
        facts = [{'field1': 1,
                  'field2': 2.3,
                  'field3': 'foo',
                  'field4': 'bar',
                  'field5': i,
                  'field6': 'a'*100 + str(i)}
                 for i in range(MAX_TUPLES)]
        driver.client_data = facts

        # Send formula to engine (so engine subscribes to data:p)
        policy = self.engine.DEFAULT_THEORY
        formula = compile.parse1(
            'q(1) :- data:p(1, 2.3, "foo", "bar", 1, %s)' % ('a'*100 + '1'))
        LOG.info("publishing rule")
        self.api['rule'].publish(
            'policy-update', [compile.Event(formula, target=policy)])

        # Poll data and wait til it arrives at engine
        driver.poll()
        self.wait_til_query_nonempty('q(1)', policy)
