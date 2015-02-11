# Copyright (c) 2015 Hewlett-Packard. All rights reserved.
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
import keystoneclient.v2_0.client as ksclient
import muranoclient.client

from congress.datasources import datasource_driver
from congress.datasources import datasource_utils
from congress.openstack.common import log as logging
from congress.utils import value_to_congress


logger = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return MuranoDriver(name, keys, inbox, datapath, args)


class MuranoDriver(datasource_driver.DataSourceDriver):
    OBJECTS = "objects"
    PARENT_TYPES = "parent_types"
    PROPERTIES = "properties"
    RELATIONSHIPS = "relationships"
    STATES = "states"

    instance_types = [
        'io.murano.resources.Instance',
        'io.murano.resources.LinuxInstance',
        'io.murano.resources.LinuxMuranoInstance',
        'io.murano.resources.WindowsInstance']

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(MuranoDriver, self).__init__(name, keys, inbox, datapath, args)
        self.creds = datasource_utils.get_credentials(name, args)
        logger.debug("Credentials = %s" % self.creds)
        keystone = ksclient.Client(**self.creds)
        murano_endpoint = keystone.service_catalog.url_for(
            service_type='application_catalog',
            endpoint_type='publicURL')
        logger.debug("murano_endpoint = %s" % murano_endpoint)
        client_version = "1"
        self.murano_client = muranoclient.client.Client(
            client_version,
            endpoint=murano_endpoint,
            token=keystone.auth_token)
        logger.debug("Successfully created murano_client")

        self.initialized = True

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'murano'
        result['description'] = ('Datasource driver that interfaces with '
                                 'murano')
        result['config'] = datasource_utils.get_openstack_required_config()
        return result

    def update_from_datasource(self):
        """Called when it is time to pull new data from this datasource.

        Sets self.state[tablename] = <set of tuples of strings/numbers>
        for every tablename exported by this datasource.
        """
        logger.debug("Murano grabbing environments")
        environments = self.murano_client.environments.list()
        self.state[self.STATES] = set()
        self.state[self.OBJECTS] = set()
        self.state[self.PROPERTIES] = set()
        self.state[self.PARENT_TYPES] = set()

        self._translate_environments(environments)
        self._translate_services(environments)

        logger.debug("Murano grabbing packages")
        packages = self.murano_client.packages.list()
        self._translate_packages(packages)

    @classmethod
    def get_schema(cls):
        """Returns a dictionary of table schema.

        The dictionary mapping tablenames to the list of column names
        for that table. Both tablenames and columnnames are strings.
        """
        d = {}
        d[cls.OBJECTS] = ('object_id', 'owner_id', 'type')
        d[cls.PARENT_TYPES] = ('id', 'parent_type')
        d[cls.PROPERTIES] = ('id', 'name', 'value')
        d[cls.RELATIONSHIPS] = ('source_id', 'target_id', 'name')
        d[cls.STATES] = ('id', 'state')
        return d

    def _translate_environments(self, environments):
        """Translate the environments into tables.

        Assigns self.state[tablename] for all those TABLENAMEs
        generated from environments
        """
        logger.debug("_translate_environments: %s", environments)
        if not environments:
            return
        self.state[self.STATES] = set()
        if self.OBJECTS not in self.state:
            self.state[self.OBJECTS] = set()
        if self.PROPERTIES not in self.state:
            self.state[self.PROPERTIES] = set()
        if self.PARENT_TYPES not in self.state:
            self.state[self.PARENT_TYPES] = set()

        for env in environments:
            self.state[self.OBJECTS].add(
                (env.id, env.tenant_id, 'io.murano.Environment'))
            self.state[self.PROPERTIES].add((env.id, 'name', env.name))
            self.state[self.STATES].add((env.id, env.status))
        logger.debug("Environments: %s", self.state[self.OBJECTS])

    def _translate_services(self, environments):
        """Translate the environment services into tables.

        Assigns self.state[tablename] for all those TABLENAMEs
        generated from services
        """
        logger.debug("Murano grabbing environments services")
        if not environments:
            return
        for env in environments:
            services = self.murano_client.services.list(env.id)
            self._translate_environment_services(services, env.id)

    def _translate_environment_services(self, services, env_id):
        """Translate the environment services into tables.

        Assigns self.state[tablename] for all those TABLENAMEs
        generated from services
        """
        if not services:
            return
        for s in services:
            s_dict = s.to_dict()
            s_id = s_dict['?']['id']
            s_type = s_dict['?']['type']
            self.state[self.OBJECTS].add((s_id, env_id, s_type))
            self.state[self.PROPERTIES].add((s_id, 'name', s.name))
            if 'io.murano.apps' in s_type:
                self.state[self.PARENT_TYPES].add(
                    (s_id, 'io.murano.Application'))

            if 'instance' not in s_dict:
                continue
            # populate service instance
            si_dict = s.instance
            si_id = si_dict['?']['id']
            si_type = si_dict['?']['type']
            self.state[self.OBJECTS].add((si_id, s_id, si_type))
            if 'securityGroupName' in si_dict and si_dict['securityGroupName']:
                si_security_group_name = value_to_congress(
                    si_dict['securityGroupName'])
                self.state[self.PROPERTIES].add(
                    (si_id, 'security_group_name', si_security_group_name))
            self.state[self.PROPERTIES].add(
                (si_id, 'name', si_dict['name']))
            if 'flavor' in si_dict:
                self.state[self.PROPERTIES].add(
                    (si_id, 'flavor', si_dict['flavor']))
            if 'image' in si_dict:
                self.state[self.PROPERTIES].add(
                    (si_id, 'image', si_dict['image']))
            if si_type in self.instance_types:
                self.state[self.PARENT_TYPES].add(
                    (si_id, 'io.murano.resources.Instance'))

            if 'ipAddresses' in si_dict:
                for ip_addr in si_dict['ipAddresses']:
                    self.state[self.PROPERTIES].add(
                        (si_id, 'ip_address', ip_addr))
            if 'floatingIpAddress' in si_dict and si_dict['floatingIpAddress']:
                self.state[self.PROPERTIES].add(
                    (si_id, 'floating_ip_address',
                     si_dict['floatingIpAddress']))

    def _translate_packages(self, packages):
        """Translate the packages into tables.

        Assigns self.state[tablename] for all those TABLENAMEs
        generated from packages/applications
        """
        # packages is a generator type
        if not packages:
            return
        if self.OBJECTS not in self.state:
            self.state[self.OBJECTS] = set()
        if self.PROPERTIES not in self.state:
            self.state[self.PROPERTIES] = set()

        for pkg in packages:
            logger.debug("pkg=%s", pkg.to_dict())
            self.state[self.OBJECTS].add((pkg.id, pkg.owner_id, pkg.type))
            self.state[self.PROPERTIES].add((pkg.id, 'name', pkg.name))
            self.state[self.PROPERTIES].add(
                (pkg.id, 'fully_qualified_name', pkg.fully_qualified_name))
            self.state[self.PROPERTIES].add((pkg.id, 'enabled', pkg.enabled))
            self.state[self.PROPERTIES].add((pkg.id, 'author', pkg.author))
            self.state[self.PROPERTIES].add(
                (pkg.id, 'is_public', pkg.is_public))
            for tag in pkg.tags:
                self.state[self.PROPERTIES].add((pkg.id, 'tag', tag))
            for category in pkg.categories:
                self.state[self.PROPERTIES].add(
                    (pkg.id, 'category', category))
