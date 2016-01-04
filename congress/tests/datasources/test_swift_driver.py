# Copyright (c) 2014 Montavista Software, LLC.
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

import mock

from congress.datasources import swift_driver
from congress.tests import base
from congress.tests import helper


class TestSwiftDriver(base.TestCase):

    def setUp(self):
        super(TestSwiftDriver, self).setUp()
        self.swift_client = mock.MagicMock()

        args = helper.datasource_openstack_args()
        self.driver = swift_driver.SwiftDriver(name='testswift', args=args)

    def test_list_containers(self):
        containers_data = [{'count': '1',
                            'bytes': '1048',
                            'name': 'container1'},
                           {'count': '2',
                            'bytes': '2086',
                            'name': 'container2'}]

        self.driver._translate_containers(containers_data)
        container_list = list(self.driver.state[self.driver.CONTAINERS])
        self.assertIsNotNone(container_list)
        self.assertEqual(2, len(container_list))

        if container_list[0][2] == 'container1':
            self.assertEqual(('1', '1048', 'container1'), container_list[0])
            self.assertEqual(('2', '2086', 'container2'), container_list[1])
        if container_list[1][2] == 'container1':
            self.assertEqual(('1', '1048', 'container1'), container_list[1])
            self.assertEqual(('2', '2086', 'container2'), container_list[0])

    def test_list_objects(self):
        objects_data = [{'bytes': '2200',
                         'last_modified': '2014-11-06T05:40:34.052100',
                         'hash': '9204776814ca62c92c7996de725ecc6b',
                         'name': 'file-1',
                         'content_type': 'application/octet-stream',
                         'container_name': 'container1'},
                        {'bytes': '2350',
                         'last_modified': '2014-11-06T05:39:57.424800',
                         'hash': 'c2b86044dd50a29d60c0e92e23e3ceea',
                         'name': 'file-2',
                         'content_type': 'application/octet-stream',
                         'container_name': 'container2'}]

        self.driver._translate_objects(objects_data)
        object_list = list(self.driver.state[self.driver.OBJECTS])
        self.assertIsNotNone(object_list)
        self.assertEqual(2, len(object_list))

        if object_list[0][5] == 'container1':
            self.assertEqual(('2200', '2014-11-06T05:40:34.052100',
                              '9204776814ca62c92c7996de725ecc6b', 'file-1',
                              'application/octet-stream',
                              'container1'), object_list[0])

            self.assertEqual(('2350', '2014-11-06T05:39:57.424800',
                              'c2b86044dd50a29d60c0e92e23e3ceea', 'file-2',
                              'application/octet-stream',
                              'container2'), object_list[1])

        if object_list[1][5] == 'container1':
            self.assertEqual(('2200', '2014-11-06T05:40:34.052100',
                              '9204776814ca62c92c7996de725ecc6b', 'file-1',
                              'application/octet-stream',
                              'container1'), object_list[1])

            self.assertEqual(('2350', '2014-11-06T05:39:57.424800',
                              'c2b86044dd50a29d60c0e92e23e3ceea', 'file-2',
                              'application/octet-stream',
                              'container2'), object_list[0])

    def test_execute(self):
        class SwiftClient(object):
            def __init__(self):
                self.testkey = None

            def updateObject(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        swift_client = SwiftClient()
        self.driver.swift_service = swift_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('updateObject', api_args)

        self.assertEqual(expected_ans, swift_client.testkey)
