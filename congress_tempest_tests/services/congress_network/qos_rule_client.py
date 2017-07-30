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

from tempest.lib.services.network import base


class QosRuleClient(base.BaseNetworkClient):

    def create_qos_rule(self, qos_policy_id, qos_rule_type, **kwargs):
        """Creates an OpenStack Networking qos rule.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/index.html#quality-of-service
        """
        uri = '/qos/policies/%s/%s' % (qos_policy_id, qos_rule_type)
        post_data = {qos_rule_type[:-1]: kwargs}
        return self.create_resource(uri, post_data)

    def update_qos_rule(self, qos_policy_id, qos_rule_type,
                        qos_rule_id, **kwargs):
        """Updates a qos rule policy.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/index.html#quality-of-service
        """
        uri = '/qos/policies/%s/%s/%s' % (qos_policy_id,
                                          qos_rule_type, qos_rule_id)
        post_data = {'bandwidth_limit_rules': kwargs}
        return self.update_resource(uri, post_data)

    def show_qos_rule(self, qos_policy_id, qos_rule_type,
                      qos_rule_id, **fields):
        """Shows details for a qos rule policy.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/index.html#quality-of-service
        """
        uri = '/qos/policies/%s/%s/%s' % (qos_policy_id,
                                          qos_rule_type, qos_rule_id)
        return self.show_resource(uri, **fields)

    def delete_qos_rule(self, qos_policy_id, qos_rule_type, qos_rule_id):
        """Deletes an OpenStack Networking qos rule policy.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/index.html#quality-of-service
        """
        uri = '/qos/policies/%s/%s/%s' % (qos_policy_id,
                                          qos_rule_type, qos_rule_id)
        return self.delete_resource(uri)

    def list_qos_rule(self, qos_policy_id, **filters):
        """Lists OpenStack Networking qos rule policies.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/index.html#quality-of-service
        """
        uri = '/qos/policies/%s' % (qos_policy_id)
        return self.list_resources(uri, **filters)
