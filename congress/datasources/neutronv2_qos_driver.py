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
import neutronclient.v2_0.client
from oslo_log import log as logging

from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils

LOG = logging.getLogger(__name__)


class NeutronV2QosDriver(datasource_driver.PollingDataSourceDriver):

    PORTS = 'ports'
    QOS_POLICY_PORT_BINDINGS = 'qos_policy_port_bindings'
    QOS_POLICIES = 'policies'
    QOS_RULES = 'rules'

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    ports_qos_policies_translator = {
        'translation-type': 'LIST',
        'table-name': QOS_POLICY_PORT_BINDINGS,
        'parent-key': 'id',
        'parent-col-name': 'port_id',
        'parent-key-desc': 'UUID of port',
        'val-col': 'qos_policy_id',
        'val-col-desc': 'UUID of qos policy',
        'translator': value_trans}

    ports_translator = {
        'translation-type': 'HDICT',
        'table-name': PORTS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'UUID of port',
              'translator': value_trans},
             {'fieldname': 'qos_policies',
              'translator': ports_qos_policies_translator})}

    qos_rules_translator = {
        'translation-type': 'HDICT',
        'table-name': QOS_RULES,
        'parent-key': 'id',
        'parent-col-name': 'qos_policy_id',
        'parent-key-desc': 'uuid of qos policy',
        'selector-type': 'DICT_SELECTOR',
        'in-list': True,
        'field-translators':
            ({'fieldname': 'id', 'desc': 'The UUID for the QoS minimum'
                                         'bandwidth rule translator',
              'translator': value_trans},
             {'fieldname': 'min_kbps', 'desc': 'min_kbps bandwidth '
                                               'limit rule',
              'translator': value_trans},
             {'fieldname': 'direction', 'desc': 'minimum bandwidth '
                                                'rule direction',
              'translator': value_trans},
             {'fieldname': 'type', 'desc': 'type of qos rule',
              'translator': value_trans},
             {'fieldname': 'dscp_mark', 'desc': 'mark of the dscp rule',
              'translator': value_trans},
             {'fieldname': 'max_burst_kbps', 'desc': 'max_burst_kps limit',
              'translator': value_trans},
             {'fieldname': 'max_kbps', 'desc': 'max_kps bandwidth limit',
              'translator': value_trans})}

    qos_policy_translator = {
        'translation-type': 'HDICT',
        'table-name': QOS_POLICIES,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'desc': 'The UUID for the qos policy',
              'translator': value_trans},
             {'fieldname': 'tenant_id', 'desc': 'Tenant ID',
              'translator': value_trans},
             {'fieldname': 'name', 'desc': 'The qos policy name',
              'translator': value_trans},
             {'fieldname': 'description', 'desc': 'qos policy description',
              'translator': value_trans},
             {'fieldname': 'shared', 'desc': 'The qos policy share',
              'translator': value_trans},
             {'fieldname': 'rules',
              'translator': qos_rules_translator})}

    TRANSLATORS = [ports_translator, qos_policy_translator]

    def __init__(self, name='', args=None):
        super(NeutronV2QosDriver, self).__init__(name, args=args)
        self.creds = args
        session = ds_utils.get_keystone_session(self.creds)
        self.neutron = neutronclient.v2_0.client.Client(session=session)
        self.initialize_update_methods()
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'neutronv2_qos'
        result['description'] = ('Datasource driver that interfaces with QoS '
                                 'extension of '
                                 'OpenStack Networking aka Neutron.')
        result['config'] = ds_utils.get_openstack_required_config()
        result['config']['lazy_tables'] = constants.OPTIONAL
        result['secret'] = ['password']
        return result

    def initialize_update_methods(self):
        ports_method = lambda: self._translate_ports(self.neutron.list_ports())
        self.add_update_method(ports_method, self.ports_translator)
        qos_policy_method = lambda: self._translate_qos_policies(
            self.neutron.list_qos_policies())
        self.add_update_method(qos_policy_method,
                               self.qos_policy_translator)

    @ds_utils.update_state_on_changed(PORTS)
    def _translate_ports(self, obj):
        LOG.debug("ports: %s", obj)
        row_data = NeutronV2QosDriver.convert_objs(obj['ports'],
                                                   self.ports_translator)
        return row_data

    @ds_utils.update_state_on_changed(QOS_POLICIES)
    def _translate_qos_policies(self, obj):
        LOG.debug("qos_policies: %s", obj)
        row_data = NeutronV2QosDriver.convert_objs(obj['policies'],
                                                   self.qos_policy_translator)
        return row_data
