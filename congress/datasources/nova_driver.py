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


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""
    return NovaDriver(name, keys, inbox, datapath, args)


class NovaDriver(DataSourceDriver):
    SERVERS = "servers"
    FLAVORS = "flavors"
    HOSTS = "hosts"
    FLOATING_IPS = "floating_IPs"

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None):
        if args is None:
            args = self.empty_credentials()
        super(NovaDriver, self).__init__(name, keys, inbox, datapath, args)
        if 'client' in args:
            self.nova_client = args['client']
        else:
            self.creds = self.get_nova_credentials_v2(name, args)
            self.nova_client = novaclient.client.Client(**self.creds)

    def update_from_datasource(self):
        self.state = {}
        servers = self.nova_client.servers.list(
            detailed=True, search_opts={"all_tenants": 1})
        self._translate_servers(servers)
        self._translate_flavors(self.nova_client.flavors.list())
        # TODO(thinrichs): debug and re-enable
        # self._translate_hosts(self.nova_client.hosts.list())
        self._translate_floating_ips(self.nova_client.floating_ips.list())

    def get_tuple_names(self):
        return (self.SERVERS, self.FLAVORS, self.HOSTS, self.FLOATING_IPS)

    @classmethod
    def get_schema(cls):
        """Returns a dictionary mapping tablenames to the list of
        column names for that table.  Both tablenames and columnnames
        are strings.
        """
        d = {}
        d[cls.SERVERS] = ("id", "name", "host_id", "status", "tenant_id",
                          "user_id", "image_id", "flavor_id")
        d[cls.FLAVORS] = ("id", "name", "vcpus", "ram", "disk", "ephemeral",
                          "rxtx_factor")
        d[cls.HOSTS] = ("host_name", "service", "zone")
        d[cls.FLOATING_IPS] = ("floating_ip", "id", "ip", "host_id", "pool")
        return d

    def get_nova_credentials_v2(self, name, args):
        creds = self.get_credentials(name, args)
        d = {}
        d['version'] = '2'
        d['username'] = creds['username']
        d['api_key'] = creds['password']
        d['auth_url'] = creds['auth_url']
        d['project_id'] = creds['tenant_name']
        return d

        self.state[self.SERVERS] = set(self.servers)
        self.state[self.FLAVORS] = set(self.flavors)
        self.state[self.HOSTS] = set(self.hosts)
        self.state[self.FLOATING_IPS] = set(self.floating_ips)

    def _translate_servers(self, obj):
        self.state[self.SERVERS] = set()
        for s in obj:
            image = s.image["id"]
            flavor = s.flavor["id"]
            row = (s.id, s.name, s.hostId, s.status, s.tenant_id,
                   s.user_id, image, flavor)
            self.state[self.SERVERS].add(row)

    def _translate_flavors(self, obj):
        self.state[self.FLAVORS] = set()
        for f in obj:
            row = (f.id, f.name, f.vcpus, f.ram, f.disk, f.ephemeral,
                   f.rxtx_factor)
            self.state[self.FLAVORS].add(row)

    def _translate_hosts(self, obj):
        self.state[self.HOSTS] = set()
        for h in obj:
            row = (h.host_name, h.service, h.zone)
            self.state[self.HOSTS].add(row)

    def _translate_floating_ips(self, obj):
        self.state[self.FLOATING_IPS] = set()
        for i in obj:
            row = (i.fixed_ip, i.id, i.ip, i.instance_id, i.pool)
            self.state[self.FLOATING_IPS].add(row)


# Useful to have a main so we can run manual tests easily
#   and see the Input/Output for the mocked Neutron
def main():
    driver = NovaDriver()
    driver.update_from_datasource()
    print "Original api data"
    print str(driver.raw_state)
    print "Resulting state"
    print str(driver.state)


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        raise
