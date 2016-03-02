# Copyright (c) 2014 OpenStack Foundation
#
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

from oslo_config import cfg
cfg.CONF.distributed_architecture = True

from congress import exception as congressException
from congress.tests import base
from congress.tests import fake_datasource
from congress.tests import helper


class TestDataSource(base.SqlTestCase):

    def setUp(self):
        super(TestDataSource, self).setUp()
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource'])
        self.dseNode = helper.make_dsenode_new_partition('testnode')

    def _get_datasource_request(self):
        # leave ID out--generated during creation
        return {'name': 'aaron',
                'driver': 'fake_datasource',
                'description': 'hello world!',
                'enabled': True,
                'type': None,
                'config': {'auth_url': 'foo',
                           'username': 'armax',
                           'password': 'password',
                           'tenant_name': 'armax'}}

    def test_add_datasource(self):
        req = self._get_datasource_request()
        result = self.dseNode.add_datasource(req)
        # test equality of return value except for 'id' field
        del(result['id'])
        self.assertEqual(req, result)
        # check that service actually on dseNode
        services = self.dseNode.get_services()
        self.assertEqual(len(services), 1)
        self.assertEqual(services[0].service_id, req['name'])
        self.assertTrue(isinstance(services[0],
                        fake_datasource.FakeDataSource))
        obj = self.dseNode.invoke_service_rpc(
            req['name'], 'get_status', source_id=None, params=None)
        self.assertIsNotNone(obj)

    def test_get_datasource(self):
        req = self._get_datasource_request()
        ds = self.dseNode.add_datasource(req)
        result = self.dseNode.get_datasource(ds['id'])
        # test equality except for 'id' field
        del(result['id'])
        self.assertEqual(req, result)

    def test_get_datasources(self):
        req = self._get_datasource_request()
        self.dseNode.add_datasource(req)
        result = self.dseNode.get_datasources()
        self.assertEqual(len(result), 1)
        result = result[0]
        # test equality except for 'id' field
        del(result['id'])
        self.assertEqual(req, result)

    def test_get_datasources2(self):
        req1 = self._get_datasource_request()
        req1['name'] = 'datasource1'
        result1 = self.dseNode.add_datasource(req1)
        req2 = self._get_datasource_request()
        req2['name'] = 'datasource2'
        result2 = self.dseNode.add_datasource(req2)
        # check results of add_datasource
        for key, value in req1.items():
            self.assertEqual(value, result1[key])
        for key, value in req2.items():
            self.assertEqual(value, result2[key])
        # check services actually on dseNode
        services = self.dseNode.get_services()
        self.assertEqual(len(services), 2)
        self.assertEqual(set([s.service_id for s in services]),
                         set(['datasource1', 'datasource2']))
        self.assertTrue(isinstance(services[0],
                        fake_datasource.FakeDataSource))
        self.assertTrue(isinstance(services[1],
                        fake_datasource.FakeDataSource))
        # check results of get_datasources
        resultall = self.dseNode.get_datasources()
        self.assertEqual(len(resultall), 2)
        # check equality except for 'id' field
        byname = {x['name']: x for x in resultall}
        for x in byname.values():
            del(x['id'])
        self.assertEqual(byname, {'datasource1': req1, 'datasource2': req2})

    def test_get_datasources_hide_secret(self):
        req = self._get_datasource_request()
        self.dseNode.add_datasource(req)
        result = self.dseNode.get_datasources(filter_secret=True)
        result = result[0]
        # check equality except that 'config'/'password' is hidden
        req['config']['password'] = "<hidden>"
        del(result['id'])
        self.assertEqual(result, req)

    def test_create_datasource_duplicate_name(self):
        req = self._get_datasource_request()
        self.dseNode.add_datasource(req)
        self.assertRaises(congressException.DatasourceNameInUse,
                          self.dseNode.add_datasource, req)

    def test_delete_datasource(self):
        req = self._get_datasource_request()
        result = self.dseNode.add_datasource(req)
        self.dseNode.delete_datasource(result)
        # check that service is actually deleted
        services = self.dseNode.get_services()
        self.assertEqual(len(services), 0)
        self.assertRaises(
            congressException.NotFound, self.dseNode.invoke_service_rpc,
            req['name'], 'get_status', source_id=None, params=None)
        # TODO(thinrichs): test that we've actually removed
        #   the row from the DB

    # TODO(dse2): this test relies on coordination between dseNode and
    #  policy engine.  Much harder in distributed system.  Need to decide
    #  if we want that kind of invariant and if so implement it.
    # def test_delete_datasource_error(self):
    #     req = self._get_datasource_request()
    #     req['driver'] = 'fake_datasource'
    #     req['config'] = {'auth_url': 'foo',
    #                      'username': 'armax',
    #                      'password': 'password',
    #                      'tenant_name': 'armax'}
    #     # let driver generate this for us.
    #     del req['id']
    #     result = self.datasource_mgr.add_datasource(req)
    #     engine = self.dseNode.service_object('engine')
    #     engine.create_policy('alice')
    #     engine.insert('p(x) :- %s:q(x)' % req['name'], 'alice')
    #     self.assertRaises(exception.DanglingReference,
    #                       self.datasource_mgr.delete_datasource,
    #                       result['id'])

    def test_delete_invalid_datasource(self):
        req = self._get_datasource_request()
        req['id'] = 'fake-id'
        self.assertRaises(congressException.DatasourceNotFound,
                          self.dseNode.delete_datasource, req)

    # TODO(dse2): Doesn't seem like we need this (or it will be moved to API).
    # def test_get_driver_schema(self):
    #     schema = self.datasource_mgr.get_driver_schema(
    #         'fake_datasource')
    #     self.assertEqual(
    #         schema,
    #         fake_datasource.FakeDataSource.get_schema())

    def test_duplicate_driver_name_raises(self):
        # Load the driver twice
        cfg.CONF.set_override(
            'drivers',
            ['congress.tests.fake_datasource.FakeDataSource',
             'congress.tests.fake_datasource.FakeDataSource'])
        self.assertRaises(congressException.BadConfig,
                          self.dseNode.load_drivers)
