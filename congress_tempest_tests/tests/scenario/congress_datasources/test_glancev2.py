# Copyright 2014 OpenStack Foundation
# All Rights Reserved.
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
from oslo_log import log as logging
from tempest import clients  # noqa
from tempest import config  # noqa
from tempest import test  # noqa
from tempest_lib import exceptions

from congress_tempest_tests.tests.scenario import manager_congress  # noqa

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestGlanceV2Driver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def skip_checks(cls):
        super(TestGlanceV2Driver, cls).skip_checks()
        if not (CONF.network.tenant_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    def setUp(cls):
        super(TestGlanceV2Driver, cls).setUp()
        cls.os = clients.Manager(cls.admin_manager.auth_provider.credentials)
        cls.glancev2 = cls.os.image_client_v2
        cls.datasource_id = manager_congress.get_datasource_id(
            cls.admin_manager.congress_client, 'glancev2')

    @test.attr(type='smoke')
    @test.services('image')
    def test_glancev2_images_table(self):
        image_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'images')['columns'])
        image_id_col = next(i for i, c in enumerate(image_schema)
                            if c['name'] == 'id')

        def _check_data_table_glancev2_images():
            # Fetch data from glance each time, because this test may start
            # before glance has all the users.
            images = self.glancev2.list_images()['images']
            image_map = {}
            for image in images:
                image_map[image['id']] = image

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'images'))
            for row in results['results']:
                try:
                    image_row = image_map[row['data'][image_id_col]]
                except KeyError:
                    return False
                for index in range(len(image_schema)):
                    # glancev2 doesn't return kernel_id/ramdisk_id if
                    # it isn't present...
                    if ((image_schema[index]['name'] == 'kernel_id' and
                            'kernel_id' not in row['data']) or
                        (image_schema[index]['name'] == 'ramdisk_id' and
                         'ramdisk_id' not in row['data'])):
                        continue

                    # FIXME(arosen): congress-server should retain the type
                    # but doesn't today.
                    if (str(row['data'][index]) !=
                            str(image_row[image_schema[index]['name']])):
                        return False
            return True

        if not test.call_until_true(func=_check_data_table_glancev2_images,
                                    duration=100, sleep_for=4):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @test.attr(type='smoke')
    @test.services('image')
    def test_glancev2_tags_table(self):
        def _check_data_table_glance_images():
            # Fetch data from glance each time, because this test may start
            # before glance has all the users.
            images = self.glancev2.list_images()['images']
            image_tag_map = {}
            for image in images:
                image_tag_map[image['id']] = image['tags']

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'tags'))
            for row in results['results']:
                image_id, tag = row['data'][0], row['data'][1]
                glance_image_tags = image_tag_map.get(image_id)
                if not glance_image_tags:
                    # congress had image that glance doesn't know about.
                    return False
                if tag not in glance_image_tags:
                    # congress had a tag that wasn't on the image.
                    return False
            return True

        if not test.call_until_true(func=_check_data_table_glance_images,
                                    duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")
