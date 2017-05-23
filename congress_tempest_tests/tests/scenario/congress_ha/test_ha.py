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
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions
from tempest import manager as tempestmanager
from urllib3 import exceptions as urllib3_exceptions

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
        self.client = self.admin_manager.congress_client

    def _prepare_replica(self, port_num):
        replica_url = "http://127.0.0.1:%d" % port_num
        resp = self.services_client.create_service(
            name='congressha',
            type=CONF.congressha.replica_type,
            description='policy ha service')
        self.replica_service_id = resp['OS-KSADM:service']['id']
        resp = self.endpoints_client.create_endpoint(
            service_id=self.replica_service_id,
            region=CONF.identity.region,
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
        conf = (conf[:index] +
                'bind_port = %d\n' % port_num +
                conf[index:])
        # set datasource sync period interval to 5
        conf = conf.replace('datasource_sync_period = 30',
                            'datasource_sync_period = 5')
        sindex = conf.find('signing_dir')
        conf = conf[:sindex] + '#' + conf[sindex:]
        conf = conf + '\n[dse]\nbus_id = replica-node\n'
        LOG.debug("Configuration file for replica: %s\n", conf)
        f.write(conf)
        f.close()

        # start all services on replica node
        api = self.start_service('api', conf_file)
        pe = self.start_service('policy-engine', conf_file)
        data = self.start_service('datasources', conf_file)

        assert port_num not in self.replicas
        LOG.debug("successfully started replica services\n")
        self.replicas[port_num] = ([api, pe, data], conf_file)

    def start_service(self, name, conf_file):
        port_num = CONF.congressha.replica_port
        out = tempfile.NamedTemporaryFile(
            mode='w', suffix='.out',
            prefix='congress-%s-%d-' % (name, port_num),
            dir='/tmp', delete=False)

        err = tempfile.NamedTemporaryFile(
            mode='w', suffix='.err',
            prefix='congress-%s-%d-' % (name, port_num),
            dir='/tmp', delete=False)

        service = '--' + name
        node = name + '-replica-node'
        args = ['/usr/bin/python', 'bin/congress-server', service,
                '--node-id', node, '--config-file', conf_file]

        p = subprocess.Popen(args, stdout=out, stderr=err,
                             cwd=helper.root_path())
        return p

    def stop_replica(self, port_num):
        procs, conf_file = self.replicas[port_num]
        # Using proc.terminate() will block at proc.wait(), no idea why yet
        # kill all processes
        for p in procs:
            p.kill()
            p.wait()

        os.unlink(conf_file)
        self.replicas[port_num] = (None, conf_file)
        self._cleanup_replica()

    def create_client(self, client_type):
        creds = credentials.get_configured_admin_credentials('identity_admin')
        auth_prov = tempestmanager.get_auth_provider(creds)

        return policy_client.PolicyClient(
            auth_prov, client_type,
            CONF.identity.region)

    def _check_replica_server_status(self, client):
        try:
            LOG.debug("Check replica server status")
            client.list_policy()
            LOG.debug("replica server ready")
            return True
        except exceptions.Unauthorized:
            LOG.debug("connection refused")
            return False
        except (socket.error, urllib3_exceptions.MaxRetryError):
            LOG.debug("Replica server not ready")
            return False
        except Exception:
            raise
        return False

    def find_fake(self, client):
        datasources = client.list_datasources()
        for r in datasources['results']:
            if r['name'] == 'fake':
                LOG.debug('existing fake driver: %s', str(r['id']))
                return r['id']
        return None

    def _check_resource_exists(self, client, resource):
        try:
            body = None
            if resource == 'datasource':
                LOG.debug("Check datasource exists")
                body = self.client.list_datasource_status('fake')
            else:
                LOG.debug("Check policy exists")
                body = self.client.list_policy_status('fake')

            LOG.debug("resource status: %s", str(body))

        except exceptions.NotFound:
            LOG.debug("resource 'fake' not found")
            return False
        return True

    def _check_resource_missing(self, client, resource):
        return not self._check_resource_exists(client, resource)

    def create_fake(self, client):
        # Create fake datasource if it does not exist.  Returns the
        # fake datasource id.
        fake_id = self.find_fake(client)
        if fake_id:
            return fake_id

        item = {'id': None,
                'name': 'fake',
                'driver': 'fake_datasource',
                'config': {"username": "fakeu",
                           "tenant_name": "faket",
                           "password": "fakep",
                           "auth_url": "http://127.0.0.1:5000/v2"},
                'description': 'bar',
                'enabled': True}
        ret = client.create_datasource(item)
        LOG.debug('created fake driver: %s', str(ret['id']))
        return ret['id']

    @decorators.skip_because(bug="1689220")
    @decorators.attr(type='smoke')
    def test_datasource_db_sync_add_remove(self):
        # Verify that a replica adds a datasource when a datasource
        # appears in the database.
        replica_server = False
        try:
            # Check fake if exists. else create
            fake_id = self.create_fake(self.client)

            # Start replica
            self.start_replica(CONF.congressha.replica_port)
            replica_client = self.create_client(CONF.congressha.replica_type)

            # Check replica server status
            if not test_utils.call_until_true(
                    func=lambda: self._check_replica_server_status(
                        replica_client),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException("Replica Server not ready")
            # Relica server is up
            replica_server = True

            # primary server might sync later than replica server due to
            # diff in datasource sync interval(P-30, replica-5). So checking
            # replica first

            # Verify that replica server synced fake dataservice and policy
            if not test_utils.call_until_true(
                    func=lambda: self._check_resource_exists(
                        replica_client, 'datasource'),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException(
                    "replica doesn't have fake dataservice, data sync failed")
            if not test_utils.call_until_true(
                    func=lambda: self._check_resource_exists(
                        replica_client, 'policy'),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException(
                    "replica doesn't have fake policy, policy sync failed")

            # Verify that primary server synced fake dataservice and policy
            if not test_utils.call_until_true(
                    func=lambda: self._check_resource_exists(
                        self.client, 'datasource'),
                    duration=90, sleep_for=1):
                raise exceptions.TimeoutException(
                    "primary doesn't have fake dataservice, data sync failed")
            if not test_utils.call_until_true(
                    func=lambda: self._check_resource_exists(
                        self.client, 'policy'),
                    duration=90, sleep_for=1):
                raise exceptions.TimeoutException(
                    "primary doesn't have fake policy, policy sync failed")

            # Remove fake from primary server instance.
            LOG.debug("removing fake datasource %s", str(fake_id))
            self.client.delete_datasource(fake_id)

            # Verify that replica server has no fake datasource and fake policy
            if not test_utils.call_until_true(
                    func=lambda: self._check_resource_missing(
                        replica_client, 'datasource'),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException(
                    "replica still has fake dataservice, sync failed")
            if not test_utils.call_until_true(
                    func=lambda: self._check_resource_missing(
                        replica_client, 'policy'),
                    duration=60, sleep_for=1):
                raise exceptions.TimeoutException(
                    "replica still fake policy, policy synchronizer failed")

            LOG.debug("removed fake datasource from replica instance")

            # Verify that primary server has no fake datasource and fake policy
            if not test_utils.call_until_true(
                    func=lambda: self._check_resource_missing(
                        self.client, 'datasource'),
                    duration=90, sleep_for=1):
                raise exceptions.TimeoutException(
                    "primary still has fake dataservice, sync failed")
            if not test_utils.call_until_true(
                    func=lambda: self._check_resource_missing(
                        self.client, 'policy'),
                    duration=90, sleep_for=1):
                raise exceptions.TimeoutException(
                    "primary still fake policy, policy synchronizer failed")

            LOG.debug("removed fake datasource from primary instance")

        finally:
            if replica_server:
                self.stop_replica(CONF.congressha.replica_port)
