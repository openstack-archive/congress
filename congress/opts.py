# Copyright 2015 Huawei.
# All Rights Reserved.
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

import itertools

import congress.common.config
import congress.dse2.dse_node
import congress.exception
import congress.utils


def list_opts():
    return [
        ('DEFAULT',
         itertools.chain(
             congress.common.config.core_opts,
             congress.utils.utils_opts,
             congress.exception.exc_log_opts,
         )),
        ('dse', congress.common.config.dse_opts)
    ]
