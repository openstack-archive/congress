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
from oslo.vmware import api
from oslo.vmware import vim_util

from congress.datasources.datasource_driver import DataSourceDriver
from congress.datasources import datasource_utils
from congress.openstack.common import log as logging


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance.

    """

    return VCenterDriver(name, keys, inbox, datapath, args)


class VCenterDriver(DataSourceDriver):
    HOSTS = "hosts"
    HOST_DNS = "host.DNS_IPs"
    HOST_PNICS = "host.PNICs"
    HOST_VNICS = "host.VNICs"
    VMS = "vms"

    value_trans = {'translation-type': 'VALUE'}

    vms_translator = {
        'translation-type': 'HDICT',
        'table-name': VMS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'uuid', 'translator': value_trans},
             {'fieldname': 'host_uuid', 'translator': value_trans},
             {'fieldname': 'pathName', 'translator': value_trans},
             {'fieldname': 'status', 'translator': value_trans},
             {'fieldname': 'CpuDemand', 'translator': value_trans},
             {'fieldname': 'CpuUsage', 'translator': value_trans},
             {'fieldname': 'memorySizeMB', 'translator': value_trans},
             {'fieldname': 'MemoryUsage', 'translator': value_trans},
             {'fieldname': 'committedStorage', 'translator': value_trans},
             {'fieldname': 'uncommittedStorage', 'translator': value_trans},
             {'fieldname': 'annotation', 'translator': value_trans})}

    pnic_translator = {
        'translation-type': 'HDICT',
        'table-name': HOST_PNICS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'host_uuid', 'translator': value_trans},
             {'fieldname': 'device', 'translator': value_trans},
             {'fieldname': 'mac', 'translator': value_trans},
             {'fieldname': 'ipAddress', 'translator': value_trans},
             {'fieldname': 'subnetMask', 'translator': value_trans})}

    vnic_translator = {
        'translation-type': 'HDICT',
        'table-name': HOST_VNICS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'host_uuid', 'translator': value_trans},
             {'fieldname': 'device', 'translator': value_trans},
             {'fieldname': 'mac', 'translator': value_trans},
             {'fieldname': 'portgroup', 'translator': value_trans},
             {'fieldname': 'ipAddress', 'translator': value_trans},
             {'fieldname': 'subnetMask', 'translator': value_trans})}

    hosts_translator = {
        'translation-type': 'HDICT',
        'table-name': HOSTS,
        'selector-type': 'DICT_SELECTOR',
        'field-translators':
            ({'fieldname': 'name', 'translator': value_trans},
             {'fieldname': 'uuid', 'translator': value_trans},
             {'fieldname': HOST_DNS, 'col': 'Host:DNS_id',
              'translator': {'translation-type': 'LIST',
                             'table-name': HOST_DNS,
                             'id-col': 'Host:DNS_id',
                             'val-col': 'DNS_IPs',
                             'translator': value_trans}})}

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None,
                 session=None):
        if args is None:
            args = self.empty_credentials()
        else:
            args['tenant_name'] = None
        super(VCenterDriver, self).__init__(name, keys, inbox, datapath, args)
        self.register_translator(VCenterDriver.hosts_translator)
        self.register_translator(VCenterDriver.pnic_translator)
        self.register_translator(VCenterDriver.vnic_translator)
        self.register_translator(VCenterDriver.vms_translator)
        try:
            self.max_VMs = int(args['max_vms'])
        except (KeyError, ValueError):
            LOG.warning("max_vms has not been configured in "
                        "datasources.conf, defaulting to 999.")
            self.max_VMs = 999
        try:
            self.max_Hosts = int(args['max_hosts'])
        except (KeyError, ValueError):
            LOG.warning("max_hosts has not been configured in "
                        "datasources.conf, defaulting to 999.")
            self.max_Hosts = 999
        self.raw_state = {}
        self.creds = datasource_utils.get_credentials(name, args)
        if session is None:
            self.session = api.VMwareAPISession(self.creds['auth_url'],
                                                self.creds['username'],
                                                self.creds['password'],
                                                10, 1,
                                                create_session=True)
        self.initialized = True

    def update_from_datasource(self):
        """Called when it is time to pull new data from this datasource.

        Pulls lists of objects from vCenter, if the data does not match
        the correspondig table in the driver's raw state or has not yet been
        added to the state, the driver calls methods to parse this data.
        """

        rawHosts = self.get_hosts()
        if (self.HOSTS not in self.raw_state or
           rawHosts != self.raw_state[self.HOSTS]):
            self._translate_hosts(rawHosts)
            self.raw_state[self.HOSTS] = rawHosts
        else:
            self.hosts = self.state[self.HOSTS]
            self.pnics = self.state[self.HOST_PNICS]
            self.nics = self.state[self.HOST_VNICS]

        rawVMs = self.get_vms()
        if (self.VMS not in self.raw_state or
           rawVMs != self.raw_state[self.VMS]):
            self._translate_vms(rawVMs)
            self.raw_state[self.VMS] = rawVMs
        else:
            self.vms = self.state[self.VMS]

    def _translate_hosts(self, rawhosts):
        """Translate the host data from vCenter

        First the raw host data aquired from vCenter is parsed and organized
        into a simple format that can be read by congress translators. This
        creates three lists, hosts, pnics and vnics. These lists are then
        parsed by congress translators to create tables.
        """

        hosts = []
        pnics = []
        vnics = []
        for host in rawhosts['objects']:
            h = {}
            h['vCenter_id'] = host.obj['value']
            for prop in host['propSet']:
                if prop.name == "hardware.systemInfo.uuid":
                    h['uuid'] = prop.val
                    break
            for prop in host['propSet']:
                if prop.name == "name":
                    h['name'] = prop.val
                    continue
                if prop.name == "config.network.dnsConfig.address":
                    try:
                        h[self.HOST_DNS] = prop.val.string
                    except AttributeError:
                        h[self.HOST_DNS] = ["No DNS IP adddresses configured"]
                    continue
                if prop.name == "config.network.pnic":
                    for pnic in prop.val.PhysicalNic:
                        p = {}
                        p['host_uuid'] = h['uuid']
                        p['mac'] = pnic['mac']
                        p['device'] = pnic['device']
                        p['ipAddress'] = pnic['spec']['ip']['ipAddress']
                        p['subnetMask'] = pnic['spec']['ip']['subnetMask']
                        pnics.append(p)
                if prop.name == "config.network.vnic":
                    for vnic in prop.val.HostVirtualNic:
                        v = {}
                        v['host_uuid'] = h['uuid']
                        v['device'] = vnic['device']
                        v['portgroup'] = vnic['portgroup']
                        v['mac'] = vnic['spec']['mac']
                        v['ipAddress'] = vnic['spec']['ip']['ipAddress']
                        v['subnetMask'] = vnic['spec']['ip']['subnetMask']
                        vnics.append(v)
            hosts.append(h)
        row_data = VCenterDriver.convert_objs(hosts,
                                              VCenterDriver.hosts_translator)
        host_tables = (self.HOSTS, self.HOST_DNS)
        for table in host_tables:
            self.state[table] = set()
        for table, row in row_data:
            assert table in host_tables
            self.state[table].add(row)
        self.hosts = hosts

        row_data = VCenterDriver.convert_objs(pnics,
                                              VCenterDriver.pnic_translator)
        self.state[self.HOST_PNICS] = set()
        for table, row in row_data:
            assert table == self.HOST_PNICS
            self.state[table].add(row)
        self.pnics = pnics

        row_data = VCenterDriver.convert_objs(vnics,
                                              VCenterDriver.vnic_translator)
        self.state[self.HOST_VNICS] = set()
        for table, row in row_data:
            assert table == self.HOST_VNICS
            self.state[table].add(row)
        self.vnics = vnics

    def _translate_vms(self, rawvms):
        """Translate the VM data from vCenter

        First the raw VM data aquired from vCenter is parsed and organized
        into a simple format that can be read by congress translators. This
        is a single list named vms that is then parsed by a congress
        translator to create the vms table.
        """

        vms = []
        for vm in rawvms['objects']:
            v = {}
            for prop in vm['propSet']:
                if prop.name == "name":
                    v['name'] = prop.val
                    continue
                if prop.name == "config.uuid":
                    v['uuid'] = prop.val
                    continue
                if prop.name == "config.annotation":
                    v['annotation'] = prop.val
                    continue
                if prop.name == "summary.config.vmPathName":
                    v['pathName'] = prop.val
                    continue
                if prop.name == "summary.config.memorySizeMB":
                    v['memorySizeMB'] = prop.val
                    continue
                if prop.name == "summary.quickStats":
                    v['MemoryUsage'] = prop.val['guestMemoryUsage']
                    v['CpuDemand'] = prop.val['overallCpuDemand']
                    v['CpuUsage'] = prop.val['overallCpuUsage']
                    continue
                if prop.name == "summary.overallStatus":
                    v['status'] = prop.val
                if prop.name == "summary.storage":
                    v['committedStorage'] = prop.val['committed']
                    v['uncommittedStorage'] = prop.val['uncommitted']
                    continue
                if prop.name == 'runtime.host':
                    for host in self.hosts:
                        if host['vCenter_id'] == prop.val['value']:
                            v['host_uuid'] = host['uuid']
                            continue
                        continue
            vms.append(v)
        row_data = VCenterDriver.convert_objs(vms,
                                              VCenterDriver.vms_translator)
        self.state[self.VMS] = set()
        for table, row in row_data:
            assert table == self.VMS
            self.state[table].add(row)
        self.vms = vms

    def get_hosts(self):
        """Called to pull host data from vCenter

        """

        dataFields = ['name',
                      'hardware.systemInfo.uuid',
                      'config.network.dnsConfig.address',
                      'config.network.pnic',
                      'config.network.vnic']
        return self.session.invoke_api(vim_util, 'get_objects',
                                       self.session.vim, 'HostSystem',
                                       self.max_Hosts, dataFields)

    def get_vms(self):
        """Called to pull VM data from vCenter

        """

        dataFields = ['name',
                      'config.uuid',
                      'config.annotation',
                      'summary.config.vmPathName',
                      'runtime.host',
                      'summary.config.memorySizeMB',
                      'summary.quickStats',
                      'summary.overallStatus',
                      'summary.storage']
        return self.session.invoke_api(vim_util, 'get_objects',
                                       self.session.vim, 'VirtualMachine',
                                       self.max_VMs, dataFields)
