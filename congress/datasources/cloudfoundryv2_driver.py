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
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from cloudfoundryclient.v2 import client
from oslo_log import log as logging

from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return CloudFoundryV2Driver(name, keys, inbox, datapath, args)


class CloudFoundryV2Driver(datasource_driver.PollingDataSourceDriver,
                           datasource_driver.ExecutionDriver):
    ORGANIZATIONS = 'organizations'
    SERVICE_BINDINGS = 'service_bindings'
    APPS = 'apps'
    SPACES = 'spaces'
    SERVICES = 'services'

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    organizations_translator = {
        'translation-type': 'HDICT',
        'table-name': ORGANIZATIONS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'guid', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans})}

    service_bindings_translator = {
        'translation-type': 'LIST',
        'table-name': SERVICE_BINDINGS,
        'parent-key': 'guid',
        'parent-col-name': 'app_guid',
        'val-col': 'service_instance_guid',
        'translator': value_trans}

    apps_translator = {
        'translation-type': 'HDICT',
        'table-name': APPS,
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
             {'fieldname': 'detected_buildpack', 'translator': value_trans},
             {'fieldname': 'detected_start_command',
              'translator': value_trans},
             {'fieldname': 'disk_quota', 'translator': value_trans},
             {'fieldname': 'docker_image', 'translator': value_trans},
             {'fieldname': 'environment_json', 'translator': value_trans},
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
             {'fieldname': 'updated_at', 'translator': value_trans},
             {'fieldname': 'service_bindings',
              'translator': service_bindings_translator})}

    spaces_translator = {
        'translation-type': 'HDICT',
        'table-name': SPACES,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'guid', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'created_at', 'translator': value_trans},
             {'fieldname': 'updated_at', 'translator': value_trans},
             {'fieldname': 'apps', 'translator': apps_translator})}

    services_translator = {
        'translation-type': 'HDICT',
        'table-name': SERVICES,
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
        datasource_driver.ExecutionDriver.__init__(self)
        self.creds = args
        self.cloudfoundry = client.Client(username=self.creds['username'],
                                          password=self.creds['password'],
                                          base_url=self.creds['auth_url'])
        self.cloudfoundry.login()
        self._cached_organizations = []
        self._init_end_start_poll()

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

    def _get_app_services_guids(self, service_bindings):
        result = []
        for service_binding in service_bindings['resources']:
            result.append(service_binding['entity']['service_instance_guid'])
        return result

    def update_from_datasource(self):
        LOG.debug("CloudFoundry grabbing Data")
        organizations = self.cloudfoundry.get_organizations()
        self._translate_organizations(organizations)
        self._save_organizations(organizations)

        spaces = self._get_spaces()
        services = self._get_services_update_spaces(spaces)

        self._translate_spaces(spaces)
        self._translate_services(services)

    def _get_services_update_spaces(self, spaces):
        services = []
        for space in spaces:
            space['apps'] = []
            temp_apps = self.cloudfoundry.get_apps_in_space(space['guid'])
            for temp_app in temp_apps['resources']:
                service_bindings = self.cloudfoundry.get_app_service_bindings(
                    temp_app['metadata']['guid'])
                data = dict(list(temp_app['metadata'].items()) +
                            list(temp_app['entity'].items()))
                app_services = self._get_app_services_guids(service_bindings)
                if app_services:
                    data['service_bindings'] = app_services
                space['apps'].append(data)
            services.extend(self._parse_services(
                self.cloudfoundry.get_spaces_summary(space['guid'])))
        return services

    def _get_spaces(self):
        spaces = []
        for org in self._cached_organizations:
            temp_spaces = self.cloudfoundry.get_organization_spaces(org)
            for temp_space in temp_spaces['resources']:
                spaces.append(dict(list(temp_space['metadata'].items()) +
                                   list(temp_space['entity'].items())))
        return spaces

    @ds_utils.update_state_on_changed(SERVICES)
    def _translate_services(self, obj):
        LOG.debug("services: %s", obj)
        row_data = CloudFoundryV2Driver.convert_objs(
            obj, self.services_translator)
        return row_data

    @ds_utils.update_state_on_changed(ORGANIZATIONS)
    def _translate_organizations(self, obj):
        LOG.debug("organziations: %s", obj)

        # convert_objs needs the data structured a specific way so we
        # do this here. Perhaps we can improve convert_objs later to be
        # more flexiable.
        results = [dict(list(o['metadata'].items()) +
                        list(o['entity'].items()))
                   for o in obj['resources']]
        row_data = CloudFoundryV2Driver.convert_objs(
            results,
            self.organizations_translator)
        return row_data

    @ds_utils.update_state_on_changed(SPACES)
    def _translate_spaces(self, obj):
        LOG.debug("spaces: %s", obj)
        row_data = CloudFoundryV2Driver.convert_objs(
            obj,
            self.spaces_translator)
        return row_data

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.cloudfoundry, action, action_args)
