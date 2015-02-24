#!/usr/bin/env python
# Copyright (c) 2014 VMware, Inc. All rights reserved.
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
from cloudfoundryclient.v2 import client

from congress.datasources import constants
from congress.datasources.datasource_driver import DataSourceDriver
from congress.openstack.common import log as logging

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return CloudFoundryV2Driver(name, keys, inbox, datapath, args)


class CloudFoundryV2Driver(DataSourceDriver):

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    organizations_translator = {
        'translation-type': 'HDICT',
        'table-name': 'organizations',
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'guid', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans})}

    apps_translator = {
        'translation-type': 'HDICT',
        'table-name': 'apps',
        'in-list': True,
        'parent-key': 'guid',
        'parent-col-name': 'space_guid',
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'guid', 'translator': value_trans},
             {'fieldname': 'buildpack', 'translator': value_trans},
             {'fieldname': 'command', 'translator': value_trans},
             {'fieldname': 'console', 'translator': value_trans},
             {'fieldname': 'debug', 'translator': value_trans},
             {'fieldname': 'detect_buildpack', 'translator': value_trans},
             {'fieldname': 'detect_start_command', 'translator': value_trans},
             {'fieldname': 'disk_quota', 'translator': value_trans},
             {'fieldname': 'docker_image', 'translator': value_trans},
             {'fieldname': 'enviroment_json', 'translator': value_trans},
             {'fieldname': 'health_check_timeout', 'translator': value_trans},
             {'fieldname': 'instances', 'translator': value_trans},
             {'fieldname': 'memory', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'package_state', 'translator': value_trans},
             {'fieldname': 'package_updated_at', 'translator': value_trans},
             {'fieldname': 'production', 'translator': value_trans},
             {'fieldname': 'staging_failed_reason', 'translator': value_trans},
             {'fieldname': 'staging_task_id', 'translator': value_trans},
             {'fieldname': 'state', 'translator': value_trans},
             {'fieldname': 'version', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans})}

    spaces_translator = {
        'translation-type': 'HDICT',
        'table-name': 'spaces',
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'guid', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans},
             {'fieldname': 'apps', 'translator': apps_translator})}

    services_translator = {
        'translation-type': 'HDICT',
        'table-name': 'services',
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'guid', 'translator': value_trans},
             {'fieldname': 'space_guid', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'bound_app_count', 'translator': value_trans},
             {'fieldname': 'last_operation', 'translator': value_trans},
             {'fieldname': 'service_plan_name', 'translator': value_trans})}

    TRANSLATORS = [organizations_translator,
                   spaces_translator, services_translator]

    def __init__(self, name='', keys='', inbox=None,
                 datapath=None, args=None):
        super(CloudFoundryV2Driver, self).__init__(name, keys, inbox,
                                                   datapath, args)
        self.creds = args
        self.cloudfoundry = client.Client(username=self.creds['username'],
                                          password=self.creds['password'],
                                          base_url=self.creds['auth_url'])
        self.cloudfoundry.login()

        # Store raw state (result of API calls) so that we can
        #   avoid re-translating and re-sending if no changes occurred.
        #   Because translation is not deterministic (we're generating
        #   UUIDs), it's hard to tell if no changes occurred
        #   after performing the translation.
        self.raw_state = {}
        self.initialized = True
        self._cached_organizations = []

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'cloudfoundryv2'
        result['description'] = ('Datasource driver that interfaces with '
                                 'cloudfoundry')
        result['config'] = {'username': constants.REQUIRED,
                            'password': constants.REQUIRED,
                            'poll_time': constants.OPTIONAL,
                            'auth_url': constants.REQUIRED}
        result['secret'] = ['password']
        return result

    def _save_organizations(self, organizations):
        temp_organizations = []
        for organization in organizations['resources']:
            temp_organizations.append(organization['metadata']['guid'])
        self._cached_organizations = temp_organizations

    def _parse_services(self, services):
        data = []
        space_guid = services['guid']
        for service in services['services']:
            data.append(
                {'bound_app_count': service['bound_app_count'],
                 'guid': service['guid'],
                 'name': service['name'],
                 'service_plan_name': service['service_plan']['name'],
                 'space_guid': space_guid})
        return data

    def update_from_datasource(self):
        LOG.debug("CloudFoundry grabbing Data")
        organizations = self.cloudfoundry.get_organizations()
        if ('organizations' not in self.raw_state or
                organizations != self.raw_state['organizations']):
            self.raw_state['organizations'] = organizations
            self._translate_organizations(organizations)
        self._save_organizations(organizations)

        spaces = []
        for org in self._cached_organizations:
            temp_spaces = self.cloudfoundry.get_organization_spaces(org)
            for temp_space in temp_spaces['resources']:
                spaces.append(dict(temp_space['metadata'].items() +
                                   temp_space['entity'].items()))

        services = []
        for space in spaces:
            space['apps'] = []
            temp_apps = self.cloudfoundry.get_apps_in_space(space['guid'])
            for temp_app in temp_apps['resources']:
                space['apps'].append(dict(temp_app['metadata'].items() +
                                          temp_app['entity'].items()))
            services.extend(self._parse_services(
                self.cloudfoundry.get_spaces_summary(space['guid'])))

        if ('spaces' not in self.raw_state or
                spaces != self.raw_state['spaces']):
            self.raw_state['spaces'] = spaces
            self._translate_spaces(spaces)

        if ('services' not in self.raw_state or
                services != self.raw_state['services']):
            self._translate_services(services)

    def _translate_services(self, obj):
        LOG.debug("services: %s", obj)
        row_data = CloudFoundryV2Driver.convert_objs(
            obj, self.services_translator)
        self.state['services'] = set()
        for table, row in row_data:
            self.state[table].add(row)

    def _translate_organizations(self, obj):
        LOG.debug("organziations: %s", obj)

        # convert_objs needs the data structured a specific way so we
        # do this here. Perhaps we can improve convert_objs later to be
        # more flexiable.
        results = [dict(o['metadata'].items() + o['entity'].items())
                   for o in obj['resources']]
        row_data = CloudFoundryV2Driver.convert_objs(
            results,
            self.organizations_translator)
        self.state['organizations'] = set()
        for table, row in row_data:
            self.state[table].add(row)

    def _translate_spaces(self, obj):
        LOG.debug("spaces: %s", obj)
        row_data = CloudFoundryV2Driver.convert_objs(
            obj,
            self.spaces_translator)
        self.state['spaces'] = set()
        for table, row in row_data:
            self.state[table].add(row)
