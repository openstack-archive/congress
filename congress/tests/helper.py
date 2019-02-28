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

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
import os

import tenacity
import time

from oslo_config import cfg
from oslo_log import log as logging
from oslo_messaging import conffixture

from congress.datalog import compile
from congress.datalog import unify
from congress.policy_engines import agnostic

from congress.dse2 import dse_node


LOG = logging.getLogger(__name__)

ROOTDIR = os.path.dirname(__file__)
ETCDIR = os.path.join(ROOTDIR, 'etc')

# single, global variable used to ensure different tests from
#  different subclasses of TestCase all can get a unique ID
#  so that the tests do not interact on oslo-messaging
partition_counter = 0


def make_dsenode_new_partition(node_id,
                               messaging_config=None,
                               node_rpc_endpoints=None):
    """Get new DseNode in it's own new DSE partition."""
    messaging_config = messaging_config or generate_messaging_config()
    node_rpc_endpoints = node_rpc_endpoints or []
    return dse_node.DseNode(messaging_config, node_id, node_rpc_endpoints,
                            partition_id=get_new_partition())


def make_dsenode_same_partition(existing,
                                node_id,
                                messaging_config=None,
                                node_rpc_endpoints=None):
    """Get new DseNode in the same DSE partition as existing (node or part)."""
    partition_id = (existing.partition_id if
                    isinstance(existing, dse_node.DseNode) else existing)

    messaging_config = messaging_config or generate_messaging_config()
    node_rpc_endpoints = node_rpc_endpoints or []
    return dse_node.DseNode(
        messaging_config, node_id, node_rpc_endpoints, partition_id)


def get_new_partition():
    """Create a new partition number, unique within each process."""
    global partition_counter
    old = partition_counter
    partition_counter += 1
    return old


def generate_messaging_config():
    mc_fixture = conffixture.ConfFixture(cfg.CONF)
    mc_fixture.conf.transport_url = 'kombu+memory://'
    messaging_config = mc_fixture.conf
    messaging_config.rpc_response_timeout = 10
    return messaging_config


def etcdir(*p):
    return os.path.join(ETCDIR, *p)


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
    path = os.path.join(path, "policy_engines")
    path = os.path.join(path, "agnostic.py")
    return path


def api_module_path():
    """Return path to api module."""
    path = source_path()
    path = os.path.join(path, "datasources")
    path = os.path.join(path, "test_driver.py")
    return path


def test_path(file=None):
    """Return path to root of top-level tests. Joined with file if provided."""
    path = source_path()
    path = os.path.join(path, "tests")
    if file is not None:
        path = os.path.join(path, file)
    return path


def datasource_config_path():
    """Return path to configuration info for datasources."""
    path = test_path()
    path = os.path.join(path, "datasources.conf")
    return path


def datasource_openstack_args():
    """Return basic args for creating an openstack datasource."""
    return {'username': '',
            'password': '',
            'auth_url': '',
            'tenant_name': '',
            'poll_time': 1}


def pause(factor=1):
    """Timeout so other threads can run."""
    time.sleep(factor * 1)


def datalog_same(actual_code, correct_code, msg=None):
    return datalog_equal(
        actual_code, correct_code, msg=msg,
        equal=lambda x, y: unify.same(x, y) is not None)


