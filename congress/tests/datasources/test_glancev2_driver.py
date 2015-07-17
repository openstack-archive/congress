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

from congress.datasources import glancev2_driver
from congress.tests import base
from congress.tests import helper


class TestGlanceV2Driver(base.TestCase):

    def setUp(self):
        super(TestGlanceV2Driver, self).setUp()
        self.keystone_client_p = mock.patch(
            "keystoneclient.v2_0.client.Client")
        self.keystone_client_p.start()
        self.glance_client_p = mock.patch("glanceclient.v2.client.Client")
        self.glance_client_p.start()

        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        args['client'] = mock.MagicMock()
        self.driver = glancev2_driver.GlanceV2Driver(args=args)

        self.mock_images = {'images': [
            {u'checksum': u'9e486c3bf76219a6a37add392e425b36',
             u'container_format': u'bare',
             u'created_at': u'2014-10-01T20:28:08Z',
             u'disk_format': u'qcow2',
             u'file': u'/v2/images/c42736e7-8b09-4906-abd2-d6dc8673c297/file',
             u'id': u'c42736e7-8b09-4906-abd2-d6dc8673c297',
             u'min_disk': 0,
             u'min_ram': 0,
             u'name': u'Fedora-x86_64-20-20140618-sda',
             u'owner': u'4dfdcf14a20940799d89c7a5e7345978',
             u'protected': False,
             u'schema': u'/v2/schemas/image',
             u'size': 209649664,
             u'status': u'active',
             u'tags': ['type=xen2', 'type=xen'],
             u'updated_at': u'2014-10-01T20:28:09Z',
             u'visibility': u'public'},
            {u'checksum': u'4eada48c2843d2a262c814ddc92ecf2c',
             u'container_format': u'ami',
             u'created_at': u'2014-10-01T20:28:06Z',
             u'disk_format': u'ami',
             u'file': u'/v2/images/6934941f-3eef-43f7-9198-9b3c188e4aab/file',
             u'id': u'6934941f-3eef-43f7-9198-9b3c188e4aab',
             u'kernel_id': u'15ed89b8-588d-47ad-8ee0-207ed8010569',
             u'min_disk': 0,
             u'min_ram': 0,
             u'name': u'cirros-0.3.2-x86_64-uec',
             u'owner': u'4dfdcf14a20940799d89c7a5e7345978',
             u'protected': False,
             u'ramdisk_id': u'c244d5c7-1c83-414c-a90d-af7cea1dd3b5',
             u'schema': u'/v2/schemas/image',
             u'size': 25165824,
             u'status': u'active',
             u'tags': [],
             u'updated_at': u'2014-10-01T20:28:07Z',
             u'visibility': u'public'}]}

    def test_update_from_datasource(self):
        with mock.patch.object(self.driver.glance.images, "list") as img_list:
            img_list.return_value = self.mock_images['images']
            self.driver.update_from_datasource()
        expected = {'images': set([
            (u'6934941f-3eef-43f7-9198-9b3c188e4aab',
             u'active',
             u'cirros-0.3.2-x86_64-uec',
             u'ami',
             u'2014-10-01T20:28:06Z',
             u'2014-10-01T20:28:07Z',
             u'ami',
             u'4dfdcf14a20940799d89c7a5e7345978',
             'False',
             0,
             0,
             u'4eada48c2843d2a262c814ddc92ecf2c',
             25165824,
             u'/v2/images/6934941f-3eef-43f7-9198-9b3c188e4aab/file',
             u'15ed89b8-588d-47ad-8ee0-207ed8010569',
             u'c244d5c7-1c83-414c-a90d-af7cea1dd3b5',
             u'/v2/schemas/image',
             u'public'),
            (u'c42736e7-8b09-4906-abd2-d6dc8673c297',
             u'active',
             u'Fedora-x86_64-20-20140618-sda',
             u'bare',
             u'2014-10-01T20:28:08Z',
             u'2014-10-01T20:28:09Z',
             u'qcow2',
             u'4dfdcf14a20940799d89c7a5e7345978',
             'False',
             0,
             0,
             u'9e486c3bf76219a6a37add392e425b36',
             209649664,
             u'/v2/images/c42736e7-8b09-4906-abd2-d6dc8673c297/file',
             'None',
             'None',
             u'/v2/schemas/image',
             u'public')]),
            'tags': set([
                (u'c42736e7-8b09-4906-abd2-d6dc8673c297', 'type=xen'),
                (u'c42736e7-8b09-4906-abd2-d6dc8673c297', 'type=xen2')])}
        self.assertEqual(self.driver.state, expected)

    def test_execute(self):
        class GlanceClient(object):
            def __init__(self):
                self.testkey = None

            def createSnapshot(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        glance_client = GlanceClient()
        self.driver.glance = glance_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('createSnapshot', api_args)

        self.assertEqual(glance_client.testkey, expected_ans)
