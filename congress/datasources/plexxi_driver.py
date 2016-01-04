# Copyright (c) 2014 Marist SDN Innovation lab Joint with Plexxi Inc.
# All rights reserved.
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

import json

try:
    from plexxi.core.api.binding import AffinityGroup
    from plexxi.core.api.binding import Job
    from plexxi.core.api.binding import PhysicalPort
    from plexxi.core.api.binding import PlexxiSwitch
    from plexxi.core.api.binding import VirtualizationHost
    from plexxi.core.api.binding import VirtualMachine
    from plexxi.core.api.binding import VirtualSwitch
    from plexxi.core.api.binding import VmwareVirtualMachine
    from plexxi.core.api.session import CoreSession
except ImportError:
    pass

from oslo_config import cfg
from oslo_log import log as logging
import requests

from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.managers import datasource as datasource_mgr

LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance."""

    return PlexxiDriver(name, keys, inbox, datapath, args)


class PlexxiDriver(datasource_driver.PollingDataSourceDriver,
                   datasource_driver.ExecutionDriver):
    HOSTS = "hosts"
    HOST_MACS = HOSTS + '.macs'
    HOST_GUESTS = HOSTS + '.guests'
    VMS = "vms"
    VM_MACS = VMS + '.macs'
    AFFINITIES = "affinities"
    VSWITCHES = "vswitches"
    VSWITCHES_MACS = VSWITCHES + '.macs'
    VSWITCHES_HOSTS = VSWITCHES + '.hosts'
    PLEXXISWITCHES = "plexxiswitches"
    PLEXXISWITCHES_MACS = PLEXXISWITCHES + '.macs'
    PORTS = "ports"
    NETWORKLINKS = "networklinks"

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None,
                 session=None):
        super(PlexxiDriver, self).__init__(name, keys, inbox, datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        self.exchange = session
        self.creds = args
        self.raw_state = {}
        try:
            self.unique_names = self.string_to_bool(args['unique_names'])
        except KeyError:
            LOG.warning("unique_names has not been configured, "
                        "defaulting to False.")
            self.unique_names = False
        port = str(cfg.CONF.bind_port)
        host = str(cfg.CONF.bind_host)
        self.headers = {'content-type': 'application/json'}
        self.name_cooldown = False
        self.api_address = "http://" + host + ":" + port + "/v1"
        self.name_rule_needed = True
        if str(cfg.CONF.auth_strategy) == 'keystone':
            if 'keystone_pass' not in args:
                LOG.error("Keystone is enabled, but a password was not " +
                          "provided. All automated API calls are disabled")
                self.unique_names = False
                self.name_rule_needed = False
            elif 'keystone_user' not in args:
                LOG.error("Keystone is enabled, but a username was not " +
                          "provided. All automated API calls are disabled")
                self.unique_names = False
                self.name_rule_needed = False
            else:
                self.keystone_url = str(cfg.CONF.keystone_authtoken.auth_uri)
                self.keystoneauth()
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'plexxi'
        result['description'] = ('Datasource driver that interfaces with '
                                 'PlexxiCore.')
        result['config'] = {'auth_url': constants.REQUIRED,  # PlexxiCore url
                            'username': constants.REQUIRED,
                            'password': constants.REQUIRED,
                            'poll_time': constants.OPTIONAL,
                            'tenant_name': constants.REQUIRED,
                            'unique_names': constants.OPTIONAL,
                            'keystone_pass': constants.OPTIONAL,
                            'keystone_user': constants.OPTIONAL}
        result['secret'] = ['password']
        return result

    def update_from_datasource(self):
        """Called when it is time to pull new data from this datasource.

        Pulls lists of objects from PlexxiCore, if the data does not match
        the correspondig table in the driver's raw state or has not yet been
        added to the state, the driver calls methods to parse this data.

        Once all data has been updated,sets
        self.state[tablename] = <list of tuples of strings/numbers>
        for every tablename exported by PlexxiCore.
        """

        # Initialize instance variables that get set during update
        self.hosts = []
        self.mac_list = []
        self.guest_list = []
        self.plexxi_switches = []
        self.affinities = []
        self.vswitches = []
        self.vms = []
        self.vm_macs = []
        self.ports = []
        self.network_links = []

        if self.exchange is None:
            self.connect_to_plexxi()

        # Get host data from PlexxiCore
        hosts = VirtualizationHost.getAll(session=self.exchange)
        if (self.HOSTS not in self.state or
           hosts != self.raw_state[self.HOSTS]):
            self._translate_hosts(hosts)
            self.raw_state[self.HOSTS] = hosts
        else:
            self.hosts = self.state[self.HOSTS]
            self.mac_list = self.state[self.HOST_MACS]
            self.guest_list = self.state[self.HOST_GUESTS]

        # Get PlexxiSwitch Data from PlexxiCore
        plexxiswitches = PlexxiSwitch.getAll(session=self.exchange)
        if (self.PLEXXISWITCHES not in self.state or
           plexxiswitches != self.raw_state[self.PLEXXISWITCHES]):
            self._translate_pswitches(plexxiswitches)
            self.raw_state[self.PLEXXISWITCHES] = plexxiswitches
        else:
            self.plexxi_switches = self.state[self.PLEXXISWITCHES]

        # Get affinity data from PlexxiCore
        affinities = AffinityGroup.getAll(session=self.exchange)
        if (self.AFFINITIES not in self.state or
           affinities != self.raw_state[self.AFFINITIES]):
            if AffinityGroup.getCount(session=self.exchange) == 0:
                self.state[self.AFFINITIES] = ['No Affinities found']
            else:
                self._translate_affinites(affinities)
            self.raw_state[self.AFFINITIES] = affinities
        else:
            self.affinties = self.state[self.AFFINITIES]

        # Get vswitch data from PlexxiCore
        vswitches = VirtualSwitch.getAll(session=self.exchange)
        if (self.VSWITCHES not in self.state or
           vswitches != self.raw_state[self.VSWITCHES]):
            self._translate_vswitches(vswitches)
            self.raw_state[self.VSWITCHES] = vswitches
        else:
            self.vswitches = self.state[self.VSWITCHES]

        # Get virtual machine data from PlexxiCore
        vms = VirtualMachine.getAll(session=self.exchange)
        if (self.VMS not in self.state or
           vms != self.raw_state[self.VMS]):
            self._translate_vms(vms)
            self.raw_state[self.VMS] = set(vms)
        else:
            self.vms = self.state[self.VMS]
            self.vm_macs = self.state[self.VMS_MACS]
        # Get port data from PlexxiCore
        ports = PhysicalPort.getAll(session=self.exchange)
        if(self.PORTS not in self.state or
           ports != self.raw_state[self.PORTS]):
            self._translate_ports(ports)
            self.raw_state[self.PORTS] = set(ports)
        else:
            self.ports = self.state[self.PORTS]
            self.network_links = self.state[self.NETWORKLINKS]

        LOG.debug("Setting Plexxi State")
        self.state = {}
        self.state[self.HOSTS] = set(self.hosts)
        self.state[self.HOST_MACS] = set(self.mac_list)
        self.state[self.HOST_GUESTS] = set(self.guest_list)
        self.state[self.PLEXXISWITCHES] = set(self.plexxi_switches)
        self.state[self.PLEXXISWITCHES_MACS] = set(self.ps_macs)
        self.state[self.AFFINITIES] = set(self.affinities)
        self.state[self.VSWITCHES] = set(self.vswitches)
        self.state[self.VSWITCHES_MACS] = set(self.vswitch_macs)
        self.state[self.VSWITCHES_HOSTS] = set(self.vswitch_hosts)
        self.state[self.VMS] = set(self.vms)
        self.state[self.VM_MACS] = set(self.vm_macs)
        self.state[self.PORTS] = set(self.ports)
        self.state[self.NETWORKLINKS] = set(self.network_links)

        # Create Rules
        if self.name_rule_needed is True:
            if self.name_rule_check() is True:
                self.name_rule_create()
            else:
                self.name_rule_needed = False
        # Act on Policy
        if self.unique_names is True:
            if not self.name_cooldown:
                self.name_response()
            else:
                self.name_cooldown = False

    @classmethod
    def get_schema(cls):
        """Creates a table schema for incoming data from PlexxiCore.

        Returns a dictionary map of tablenames corresponding to column names
        for that table. Both tableNames and columnnames are strings.
        """

        d = {}
        d[cls.HOSTS] = ("uuid", "name", "mac_count", "vmcount")
        d[cls.HOST_MACS] = ("Host_uuid", "Mac_Address")
        d[cls.HOST_GUESTS] = ("Host_uuid", "VM_uuid")
        d[cls.VMS] = ("uuid", "name", "host_uuid", "ip", "mac_count")
        d[cls.VM_MACS] = ("vmID", "Mac_Address")
        d[cls.AFFINITIES] = ("uuid", "name")
        d[cls.VSWITCHES] = ("uuid", "host_count", "vnic_count")
        d[cls.VSWITCHES_MACS] = ("vswitch_uuid", "Mac_Address")
        d[cls.VSWITCHES_HOSTS] = ("vswitch_uuid", "hostuuid")
        d[cls.PLEXXISWITCHES] = ("uuid", "ip", "status")
        d[cls.PLEXXISWITCHES_MACS] = ("Switch_uuid", "Mac_Address")
        d[cls.PORTS] = ("uuid", "name")
        d[cls.NETWORKLINKS] = ("uuid", "name", "port_uuid", "start_uuid",
                               "start_name", "stop_uuid", "stop_name")
        return d

    def _translate_hosts(self, hosts):
        """Translates data about Hosts from PlexxiCore for Congress.

        Responsible for the states 'hosts','hosts.macs' and 'hosts.guests'
        """

        row_keys = self.get_column_map(self.HOSTS)
        hostlist = []
        maclist = []
        vm_uuids = []
        for host in hosts:
            row = ['None'] * (max(row_keys.values()) + 1)
            hostID = host.getForeignUuid()
            row[row_keys['uuid']] = hostID
            row[row_keys['name']] = host.getName()
            pnics = host.getPhysicalNetworkInterfaces()
            if pnics:
                for pnic in pnics:
                    mac = str(pnic.getMacAddress())
                    tuple_mac = (hostID, mac)
                    maclist.append(tuple_mac)
            mac_count = len(maclist)
            if (mac_count > 0):
                row[row_keys['mac_count']] = mac_count
            vmCount = host.getVirtualMachineCount()
            row[row_keys['vmcount']] = vmCount
            if vmCount != 0:
                vms = host.getVirtualMachines()
                for vm in vms:
                    tuple_vmid = (hostID, vm.getForeignUuid())
                    vm_uuids.append(tuple_vmid)
            hostlist.append(tuple(row))
        self.hosts = hostlist
        self.mac_list = maclist
        self.guest_list = vm_uuids

    def _translate_pswitches(self, plexxi_switches):
        """Translates data on Plexxi Switches from PlexxiCore for Congress.

        Responsible for state 'Plexxi_swtiches' and 'Plexxi_switches.macs'
        """

        row_keys = self.get_column_map(self.PLEXXISWITCHES)
        pslist = []
        maclist = []
        for switch in plexxi_switches:
            row = ['None'] * (max(row_keys.values()) + 1)
            psuuid = str(switch.getUuid())
            row[row_keys['uuid']] = psuuid
            psip = str(switch.getIpAddress())
            row[row_keys['ip']] = psip
            psstatus = str(switch.getStatus())
            row[row_keys['status']] = psstatus
            pnics = switch.getPhysicalNetworkInterfaces()
            for pnic in pnics:
                mac = str(pnic.getMacAddress())
                macrow = [psuuid, mac]
                maclist.append(tuple(macrow))
            pslist.append(tuple(row))
        self.plexxi_switches = pslist
        self.ps_macs = maclist

    def _translate_affinites(self, affinites):
        """Translates data about affinites from PlexxiCore for Congress.

        Responsible for state 'affinities'
        """

        row_keys = self.get_column_map(self.AFFINITIES)
        affinitylist = []
        for affinity in affinites:
            row = ['None'] * (max(row_keys.values()) + 1)
            uuid = str(affinity.getUuid())
            row[row_keys['uuid']] = uuid
            row[row_keys['name']] = affinity.getName()
            affinitylist.append(tuple(row))
        self.affinities = affinitylist

    def _translate_vswitches(self, vswitches):
        """Translates data about vswitches from PlexxiCore for Congress.

        Responsible for states vswitchlist,vswitch_macs,vswitch_hosts
        """

        # untested
        row_keys = self.get_column_map(self.VSWITCHES)
        vswitchlist = []
        tuple_macs = []
        vswitch_host_list = []
        for vswitch in vswitches:
            row = ['None'] * (max(row_keys.values()) + 1)
            vswitchID = vswitch.getForeignUuid()
            row[row_keys['uuid']] = vswitchID
            vSwitchHosts = vswitch.getVirtualizationHosts()
            try:
                host_count = len(vSwitchHosts)
            except TypeError:
                host_count = 0
            row[row_keys['host_count']] = host_count
            if host_count != 0:
                for host in vSwitchHosts:
                    hostuuid = host.getForeignUuid()
                    hostrow = [vswitchID, hostuuid]
                    vswitch_host_list.append(tuple(hostrow))
            vswitch_vnics = vswitch.getVirtualNetworkInterfaces()
            try:
                vnic_count = len(vswitch_vnics)
            except TypeError:
                vnic_count = 0
            row[row_keys['vnic_count']] = vnic_count
            if vnic_count != 0:
                for vnic in vswitch_vnics:
                    mac = vnic.getMacAddress()
                    macrow = [vswitchID, str(mac)]
                    tuple_macs.append(tuple(macrow))
            vswitchlist.append(tuple(row))
        self.vswitches = vswitchlist
        self.vswitch_macs = tuple_macs
        self.vswitch_hosts = vswitch_host_list

    def _translate_vms(self, vms):
        """Translate data on VMs from PlexxiCore for Congress.

        Responsible for states 'vms' and 'vms.macs'
        """

        row_keys = self.get_column_map(self.VMS)
        vmlist = []
        maclist = []
        for vm in vms:
            row = ['None'] * (max(row_keys.values()) + 1)
            vmID = vm.getForeignUuid()
            row[row_keys['uuid']] = vmID
            vmName = vm.getName()
            row[row_keys['name']] = vmName
            try:
                vmhost = vm.getVirtualizationHost()
                vmhostuuid = vmhost.getForeignUuid()
                row[row_keys['host_uuid']] = vmhostuuid
            except AttributeError:
                LOG.debug("The host for " + vmName + " could not be found")
            vmIP = vm.getIpAddress()
            if vmIP:
                row[row_keys['ip']] = vmIP
            vmVnics = vm.getVirtualNetworkInterfaces()
            mac_count = 0
            for vnic in vmVnics:
                mac = str(vnic.getMacAddress())
                tuple_mac = (vmID, mac)
                maclist.append(tuple_mac)
                mac_count += 1
            row[row_keys['mac_count']] = mac_count
            vmlist.append(tuple(row))
        self.vms = vmlist
        self.vm_macs = maclist

    def _translate_ports(self, ports):
        """Translate data about ports from PlexxiCore for Congress.

        Responsible for states 'ports' and 'ports.links'
        """

        row_keys = self.get_column_map(self.PORTS)
        link_keys = self.get_column_map(self.NETWORKLINKS)
        port_list = []
        link_list = []
        for port in ports:
            row = ['None'] * (max(row_keys.values()) + 1)
            portID = str(port.getUuid())
            row[row_keys['uuid']] = portID
            portName = str(port.getName())
            row[row_keys['name']] = portName
            links = port.getNetworkLinks()
            if links:
                link_keys = self.get_column_map(self.NETWORKLINKS)
                for link in links:
                    link_row = self._translate_network_link(link, link_keys,
                                                            portID)
                    link_list.append(tuple(link_row))
            port_list.append(tuple(row))
        self.ports = port_list
        self.network_links = link_list

    def _translate_network_link(self, link, row_keys, sourcePortUuid):
        """Translates data about network links from PlexxiCore for Congress.

        Subfunction of translate_ports,each  handles a set of network links
        attached to a port. Directly responsible for the state of
        'ports.links'
        """

        row = ['None'] * (max(row_keys.values()) + 1)
        linkID = str(link.getUuid())
        row[row_keys['uuid']] = linkID
        row[row_keys['port_uuid']] = sourcePortUuid
        linkName = str(link.getName())
        row[row_keys['name']] = linkName
        linkStartObj = link.getStartNetworkInterface()
        linkStartName = str(linkStartObj.getName())
        row[row_keys['start_name']] = linkStartName
        linkStartUuid = str(linkStartObj.getUuid())
        row[row_keys['start_uuid']] = linkStartUuid
        linkStopObj = link.getStopNetworkInterface()
        linkStopUuid = str(linkStopObj.getUuid())
        row[row_keys['stop_uuid']] = linkStopUuid
        linkStopName = str(linkStopObj.getName())
        row[row_keys['stop_name']] = linkStopName
        return row

    def string_to_bool(self, string):
        """Used for parsing boolean variables stated in datasources.conf."""

        string = string.strip()
        s = string.lower()
        if s in['true', 'yes', 'on']:
            return True
        else:
            return False

    def connect_to_plexxi(self):
        """Connect to PlexxiCore.

        Create a CoreSession connecting congress to PlexxiCore using
        credentials provided in datasources.conf
        """

        if 'auth_url' not in self.creds:
            LOG.error("Plexxi url not supplied. Could not start Plexxi" +
                      "connection driver")
        if 'username' not in self.creds:
            LOG.error("Plexxi username not supplied. Could not start " +
                      "Plexxi connection driver")
        if 'password' not in self.creds:
            LOG.error("Plexxi password not supplied. Could not start " +
                      "Plexxi connection driver")
        try:
            self.exchange = CoreSession.connect(
                baseUrl=self.creds['auth_url'],
                allowUntrusted=True,
                username=self.creds['username'],
                password=self.creds['password'])
        except requests.exceptions.HTTPError as error:
            if (int(error.response.status_code) == 401 or
                    int(error.response.status_code) == 403):
                msg = ("Incorrect username/password combination. Passed" +
                       "in username was " + self.creds['username'])

                raise Exception(requests.exceptions.HTTPErrror(msg))
            else:
                raise Exception(requests.exceptions.HTTPError(error))

        except requests.exceptions.ConnectionError:
            msg = ("Cannot connect to PlexxiCore at " +
                   self.creds['auth_url'] + " with the username " +
                   self.creds['username'])
            raise Exception(requests.exceptions.ConnectionError(msg))

    def keystoneauth(self):
        """Acquire a keystone auth token for API calls

        Called when congress is running with keystone as the authentication
        method.This provides the driver a keystone token that is then placed
        in the header of API calls made to congress.
        """
        try:
            authreq = {
                "auth": {
                    "tenantName": self.creds['tenant_name'],
                    "passwordCredentials": {
                        "username": self.creds['keystone_user'],
                        "password": self.creds['keystone_pass']
                        }
                    }
                }
            headers = {'content-type': 'application/json',
                       'accept': 'application/json'}
            request = requests.post(url=self.keystone_url+'/v2.0/tokens',
                                    data=json.dumps(authreq),
                                    headers=headers)
            response = request.json()
            token = response['access']['token']['id']
            self.headers['X-Auth-Token'] = token
        except Exception:
            LOG.exception("Could not authenticate with keystone." +
                          "All automated API calls have been disabled")
            self.unique_names = False
            self.name_rule_needed = False

    def name_rule_check(self):
        """Checks to see if a RepeatedNames rule already exists

        This method is used to prevent the driver from recreating additional
        RepeatedNames tables each time congress is restarted.
        """
        try:
            table = requests.get(self.api_address + "/policies/" +
                                 "plexxi/rules",
                                 headers=self.headers)
            result = json.loads(table.text)
            for entry in result['results']:
                if entry['name'] == "RepeatedNames":
                    return False
            return True
        except Exception:
            LOG.exception("An error has occurred when accessing the " +
                          "Congress API.All automated API calls have been " +
                          "disabled.")
            self.unique_names = False
            self.name_rule_needed = False
            return False

    def name_rule_create(self):
        """Creates RepeatedName table for unique names policy.

        The RepeatedName table contains the name and plexxiUuid of
        VMs that have the same name in the Plexxi table and the Nova Table.
        """
        try:
            datasources = datasource_mgr.DataSourceManager.get_datasources()
            for datasource in datasources:
                if datasource['driver'] == 'nova':
                    repeated_name_rule = ('{"rule": "RepeatedName' +
                                          '(vname,pvuuid):-' + self.name +
                                          ':vms(0=pvuuid,1=vname),' +
                                          datasource['name'] +
                                          ':servers(1=vname)",' +
                                          '"name": "RepeatedNames"}')
                    requests.post(url=self.api_address +
                                  '/policies/plexxi/rules',
                                  data=repeated_name_rule,
                                  headers=self.headers)
                    self.name_rule_needed = False
                    break
        except Exception:
            LOG.exception("Could not create Repeated Name table")

    def name_response(self):
        """Checks for any entries in the RepeatedName table.

        For all entries found in the RepeatedName table, the corresponding
        VM will be then prefixed with 'conflict-' in PlexxiCore.
        """

        vmname = False
        vmuuid = False
        json_response = []
        self.name_cooldown = True
        try:
            plexxivms = VmwareVirtualMachine.getAll(session=self.exchange)
            table = requests.get(self.api_address + "/policies/" +
                                 "plexxi/tables/RepeatedName/rows",
                                 headers=self.headers)
            if table.text == "Authentication required":
                self.keystoneauth()
                table = requests.get(self.api_address + "/policies/" +
                                     "plexxi/tables/RepeatedName/rows",
                                     headers=self.headers)
            json_response = json.loads(table.text)

            for row in json_response['results']:
                vmname = row['data'][0]
                vmuuid = row['data'][1]
                if vmname and vmuuid:
                    for plexxivm in plexxivms:
                        if (plexxivm.getForeignUuid() == vmuuid):
                            new_vm_name = "Conflict-" + vmname
                            desc = ("Congress has found a VM with the same " +
                                    "name on the nova network. This vm " +
                                    "will now be renamed to " + new_vm_name)
                            job_name = (" Congress Driver:Changing virtual" +
                                        "machine, " + vmname + "\'s name")
                            changenamejob = Job.create(name=job_name,
                                                       description=desc + ".",
                                                       session=self.exchange)
                            changenamejob.begin()
                            plexxivm.setName(new_vm_name)
                            changenamejob.commit()
                            LOG.info(desc + " in PlexxiCore.")
        except Exception:
            LOG.exception("error in name_response")
