# Copyright (c) 2017 VMware, Inc. All rights reserved.
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

"""Encryption module for handling passwords in Congress."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import io
import os

from cryptography import fernet
from cryptography.fernet import Fernet
from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)

__key = None
__fernet = None


def _get_key_file_path():
    return os.path.join(cfg.CONF.encryption_key_path, 'aes_key')


def key_file_exists():
    return os.path.isfile(_get_key_file_path())


def read_key_from_file():
    with io.open(_get_key_file_path(), 'r', encoding='ascii') as key_file:
        key = str(key_file.read()).encode('ascii')
    return key


def create_new_key_file():
    LOG.debug("Generate new key file")
    dir_path = os.path.dirname(_get_key_file_path())
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path, mode=0o700)  # important: restrictive permissions
    key = Fernet.generate_key()
    # first create file with restrictive permissions, then write key
    # two separate file opens because each version supports
    # permissions and encoding respectively, but neither supports both.
    with os.fdopen(os.open(_get_key_file_path(), os.O_CREAT | os.O_WRONLY,
                           0o600), 'w'):
        pass
    with io.open(_get_key_file_path(), 'w', encoding='ascii') as key_file:
        key_file.write(key.decode('ascii'))
    return key


def initialize_key():
    '''initialize key.'''
    global __key
    global __fernet
    if key_file_exists():
        __key = read_key_from_file()
    else:
        __key = create_new_key_file()

    __fernet = Fernet(__key)


def initialize_if_needed():
    '''initialize key if not already initialized.'''
    global __fernet
    if not __fernet:
        initialize_key()


def encrypt(string):
    initialize_if_needed()
    return __fernet.encrypt(string.encode('utf-8')).decode('utf-8')


class InvalidToken(fernet.InvalidToken):
    pass


def decrypt(string):
    initialize_if_needed()
    try:
        return __fernet.decrypt(string.encode('utf-8')).decode('utf-8')
    except fernet.InvalidToken as exc:
        raise InvalidToken(exc)
