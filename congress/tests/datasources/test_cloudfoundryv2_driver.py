# Copyright (c) 2013 VMware, Inc. All rights reserved.
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
import sys

# NOTE(arosen): done to avoid the fact that cloudfoundryclient
# isn't in the openstack global reqirements.
import mock
sys.modules['cloudfoundryclient.v2.client'] = mock.Mock()
sys.modules['cloudfoundryclient.v2'] = mock.Mock()
sys.modules['cloudfoundryclient'] = mock.Mock()

from congress.datasources import cloudfoundryv2_driver
from congress.tests import base
from congress.tests import helper


ORG1_GUID = '5187136c-ef7d-47e6-9e6b-ac7780bab3db'
ORG_DATA = (
    {"total_results": 1,
     "next_url": 'null',
     "total_pages": 1,
     "prev_url": 'null',
     "resources": [{
         "entity":
             {"status": "active",
              "spaces_url": "/v2/organizations/" + ORG1_GUID + "/spaces",
              "private_domains_url":
                 "/v2/organizations/" + ORG1_GUID + "/private_domains",
              "name": "foo.com",
              "domains_url":
                 "/v2/organizations/" + ORG1_GUID + "/domains",
              "billing_enabled": 'true',
              "quota_definition_guid":
                 "b72b1acb-ff4f-468d-99c0-05cd91012b62",
              "app_events_url":
                 "/v2/organizations/" + ORG1_GUID + "/app_events",
              "space_quota_definitions_url":
                 "/v2/organizations/" + ORG1_GUID + "/space_quota_definitions",
              "quota_definition_url":
                 "/v2/quota_definitions/b72b1acb-ff4f-468d-99c0-05cd91012b62",
              "auditors_url":
                 "/v2/organizations/" + ORG1_GUID + "/auditors",
              "managers_url":
                 "/v2/organizations/" + ORG1_GUID + "/managers",
              "users_url":
                 "/v2/organizations/" + ORG1_GUID + "/users",
              "billing_managers_url":
                 "/v2/organizations/" + ORG1_GUID + "/billing_managers"
              },
         "metadata":
             {"url":
                 "/v2/organizations/5187136c-ef7d-47e6-9e6b-ac7780bab3db",
              "created_at": "2015-01-21T02:17:28+00:00",
              "guid": "5187136c-ef7d-47e6-9e6b-ac7780bab3db",
              "updated_at": "2015-01-21T02:17:28+00:00"
              }
     }
     ]
     }
)


SPACE1_GUID = "8da5477d-340e-4bb4-808a-54d9f72017d1"
SPACE2_GUID = "79479021-1e77-473a-8c63-28de9d2ca697"
ORG1_SPACES_DATA = (
    {"total_results": 2,
     "next_url": "null",
     "total_pages": 1,
     "prev_url": "null",
     "resources": [{
         "entity":
             {"developers_url": "/v2/spaces/" + SPACE1_GUID + "/developers",
              "service_instances_url":
                 "/v2/spaces/" + SPACE1_GUID + "/service_instances",
              "events_url": "/v2/spaces/" + SPACE1_GUID + "/events",
              "name": "development",
              "domains_url": "/v2/spaces/" + SPACE1_GUID + "/domains",
              "app_events_url": "/v2/spaces/" + SPACE1_GUID + "/app_events",
              "routes_url": "/v2/spaces/" + SPACE1_GUID + "/routes",
              "organization_guid": "5187136c-ef7d-47e6-9e6b-ac7780bab3db",
              "space_quota_definition_guid": "null",
              "apps_url": "/v2/spaces/" + SPACE1_GUID + "/apps",
              "auditors_url": "/v2/spaces/" + SPACE1_GUID + "/auditors",
              "managers_url": "/v2/spaces/" + SPACE1_GUID + "/managers",
              "organization_url":
                 "/v2/organizations/5187136c-ef7d-47e6-9e6b-ac7780bab3db",
              "security_groups_url":
                 "/v2/spaces/" + SPACE1_GUID + "/security_groups"
              },
         "metadata":
             {"url": "/v2/spaces/" + SPACE1_GUID,
              "created_at": "2015-01-21T02:17:28+00:00",
              "guid": SPACE1_GUID,
              "updated_at": "null"
              }
         },
         {"entity":
             {"developers_url": "/v2/spaces/" + SPACE2_GUID + "/developers",
              "service_instances_url":
                 "/v2/spaces/" + SPACE2_GUID + "/service_instances",
              "events_url": "/v2/spaces/" + SPACE2_GUID + "/events",
              "name": "test2",
              "domains_url": "/v2/spaces/" + SPACE2_GUID + "/domains",
              "app_events_url": "/v2/spaces/" + SPACE2_GUID + "/app_events",
              "routes_url": "/v2/spaces/" + SPACE2_GUID + "/routes",
              "organization_guid": "5187136c-ef7d-47e6-9e6b-ac7780bab3db",
              "space_quota_definition_guid": "null",
              "apps_url": "/v2/spaces/" + SPACE2_GUID + "/apps",
              "auditors_url": "/v2/spaces/" + SPACE2_GUID + "/auditors",
              "managers_url": "/v2/spaces/" + SPACE2_GUID + "/managers",
              "organization_url":
                 "/v2/organizations/5187136c-ef7d-47e6-9e6b-ac7780bab3db",
              "security_groups_url":
                 "/v2/spaces/" + SPACE2_GUID + "/security_groups"
              },
          "metadata":
              {"url": "/v2/spaces/" + SPACE2_GUID,
               "created_at": "2015-01-22T19:02:32+00:00",
               "guid": SPACE2_GUID,
               "updated_at": "null"
               }
          }
         ]
     }
)

