# Copyright (c) 2016 NTT All rights reserved.
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

import mock

from congress.datasources import doctor_driver
from congress.tests import base


class TestDoctorDriver(base.TestCase):

    def setUp(self):
        super(TestDoctorDriver, self).setUp()
        self.doctor = doctor_driver.DoctorDriver('test-doctor')

    def numbered_string(self, string, number):
        return string + str(number)

    def generate_events_objects(self, row_number):
        objects = []
        for i in range(0, row_number):
            obj = {
                "id": self.numbered_string('id', i),
                "time": self.numbered_string('time', i),
                "type": self.numbered_string('type', i),
                "details": {
                    "hostname": self.numbered_string('hostname', i),
                    "status": self.numbered_string('status', i),
                    "monitor": self.numbered_string('monitor', i),
                    "monitor_event_id": self.numbered_string('event_id', i),
                    }
                }
            objects.append(obj)
        return objects

    @mock.patch.object(doctor_driver.DoctorDriver, 'publish')
    def test_events_table(self, mocked_publish):
        objs = self.generate_events_objects(3)
        self.doctor.update_entire_data('events', objs)

        self.assertEqual(3, len(self.doctor.state['events']))

        # change elements in state['events'] set to list and sort by id
        sorted_state = sorted(list(self.doctor.state['events']),
                              key=lambda x: x[0])
        for i, row in enumerate(sorted_state):
            self.assertEqual(self.numbered_string('id', i), row[0])
            self.assertEqual(self.numbered_string('time', i), row[1])
            self.assertEqual(self.numbered_string('type', i), row[2])
            self.assertEqual(self.numbered_string('hostname', i), row[3])
            self.assertEqual(self.numbered_string('status', i), row[4])
            self.assertEqual(self.numbered_string('monitor', i), row[5])
            self.assertEqual(self.numbered_string('event_id', i), row[6])
