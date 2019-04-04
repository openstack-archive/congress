# Copyright (c) 2019 VMware, Inc. All rights reserved.
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

'''
This module provides a minimal implementation psycopg2.sql features used by
Congress. The purpose is to avoid requiring psycopg2>=2.7 which is not
available in CentOS 7.
'''
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import re


def SQL(input_statement):
    return input_statement


def Identifier(identifier):
    '''Validate and return quoted SQL identifier.'''
    if re.search('^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        return '"' + identifier + '"'
    else:
        raise Exception('Unacceptable SQL identifier: {}'.format(identifier))
