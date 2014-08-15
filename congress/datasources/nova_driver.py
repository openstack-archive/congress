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
import datetime
import novaclient.client

from congress.datasources.datasource_driver import DataSourceDriver


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice
    instance.  There are a couple of parameters we found useful
    to add to that call, so we included them here instead of
    modifying d6cage (and all the d6cage.createservice calls).
    """
    return NovaDriver(name, keys, inbox, datapath, args)


# TODO(thinrichs): figure out how to move even more of this boilerplate
#   into DataSourceDriver.  E.g. change all the classes to Driver instead of
#   NeutronDriver, NovaDriver, etc. and move the d6instantiate function to
#   DataSourceDriver.
class NovaDriver(DataSourceDriver):
    SERVERS = "servers"
    FLAVORS = "flavors"
    HOSTS = "hosts"
    FLOATING_IPS = "floating_IPs"

    last_updated = -1

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
        self.servers = self._get_tuple_list(
            self.nova_client.servers.list(detailed=True,
                                          search_opts={"all_tenants": 1}),
            self.SERVERS)
        self.flavors = self._get_tuple_list(
            self.nova_client.flavors.list(), self.FLAVORS)
        # TEMP(thinrichs): commented out so I can get demo working
        # self.hosts = self._get_tuple_list(self.nova_client.hosts.list(),
        #                                   self.HOSTS)
        self.hosts = []
        self.floating_ips = self._get_tuple_list(
            self.nova_client.floating_ips.list(), self.FLOATING_IPS)
        self.last_updated = datetime.datetime.now()
        # set state
        # TODO(thinrichs): use self.state everywhere instead of self.servers...
        self.state[self.SERVERS] = set(self.servers)
        self.state[self.FLAVORS] = set(self.flavors)
        self.state[self.HOSTS] = set(self.hosts)
        self.state[self.FLOATING_IPS] = set(self.floating_ips)

    def get_all(self, type):
        if type not in self.state:
            self.update_from_datasource()
        assert type in self.state, "Must choose existing tablename"
        return self.state[type]

    def get_tuple_names(self):
        return (self.SERVERS, self.FLAVORS, self.HOSTS, self.FLOATING_IPS)

    # TODO(thinrichs): figure out right way of returning
    #   meta-data for tables.  Nova and Neutron do this
    #   differently right now.  Would be nice
    #   if _get_tuple_list obeyed the metadata by construction.
    @classmethod
    def get_tuple_metadata(cls, type):
        if type == cls.SERVERS:
            return ("id", "name", "host_id", "status", "tenant_id",
                    "user_id", "image_id", "flavor_id")
        elif type == cls.FLAVORS:
            return ("id", "name", "vcpus", "ram", "disk", "ephemeral",
                    "rxtx_factor")
        elif type == cls.HOSTS:
            return ("host_name", "service", "zone")
        elif type == cls.FLOATING_IPS:
            return ("floating_ip", "id", "ip", "host_id", "pool")
        else:
            return ()

    def get_last_updated_time(self):
        return self.last_updated

    def get_nova_credentials_v2(self, name, args):
        creds = self.get_credentials(name, args)
        d = {}
        d['version'] = '2'
        d['username'] = creds['username']
        d['api_key'] = creds['password']
        d['auth_url'] = creds['auth_url']
        d['project_id'] = creds['tenant_name']
        return d

    def _get_tuple_list(self, obj, type):
        t_list = []
        if type == self.SERVERS:
            for s in obj:
                image = s.image["id"]
                flavor = s.flavor["id"]
                tuple = (s.id, s.name, s.hostId, s.status, s.tenant_id,
                         s.user_id, image, flavor)
                t_list.append(tuple)
        elif type == self.FLAVORS:
            for f in obj:
                tuple = (f.id, f.name, f.vcpus, f.ram, f.disk, f.ephemeral,
                         f.rxtx_factor)
                t_list.append(tuple)
        elif type == self.HOSTS:
            for h in obj:
                tuple = (h.host_name, h.service, h.zone)
                t_list.append(tuple)
        elif type == self.FLOATING_IPS:
            for i in obj:
                tuple = (i.fixed_ip, i.id, i.ip, i.instance_id, i.pool)
                t_list.append(tuple)
        return t_list


def main():
    driver = NovaDriver()
    # logger.setLevel(logging.DEBUG)
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.INFO)
    # # create formatter
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -'
    #                               ' %(message)s')
    # ch.setFormatter(formatter)
    # logger.addHandler(ch)
    print "Last updated: %s" % driver.get_last_updated_time()

    print "Starting Nova Sync Service"
    print "Tuple Names : " + str(driver.get_tuple_names())
    print ("Tuple Metadata - 'servers' : " +
           str(driver.get_tuple_metadata(driver.SERVERS)))
    #sync with the nova service
    driver.update_from_datasource()
    print "Servers: %s" % driver.get_all(driver.SERVERS)
    print "Flavors: %s" % driver.get_all(driver.FLAVORS)
    print "Hosts: %s" % driver.get_all(driver.HOSTS)
    print "Floating IPs: %s" % driver.get_all(driver.FLOATING_IPS)
    print "Last updated: %s" % driver.get_last_updated_time()
    print "Sync completed"

    print "-----------------------------------------"


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        # Let system.exit() calls complete normally
        raise
    except Exception:
        raise
