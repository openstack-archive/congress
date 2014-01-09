#!/usr/bin/python
#
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

import httplib
import json
import os
import socket
import subprocess
import time
import unittest
import uuid


FUNCTIONAL_TESTS_PATH = os.path.dirname(os.path.realpath(__file__))
TESTS_PATH = os.path.dirname(FUNCTIONAL_TESTS_PATH)
PROJECT_PATH = os.path.dirname(TESTS_PATH)
SRC_PATH = os.path.join(PROJECT_PATH, 'src')


class AbstractApiTest(unittest.TestCase):
    API_SERVER_PATH = None  # Subclass must override
    API_SERVER_PORT = '8888'
    API_SERVER_ADDR = '127.0.0.1'
    API_SERVER_ARGS = ['--http_listen_port', API_SERVER_PORT,
                       '--http_listen_addr', API_SERVER_ADDR, '--verbose']
    SERVER_STARTUP_WAIT_MS = 5000
    SERVER_SHUTDOWN_WAIT_MS = 3000

    @classmethod
    def setUpClass(cls):
        cls.server = subprocess.Popen(
            [cls.API_SERVER_PATH] + cls.API_SERVER_ARGS)
        hconn = httplib.HTTPConnection(cls.API_SERVER_ADDR,
                                       cls.API_SERVER_PORT)
        starttm = time.time() * 1000
        exc = None
        while (hconn.sock is None and
               (time.time() * 1000 - starttm) < cls.SERVER_STARTUP_WAIT_MS):
            time.sleep(0.1)
            try:
                hconn.connect()
            except socket.error, e:
                exc = e
        if hconn.sock is None:
            raise exc

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        starttm = time.time() * 1000
        while (cls.server.poll() is None and
               (time.time() * 1000 - starttm) < cls.SERVER_SHUTDOWN_WAIT_MS):
            time.sleep(0.01)
        if cls.server.poll() is None:
            cls.server.kill()

    def setUp(self):
        self.hconn = httplib.HTTPConnection(self.API_SERVER_ADDR,
                                            self.API_SERVER_PORT)
        self.hconn.connect()

    def tearDown(self):
        self.hconn.close()

    def check_response(self, response, description, status=httplib.OK,
                       content_type='text/plain'):
        body = response.read()
        self.assertTrue(response.status == status,
                        '%s response status == %s' % (description, status))

        if content_type is not None:
            if ';' in content_type:
                self.assertTrue(
                    response.getheader('content-type') == content_type,
                    "'%s response Content-Type (with params)  is '%s'"
                    % (description, content_type))
            else:
                ct_start = response.getheader('content-type').split(';', 1)[0]
                self.assertTrue(ct_start == content_type,
                                "'%s response Content-Type (no params) is '%s'"
                                % (description, content_type))
        return body

    def check_json_response(self, response, description, status=httplib.OK):
        raw_body = self.check_response(
            response, description, status, 'application/json')
        body = json.loads(raw_body)
        return body


