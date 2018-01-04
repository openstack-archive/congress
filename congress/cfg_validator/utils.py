#
# Copyright (c) 2017 Orange.
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

"""Support functions for cfg_validator"""
import uuid

from oslo_log import log as logging

from congress.api import base
from congress import exception
from congress import utils

LOG = logging.getLogger(__name__)

#: Topic for RPC between cfg validator driver (client) and the agents (server)
AGENT_TOPIC = 'congress-validator-agent'
NAMESPACE_CONGRESS = uuid.uuid3(
    uuid.NAMESPACE_URL,
    'http://openstack.org/congress/agent')


def compute_hash(*args):
    """computes a hash from the arguments. Not cryptographically strong."""
    inputs = ''.join([str(arg) for arg in args])
    return str(uuid.uuid3(NAMESPACE_CONGRESS, inputs))


def cfg_value_to_congress(value):
    """Sanitize values for congress

    values of log formatting options typically contains
    '%s' etc, which should not be put in datalog
    """
    if isinstance(value, str):
        value = value.replace('%', '')
    if value is None:
        return ''
    return utils.value_to_congress(value)


def add_rule(bus, policy_name, rules):
    "Adds a policy and rules to the engine"
    try:
        policy_metadata = bus.rpc(
            base.ENGINE_SERVICE_ID,
            'persistent_create_policy_with_rules',
            {'policy_rules_obj': {
                "name": policy_name,
                "kind": "nonrecursive",
                "rules": rules}})
        return policy_metadata
    except exception.CongressException as err:
        LOG.error(err)
        return None