def datalog_equal(actual_code, correct_code,
                  msg=None, equal=None, theories=None,
                  output_diff=True):
    """Check equality.

    Check if the strings given by actual_code
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

    LOG.debug("** Checking equality: %s **", msg)
    actual = compile.parse(actual_code, theories=theories)
    correct = compile.parse(correct_code, theories=theories)
    extra = minus(actual, correct)
    # in case EQUAL is asymmetric, always supply actual as the first arg
    #   and set INVERT to true
    missing = minus(correct, actual, invert=True)
    if output_diff:
        output_diffs(extra, missing, msg)
    LOG.debug("** Finished equality: %s **", msg)
    is_equal = len(extra) == 0 and len(missing) == 0
    if not is_equal:
        LOG.debug('datalog_equal failed, extras: %s, missing: %s', extra,
                  missing)
    return is_equal


def db_equal(actual_string, correct_string, output_diff=True):
    """Check if two strings representing data theories are the same."""
    actual = agnostic.string_to_database(actual_string)
    correct = agnostic.string_to_database(correct_string)
    return check_db_diffs(actual, correct, output_diff=output_diff)


def check_db_diffs(actual, correct, output_diff=True):
    extra = actual - correct
    missing = correct - actual
    extra = [e for e in extra if not e[0].startswith("___")]
    missing = [m for m in missing if not m[0].startswith("___")]
    if output_diff:
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


def str2form(formula_string, theories=None):
    return compile.parse1(formula_string, theories=theories)


def str2pol(policy_string, theories=None):
    return compile.parse(policy_string, theories=theories)


def pol2str(policy):
    return " ".join(str(x) for x in policy)


def form2str(formula):
    return str(formula)


@tenacity.retry(stop=tenacity.stop_after_attempt(1000),
                wait=tenacity.wait_fixed(0.1))
def retry_check_for_last_message(obj):
    if not hasattr(obj, "last_msg"):
        raise AttributeError("Missing 'last_msg' attribute")


@tenacity.retry(stop=tenacity.stop_after_attempt(1000),
                wait=tenacity.wait_fixed(0.1))
def retry_check_for_message_to_arrive(obj):
    if not hasattr(obj.msg, "body"):
        raise AttributeError("Missing 'body' attribute")


@tenacity.retry(stop=tenacity.stop_after_attempt(1000),
                wait=tenacity.wait_fixed(0.1))
def retry_check_for_message_data(obj, data):
    if not hasattr(obj.msg, "body"):
        raise AttributeError("Missing 'body' attribute")
    if obj.get_msg_data() != data:
        raise TestFailureException("Missing expected data in msg")


@tenacity.retry(stop=tenacity.stop_after_attempt(1000),
                wait=tenacity.wait_fixed(0.1))
def retry_check_nonempty_last_policy_change(obj):
    if not hasattr(obj, "last_policy_change"):
        raise AttributeError("Missing 'last_policy_change' attribute")
    if obj.last_policy_change is None:
        raise TestFailureException("last_policy_change == None")
    if len(obj.last_policy_change) == 0:
        raise TestFailureException("last_policy_change == 0")


@tenacity.retry(stop=tenacity.stop_after_attempt(1000),
                wait=tenacity.wait_fixed(0.1))
def retry_check_empty_last_policy_change(obj):
    if not hasattr(obj, "last_policy_change"):
        raise AttributeError("Missing 'last_policy_change' attribute")
    if len(obj.last_policy_change) != 0:
        raise TestFailureException("last_policy_change != 0")


@tenacity.retry(stop=tenacity.stop_after_attempt(1000),
                wait=tenacity.wait_fixed(0.1))
def retry_check_db_equal(policy, query, correct, target=None):
    if not hasattr(policy, "select"):
        raise AttributeError("Missing 'select' attribute")
    if target is None:
        actual = policy.select(query)
    else:
        actual = policy.select(query, target=target)
    if not db_equal(actual, correct, output_diff=False):
        raise TestFailureException(
            "Query {} produces {}, should produce {}".format(
                str(query), str(actual), str(correct)))


@tenacity.retry(stop=tenacity.stop_after_attempt(1000),
                wait=tenacity.wait_fixed(0.1))
def retry_check_number_of_updates(deepsix, value):
    if not hasattr(deepsix, "number_of_updates"):
        raise AttributeError("Missing 'number_of_updates' attribute")
    if deepsix.number_of_updates != value:
        raise TestFailureException("number_of_updates is {}, not {}".format(
            deepsix.number_of_updates, value))


@tenacity.retry(stop=tenacity.stop_after_attempt(1000),
                wait=tenacity.wait_fixed(0.1))
def retry_check_subscriptions(deepsix, subscription_list):
    if not check_subscriptions(deepsix, subscription_list):
        raise TestFailureException(
            "{} does not have subscription list {}".format(
                deepsix.name, str(subscription_list)))


def check_subscriptions(deepsix, subscription_list):
    """Check subscriptions.

    Check that the instance DEEPSIX is subscribed to all of the
    (key, dataindex) pairs in KEY_DATAINDEX_LIST.  Return True if
    all subscriptions exists; otherwise returns False.
    """
    actual = set([(value.key, value.dataindex)
                  for value in deepsix.subdata.values()])
    correct = set(subscription_list)
    missing = correct - actual
    if missing:
        LOG.debug("Missing key/dataindex subscriptions: %s", missing)
    return not missing


@tenacity.retry(stop=tenacity.stop_after_attempt(1000),
                wait=tenacity.wait_fixed(0.1))
def retry_check_subscribers(deepsix, subscriber_list):
    if not check_subscribers(deepsix, subscriber_list):
        raise TestFailureException(
            "{} does not have subscriber list {}".format(
                deepsix.name, str(subscriber_list)))


@tenacity.retry(stop=tenacity.stop_after_attempt(1000),
                wait=tenacity.wait_fixed(0.1))
def retry_check_no_subscribers(deepsix, subscriber_list):
    """Check that deepsix has none of the subscribers in subscriber_list"""
    if check_subscribers(deepsix, subscriber_list, any_=True):
        raise TestFailureException(
            "{} still has some subscribers in list {}".format(
                deepsix.name, str(subscriber_list)))


def check_subscribers(deepsix, subscriber_list, any_=False):
    """Check subscribers.

    Check that the instance DEEPSIX includes subscriptions for all of
    the (name, dataindex) pairs in SUBSCRIBER_LIST.  Return True if
    all subscribers exist; otherwise returns False.

    If any_=True, then return True if ANY subscribers exist in subscriber_list
    """
    actual = set([(name, pubdata.dataindex)
                  for pubdata in deepsix.pubdata.copy().values()
                  for name in pubdata.subscribers])
    correct = set(subscriber_list)
    missing = correct - actual
    if missing:
        LOG.debug("Missing name/dataindex subscribers: %s", missing)
    if any_:
        return (len(missing) < len(actual))
    return not missing


@tenacity.retry(stop=tenacity.stop_after_attempt(20),
                wait=tenacity.wait_fixed(1))
def retry_check_function_return_value(f, expected_value):
    """Check if function f returns expected key."""
    result = f()
    if result != expected_value:
        raise TestFailureException(
            "Expected value '%s' not received.  "
            "Got %s instead." % (expected_value, result))


@tenacity.retry(stop=tenacity.stop_after_attempt(10),
                wait=tenacity.wait_fixed(0.5))
def retry_check_function_return_value_not_eq(f, value):
    """Check if function f does not return expected value."""
    result = f()
    if result == value:
        raise TestFailureException(
            "Actual value '%s' should be different "
            "from '%s'" % (result, value))


@tenacity.retry(stop=tenacity.stop_after_attempt(10),
                wait=tenacity.wait_fixed(0.5))
def retry_til_exception(expected_exception, f):
    """Check if function f does not return expected value."""
    try:
        val = f()
        raise TestFailureException("No exception thrown; received %s" % val)
    except expected_exception:
        return
    except Exception as e:
        raise TestFailureException("Wrong exception thrown: %s" % e)


@tenacity.retry(stop=tenacity.stop_after_attempt(20),
                wait=tenacity.wait_fixed(1))
def retry_check_function_return_value_table(f, expected_values):
    """Check if function f returns expected table."""
    result = f()
    actual = set(tuple(x) for x in result)
    correct = set(tuple(x) for x in expected_values)
    extra = actual - correct
    missing = correct - actual
    if len(extra) > 0 or len(missing) > 0:
        s = "Actual: %s\nExpected: %s\n" % (result, expected_values)
        if len(extra) > 0:
            s += "Extra: %s\n" % extra
        if len(missing) > 0:
            s += "Missing: %s\n" % missing
        raise TestFailureException(s)


class FakeRequest(object):
    def __init__(self, body):
        self.body = json.dumps(body)


class FakeServiceObj(object):
    def __init__(self):
        self.state = {}


class TestFailureException(Exception):
    """Custom exception thrown on test failure

    Facilitates using assertRaises to check for failure on retry tests
    (generic Exception in assertRaises disallowed by pep8 check/gate)
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


