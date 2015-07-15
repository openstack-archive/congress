# Copyright 2012 OpenStack Foundation
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

import json

from tempest.common import service_client

class PolicyClient(service_client.ServiceClient):


    policy = '/v1/policies'
    policy_path = '/v1/policies/%s'
    policy_rules = '/v1/policies/%s/rules'
    policy_rules_path = '/v1/policies/%s/rules/%s'
    policy_tables = '/v1/policies/%s/tables'
    policy_table_path = '/v1/policies/%s/tables/%s'
    policy_rows = '/v1/policies/%s/tables/%s/rows'
    policy_rows_trace = '/v1/policies/%s/tables/%s/rows?trace=True'
    policies = '/v1/policies'
    policy_action = '/v1/policies/%s?%s'
    datasources = '/v1/data-sources'
    datasource_path = '/v1/data-sources/%s'
    datasource_tables = '/v1/data-sources/%s/tables'
    datasource_table_path = '/v1/data-sources/%s/tables/%s'
    datasource_status = '/v1/data-sources/%s/status'
    datasource_schema = '/v1/data-sources/%s/schema'
    datasource_table_schema = '/v1/data-sources/%s/tables/%s/spec'
    datasource_rows = '/v1/data-sources/%s/tables/%s/rows'
    driver = '/v1/system/drivers'
    driver_path = '/v1/system/drivers/%s'

    def _resp_helper(self, resp, body):
        body = json.loads(body)
        return service_client.ResponseBody(resp, body)

    def create_policy(self, body):
        body = json.dumps(body)
        resp, body = self.post(
            self.policy, body=body)
        return self._resp_helper(resp, body)

    def delete_policy(self, policy):
        resp, body = self.delete(
            self.policy_path % policy)
        return self._resp_helper(resp, body)

    def show_policy(self, policy):
        resp, body = self.get(
            self.policy_path % policy)
        return self._resp_helper(resp, body)

    def create_policy_rule(self, policy_name, body=None):
        body = json.dumps(body)
        resp, body = self.post(
            self.policy_rules % policy_name, body=body)
        return self._resp_helper(resp, body)

    def delete_policy_rule(self, policy_name, rule_id):
        resp, body = self.delete(
            self.policy_rules_path % (policy_name, rule_id))
        return self._resp_helper(resp, body)

    def show_policy_rule(self, policy_name, rule_id):
        resp, body = self.get(
            self.policy_rules_path % (policy_name, rule_id))
        return self._resp_helper(resp, body)

    def list_policy_rows(self, policy_name, table, trace=None):
        if trace:
            query = self.policy_rows_trace
        else:
            query = self.policy_rows
        resp, body = self.get(query % (policy_name, table))
        return self._resp_helper(resp, body)

    def list_policy_rules(self, policy_name):
        resp, body = self.get(self.policy_rules % (policy_name))
        return self._resp_helper(resp, body)

    def list_policy(self):
        resp, body = self.get(self.policies)
        return self._resp_helper(resp, body)

    def list_policy_tables(self, policy_name):
        resp, body = self.get(self.policy_tables % (policy_name))
        return self._resp_helper(resp, body)

    def execute_policy_action(self, policy_name, action, trace, delta, body):
        body = json.dumps(body)
        uri = "?action=%s&trace=%s&delta=%s" % (action, trace, delta)
        resp, body = self.post(
            (self.policy_path % policy_name) + str(uri), body=body)
        return self._resp_helper(resp, body)

    def show_policy_table(self, policy_name, table_id):
        resp, body = self.get(self.policy_table_path %
                                         (policy_name, table_id))
        return self._resp_helper(resp, body)

    def list_datasources(self):
        resp, body = self.get(self.datasources)
        return self._resp_helper(resp, body)

    def list_datasource_tables(self, datasource_name):
        resp, body = self.get(self.datasource_tables %
                                         (datasource_name))
        return self._resp_helper(resp, body)

    def list_datasource_rows(self, datasource_name, table_name):
        resp, body = self.get(self.datasource_rows %
                                         (datasource_name, table_name))
        return self._resp_helper(resp, body)

    def list_datasource_status(self, datasource_name):
        resp, body = self.get(self.datasource_status %
                                         datasource_name)
        return self._resp_helper(resp, body)

    def show_datasource_schema(self, datasource_name):
        resp, body = self.get(self.datasource_schema %
                                         datasource_name)
        return self._resp_helper(resp, body)

    def show_datasource_table_schema(self, datasource_name, table_name):
        resp, body = self.get(self.datasource_table_schema %
                                         (datasource_name, table_name))
        return self._resp_helper(resp, body)

    def show_datasource_table(self, datasource_name, table_id):
        resp, body = self.get(self.datasource_table_path %
                                         (datasource_name, table_id))
        return self._resp_helper(resp, body)

    def create_datasource(self, body=None):
        body = json.dumps(body)
        resp, body = self.post(
            self.datasources, body=body)
        return self._resp_helper(resp, body)

    def delete_datasource(self, datasource):
        resp, body = self.delete(
            self.datasource_path % datasource)
        return self._resp_helper(resp, body)

    def execute_datasource_action(self, service_name, action, body):
        body = json.dumps(body)
        uri = "?action=%s" % (action)
        resp, body = self.post(
            (self.datasource_path % service_name) + str(uri), body=body)
        return self._resp_helper(resp, body)

    def list_drivers(self):
        resp, body = self.get(self.driver)
        return self._resp_helper(resp, body)

    def show_driver(self, driver):
        resp, body = self.get(self.driver_path %
                                         (driver))
        return self._resp_helper(resp, body)

    def request_refresh(self, driver, body=None):
        body = json.dumps(body)
        resp, body = self.post(self.datasource_path %
                                          (driver) + "?action=request-refresh",
                                          body=body)
        return self._resp_helper(resp, body)
