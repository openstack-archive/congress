# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import functools
import logging

import eventlet
from mox3 import mox
from six.moves import range

from congress.datalog import compile
from congress.dse import dataobj
from congress import harness
from congress.policy_engines import agnostic
from congress.tests import base
from congress.tests import helper


LOG = logging.getLogger(__name__)


class BenchmarkDatasource(base.Benchmark):

    def setUp(self):
        super(BenchmarkDatasource, self).setUp()
        config = {'benchmark': {
                  'module': helper.data_module_path('benchmark_driver.py'),
                  'poll_time': 0}}
        cage = harness.create(helper.root_path(), None, config)
        engine = cage.service_object('engine')
        api = {'policy': cage.service_object('api-policy'),
               'rule': cage.service_object('api-rule'),
               'table': cage.service_object('api-table'),
               'row': cage.service_object('api-row'),
               'datasource': cage.service_object('api-datasource'),
               'status': cage.service_object('api-status'),
               'schema': cage.service_object('api-schema')}
        helper.retry_check_subscriptions(engine, [(api['rule'].name,
                                         'policy-update')])
        helper.retry_check_subscribers(api['rule'], [(engine.name,
                                       'policy-update')])
        self.assertTrue('benchmark' in cage.services)
        datasource = cage.service_object('benchmark')
        table_name = datasource.BENCHTABLE

        self.assertEqual(datasource.state, {})

        # add a subscriber to ensure the updates end up in datasource.dataPath
        pubdata = datasource.pubdata.setdefault(table_name,
                                                dataobj.pubData(table_name))
        pubdata.addsubscriber(self.__class__.__name__, "push", "")
        self.assertTrue(datasource.pubdata[table_name])

        self.cage = cage
        self.engine = engine
        self.api = api
        self.table_name = table_name
        self.datasource = datasource

    def benchmark_datasource_update(self, size):
        """Benchmark a datasource update.

        Time the propagation of a datasource update from datasource.poll() to
        ending up in the datasource.dataPath queue.
        """

        LOG.info("%s:: benchmarking datasource update of %d rows", size)
        self.datasource.datarows = size

        # intercept the queue addition so it doesn't immediately get pulled off
        # by the d6cage
        received = eventlet.Queue()
        self.mox.StubOutWithMock(self.datasource.dataPath, "put_nowait")
        self.datasource.dataPath.put_nowait(mox.IgnoreArg()).WithSideEffects(
            received.put_nowait)
        self.mox.ReplayAll()

        # poll and then wait until we've got an item from our queue
        LOG.info("%s:: polling datasource", self.__class__.__name__)
        self.datasource.poll()
        result = received.get(timeout=30)
        self.assertTrue(result.body)
        self.assertEqual(len(result.body.data), size)
        self.mox.VerifyAll()

    def benchmark_datasource_to_policy_update(self, size):
        """Benchmark small datsource update to policy propagation.

        Time the propagation of a datasource update from datasource.poll() to
        completion of a simple policy update.
        """
        LOG.info("%s:: benchmarking datasource update of %d rows", size)
        self.datasource.datarows = size
        table_name = self.table_name

        # dummy policy only intended to produce a subscriber for the table
        key_to_index = self.datasource.get_column_map(table_name)
        id_index = 'x%d' % list(key_to_index.items())[0][1]
        max_index = max(key_to_index.values())
        args = ['x%d' % i for i in range(max_index + 1)]
        formula = compile.parse1('p(%s) :- benchmark:%s(%s)' % (id_index,
                                 table_name, ','.join(args)))

        # publish the formula and verify we see a subscription
        LOG.debug('%s:: sending formula: %s', self.__class__.__name__, formula)
        self.api['rule'].publish('policy-update', [agnostic.Event(formula)])
        helper.retry_check_subscriptions(
            self.engine, [('benchmark', table_name)])
        helper.retry_check_subscribers(
            self.datasource, [(self.engine.name, table_name)])

        # intercept inbox.task_done() so we know when it's finished. Sadly,
        # eventlet doesn't have a condition-like object.
        fake_condition = eventlet.Queue()
        fake_notify = functools.partial(fake_condition.put_nowait, True)
        self.mox.StubOutWithMock(self.engine.inbox, "task_done")
        self.engine.inbox.task_done().WithSideEffects(fake_notify)
        self.mox.ReplayAll()

        LOG.info("%s:: polling datasource", self.__class__.__name__)
        self.datasource.poll()
        fake_condition.get(timeout=30)
        self.mox.VerifyAll()

    def test_benchmark_datasource_update_small(self):
        """Benchmark a small datasource update.

        Time the propagation of a small (10 row) datasource update from
        datasource.poll() to ending up in the datasource.dataPath queue.
        """
        self.benchmark_datasource_update(10)

    def test_benchmark_datasource_update_large(self):
        """Benchmark a large datasource update.

        Time the propagation of a large (100k row) datasource update from
        datasource.poll() to ending up in the datasource.dataPath queue.
        """
        self.benchmark_datasource_update(100000)

    def test_benchmark_datasource_to_policy_update_small(self):
        """Benchmark small datsource update to policy propagation.

        Time the propagation of a small (10 row) datasource update from
        datasource.poll() to a simple policy update.
        """
        self.benchmark_datasource_to_policy_update(10)

    def test_benchmark_datasource_to_policy_update_large(self):
        """Benchmark small datsource update to policy propagation.

        Time the propagation of a large (100k row) datasource update from
        datasource.poll() to a simple policy update.
        """
        self.benchmark_datasource_to_policy_update(100000)