def supported_drivers():
    """Get list of supported drivers by congress"""

    results = [
        {"id": "monasca",
         "description": "Datasource driver that interfaces with monasca."},
        {"id": "plexxi",
         "description": "Datasource driver that interfaces with PlexxiCore."},
        {"id": "doctor",
         "description": "Datasource driver that allows external systems "
                        "to push data in accordance with OPNFV Doctor "
                        "Inspector southbound interface specification."},
        {"id": "aodh",
         "description": "Datasource driver that interfaces with aodh."},
        {"id": "neutronv2_qos",
         "description": "Datasource driver that interfaces with QoS "
                        "extension of OpenStack Networking aka Neutron."},
        {"id": "cloudfoundryv2",
         "description": "Datasource driver that interfaces with cloudfoundry"},
        {"id": "heat",
         "description": "Datasource driver that interfaces with OpenStack "
                        "orchestration aka heat."},
        {"id": "nova",
         "description": "Datasource driver that interfaces with OpenStack "
                        "Compute aka nova."},
        {"id": "murano",
         "description": "Datasource driver that interfaces with murano"},
        {"id": "neutronv2",
         "description": "Datasource driver that interfaces with OpenStack "
                        "Networking aka Neutron."},
        {"id": "swift",
         "description": "Datasource driver that interfaces with swift."},
        {"id": "ironic",
         "description": "Datasource driver that interfaces with OpenStack "
                        "bare metal aka ironic."},
        {"id": "cinder",
         "description": "Datasource driver that interfaces with OpenStack "
                        "cinder."},
        {"id": "fake_datasource",
         "description": "This is a fake driver used for testing"},
        {"id": "config",
         "description": "Datasource driver that allows OS configs retrieval."},
        {"id": "glancev2",
         "description": "Datasource driver that interfaces with OpenStack "
                        "Images aka Glance."},
        {"id": "vcenter",
         "description": "Datasource driver that interfaces with vcenter"},
        {"id": "keystonev3",
         "description": "Datasource driver that interfaces with keystone."},
        {"id": "keystone",
         "description": "Datasource driver that interfaces with keystone."},
        {"id": "mistral",
         "description": "Datasource driver that interfaces with Mistral."},
        {"id": "vitrage",
         "description": "Datasource driver that accepts Vitrage "
                        "webhook alarm notifications."},
        {"id": "monasca_webhook",
         "description": "Datasource driver that accepts Monasca webhook "
                        "alarm notifications."},
        {"id": "tacker",
         "description": "Datasource driver that interfaces with OpenStack "
                        "tacker."}]
    return results
