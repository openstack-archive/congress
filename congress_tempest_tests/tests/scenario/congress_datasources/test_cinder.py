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
from tempest_lib import exceptions

from tempest import clients  # noqa
from tempest import config  # noqa
from tempest import test  # noqa

from congress_tempest_tests.tests.scenario import manager_congress  # noqa


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestCinderDriver(manager_congress.ScenarioPolicyBase):

    @classmethod
    def skip_checks(cls):
        super(TestCinderDriver, cls).skip_checks()
        if not (CONF.network.tenant_networks_reachable or
                CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or'
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    def setUp(cls):
        super(TestCinderDriver, cls).setUp()
        cls.os = clients.Manager(cls.admin_manager.auth_provider.credentials)
        cls.cinder = cls.os.volumes_client
        cls.datasource_id = manager_congress.get_datasource_id(
            cls.admin_manager.congress_client, 'cinder')

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
            volumes_map = {}
            for volume in volumes:
                volumes_map[volume['id']] = volume

            results = (
                self.admin_manager.congress_client.list_datasource_rows(
                    self.datasource_id, 'volumes'))
            for row in results['results']:
                try:
                    volume_row = volumes_map[row['data'][volume_id_col]]
                except KeyError:
                    return False
                for index in range(len(volume_schema)):
                    if (str(row['data'][index]) !=
                            str(volume_row[volume_schema[index]['name']])):
                        return False
            return True

        if not test.call_until_true(func=_check_data_table_cinder_volumes,
                                    duration=100, sleep_for=5):
            raise exceptions.TimeoutException("Data did not converge in time "
                                              "or failure in server")
