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
import mock

from heatclient.v1 import software_deployments as deployments
from heatclient.v1 import stacks

from congress.datasources import heatv1_driver
from congress.tests import base
from congress.tests import helper


class TestHeatV1Driver(base.TestCase):

    def setUp(self):
        super(TestHeatV1Driver, self).setUp()
        self.keystone_client_p = mock.patch(
            "keystoneclient.v2_0.client.Client")
        self.keystone_client_p.start()
        self.heat_client_p = mock.patch("heatclient.v1.client.Client")
        self.heat_client_p.start()

        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        args['client'] = mock.MagicMock()
        self.driver = heatv1_driver.HeatV1Driver(args=args)

        self.mock_stacks = {'stacks': [
            {u'id': u'da4e63e2-f79b-4cbb-bee8-33b2a9bd1ac8',
             u'stack_name': u'my-stack',
             u'description':
             u'Simple template to deploy a single compute instance ',
             u'creation_time': u'2015-04-25T21:20:35Z',
             u'updated_time': u'None',
             u'stack_status': u'CREATE_COMPLETE',
             u'stack_status_reason': u'Stack CREATE completed successfully',
             u'stack_owner': u'demo',
             u'parent': u'None',
             u'links': [
                    {u'href': u'http://192.168.123.200:8004/v1',
                     u'rel': u'self'}]}]}

        self.mock_software_deployments = {'deployments': [
            {u'status': u'COMPLETE',
             u'server_id': u'ec14c864-096e-4e27-bb8a-2c2b4dc6f3f5',
             u'config_id': u'8da95794-2ad9-4979-8ae5-739ce314c5cd',
             u'action': u'CREATE',
             u'status_reason': u'Outputs received',
             u'id': u'ef422fa5-719a-419e-a10c-72e3a367b0b8',
             u'output_values': {
                 u'deploy_stdout': u'Writing to /tmp/barmy\n',
                 u'deploy_stderr': u'+ echo Writing to /tmp/barmy\n',
                 u'deploy_status_code': u'0',
                 u'result': u'The file /tmp/barmy contains fu for server'}}]}

    def mock_value(self, mock_data, key, obj_class):
        data = mock_data[key]
        return [obj_class(self, res, loaded=True) for res in data if res]

    def test_update_from_datasource(self):
        dep = self.mock_software_deployments
        with base.nested(
                mock.patch.object(self.driver.heat.stacks,
                                  "list",
                                  return_value=self.mock_value(
                                      self.mock_stacks,
                                      "stacks",
                                      stacks.Stack)),
                mock.patch.object(self.driver.heat.software_deployments,
                                  "list",
                                  return_value=self.mock_value(
                                      dep,
                                      'deployments',
                                      deployments.SoftwareDeployment)),
                ) as (list, list):
                self.driver.update_from_datasource()
        expected = {
            'stacks': set([
                (u'da4e63e2-f79b-4cbb-bee8-33b2a9bd1ac8',
                 u'my-stack',
                 u'Simple template to deploy a single compute instance ',
                 u'2015-04-25T21:20:35Z',
                 u'None',
                 u'CREATE_COMPLETE',
                 u'Stack CREATE completed successfully',
                 u'demo',
                 u'None')]),
            'stacks_links': set([
                (u'da4e63e2-f79b-4cbb-bee8-33b2a9bd1ac8',
                 u'http://192.168.123.200:8004/v1',
                 u'self')]),
            'deployments': set([
                (u'COMPLETE',
                 u'ec14c864-096e-4e27-bb8a-2c2b4dc6f3f5',
                 u'8da95794-2ad9-4979-8ae5-739ce314c5cd',
                 u'CREATE',
                 u'Outputs received',
                 u'ef422fa5-719a-419e-a10c-72e3a367b0b8')]),
            'deployment_output_values': set([
                (u'ef422fa5-719a-419e-a10c-72e3a367b0b8',
                 u'Writing to /tmp/barmy\n',
                 u'+ echo Writing to /tmp/barmy\n',
                 u'0',
                 u'The file /tmp/barmy contains fu for server')])}
        self.assertEqual(expected, self.driver.state)

    def test_execute(self):
        class HeatClient(object):
            def __init__(self):
                self.testkey = None

            def abandanStack(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        heat_client = HeatClient()
        self.driver.heat = heat_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('abandanStack', api_args)

        self.assertEqual(expected_ans, heat_client.testkey)
