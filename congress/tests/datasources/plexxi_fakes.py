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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import


class MockAffinity(object):
    def __init__(self, uuid, name):
        self.uuid = uuid
        self.name = name

    def getUuid(self):
        return self.uuid

    def getName(self):
        return self.name


class MockCoreSession(object):
    def __init__(self):
        pass

    def disconnect():
        pass


class MockHost(object):
    def __init__(self, uuid, name, mac_count, pnics):
        self.uuid = uuid
        self.name = name
        self.mac_count = mac_count
        self.pnics = pnics
        self.vms = []

    def addvm(self, vm):
        self.vms.append(vm)

    def getForeignUuid(self):
        return self.uuid

    def getUuid(self):
        return self.uuid

    def getName(self):
        return self.name

    def getPhysicalNetworkInterfaces(self):
        return self.pnics

    def getVirtualMachineCount(self):
        return len(self.vms)

    def getVirtualMachines(self):
        return self.vms


class MockNetworkLink(object):
    def __init__(self, uuid, name, stopint, startint):
        self.uuid = uuid
        self.name = name
        self.startint = startint
        self.stopint = stopint

    def getUuid(self):
        return self.uuid

    def getName(self):
        return self.name

    def getStartNetworkInterface(self):
        return self.startint

    def getStopNetworkInterface(self):
        return self.stopint


class MockNIC(object):
    def __init__(self, uuid, mac):
        self.uuid = uuid
        self.mac = mac

    def getMacAddress(self):
        return self.mac


class MockPort(object):
    def __init__(self, uuid, name, networklinks):
        self.uuid = uuid
        self.name = name
        self.networklinks = networklinks

    def getUuid(self):
        return self.uuid

    def getName(self):
        return self.name

    def getNetworkLinks(self):
        return self.networklinks


class MockSwitch(object):
    def __init__(self, uuid, ip, name, status, pnics):
        self.uuid = uuid
        self.ip = ip
        self.status = status
        self.pnics = pnics
        self.name = name

    def getUuid(self):
        return self.uuid

    def getName(self):
        return self.name

    def getIpAddress(self):
        return self.ip

    def getStatus(self):
        return self.status

    def getPhysicalNetworkInterfaces(self):
        return self.pnics


class MockVM(object):
    def __init__(self, uuid, ip, name, host, vnics):
        self.uuid = uuid
        self.ip = ip
        self.host = host
        self.name = name
        self.vnics = vnics

    def getForeignUuid(self):
        return self.uuid

    def getVirtualizationHost(self):
        return self.host

    def getName(self):
        return self.name

    def getIpAddress(self):
        return self.ip

    def getVirtualNetworkInterfaces(self):
        return self.vnics


class MockVSwitch(object):
    def __init__(self, uuid, hosts, vnics):
        self.uuid = uuid
        self.hosts = hosts
        self.vnics = vnics

    def getForeignUuid(self):
        return self.uuid

    def getVirtualizationHosts(self):
        return self.hosts

    def getVirtualNetworkInterfaces(self):
        return self.vnics
