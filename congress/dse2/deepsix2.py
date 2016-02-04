# Copyright 2016 Styra, Inc.
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

from oslo_log import log as logging

from congress.dse2.data_service import DataService

LOG = logging.getLogger(__name__)


class deepSix(DataService):
    """A placeholder while we transition to the new arch."""
    def __init__(self, name, keys, inbox=None, dataPath=None):
        DataService.__init__(self, name)
        self.name = name
        self.running = True

    def log_info(self, msg, *args):
        LOG.info(msg, *args)

    def log(self, msg, *args):
        LOG.debug(msg, *args)
