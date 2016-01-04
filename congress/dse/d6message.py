# Copyright 2014 Plexxi, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import uuid


class d6msg(object):
    def __init__(self,
                 key="",
                 replyTo="",
                 correlationId="",
                 type="",
                 dataindex="",
                 body={},
                 srcmsg={}):

        self.header = {}

        self.body = body

        self.replyTo = replyTo
        self.type = type

        if srcmsg:
            self.key = srcmsg.replyTo
            self.correlationId = srcmsg.correlationId
            self.header['dataindex'] = srcmsg.header['dataindex']
        else:
            self.key = key
            self.header['dataindex'] = dataindex
            if correlationId:
                self.correlationId = correlationId
            else:
                newuuid = uuid.uuid4()
                self.correlationId = str(newuuid)

    def __str__(self):
        return ("<to:{}, from:{}, corrId:{}, type:{}, dataindex:{}, "
                "body:{}>").format(
                    self.key, self.replyTo, self.correlationId, self.type,
                    self.header['dataindex'], str(self.body))
