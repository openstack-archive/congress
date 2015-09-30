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
import ironicclient.v1.chassis as IrChassis
import ironicclient.v1.driver as IrDriver
import ironicclient.v1.node as IrNode
import ironicclient.v1.port as IrPort
import mock

from congress.datasources import ironic_driver
from congress.tests import base
from congress.tests import helper


class TestIronicDriver(base.TestCase):

    def setUp(self):
        super(TestIronicDriver, self).setUp()
        self.ironic_client_p = mock.patch("ironicclient.client.get_client")
        self.ironic_client_p.start()

        args = helper.datasource_openstack_args()
        args['poll_time'] = 0
        args['client'] = mock.MagicMock()

        self.driver = ironic_driver.IronicDriver(args=args)

        self.mock_chassis = {"chassis": [
            {"uuid": "89a15e07-5c80-48a4-b440-9c61ddb7e652",
             "extra": {},
             "created_at": "2015-01-13T06:52:01+00:00",
             "updated_at": None,
             "description": "ironic test chassis"}]}

        self.mock_nodes = {"nodes": [
            {"instance_uuid": "2520745f-b4da-4e10-9d32-84451cfa8b33",
             "uuid": "9cf035f0-351c-43d5-8968-f9fe2c41787b",
             "chassis_uuid": "89a15e07-5c80-48a4-b440-9c61ddb7e652",
             "properties": {"memory_mb": "512", "cpu_arch": "x86_64",
                            "local_gb": "10", "cpus": "1"},
             "driver": "pxe_ssh",
             "maintenance": False,
             "console_enabled": False,
             "created_at": "2015-01-13T06:52:02+00:00",
             "updated_at": "2015-02-10T07:55:23+00:00",
             "provision_updated_at": "2015-01-13T07:55:24+00:00",
             "provision_state": "active",
             "power_state": "power on"},
            {"instance_uuid": None,
             "uuid": "7a95ebf5-f213-4427-b669-010438f43e87",
             "chassis_uuid": "89a15e07-5c80-48a4-b440-9c61ddb7e652",
             "properties": {"memory_mb": "512", "cpu_arch": "x86_64",
                            "local_gb": "10", "cpus": "1"},
             "driver": "pxe_ssh",
             "maintenance": False,
             "console_enabled": False,
             "created_at": "2015-01-13T06:52:04+00:00",
             "updated_at": "2015-02-10T07:55:24+00:00",
             "provision_updated_at": None,
             "provision_state": None,
             "power_state": "power off"}]}

        self.mock_ports = {"ports": [
            {"uuid": "43190aae-d5fe-444f-9d50-155fca4bad82",
             "node_uuid": "9cf035f0-351c-43d5-8968-f9fe2c41787b",
             "extra": {"vif_port_id": "9175f72b-5783-4cea-8ae0-55df69fee568"},
             "created_at": "2015-01-13T06:52:03+00:00",
             "updated_at": "2015-01-30T03:17:23+00:00",
             "address": "52:54:00:7f:e7:2e"},
            {"uuid": "49f3205a-db1e-4497-9371-6011ef572981",
             "node_uuid": "7a95ebf5-f213-4427-b669-010438f43e87",
             "extra": {},
             "created_at": "2015-01-13T06:52:05+00:00",
             "updated_at": None,
             "address": "52:54:00:98:f2:4e"}]}

        self.mock_drivers = {"drivers": [
            {"hosts": ["localhost"], "name": "pxe_ssh"},
            {"hosts": ["localhost"], "name": "pxe_ipmitool"},
            {"hosts": ["localhost"], "name": "fake"}]}

        self.expected_state = {
            'drivers': set([
                ('pxe_ipmitool',),
                ('fake',),
                ('pxe_ssh',)]),
            'node_properties': set([
                ('7a95ebf5-f213-4427-b669-010438f43e87',
                 '512', 'x86_64', '10', '1'),
                ('9cf035f0-351c-43d5-8968-f9fe2c41787b',
                 '512', 'x86_64', '10', '1')]),
            'chassises': set([
                ('89a15e07-5c80-48a4-b440-9c61ddb7e652',
                 '2015-01-13T06:52:01+00:00', 'None')]),
            'active_hosts': set([
                ('pxe_ipmitool', 'localhost'),
                ('pxe_ssh', 'localhost'),
                ('fake', 'localhost')]),
            'nodes': set([
                ('9cf035f0-351c-43d5-8968-f9fe2c41787b',
                 '89a15e07-5c80-48a4-b440-9c61ddb7e652',
                 'power on',
                 'False',
                 'pxe_ssh',
                 '2520745f-b4da-4e10-9d32-84451cfa8b33',
                 '2015-01-13T06:52:02+00:00',
                 '2015-01-13T07:55:24+00:00',
                 '2015-02-10T07:55:23+00:00'),
                ('7a95ebf5-f213-4427-b669-010438f43e87',
                 '89a15e07-5c80-48a4-b440-9c61ddb7e652',
                 'power off',
                 'False',
                 'pxe_ssh',
                 'None',
                 '2015-01-13T06:52:04+00:00',
                 'None',
                 '2015-02-10T07:55:24+00:00')]),
            'ports': set([
                ('49f3205a-db1e-4497-9371-6011ef572981',
                 '7a95ebf5-f213-4427-b669-010438f43e87',
                 '52:54:00:98:f2:4e', '',
                 '2015-01-13T06:52:05+00:00', 'None'),
                ('43190aae-d5fe-444f-9d50-155fca4bad82',
                 '9cf035f0-351c-43d5-8968-f9fe2c41787b',
                 '52:54:00:7f:e7:2e',
                 '9175f72b-5783-4cea-8ae0-55df69fee568',
                 '2015-01-13T06:52:03+00:00',
                 '2015-01-30T03:17:23+00:00')])
        }

    def mock_value(self, mock_data, key, obj_class):
        data = mock_data[key]
        return [obj_class(self, res, loaded=True) for res in data if res]

    def test_driver_called(self):
        self.assertIsNotNone(self.driver.ironic_client)

    def test_update_from_datasource(self):
        with base.nested(
            mock.patch.object(self.driver.ironic_client.chassis,
                              "list",
                              return_value=self.mock_value(self.mock_chassis,
                                                           "chassis",
                                                           IrChassis.Chassis)),
            mock.patch.object(self.driver.ironic_client.node,
                              "list",
                              return_value=self.mock_value(self.mock_nodes,
                                                           "nodes",
                                                           IrNode.Node)),
            mock.patch.object(self.driver.ironic_client.port,
                              "list",
                              return_value=self.mock_value(self.mock_ports,
                                                           "ports",
                                                           IrPort.Port)),
            mock.patch.object(self.driver.ironic_client.driver,
                              "list",
                              return_value=self.mock_value(self.mock_drivers,
                                                           "drivers",
                                                           IrDriver.Driver)),
            ) as (self.driver.ironic_client.chassis.list,
                  self.driver.ironic_client.node.list,
                  self.driver.ironic_client.port.list,
                  self.driver.ironic_client.driver.list):
            self.driver.update_from_datasource()
            self.assertEqual(self.expected_state, self.driver.state)

    def test_execute(self):
        class IronicClient(object):
            def __init__(self):
                self.testkey = None

            def updateNode(self, arg1):
                self.testkey = 'arg1=%s' % arg1

        ironic_client = IronicClient()
        self.driver.ironic_client = ironic_client
        api_args = {
            'positional': ['1']
        }
        expected_ans = 'arg1=1'

        self.driver.execute('updateNode', api_args)

        self.assertEqual(expected_ans, ironic_client.testkey)
