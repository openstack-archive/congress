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
from congress.datasources import murano_classes
from congress.openstack.common import log as logging
from congress.openstack.common import uuidutils
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
    UNUSED_PKG_PROPERTIES = ['id', 'owner_id', 'type', 'class_definitions',
                             'description']
    UNUSED_ENV_PROPERTIES = ['id', 'tenant_id']

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(MuranoDriver, self).__init__(name, keys, inbox, datapath, args)
        self.creds = args
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
        result['secret'] = ['password']
        return result

    def update_from_datasource(self):
        """Called when it is time to pull new data from this datasource.

        Sets self.state[tablename] = <set of tuples of strings/numbers>
        for every tablename exported by this datasource.
        """
        self.state[self.STATES] = set()
        self.state[self.OBJECTS] = set()
        self.state[self.PROPERTIES] = set()
        self.state[self.PARENT_TYPES] = set()
        self.state[self.RELATIONSHIPS] = set()

        # Workaround for 401 error issue
        try:
            logger.debug("Murano grabbing environments")
            environments = self.murano_client.environments.list()
            self._translate_environments(environments)
            self._translate_services(environments)
            self._translate_deployments(environments)

            logger.debug("Murano grabbing packages")
            packages = self.murano_client.packages.list()
            self._translate_packages(packages)
        except Exception as e:
            if e.code == 401:
                logger.debug("Obtain keystone token again")
                keystone = ksclient.Client(**self.creds)
                self.murano_client.auth_token = keystone.auth_token
            else:
                raise e

    @classmethod
    def get_schema(cls):
        """Returns a dictionary of table schema.

        The dictionary mapping tablenames to the list of column names
        for that table. Both tablenames and columnnames are strings.
        """
        d = {}
        d[cls.OBJECTS] = ('object_id', 'owner_id', 'type')
        # parent_types include not only the type of object's immediate
        # parent but also all of its ancestors and its own type.  The
        # additional info helps writing better datalog rules.
        d[cls.PARENT_TYPES] = ('id', 'parent_type')
        d[cls.PROPERTIES] = ('owner_id', 'name', 'value')
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
        if self.RELATIONSHIPS not in self.state:
            self.state[self.RELATIONSHIPS] = set()

        for env in environments:
            self.state[self.OBJECTS].add(
                (env.id, env.tenant_id, 'io.murano.Environment'))
            self.state[self.STATES].add((env.id, env.status))
            for key, value in env.to_dict().iteritems():
                if key in self.UNUSED_ENV_PROPERTIES:
                    continue
                self._add_properties(env.id, key, value)

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
            for key, value in s_dict.iteritems():
                if key in ['instance', '?']:
                    continue
                self._add_properties(s_id, key, value)
                self._add_relationships(s_id, key, value)

            parent_types = murano_classes.get_parent_types(s_type)
            self._add_parent_types(s_id, parent_types)

            if 'instance' not in s_dict:
                continue
            # populate service instance
            si_dict = s.instance
            si_id = si_dict['?']['id']
            si_type = si_dict['?']['type']
            self.state[self.OBJECTS].add((si_id, s_id, si_type))

            for key, value in si_dict.iteritems():
                if key in ['?']:
                    continue
                self._add_properties(si_id, key, value)
                self._add_relationships(si_id, key, value)

            parent_types = murano_classes.get_parent_types(si_type)
            self._add_parent_types(si_id, parent_types)

    def _translate_deployments(self, environments):
        """Translate the environment deployments into tables.

        Assigns self.state[tablename] for all those TABLENAMEs
        generated from deployments
        """
        if not environments:
            return
        for env in environments:
            deployments = self.murano_client.deployments.list(env.id)
            self._translate_environment_deployments(deployments, env.id)

    def _translate_environment_deployments(self, deployments, env_id):
        """Translate the environment deployments into tables.

        Assigns self.state[tablename] for all those TABLENAMEs
        generated from deployments
        """
        if not deployments:
            return
        for d in deployments:
            if 'defaultNetworks' not in d.description:
                continue
            default_networks = d.description['defaultNetworks']
            net_id = None
            if 'environment' in default_networks:
                net_id = default_networks['environment']['?']['id']
                net_type = default_networks['environment']['?']['type']
                self.state[self.OBJECTS].add((net_id, env_id, net_type))

                parent_types = murano_classes.get_parent_types(net_type)
                self._add_parent_types(net_id, parent_types)

                for key, value in default_networks['environment'].iteritems():
                    if key in ['?']:
                        continue
                    self._add_properties(net_id, key, value)

            if not net_id:
                continue
            self._add_relationships(env_id, 'defaultNetworks', net_id)
            for key, value in default_networks.iteritems():
                if key in ['environment']:
                    # data from environment already populated
                    continue
                new_key = 'defaultNetworks.' + key
                self._add_properties(net_id, new_key, value)
            # services from deployment are not of interest because the same
            # info is obtained from services API

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
            pkg_type = pkg.type
            if pkg.type == 'Application':
                pkg_type = 'io.murano.Application'
            self.state[self.OBJECTS].add((pkg.id, pkg.owner_id, pkg_type))

            for key, value in pkg.to_dict().iteritems():
                if key in self.UNUSED_PKG_PROPERTIES:
                    continue
                self._add_properties(pkg.id, key, value)

    def _add_properties(self, obj_id, key, value):
        """Add a set of (obj_id, key, value) to properties table.

        :param obj_id: uuid of object
        :param key: property name. For the case value is a list, the
        same key is used for multiple values.
        :param value: property value. It can be string or list. For
        the case value is a dictionary, it's ignored for now because
        it's not clear how it fits in the properties table.
        """
        if value is None or value == '':
            return
        if isinstance(value, dict):
            for k, v in value.iteritems():
                new_key = key + "." + k
                self._add_properties(obj_id, new_key, v)
        elif isinstance(value, list):
            if len(value) == 0:
                return
            for item in value:
                self.state[self.PROPERTIES].add(
                    (obj_id, key, value_to_congress(item)))
        else:
            self.state[self.PROPERTIES].add(
                (obj_id, key, value_to_congress(value)))

    def _add_relationships(self, obj_id, key, value):
        """Add a set of (obj_id, value, key) to relationships table.

        :param obj_id: source uuid
        :param key: relationship name
        :param value: target uuid
        """
        if (not isinstance(value, basestring) or
                not uuidutils.is_uuid_like(value)):
            return
        logger.debug("Relationship: source = %s, target = %s, rel_name = %s"
                     % (obj_id, value, key))
        self.state[self.RELATIONSHIPS].add((obj_id, value, key))

    def _add_parent_types(self, obj_id, parent_types):
        """Add sets of (obj_id, parent_type) to parent_types table.

        :param obj_id: uuid of object
        :param parent_types: list of parent type string
        """
        if parent_types:
            for p_type in parent_types:
                self.state[self.PARENT_TYPES].add((obj_id, p_type))