APP1_GUID = "c3bd7fc1-73b4-4cc7-a6c8-9976c30edad5"
APP2_GUID = "f7039cca-95ac-49a6-b116-e32a53ddda69"
APPS_IN_SPACE1 = (
    {"total_results": 2,
     "next_url": "null",
     "total_pages": 1,
     "prev_url": "null",
     "resources": [{
         "entity":
             {"version": "fec00ce7-a980-49e1-abec-beed5516618f",
              "staging_failed_reason": "null",
              "instances": 1,
              "routes_url": "/v2/apps" + APP1_GUID + "routes",
              "space_url": "/v2/spaces/8da5477d-340e-4bb4-808a-54d9f72017d1",
              "docker_image": "null",
              "console": "false",
              "package_state": "STAGED",
              "state": "STARTED",
              "production": "false",
              "detected_buildpack": "Ruby",
              "memory": 256,
              "package_updated_at": "2015-01-21T21:00:40+00:00",
              "staging_task_id": "71f75ad3cad64884a92c4e7738eaae16",
              "buildpack": "null",
              "stack_url": "/v2/stacks/50688ae5-9bfc-4bf6-a4bf-caadb21a32c6",
              "events_url": "/v2/apps" + APP1_GUID + "events",
              "service_bindings_url":
                 "/v2/apps" + APP1_GUID + "service_bindings",
              "detected_start_command":
                 "bundle exec rake db:migrate && bundle exec rails s -p $PORT",
              "disk_quota": 1024,
              "stack_guid": "50688ae5-9bfc-4bf6-a4bf-caadb21a32c6",
              "space_guid": "8da5477d-340e-4bb4-808a-54d9f72017d1",
              "name": "rails_sample_app",
              "health_check_type": "port",
              "command":
                 "bundle exec rake db:migrate && bundle exec rails s -p $PORT",
              "debug": "null",
              "environment_json": "null",
              "health_check_timeout": "null"
              },
         "metadata":
             {"url": "/v2/apps/c3bd7fc1-73b4-4cc7-a6c8-9976c30edad5",
              "created_at": "2015-01-21T21:01:19+00:00",
              "guid": "c3bd7fc1-73b4-4cc7-a6c8-9976c30edad5",
              "updated_at": "2015-01-21T21:01:19+00:00"
              }
         },
         {"entity":
             {"version": "a1b52559-32f3-4765-9fd3-6e35293fb6d0",
              "staging_failed_reason": "null",
              "instances": 1,
              "routes_url": "/v2/apps" + APP2_GUID + "routes",
              "space_url": "/v2/spaces/8da5477d-340e-4bb4-808a-54d9f72017d1",
              "docker_image": "null",
              "console": "false",
              "package_state": "PENDING",
              "state": "STOPPED",
              "production": "false",
              "detected_buildpack": "null",
              "memory": 1024,
              "package_updated_at": "null",
              "staging_task_id": "null",
              "buildpack": "null",
              "stack_url": "/v2/stacks/50688ae5-9bfc-4bf6-a4bf-caadb21a32c6",
              "events_url": "/v2/apps" + APP2_GUID + "events",
              "service_bindings_url":
                 "/v2/apps" + APP2_GUID + "service_bindings",
              "detected_start_command": "",
              "disk_quota": 1024,
              "stack_guid": "50688ae5-9bfc-4bf6-a4bf-caadb21a32c6",
              "space_guid": "8da5477d-340e-4bb4-808a-54d9f72017d1",
              "name": "help",
              "health_check_type": "port",
              "command": "null",
              "debug": "null",
              "environment_json": "null",
              "health_check_timeout": "null"
              },
          "metadata":
             {"url": "/v2/apps/f7039cca-95ac-49a6-b116-e32a53ddda69",
              "created_at": "2015-01-21T18:48:34+00:00",
              "guid": "f7039cca-95ac-49a6-b116-e32a53ddda69",
              "updated_at": "null"
              }
          }
         ]
     }
)


APPS_IN_SPACE2 = {"total_results": 0,
                  "next_url": "null",
                  "total_pages": 1,
                  "prev_url": "null",
                  "resources": []}

