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

from congress.datasources import cinder_driver
from congress.tests import base
from congress.tests.datasources import util
from congress.tests import helper

ResponseObj = util.ResponseObj


class TestCinderDriver(base.TestCase):

    def setUp(self):
        super(TestCinderDriver, self).setUp()
        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        self.driver = cinder_driver.CinderDriver(name='testcinder', args=args)

    def test_list_volumes(self):
        volumes_data = [
            ResponseObj({'id': '8bf2eddb-0e1a-46f9-a49a-853f8016f476',
                         'size': '1',
                         'user_id': 'b75055d5f0834d99ae874f085cf95272',
                         'status': 'available',
                         'description': 'foo',
                         'name': 'bar',
                         'bootable': 'false',
                         'created_at': '2014-10-09T12:16:23.000000',
                         'volume_type': 'lvmdriver-1',
                         'encrypted': False,
                         'availability_zone': 'nova1',
                         'replication_status': 'r_status1',
                         'multiattach': True,
                         'snapshot_id': '3b890e8a-7881-4430-b087-9e9e642e5e0d',
                         'source_volid':
                             'b4c36f7a-ac1b-41a6-9e83-03a6c1149669',
                         'consistencygroup_id':
                             '7aa9787f-285d-4d22-8211-e20af07f1044',
                         'migration_status': 'm_status1',
                         'attachments':
                             [{'server_id':
                                   'a4fda93b-06e0-4743-8117-bc8bcecd651b',
                               'attachment_id':
                                   'ab4db356-253d-4fab-bfa0-e3626c0b8405',
                               'host_name': None,
                               'volume_id':
                                   'aedbc2f4-1507-44f8-ac0d-eed1d2608d38',
                               'device': '/dev/vda',
                               'id': 'aedbc2f4-1507-44f8-ac0d-eed1d2608d38'},
                              {'server_id':
                                   'b4fda93b-06e0-4743-8117-bc8bcecd651b',
                               'attachment_id':
                                   'bb4db356-253d-4fab-bfa0-e3626c0b8405',
                               'volume_id':
                                   'bedbc2f4-1507-44f8-ac0d-eed1d2608d38',
                               'device': '/dev/vdb',
                               'id': 'bedbc2f4-1507-44f8-ac0d-eed1d2608d38'}
                              ],
                         'extra_attribute': ['extra']}),
            ResponseObj({'id': '7cd8f73d-3243-49c9-a25b-a77ceb6ad1fa',
                         'size': '1',
                         'user_id': '6e14edb203a84aa6a5a6a90872cbae79',
                         'status': 'creating',
                         'description': 'wonder',
                         'name': 'alice',
                         'bootable': 'true',
                         'created_at': '2014-10-12T06:54:55.000000',
                         'volume_type': None,
                         'encrypted': True,
                         'availability_zone': 'nova2',
                         'replication_status': 'r_status2',
                         'multiattach': False,
                         'snapshot_id': '658b5663-9e83-406b-8b81-4a50cafaa2d6',
                         'source_volid':
                             'bf789ec1-b4a2-4ea0-94f4-4a6ebcc00ad8',
                         'consistencygroup_id':
                             '960ec54c-c2a4-4e4c-8192-8b1d9eb65fae',
                         'migration_status': 'm_status2',
                         'attachments': [],
                         'extra_attribute': ['extra']})]

        volume_list = self.driver._translate_volumes(volumes_data)
        self.assertIsNotNone(volume_list)
        self.assertEqual(4, len(volume_list))

        self.assertEqual({('8bf2eddb-0e1a-46f9-a49a-853f8016f476', '1',
                           'b75055d5f0834d99ae874f085cf95272', 'available',
                           'foo', 'bar', 'false', '2014-10-09T12:16:23.000000',
                           'lvmdriver-1', False, 'nova1', 'r_status1',
                           True, '3b890e8a-7881-4430-b087-9e9e642e5e0d',
                           'b4c36f7a-ac1b-41a6-9e83-03a6c1149669',
                           '7aa9787f-285d-4d22-8211-e20af07f1044',
                           'm_status1'),
                          ('7cd8f73d-3243-49c9-a25b-a77ceb6ad1fa', '1',
                           '6e14edb203a84aa6a5a6a90872cbae79', 'creating',
                           'wonder', 'alice', 'true',
                           '2014-10-12T06:54:55.000000', None,
                           True, 'nova2', 'r_status2', False,
                           '658b5663-9e83-406b-8b81-4a50cafaa2d6',
                           'bf789ec1-b4a2-4ea0-94f4-4a6ebcc00ad8',
                           '960ec54c-c2a4-4e4c-8192-8b1d9eb65fae',
                           'm_status2')},
                         self.driver.state['volumes'])

        self.assertEqual({('8bf2eddb-0e1a-46f9-a49a-853f8016f476',
                           'a4fda93b-06e0-4743-8117-bc8bcecd651b',
                           'ab4db356-253d-4fab-bfa0-e3626c0b8405',
                           None,
                           '/dev/vda'),
                          ('8bf2eddb-0e1a-46f9-a49a-853f8016f476',
                           'b4fda93b-06e0-4743-8117-bc8bcecd651b',
                           'bb4db356-253d-4fab-bfa0-e3626c0b8405',
                           None,
                           '/dev/vdb')},
                         self.driver.state['attachments'])

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

        self.assertEqual({('7cd8f73d-3243-49c9-a25b-a77ceb6ad1fa', '1',
                           'available', 'b75055d5f0834d99ae874f085cf95272',
                           'foo', '2014-10-12T06:54:55.000000'),
                          ('7cd8f73d-3243-49c9-a25b-a77ceb6ad1fa', '1',
                           'creating', '6e14edb203a84aa6a5a6a90872cbae79',
                           'baar', '2014-10-12T06:54:55.000000')},
                         self.driver.state['snapshots'])

    def test_list_services(self):
        services_data = [
            ResponseObj({'status': 'enabled',
                         'binary': 'cinder-scheduler',
                         'zone': 'nova',
                         'state': 'up',
                         'updated_at': '2014-10-10T06:25:08.000000',
                         'host': 'openstack@lvmdriver-1',
                         'disabled_reason': None}),
            ResponseObj({'status': 'enabled',
                         'binary': 'cinder-scheduler',
                         'zone': 'nova',
                         'state': 'up',
                         'updated_at': '2014-10-10T06:25:08.000000',
                         'host': 'openstack',
                         'disabled_reason': None})]

        service_list = self.driver._translate_services(services_data)
        self.assertIsNotNone(service_list)
        self.assertEqual(2, len(service_list))

        self.assertEqual({('enabled', 'cinder-scheduler', 'nova',
                           'up', '2014-10-10T06:25:08.000000',
                           'openstack@lvmdriver-1', None),
                          ('enabled', 'cinder-scheduler', 'nova',
                           'up', '2014-10-10T06:25:08.000000',
                           'openstack', None)},
                         self.driver.state['services'])

    def test_execute(self):
        class CinderClient(object):
            def __init__(self):
                self.testkey = None

            def createVolume(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        cinder_client = CinderClient()
        self.driver.cinder_client = cinder_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('createVolume', api_args)

        self.assertEqual(expected_ans, cinder_client.testkey)
