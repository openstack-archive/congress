#!/usr/bin/env python
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
from congress.datasources.cinder_driver import CinderDriver
from congress.datasources.tests.unit.util import ResponseObj
from congress.tests import base
from congress.tests import helper


class TestCinderDriver(base.TestCase):

    def setUp(self):
        super(TestCinderDriver, self).setUp()
        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        self.driver = CinderDriver(name='testcinder', args=args)

    def test_list_volumes(self):
        volumes_data = [
            ResponseObj({'id': '8bf2eddb-0e1a-46f9-a49a-853f8016f476',
                         'size': '1',
                         'user_id': 'b75055d5f0834d99ae874f085cf95272',
                         'status': 'available',
                         'description': 'foo',
                         'name': 'bar',
                         'bootable': 'False',
                         'created_at': '2014-10-09T12:16:23.000000',
                         'volume_type': 'lvmdriver-1'}),
            ResponseObj({'id': '7cd8f73d-3243-49c9-a25b-a77ceb6ad1fa',
                         'size': '1',
                         'user_id': '6e14edb203a84aa6a5a6a90872cbae79',
                         'status': 'creating',
                         'description': 'wonder',
                         'name': 'alice',
                         'bootable': 'True',
                         'created_at': '2014-10-12T06:54:55.000000',
                         'volume_type': 'None'})]

        volume_list = self.driver._translate_volumes(volumes_data)
        self.assertIsNotNone(volume_list)
        self.assertEqual(2, len(volume_list))

        self.assertEqual(('8bf2eddb-0e1a-46f9-a49a-853f8016f476', '1',
                          'b75055d5f0834d99ae874f085cf95272', 'available',
                          'foo', 'bar', 'False', '2014-10-09T12:16:23.000000',
                          'lvmdriver-1'),
                         volume_list[0])

        self.assertEqual(('7cd8f73d-3243-49c9-a25b-a77ceb6ad1fa', '1',
                          '6e14edb203a84aa6a5a6a90872cbae79', 'creating',
                          'wonder', 'alice', 'True',
                          '2014-10-12T06:54:55.000000', 'None'),
                         volume_list[1])

    def test_list_snaphosts(self):
        snapshots_data = [
            ResponseObj({'status': 'available',
                         'created_at': '2014-10-12T06:54:55.000000',
                         'volume_id': 'b75055d5f0834d99ae874f085cf95272',
                         'size': '1',
                         'id': '7cd8f73d-3243-49c9-a25b-a77ceb6ad1fa',
                         'name': 'foo'}),
            ResponseObj({'status': 'creating',
                         'created_at': '2014-10-12T06:54:55.000000',
                         'volume_id': '6e14edb203a84aa6a5a6a90872cbae79',
                         'size': '1',
                         'id': '7cd8f73d-3243-49c9-a25b-a77ceb6ad1fa',
                         'name': 'baar'})]

        snapshot_list = self.driver._translate_snapshots(snapshots_data)
        self.assertIsNotNone(snapshot_list)
        self.assertEqual(2, len(snapshot_list))

        self.assertEqual(('available', '2014-10-12T06:54:55.000000',
                          'b75055d5f0834d99ae874f085cf95272', '1',
                          '7cd8f73d-3243-49c9-a25b-a77ceb6ad1fa', 'foo'),
                         snapshot_list[0])

        self.assertEqual(('creating', '2014-10-12T06:54:55.000000',
                          '6e14edb203a84aa6a5a6a90872cbae79', '1',
                          '7cd8f73d-3243-49c9-a25b-a77ceb6ad1fa', 'baar'),
                         snapshot_list[1])

    def test_list_services(self):
        services_data = [
            ResponseObj({'status': 'enabled',
                         'binary': 'cinder-scheduler',
                         'zone': 'nova',
                         'state': 'up',
                         'updated_at': '2014-10-10T06:25:08.000000',
                         'host': 'openstack@lvmdriver-1',
                         'disabled_reason': 'None'}),
            ResponseObj({'status': 'enabled',
                         'binary': 'cinder-scheduler',
                         'zone': 'nova',
                         'state': 'up',
                         'updated_at': '2014-10-10T06:25:08.000000',
                         'host': 'openstack',
                         'disabled_reason': 'None'})]

        service_list = self.driver._translate_services(services_data)
        self.assertIsNotNone(service_list)
        self.assertEqual(2, len(service_list))

        self.assertEqual(('enabled', 'cinder-scheduler', 'nova',
                          'up', '2014-10-10T06:25:08.000000',
                          'openstack@lvmdriver-1', 'None'),
                         service_list[0])

        self.assertEqual(('enabled', 'cinder-scheduler', 'nova',
                          'up', '2014-10-10T06:25:08.000000',
                          'openstack', 'None'),
                         service_list[1])
