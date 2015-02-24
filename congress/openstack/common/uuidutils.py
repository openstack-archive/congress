# Copyright (c) 2012 Intel Corporation.
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

"""
UUID related utilities and helper functions.
"""

import uuid
import re


def generate_uuid():
    return str(uuid.uuid4())


def is_uuid_like(val):
    """Returns validation of a value as a UUID.

    For our purposes, a UUID is a canonical form string:
    aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa
    :param val: val string can be with or without dash
    """
    try:
        uuid_str = str(uuid.UUID(val))
        regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?' +
            '[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
        match = regex.match(uuid_str)
        if match:
            return True
        else:
            return False
    except (TypeError, ValueError, AttributeError):
        return False
