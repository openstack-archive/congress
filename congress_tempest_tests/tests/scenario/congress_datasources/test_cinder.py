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
from tempest import clients
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions
from tempest import test

from congress_tempest_tests.tests.scenario import manager_congress


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestCinderDriver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def skip_checks(cls):
        super(TestCinderDriver, cls).skip_checks()
        if not (CONF.network.project_networks_reachable or
                CONF.network.public_network_id):
            msg = ('Either project_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    def setUp(cls):
        super(TestCinderDriver, cls).setUp()
        cls.os = clients.Manager(cls.admin_manager.auth_provider.credentials)
        cls.cinder = cls.os.volumes_v2_client
        cls.datasource_id = manager_congress.get_datasource_id(
            cls.admin_manager.congress_client, 'cinder')
        res = cls.cinder.create_volume(size=1, description=None, name='v0',
                                       consistencygroup_id=None, metadata={})
        LOG.debug('result of creating new volume: %s', res)

    @test.attr(type='smoke')
    def test_cinder_volumes_table(self):
        volume_schema = (
            self.admin_manager.congress_client.show_datasource_table_schema(
                self.datasource_id, 'volumes')['columns'])
        volume_id_col = next(i for i, c in enumerate(volume_schema)
                             if c['name'] == 'id')

        def _check_data_table_cinder_volumes():
            # Fetch data from cinder each time, because this test may start
            # before cinder has all the users.
            volumes = self.cinder.list_volumes()['volumes']
            LOG.debug('cinder volume list: %s', volumes)
            volumes_map = {}
            for volume in volumes:
                volumes_map[volume['id']] = volume

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'volumes'))
            LOG.debug('congress cinder volumes table: %s', results)
            # check that congress and cinder return the same volume IDs
            rows_volume_id_set = set()
            for row in results['results']:
                rows_volume_id_set.add(row['data'][volume_id_col])
            if rows_volume_id_set != frozenset(volumes_map.keys()):
                LOG.debug('volumes IDs mismatch')
                return False
            # FIXME(ekcs): the following code is broken because 'user_id'
            # and 'description' fields do not appear in results provided by
            # [tempest].os.volumes_client.list_volumes().
            # Detailed checking disabled for now. Re-enable when fixed.
            # It appears the code was written for v1 volumes client but never
            # worked. The problem was not evident because the list of volumes
            # was empty.
            # Additional adaptation is needed for v2 volumes client.
            # for row in results['results']:
            #     try:
            #         volume_row = volumes_map[row['data'][volume_id_col]]
            #     except KeyError:
            #         return False
            #     for index in range(len(volume_schema)):
            #         if (str(row['data'][index]) !=
            #                 str(volume_row[volume_schema[index]['name']])):
            #             return False
            return True

        if not test_utils.call_until_true(
                func=_check_data_table_cinder_volumes,
                duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")

    @test.attr(type='smoke')
    def test_update_no_error(self):
        if not test_utils.call_until_true(
                func=lambda: self.check_datasource_no_error('cinder'),
                duration=30, sleep_for=5):
            raise exceptions.TimeoutException('Datasource could not poll '
                                              'without error.')
