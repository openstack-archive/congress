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
from congressclient.v1 import client as congress_client
import keystoneclient
from tempest import config
from tempest import exceptions
from tempest.openstack.common import log as logging
from tempest.scenario import manager_congress
from tempest import test

import os
import subprocess
import tempfile

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestHA(manager_congress.ScenarioPolicyBase):

    def setUp(self):
        super(TestHA, self).setUp()
        self.keypairs = {}
        self.servers = []
        self.replicas = {}

    def start_replica(self, port_num):
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.conf',
                                        prefix='congress%d-' % port_num,
                                        dir='/tmp', delete=False)
        conf_file = f.name
        template = open('/etc/congress/congress.conf')
        conf = template.read()
        conf = conf.replace('# bind_port = 1789',
                            'bind_port = %d\n' % port_num)
        conf = conf.replace('# datasource_sync_period = 60',
                            'datasource_sync_period = 5')
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
                             cwd='/opt/stack/congress')

        assert port_num not in self.replicas
        self.replicas[port_num] = (p, conf_file)

    def stop_replica(self, port_num):
        proc, conf_file = self.replicas[port_num]
        proc.terminate()
        proc.wait()
        os.unlink(conf_file)
        self.replicas[port_num] = (None, conf_file)

    def create_client(self, port_num):
        creds = self.admin_credentials()
        auth = keystoneclient.auth.identity.v2.Password(
            auth_url=CONF.identity.uri,
            username=creds.username,
            password=creds.password,
            tenant_name=creds.tenant_name)
        session = keystoneclient.session.Session(auth=auth)
        return congress_client.Client(
            session=session,
            auth=None,
            endpoint_override='http://127.0.0.1:%d' % port_num,
            region_name=CONF.identity.region)

    def datasource_exists(self, client, datasource_id):
        try:
            LOG.debug("datasource_exists begin")
            body = client.list_datasource_status(datasource_id)
            LOG.debug("list_datasource_status: %s", str(body))
        except Exception as e:
            if hasattr(e, 'http_status') and e.http_status == 404:
                LOG.debug("not found")
                return False
            elif isinstance(e, keystoneclient.exceptions.ConnectionRefused):
                LOG.debug("connection refused")
                return False
            raise
        return True

    def datasource_missing(self, client, datasource_id):
        try:
            LOG.debug("datasource_missing begin")
            body = client.list_datasource_status(datasource_id)
            LOG.debug("list_datasource_status: %s", str(body))
        except Exception as e:
            if hasattr(e, 'http_status') and e.http_status == 404:
                LOG.debug("not found")
                return True
            elif isinstance(e, keystoneclient.exceptions.ConnectionRefused):
                LOG.debug("connection refused")
                return False
            raise
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
                'config': '{}',
                'description': 'bar',
                'enabled': True}
        ret = client.create_datasource(item)
        LOG.debug('created fake driver: %s', str(ret['id']))
        return ret['id']

    @test.attr(type='smoke')
    @test.services('compute',)
    def test_datasource_db_sync_add(self):
        # Verify that a replica adds a datasource when a datasource
        # appears in the database.
        CLIENT2_PORT = 4001
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
            self.start_replica(CLIENT2_PORT)

            # Create session for second server.
            client2 = self.create_client(CLIENT2_PORT)

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
                self.stop_replica(CLIENT2_PORT)
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
            self.stop_replica(CLIENT2_PORT)
            if need_to_delete_fake:
                self.admin_manager.congress_client.delete_datasource(fake_id)

    @test.attr(type='smoke')
    @test.services('compute',)
    def test_datasource_db_sync_remove(self):
        # Verify that a replica removes a datasource when a datasource
        # disappears from the database.
        CLIENT2_PORT = 4001
        client1 = self.admin_manager.congress_client
        fake_id = self.create_fake(client1)
        need_to_delete_fake = True
        try:
            self.start_replica(CLIENT2_PORT)

            # Verify that primary server has fake datasource
            if not test.call_until_true(
                    func=lambda: self.datasource_exists(client1, fake_id),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException(
                    "primary should have fake, but does not")

            # Create session for second server.
            client2 = self.create_client(CLIENT2_PORT)

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
                self.stop_replica(CLIENT2_PORT)
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
            self.stop_replica(CLIENT2_PORT)
            if need_to_delete_fake:
                self.admin_manager.congress_client.delete_datasource(fake_id)
