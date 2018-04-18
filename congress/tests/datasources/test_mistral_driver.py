# Copyright (c) 2018 VMware, Inc. All rights reserved.
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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import mock
import sys

sys.modules['mistralclient.api.v2.client'] = mock.Mock()
sys.modules['mistralclient.api.v2'] = mock.Mock()

from congress.datasources import mistral_driver
from congress.tests import base
from congress.tests.datasources import util
from congress.tests import helper

ResponseObj = util.ResponseObj


class TestMistralDriver(base.TestCase):

    def setUp(self):
        super(TestMistralDriver, self).setUp()
        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        args['client'] = mock.MagicMock()
        self.driver = mistral_driver.MistralDriver(
            name='testmistral', args=args)

    def test_list_workflows(self):
        raw_data = [
            ResponseObj({u'created_at': u'2017-10-12 20:06:58',
                         u'definition':
                             u'---\nversion: \'2.0\'\n\nstd.create_instance:\n'
                             u'...',
                         u'id': u'31c429eb-c439-43ec-a633-45c4e8749261',
                         u'input': u'name, image_id, flavor_id, '
                                   u'ssh_username=None, ssh_password=None, '
                                   u'key_name=None, security_groups=None, '
                                   u'nics=None',
                         u'name': u'std.create_instance',
                         u'namespace': u'',
                         u'project_id': u'<default-project>',
                         u'scope': u'public',
                         u'tags': ['tag1', 'tag2'],
                         u'updated_at': None}),
            ResponseObj({u'created_at': u'2017-10-12 20:06:58',
                         u'definition':
                             u'---\nversion: "2.0"\n\nstd.delete_instance:\n'
                             u'...',
                         u'id': u'55f43e39-89aa-43e6-9eec-526b5aa932b9',
                         u'input': u'instance_id',
                         u'name': u'std.delete_instance',
                         u'namespace': u'',
                         u'project_id': u'<default-project>',
                         u'scope': u'public',
                         u'tags': [],
                         u'updated_at': None})]

        translated_data = self.driver._translate_workflows(raw_data)
        self.assertIsNotNone(translated_data)
        self.assertEqual(2, len(translated_data))

        self.assertEqual({
            (u'std.create_instance',
             u'31c429eb-c439-43ec-a633-45c4e8749261',
             u'public',
             u'name, image_id, flavor_id, ssh_username=None, ssh_password='
             u'None, key_name=None, security_groups=None, nics=None',
             u'',
             u'<default-project>',
             u'2017-10-12 20:06:58',
             None,
             u"---\nversion: '2.0'\n\nstd.create_instance:\n...",
             None),
            (u'std.delete_instance',
             u'55f43e39-89aa-43e6-9eec-526b5aa932b9',
             u'public',
             u'instance_id',
             u'',
             u'<default-project>',
             u'2017-10-12 20:06:58',
             None,
             u'---\nversion: "2.0"\n\nstd.delete_instance:\n...',
             None)},
            self.driver.state['workflows'])

    def test_list_actions(self):
        raw_data = [
            ResponseObj({
                u'created_at': u'2017-10-12 20:06:56',
                u'definition': None,
                u'description': u'Updates a load balancer health monitor.',
                u'id': u'f794925d-ed65-41d4-a68d-076412d6ce9d',
                u'input': u'health_monitor, action_region="", body=null',
                u'is_system': True,
                u'name': u'neutron.update_health_monitor',
                u'scope': u'public',
                u'tags': None,
                u'updated_at': None}),
            ResponseObj({
                u'created_at': u'2017-10-13 20:06:56',
                u'definition': u'action definition',
                u'description': u'Updates a load balancer health monitor.',
                u'id': u'a794925d-ed65-41d4-a68d-076412d6ce9d',
                u'input': u'health_monitor, action_region="", body=null',
                u'is_system': False,
                u'name': u'neutron.custom_action',
                u'scope': u'public',
                u'tags': ['tag1', 'tag2'],
                u'updated_at': u'2017-10-13 23:06:56'})]

        translated_data = self.driver._translate_actions(raw_data)
        self.assertIsNotNone(translated_data)
        self.assertEqual(2, len(translated_data))

        self.assertEqual({(u'a794925d-ed65-41d4-a68d-076412d6ce9d',
                           u'neutron.custom_action',
                           u'health_monitor, action_region="", body=null',
                           u'2017-10-13 20:06:56',
                           u'2017-10-13 23:06:56',
                           False,
                           u'action definition',
                           u'Updates a load balancer health monitor.',
                           u'public'),
                          (u'f794925d-ed65-41d4-a68d-076412d6ce9d',
                           u'neutron.update_health_monitor',
                           u'health_monitor, action_region="", body=null',
                           u'2017-10-12 20:06:56',
                           None,
                           True,
                           None,
                           u'Updates a load balancer health monitor.',
                           u'public')},
                         self.driver.state['actions'])

    def test_list_workflow_executions(self):
        raw_data = [
            ResponseObj({u'created_at': u'2017-12-19 22:56:50',
                         u'description': u'',
                         u'id': u'46bbba4b-8a2e-4281-be61-1e92ebfdd6b6',
                         u'input': u'{"instance_id": 1}',
                         u'params': u'{"namespace": "", "task_name": ""}',
                         u'state': u'ERROR',
                         u'state_info': u"Failure caused by error ...",
                         u'task_execution_id': None,
                         u'updated_at': u'2017-12-19 22:57:00',
                         u'workflow_id':
                             u'55f43e39-89aa-43e6-9eec-526b5aa932b9',
                         u'workflow_name': u'std.delete_instance',
                         u'workflow_namespace': u''})]

        translated_data = self.driver._translate_workflow_executions(raw_data)
        self.assertIsNotNone(translated_data)
        self.assertEqual(1, len(translated_data))

        self.assertEqual({(u'46bbba4b-8a2e-4281-be61-1e92ebfdd6b6',
                           u'std.delete_instance',
                           u'{"instance_id": 1}',
                           u'2017-12-19 22:56:50',
                           u'2017-12-19 22:57:00',
                           u'ERROR',
                           u'Failure caused by error ...',
                           u'',
                           u'55f43e39-89aa-43e6-9eec-526b5aa932b9',
                           u'',
                           u'{"namespace": "", "task_name": ""}')},
                         self.driver.state['workflow_executions'])

    def test_list_action_executions(self):
        raw_data = [
            ResponseObj({u'accepted': True,
                         u'created_at': u'2017-12-19 22:56:50',
                         u'description': u'',
                         u'id': u'5c377055-5590-479a-beec-3d4a47a2dfb6',
                         u'input': u'{"server": 1}',
                         u'name': u'nova.servers_delete',
                         u'state': u'ERROR',
                         u'state_info': None,
                         u'tags': None,
                         u'task_execution_id':
                             u'f40a0a20-958d-4948-b0c0-e1961649f2e2',
                         u'task_name': u'delete_vm',
                         u'updated_at': u'2017-12-19 22:56:50',
                         u'workflow_name': u'std.delete_instance',
                         u'workflow_namespace': u''})]

        translated_data = self.driver._translate_action_executions(raw_data)
        self.assertIsNotNone(translated_data)
        self.assertEqual(1, len(translated_data))

        self.assertEqual({(u'5c377055-5590-479a-beec-3d4a47a2dfb6',
                           u'nova.servers_delete',
                           None,
                           u'std.delete_instance',
                           u'f40a0a20-958d-4948-b0c0-e1961649f2e2',
                           u'delete_vm',
                           u'',
                           u'{"server": 1}',
                           u'2017-12-19 22:56:50',
                           u'2017-12-19 22:56:50',
                           True,
                           u'ERROR',
                           u'')},
                         self.driver.state['action_executions'])

    def test_execute(self):
        class MockClient(object):
            def __init__(self):
                self.testkey = None

            def mock_action(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        mock_client = MockClient()
        self.driver.mistral_client = mock_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('mock_action', api_args)

        self.assertEqual(expected_ans, mock_client.testkey)
