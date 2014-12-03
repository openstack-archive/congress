#!/usr/bin/env python
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
import novaclient.client

from congress.datasources.datasource_driver import DataSourceDriver
from congress.datasources import datasource_utils


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return NovaDriver(name, keys, inbox, datapath, args)


class NovaDriver(DataSourceDriver):
    SERVERS = "servers"
    FLAVORS = "flavors"
    HOSTS = "hosts"
    FLOATING_IPS = "floating_IPs"

    # This is the most common per-value translator, so define it once here.
    value_trans = {'translation-type': 'VALUE'}

    def safe_id(x):
        if isinstance(x, basestring):
            return x
        try:
            return x['id']
        except Exception:
            return str(x)

    servers_translator = {
        'translation-type': 'HDICT',
        'table-name': SERVERS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'hostId', 'col': 'host_id',
              'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'tenant_id', 'translator': value_trans},
             {'fieldname': 'user_id', 'translator': value_trans},
             {'fieldname': 'image', 'col': 'image_id',
              'translator': {'translation-type': 'VALUE',
                             'extract-fn': safe_id}},
             {'fieldname': 'flavor', 'col': 'flavor_id',
              'translator': {'translation-type': 'VALUE',
                             'extract-fn': safe_id}})}

    flavors_translator = {
        'translation-type': 'HDICT',
        'table-name': FLAVORS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'vcpus', 'translator': value_trans},
             {'fieldname': 'ram', 'translator': value_trans},
             {'fieldname': 'disk', 'translator': value_trans},
             {'fieldname': 'ephemeral', 'translator': value_trans},
             {'fieldname': 'rxtx_factor', 'translator': value_trans})}

    hosts_translator = {
        'translation-type': 'HDICT',
        'table-name': HOSTS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'host_name', 'translator': value_trans},
             {'fieldname': 'service', 'translator': value_trans},
             {'fieldname': 'zone', 'translator': value_trans})}

    floating_ips_translator = {
        'translation-type': 'HDICT',
        'table-name': FLOATING_IPS,
        'selector-type': 'DOT_SELECTOR',
        'field-translators':
            ({'fieldname': 'fixed_ip', 'translator': value_trans},
             {'fieldname': 'id', 'translator': value_trans},
             {'fieldname': 'ip', 'translator': value_trans},
             {'fieldname': 'instance_id', 'col': 'host_id',
              'translator': value_trans},
             {'fieldname': 'pool', 'translator': value_trans})}

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        super(NovaDriver, self).__init__(name, keys, inbox, datapath, args)
        self.creds = self.get_nova_credentials_v2(name, args)
        self.nova_client = novaclient.client.Client(**self.creds)
        self.register_translator(NovaDriver.servers_translator)
        self.register_translator(NovaDriver.flavors_translator)
        self.register_translator(NovaDriver.hosts_translator)
        self.register_translator(NovaDriver.floating_ips_translator)

    def get_nova_credentials_v2(self, name, args):
        creds = datasource_utils.get_credentials(name, args)
        d = {}
        d['version'] = '2'
        d['username'] = creds['username']
        d['api_key'] = creds['password']
        d['auth_url'] = creds['auth_url']
        d['project_id'] = creds['tenant_name']
        return d

    def update_from_datasource(self):
        self.state = {}
        servers = self.nova_client.servers.list(
            detailed=True, search_opts={"all_tenants": 1})
        self._translate_servers(servers)
        self._translate_flavors(self.nova_client.flavors.list())
        # TODO(thinrichs): debug and re-enable
        # self._translate_hosts(self.nova_client.hosts.list())
        self._translate_floating_ips(self.nova_client.floating_ips.list())

    def _translate_servers(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.servers_translator)
        self.state[self.SERVERS] = set()
        for table, row in row_data:
            assert table == self.SERVERS
            self.state[table].add(row)

    def _translate_flavors(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.flavors_translator)
        self.state[self.FLAVORS] = set()
        for table, row in row_data:
            assert table == self.FLAVORS
            self.state[table].add(row)

    def _translate_hosts(self, obj):
        row_data = NovaDriver.convert_objs(obj, NovaDriver.hosts_translator)
        self.state[self.HOSTS] = set()
        for table, row in row_data:
            assert table == self.HOSTS
            self.state[table].add(row)

    def _translate_floating_ips(self, obj):
        row_data = NovaDriver.convert_objs(obj,
                                           NovaDriver.floating_ips_translator)
        self.state[self.FLOATING_IPS] = set()
        for table, row in row_data:
            assert table == self.FLOATING_IPS
            self.state[table].add(row)


# Useful to have a main so we can run manual tests easily
#   and see the Input/Output for the mocked Neutron
def main():
    print('Schema:')
    print('\n'.join([k + ' ' + str(v)
                     for k, v in NovaDriver.get_schema().items()]))

    driver = NovaDriver()
    driver.update_from_datasource()
    print("Original api data")
    print(str(driver.raw_state))
    print("Resulting state")
    print(str(driver.state))


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        raise
