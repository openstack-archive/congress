#!/usr/bin/env python
# Copyright (c) 2013 VMware, Inc. All rights reserved.
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

import logging
import os.path
import policy.runtime as runtime
import time


def source_path():
    x = os.path.realpath(__file__)
    x, y = os.path.split(x)  # drop "helper.py"
    x, y = os.path.split(x)  # drop "tests"
    return x


def data_module_path(file):
    """Return path to dataservice module with given FILEname."""
    path = source_path()
    path = os.path.join(path, "datasources")
    path = os.path.join(path, file)
    return path


def policy_module_path():
    """Return path to policy engine module."""
    path = source_path()
    path = os.path.join(path, "policy")
    path = os.path.join(path, "dsepolicy.py")
    return path


def api_module_path():
    """Return path to policy engine module."""
    path = source_path()
    path = os.path.join(path, "datasources")
    path = os.path.join(path, "test_driver.py")
    return path


def pause():
    """Timeout so other threads can run."""
    time.sleep(1)


def db_equal(actual_string, correct_string):
    """Given two strings representing data theories,
    check if they are the same.
    """
    actual = runtime.string_to_database(actual_string)
    correct = runtime.string_to_database(correct_string)
    return check_db_diffs(actual, correct)


def check_db_diffs(actual, correct):
    extra = actual - correct
    missing = correct - actual
    extra = [e for e in extra if not e[0].startswith("___")]
    missing = [m for m in missing if not m[0].startswith("___")]
    output_diffs(extra, missing, actual=actual)
    return len(extra) == 0 and len(missing) == 0


def output_diffs(extra, missing, actual=None):
    if len(extra) > 0:
        logging.debug("Extra tuples")
        logging.debug(", ".join([str(x) for x in extra]))
    if len(missing) > 0:
        logging.debug("Missing tuples")
        logging.debug(", ".join([str(x) for x in missing]))
    if len(extra) > 0 or len(missing) > 0:
        logging.debug("Resulting database: {}".format(str(actual)))