class TestTablesApi(AbstractApiTest):
    API_SERVER_PATH = os.path.join(SRC_PATH, 'server', 'server.py')
    STATIC_TABLES = ['ad-groups']

    def test_tables_get(self):
        self.hconn.request('GET', '/tables')
        r = self.hconn.getresponse()
        body = self.check_json_response(r, 'List tables (empty)')
        self.assertIsInstance(body, list, 'List tables (empty) returns a list')
        self.assertTrue(len(body) == len(self.STATIC_TABLES),
                        'List tables (empty) contains default tables only')

    def test_table_create(self):
        try:
            ids = []
            for table in ['table1']:
                self.hconn.request('POST', '/tables', '{"%s": "foo"}' % table)
                r = self.hconn.getresponse()
                body = self.check_json_response(r, 'Create table',
                                                status=httplib.CREATED)
                self.assertIsInstance(body, dict,
                                      'Create table returns a dict')
                self.assertIsNotNone(body['table1'])
                self.assertIsNotNone(body['id'])
                ids.append(body['id'])

            self.hconn.request('GET', '/tables')
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'List tables')
            self.assertIsInstance(body, list,
                                  'List tables returns a list')
            self.assertTrue(
                len(body) == 1 + len(self.STATIC_TABLES),
                'List contains proper number of results')
        finally:
            self.hconn.request('DELETE', '/tables/%s' % ids[0])
            r = self.hconn.getresponse()

    def test_create_named(self):
        id = None
        try:
            table = 'table1'
            self.hconn.request('PUT', '/tables/foo_id',
                               '{"%s": "foo"}' % table)
            r = self.hconn.getresponse()
            body = self.check_json_response(r,
                                            'Create named table',
                                            status=httplib.CREATED)
            id = body['id']
            self.assertIsInstance(body, dict, 'Create table returns a dict')
            self.assertTrue(body['id'] ==
                            'foo_id', 'Created table has specified ID')
        finally:
            self.hconn.request('DELETE', '/tables/%s' % id)
            r = self.hconn.getresponse()

    def test_read(self):
        id = None
        try:
            table = 'table1'
            self.hconn.request('POST', '/tables', '{"%s": "foo"}' % table)
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'Create named table',
                                            status=httplib.CREATED)
            id = body['id']
            self.hconn.request('GET', '/tables/%s' % id)
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'Read table')
            self.assertIsInstance(body, dict, 'Read table returns a dict')
            self.assertEqual(body['id'], id, 'Read expected table instance')
            self.assertTrue('table1' in body,
                            'Read expected table instance data')

        finally:
            self.hconn.request('DELETE', '/tables/%s' % id)
            r = self.hconn.getresponse()

    def test_read_invalid(self):
        self.hconn.request('GET', '/tables/%s' % uuid.uuid4())
        r = self.hconn.getresponse()
        self.check_json_response(r, 'Read missing table',
                                 status=httplib.NOT_FOUND)

    def test_replace(self):
        id = None
        try:
            table = 'table1'
            self.hconn.request('POST', '/tables', '{"%s": "foo"}' % table)
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'Create named table',
                                            status=httplib.CREATED)
            id = body['id']
            new = json.loads('{"id": "%s", "table1": "bar"}' % id)
            self.hconn.request('PUT', '/tables/%s' % id, json.dumps(new))
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'Replace table')
            self.assertEqual(body, new, 'Replaced table returns new data')
            self.hconn.request('GET', '/tables/%s' % id)
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'Read replaced table')
            self.assertEqual(body, new, 'GET replaced table returns new data')
        finally:
            self.hconn.request('DELETE', '/tables/%s' % id)
            r = self.hconn.getresponse()

    def test_update(self):
        id = None
        try:
            table = 'table1'
            self.hconn.request('POST', '/tables', '{"%s": "foo"}' % table)
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'Create named table',
                                            status=httplib.CREATED)
            id = body['id']
            self.hconn.request('GET', '/tables/%s' % id)
            r = self.hconn.getresponse()
            old_body = self.check_json_response(r, 'Read old table')
            new = json.loads('{"newkey": "baz"}')
            self.hconn.request('PATCH', '/tables/%s' % id, json.dumps(new))
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'Update table')
            expected = old_body.copy()
            expected.update(new)
            self.assertEqual(body, expected, 'Updated table returns new data')
            self.hconn.request('GET', '/tables/%s' % id)
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'Read updated table')
            self.assertEqual(body, expected,
                             'GET replaced table returns new data')
        finally:
            self.hconn.request('DELETE', '/tables/%s' % id)
            r = self.hconn.getresponse()

    def test_delete(self):
        id = None
        try:
            table = 'table1'
            self.hconn.request('POST', '/tables', '{"%s": "foo"}' % table)
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'Create named table',
                                            status=httplib.CREATED)
            id = body['id']
            self.hconn.request('DELETE', '/tables/%s' % id)
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'Delete table')

            self.hconn.request('DELETE', '/tables/%s' % id)
            r = self.hconn.getresponse()
            body = self.check_json_response(r, 'Delete missing table',
                                            status=httplib.NOT_FOUND)
        finally:
            self.hconn.request('DELETE', '/tables/%s' % id)
            r = self.hconn.getresponse()


class TestPolicyApi(AbstractApiTest):
    API_SERVER_PATH = os.path.join(SRC_PATH, 'server', 'server.py')

    def test_policy(self):
        """Test table list API method."""
        # POST
        self.hconn.request('POST', '/policy')
        r = self.hconn.getresponse()
        body = self.check_response(r, 'POST policy',
                                   status=httplib.NOT_IMPLEMENTED,
                                   content_type=None)

        empty_policy = {'rules': []}
        # Get (empty)
        self.hconn.request('GET', '/policy')
        r = self.hconn.getresponse()
        body = self.check_json_response(r, 'Get policy (empty)')
        self.assertEqual(body, empty_policy,
                         'Get policy (empty) returns empty ruleset')

        # Update
        fake_policy = {'rules': ["foo", "bar"]}
        self.hconn.request('PUT', '/policy', json.dumps(fake_policy))
        r = self.hconn.getresponse()
        body = self.check_json_response(r, 'Update policy')
        self.assertEqual(body, fake_policy, 'Update policy returns new policy')

        # Get
        self.hconn.request('GET', '/policy')
        r = self.hconn.getresponse()
        body = self.check_json_response(r, 'Get policy')
        self.assertEqual(body, fake_policy, 'Get policy returns new policy')

        # Delete
        self.hconn.request('DELETE', '/policy')
        r = self.hconn.getresponse()
        body = self.check_response(r, 'DELETE policy',
                                   status=httplib.NOT_IMPLEMENTED,
                                   content_type=None)


if __name__ == '__main__':
    unittest.main(verbosity=2)