SERVICES_IN_SPACE1 = {
    "guid": "8da5477d-340e-4bb4-808a-54d9f72017d1",
    "name": "development",
    "services": [{
        "bound_app_count": 0,
        "guid": "88f61682-d78e-410f-88ee-1e0eabbbc7da",
        "last_operation": None,
        "name": "rails-postgres",
        "service_plan": {
            "guid": "fbcec3af-3e8d-4ee7-adfe-3f12a137ed66",
            "name": "turtle",
            "service": {
                "guid": "34dbc753-34ed-4cf1-9a87-a224dfca569b",
                "label": "elephantsql",
                "provider": None,
                "version": None
            }
        }
    }]
}

EXPECTED_STATE = {
    'organizations': set([
        ('5187136c-ef7d-47e6-9e6b-ac7780bab3db', 'foo.com',
         '2015-01-21T02:17:28+00:00', '2015-01-21T02:17:28+00:00')]),
    'spaces': set([
        ('8da5477d-340e-4bb4-808a-54d9f72017d1', 'development',
         '2015-01-21T02:17:28+00:00', 'null'),
        ('79479021-1e77-473a-8c63-28de9d2ca697', 'test2',
         '2015-01-22T19:02:32+00:00', 'null')]),
    'apps': set([
        ('8da5477d-340e-4bb4-808a-54d9f72017d1',
         'c3bd7fc1-73b4-4cc7-a6c8-9976c30edad5', 'null',
         'bundle exec rake db:migrate && bundle exec rails s -p $PORT',
         'false', 'null', 'Ruby',
         'bundle exec rake db:migrate && bundle exec rails s -p $PORT',
         1024, 'null', 'null', 'null', 1,
         256, 'rails_sample_app', 'STAGED', '2015-01-21T21:00:40+00:00',
         'false', 'null', '71f75ad3cad64884a92c4e7738eaae16', 'STARTED',
         'fec00ce7-a980-49e1-abec-beed5516618f', '2015-01-21T21:01:19+00:00',
         '2015-01-21T21:01:19+00:00'),
        ('8da5477d-340e-4bb4-808a-54d9f72017d1',
         'f7039cca-95ac-49a6-b116-e32a53ddda69', 'null', 'null', 'false',
         'null', 'null', '', 1024, 'null', 'null', 'null', 1, 1024,
         'help', 'PENDING', 'null', 'false', 'null', 'null', 'STOPPED',
         'a1b52559-32f3-4765-9fd3-6e35293fb6d0',
         '2015-01-21T18:48:34+00:00', 'null')]),
    'service_bindings': set([]),
    'services': set([
        ('88f61682-d78e-410f-88ee-1e0eabbbc7da',
         '8da5477d-340e-4bb4-808a-54d9f72017d1', 'rails-postgres',
         0, 'None', 'turtle')]),
}


class TestCloudFoundryV2Driver(base.TestCase):

    def setUp(self):
        super(TestCloudFoundryV2Driver, self).setUp()

        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        args['client'] = mock.MagicMock()
        self.driver = cloudfoundryv2_driver.CloudFoundryV2Driver(args=args)

    def test_update_from_datasource(self):
        def _side_effect_get_org_spaces(org):
            if org == ORG1_GUID:
                return ORG1_SPACES_DATA
            raise ValueError("This should occur...")

        def _side_effect_get_apps_in_space(space):
            if space == SPACE1_GUID:
                return APPS_IN_SPACE1
            elif space == SPACE2_GUID:
                return APPS_IN_SPACE2
            else:
                raise ValueError("This should not occur....")

        def _side_effect_get_spaces_summary(space):
            if space == SPACE1_GUID:
                return SERVICES_IN_SPACE1
            else:
                return {"guid": space,
                        "services": []}

        def _side_effect_get_app_services(space):
            return {'resources': []}

        with base.nested(
            mock.patch.object(self.driver.cloudfoundry,
                              "get_organizations",
                              return_value=ORG_DATA),
            mock.patch.object(self.driver.cloudfoundry,
                              "get_organization_spaces",
                              side_effect=_side_effect_get_org_spaces),
            mock.patch.object(self.driver.cloudfoundry,
                              "get_apps_in_space",
                              side_effect=_side_effect_get_apps_in_space),
            mock.patch.object(self.driver.cloudfoundry,
                              "get_spaces_summary",
                              side_effect=_side_effect_get_spaces_summary),
            mock.patch.object(self.driver.cloudfoundry,
                              "get_app_service_bindings",
                              side_effect=_side_effect_get_app_services),


            ) as (get_organizations, get_organization_spaces,
                  get_apps_in_space, get_spaces_summary,
                  get_app_services_guids):
            self.driver.update_from_datasource()
            self.assertEqual(EXPECTED_STATE, self.driver.state)

    def test_execute(self):
        class CloudfoundryClient(object):
            def __init__(self):
                self.testkey = None

            def setServices(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        cloudfoundry_client = CloudfoundryClient()
        self.driver.cloudfoundry = cloudfoundry_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('setServices', api_args)

        self.assertEqual(expected_ans, cloudfoundry_client.testkey)
