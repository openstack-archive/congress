# Copyright 2015 OpenStack Foundation
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

import os
import socket
import subprocess
import tempfile

from oslo_log import log as logging
from tempest.common import credentials_factory as credentials
from tempest import config
from tempest.lib import exceptions
from tempest import manager as tempestmanager
from tempest import test
from urllib3.exceptions import MaxRetryError

from congress_tempest_tests.services.policy import policy_client
from congress_tempest_tests.tests.scenario import helper
from congress_tempest_tests.tests.scenario import manager_congress

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestHA(manager_congress.ScenarioPolicyBase):

    def setUp(self):
        super(TestHA, self).setUp()
        self.keypairs = {}
        self.servers = []
        self.replicas = {}
        self.services_client = self.admin_manager.identity_services_client
        self.endpoints_client = self.admin_manager.endpoints_client

    def _prepare_replica(self, port_num):
        replica_url = "http://127.0.0.1:%d" % port_num
        resp = self.services_client.create_service(
            'congressha',
            CONF.congressha.replica_type,
            description='policy ha service')
        self.replica_service_id = resp['OS-KSADM:service']['id']
        resp = self.endpoints_client.create_endpoint(
            self.replica_service_id,
            CONF.identity.region,
            publicurl=replica_url,
            adminurl=replica_url,
            internalurl=replica_url)
        self.replica_endpoint_id = resp['endpoint']['id']

    def _cleanup_replica(self):
        self.endpoints_client.delete_endpoint(self.replica_endpoint_id)
        self.services_client.delete_service(self.replica_service_id)

    def start_replica(self, port_num):
        self._prepare_replica(port_num)
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.conf',
                                        prefix='congress%d-' % port_num,
                                        dir='/tmp', delete=False)
        conf_file = f.name
        template = open('/etc/congress/congress.conf')
        conf = template.read()

        # Add 'bind_port' and 'datasource_sync_period' to conf file.
        index = conf.find('[DEFAULT]') + len('[DEFAULT]\n')
        conf = (conf[:index] + 'bind_port = %d\n' % port_num +
                'datasource_sync_period = 5\n' + conf[index:])
        sindex = conf.find('signing_dir')
        conf = conf[:sindex] + '#' + conf[sindex:]

        f.write(conf)
        f.close()

        args = ['/usr/bin/python',
                'bin/congress-server',
                '--config-file',
                conf_file]
        out = tempfile.NamedTemporaryFile(mode='w', suffix='.out',
                                          prefix='congress%d-' % port_num,
                                          dir='/tmp', delete=False)
        err = tempfile.NamedTemporaryFile(mode='w', suffix='.err',
                                          prefix='congress%d-' % port_num,
                                          dir='/tmp', delete=False)
        p = subprocess.Popen(args, stdout=out, stderr=err,
                             cwd=helper.root_path())

        assert port_num not in self.replicas
        self.replicas[port_num] = (p, conf_file)

    def stop_replica(self, port_num):
        proc, conf_file = self.replicas[port_num]
        # Using proc.terminate() will block at proc.wait(), no idea why yet
        proc.kill()
        proc.wait()
        os.unlink(conf_file)
        self.replicas[port_num] = (None, conf_file)
        self._cleanup_replica()

    def create_client(self, client_type):
        creds = credentials.get_configured_admin_credentials('identity_admin')
        auth_prov = tempestmanager.get_auth_provider(creds)

        return policy_client.PolicyClient(
            auth_prov, client_type,
            CONF.identity.region)

    def datasource_exists(self, client, datasource_id):
        try:
            LOG.debug("datasource_exists begin")
            body = client.list_datasource_status(datasource_id)
            LOG.debug("list_datasource_status: %s", str(body))
        except exceptions.NotFound as e:
            LOG.debug("not found")
            return False
        except exceptions.Unauthorized as e:
            LOG.debug("connection refused")
            return False
        except socket.error as e:
            LOG.debug("Replica server not ready")
            return False
        except MaxRetryError as e:
            LOG.debug("Replica server not ready")
            return False
        except Exception as e:
            raise e
        return True

    def datasource_missing(self, client, datasource_id):
        try:
            LOG.debug("datasource_missing begin")
            body = client.list_datasource_status(datasource_id)
            LOG.debug("list_datasource_status: %s", str(body))
        except exceptions.NotFound as e:
            LOG.debug("not found")
            return True
        except exceptions.Unauthorized as e:
            LOG.debug("connection refused")
            return False
        except socket.error as e:
            LOG.debug("Replica server not ready")
            return False
        except Exception as e:
            raise e
        return False

    def find_fake(self, client):
        datasources = client.list_datasources()
        for r in datasources['results']:
            if r['name'] == 'fake':
                LOG.debug('existing fake driver: %s', str(r['id']))
                return r['id']
        return None

    def create_fake(self, client):
        # Create fake datasource if it does not exist.  Returns the
        # fake datasource id.
        fake_id = self.find_fake(client)
        if fake_id:
            return fake_id

        item = {'id': None,
                'name': 'fake',
                'driver': 'fake_datasource',
                'config': '{"username":"fakeu", "tenant_name": "faket",' +
                          '"password": "fakep",' +
                          '"auth_url": "http://127.0.0.1:5000/v2"}',
                'description': 'bar',
                'enabled': True}
        ret = client.create_datasource(item)
        LOG.debug('created fake driver: %s', str(ret['id']))
        return ret['id']

    @test.attr(type='smoke')
    def test_datasource_db_sync_add(self):
        # Verify that a replica adds a datasource when a datasource
        # appears in the database.
        client1 = self.admin_manager.congress_client

        # delete fake if it exists.
        old_fake_id = self.find_fake(client1)
        if old_fake_id:
            client1.delete_datasource(old_fake_id)

        # Verify that primary server has no fake datasource
        if not test.call_until_true(
                func=lambda: self.datasource_missing(client1, old_fake_id),
                duration=60, sleep_for=1):
            raise exceptions.TimeoutException(
                "primary should not have fake, but does")

        need_to_delete_fake = False
        try:
            # Create a new fake datasource
            fake_id = self.create_fake(client1)
            need_to_delete_fake = True

            # Verify that primary server has fake datasource
            if not test.call_until_true(
                    func=lambda: self.datasource_exists(client1, fake_id),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException(
                    "primary should have fake, but does not")

            # start replica
            self.start_replica(CONF.congressha.replica_port)

            # Create session for second server.
            client2 = self.create_client(CONF.congressha.replica_type)

            # Verify that second server has fake datasource
            if not test.call_until_true(
                    func=lambda: self.datasource_exists(client2, fake_id),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException(
                    "replica should have fake, but does not")

            # Remove fake from primary server instance.
            LOG.debug("removing fake datasource %s", str(fake_id))
            client1.delete_datasource(fake_id)
            need_to_delete_fake = False

            # Confirm that fake is gone from primary server instance.
            if not test.call_until_true(
                    func=lambda: self.datasource_missing(client1, fake_id),
                    duration=60, sleep_for=1):
                self.stop_replica(CONF.congressha.replica_port)
                raise exceptions.TimeoutException(
                    "primary instance still has fake")
            LOG.debug("removed fake datasource from primary instance")

            # Confirm that second service instance removes fake.
            if not test.call_until_true(
                    func=lambda: self.datasource_missing(client2, fake_id),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException(
                    "replica should remove fake, but still has it")

        finally:
            self.stop_replica(CONF.congressha.replica_port)
            if need_to_delete_fake:
                self.admin_manager.congress_client.delete_datasource(fake_id)

    @test.attr(type='smoke')
    def test_datasource_db_sync_remove(self):
        # Verify that a replica removes a datasource when a datasource
        # disappears from the database.
        client1 = self.admin_manager.congress_client
        fake_id = self.create_fake(client1)
        need_to_delete_fake = True
        try:
            self.start_replica(CONF.congressha.replica_port)

            # Verify that primary server has fake datasource
            if not test.call_until_true(
                    func=lambda: self.datasource_exists(client1, fake_id),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException(
                    "primary should have fake, but does not")

            # Create session for second server.
            client2 = self.create_client(CONF.congressha.replica_type)

            # Verify that second server has fake datasource
            if not test.call_until_true(
                    func=lambda: self.datasource_exists(client2, fake_id),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException(
                    "replica should have fake, but does not")

            # Remove fake from primary server instance.
            LOG.debug("removing fake datasource %s", str(fake_id))
            client1.delete_datasource(fake_id)
            need_to_delete_fake = False

            # Confirm that fake is gone from primary server instance.
            if not test.call_until_true(
                    func=lambda: self.datasource_missing(client1, fake_id),
                    duration=60, sleep_for=1):
                self.stop_replica(CONF.congressha.replica_port)
                raise exceptions.TimeoutException(
                    "primary instance still has fake")
            LOG.debug("removed fake datasource from primary instance")

            # Confirm that second service instance removes fake.
            if not test.call_until_true(
                    func=lambda: self.datasource_missing(client2, fake_id),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException(
                    "replica should remove fake, but still has it")

        finally:
            self.stop_replica(CONF.congressha.replica_port)
            if need_to_delete_fake:
                self.admin_manager.congress_client.delete_datasource(fake_id)
