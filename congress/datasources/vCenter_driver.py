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

from oslo_log import log as logging
from oslo_vmware import api
from oslo_vmware import vim_util

from congress.datasources import constants
from congress.datasources import datasource_driver
from congress.datasources import datasource_utils as ds_utils


LOG = logging.getLogger(__name__)


def d6service(name, keys, inbox, datapath, args):
    """This method is called by d6cage to create a dataservice instance.

    """

    return VCenterDriver(name, keys, inbox, datapath, args)


class VCenterDriver(datasource_driver.PollingDataSourceDriver,
                    datasource_driver.ExecutionDriver):

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

    TRANSLATORS = [hosts_translator, pnic_translator, vnic_translator,
                   vms_translator]

    def __init__(self, name='', keys='', inbox=None, datapath=None, args=None,
                 session=None):
        if args is None:
            args = self.empty_credentials()
        else:
            args['tenant_name'] = None
        super(VCenterDriver, self).__init__(name, keys, inbox, datapath, args)
        datasource_driver.ExecutionDriver.__init__(self)
        try:
            self.max_VMs = int(args['max_vms'])
        except (KeyError, ValueError):
            LOG.warning("max_vms has not been configured, "
                        " defaulting to 999.")
            self.max_VMs = 999
        try:
            self.max_Hosts = int(args['max_hosts'])
        except (KeyError, ValueError):
            LOG.warning("max_hosts has not been configured, "
                        "defaulting to 999.")
            self.max_Hosts = 999
        self.hosts = None
        self.creds = args
        self.session = session
        if session is None:
            self.session = api.VMwareAPISession(self.creds['auth_url'],
                                                self.creds['username'],
                                                self.creds['password'],
                                                10, 1,
                                                create_session=True)
        self._init_end_start_poll()

    @staticmethod
    def get_datasource_info():
        result = {}
        result['id'] = 'vcenter'
        result['description'] = ('Datasource driver that interfaces with '
                                 'vcenter')
        result['config'] = {'auth_url': constants.REQUIRED,
                            'username': constants.REQUIRED,
                            'password': constants.REQUIRED,
                            'poll_time': constants.OPTIONAL,
                            'max_vms': constants.OPTIONAL,
                            'max_hosts': constants.OPTIONAL}
        result['secret'] = ['password']

        return result

    def update_from_datasource(self):
        """Called when it is time to pull new data from this datasource.

        Pulls lists of objects from vCenter, if the data does not match
        the correspondig table in the driver's raw state or has not yet been
        added to the state, the driver calls methods to parse this data.
        """

        hosts, pnics, vnics = self._get_hosts_and_nics()
        self._translate_hosts(hosts)
        self._translate_pnics(pnics)
        self._translate_vnics(vnics)

        vms = self._get_vms()
        self._translate_vms(vms)

    @ds_utils.update_state_on_changed(HOSTS)
    def _translate_hosts(self, hosts):
        """Translate the host data from vCenter."""

        row_data = VCenterDriver.convert_objs(hosts,
                                              VCenterDriver.hosts_translator)
        return row_data

    @ds_utils.update_state_on_changed(HOST_PNICS)
    def _translate_pnics(self, pnics):
        """Translate the host pnics data from vCenter."""

        row_data = VCenterDriver.convert_objs(pnics,
                                              VCenterDriver.pnic_translator)
        return row_data

    @ds_utils.update_state_on_changed(HOST_VNICS)
    def _translate_vnics(self, vnics):
        """Translate the host vnics data from vCenter."""

        row_data = VCenterDriver.convert_objs(vnics,
                                              VCenterDriver.vnic_translator)
        return row_data

    def _get_hosts_and_nics(self):
        """Convert vCenter host object to simple format.

        First the raw host data acquired from vCenter is parsed and
        organized into a simple format that can be read by congress
        translators. This creates three lists, hosts, pnics and vnics.
        These lists are then parsed by congress translators to create tables.
        """
        rawhosts = self._get_hosts_from_vcenter()
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
        # cached the hosts for vms
        self.hosts = hosts
        return hosts, pnics, vnics

    @ds_utils.update_state_on_changed(VMS)
    def _translate_vms(self, vms):
        """Translate the VM data from vCenter."""

        row_data = VCenterDriver.convert_objs(vms,
                                              VCenterDriver.vms_translator)
        return row_data

    def _get_vms(self):
        rawvms = self._get_vms_from_vcenter()
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
        return vms

    def _get_hosts_from_vcenter(self):
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

    def _get_vms_from_vcenter(self):
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

    def execute(self, action, action_args):
        """Overwrite ExecutionDriver.execute()."""
        # action can be written as a method or an API call.
        func = getattr(self, action, None)
        if func and self.is_executable(func):
            func(action_args)
        else:
            self._execute_api(self.session, action, action_args)
