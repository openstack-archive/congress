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

import os.path
import time

from congress.openstack.common import log as logging
from congress.policy import compile
from congress.policy import runtime
from congress.policy import unify


LOG = logging.getLogger(__name__)


def root_path():
    """Return path to root of source code."""
    x = os.path.realpath(__file__)
    x, y = os.path.split(x)  # drop "helper.py"
    x, y = os.path.split(x)  # drop "tests"
    x, y = os.path.split(x)  # drop "congress"
    return x


def source_path():
    """Return path to root of source code."""
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
    """Return path to api module."""
    path = source_path()
    path = os.path.join(path, "datasources")
    path = os.path.join(path, "test_driver.py")
    return path


def test_path():
    """Return path to root of top-level tests."""
    path = source_path()
    path = os.path.join(path, "tests")
    return path


def datasource_config_path():
    """Return path to configuration info for datasources."""
    path = test_path()
    path = os.path.join(path, "datasources.conf")
    return path


def state_path():
    """Return path to policy logs for testing."""
    path = test_path()
    path = os.path.join(path, "snapshot")
    return path


def datasource_openstack_args():
    """Return basic args for creating an openstack datasource."""
    return {'username': '',
            'password': '',
            'auth_url': '',
            'tenant_name': ''}


def pause(factor=1):
    """Timeout so other threads can run."""
    time.sleep(factor * 1)


def datalog_same(actual_code, correct_code, msg=None):
    return datalog_equal(
        actual_code, correct_code, msg=msg,
        equal=lambda x, y: unify.same(x, y) is not None)


def datalog_equal(actual_code, correct_code,
                  msg=None, equal=None, module_schemas=None):
    """Check if the strings given by actual_code
    and CORRECT_CODE represent the same datalog.
    """
    def minus(iter1, iter2, invert=False):
        extra = []
        for i1 in iter1:
            found = False
            for i2 in iter2:
                # for asymmetric equality checks
                if invert:
                    test_result = equal(i2, i1)
                else:
                    test_result = equal(i1, i2)
                if test_result:
                    found = True
                    break
            if not found:
                extra.append(i1)
        return extra
    if equal is None:
        equal = lambda x, y: x == y
    LOG.debug("** Checking equality: {} **".format(msg))
    actual = compile.parse(actual_code, module_schemas=module_schemas)
    correct = compile.parse(correct_code, module_schemas=module_schemas)
    extra = minus(actual, correct)
    # in case EQUAL is asymmetric, always supply actual as the first arg
    #   and set INVERT to true
    missing = minus(correct, actual, invert=True)
    output_diffs(extra, missing, msg)
    LOG.debug("** Finished equality: {} **".format(msg))
    return len(extra) == 0 and len(missing) == 0


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
        print("Extra tuples")
        print(", ".join([str(x) for x in extra]))
    if len(missing) > 0:
        print("Missing tuples")
        print(", ".join([str(x) for x in missing]))
    if len(extra) > 0 or len(missing) > 0:
        print("Resulting database: {}".format(str(actual)))


def str2form(formula_string, module_schemas=None):
    return compile.parse1(formula_string, module_schemas=module_schemas)


def str2pol(policy_string, module_schemas=None):
    return compile.parse(policy_string, module_schemas=module_schemas)


def pol2str(policy):
    return " ".join(str(x) for x in policy)


def form2str(formula):
    return str(formula)
