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

import os

from oslo_log import log as logging

from congress.datalog import compile
from congress.datalog import unify
from congress.datalog import utility
from congress.policy_engines import agnostic
from congress.tests import base

LOG = logging.getLogger(__name__)

NREC_THEORY = 'non-recursive theory'
DB_THEORY = 'database'
MAT_THEORY = 'materialized'


# This file contains tests that are likely broken.  But the tests
#   are good ones once we get the underlying data structures fixed.
# TODO(thinrichs): fix tests so they are working again.

class TestRuntime(base.TestCase):

    def prep_runtime(self, code=None, msg=None, target=None):
        # compile source
        if msg is not None:
            LOG.debug(msg)
        if code is None:
            code = ""
        if target is None:
            target = MAT_THEORY
        run = agnostic.Runtime()
        run.theory[NREC_THEORY] = agnostic.NonrecursiveRuleTheory()
        run.theory[DB_THEORY] = agnostic.Database()
        run.theory[MAT_THEORY] = agnostic.MaterializedViewTheory()
        run.debug_mode()
        run.insert(code, target=target)
        return run

    def check_class(self, run, correct_database_code, msg=None):
        """Test MAT_THEORY.

        Check that runtime RUN's MAT_THEORY theory
        has exactly the same contents as CORRECT_DATABASE_CODE.
        """
        self.open(msg)
        db_class = run.theory[MAT_THEORY].database
        # self.showdb(run)
        correct = agnostic.string_to_database(correct_database_code)
        self.check_db_diffs(db_class, correct, msg)
        self.close(msg)

    def check_db(self, run, correct_database_code, msg=None):
        """Test DB_THEORY.

        Check that runtime RUN.theory[DB_THEORY] is
        equal to CORRECT_DATABASE_CODE.
        """
        # extract correct answer from correct_database_code
        self.open(msg)
        correct_database = agnostic.string_to_database(correct_database_code)
        self.check_db_diffs(run.theory[DB_THEORY],
                            correct_database, msg)
        self.close(msg)

    def check_db_diffs(self, actual, correct, msg):
        extra = actual - correct
        missing = correct - actual
        extra = [e for e in extra if not e[0].startswith("___")]
        missing = [m for m in missing if not m[0].startswith("___")]
        self.output_diffs(extra, missing, msg, actual=actual)

    def output_diffs(self, extra, missing, msg, actual=None):
        if len(extra) > 0:
            LOG.debug("Extra tuples")
            LOG.debug(", ".join([str(x) for x in extra]))
        if len(missing) > 0:
            LOG.debug("Missing tuples")
            LOG.debug(", ".join([str(x) for x in missing]))
        if len(extra) > 0 or len(missing) > 0:
            LOG.debug("Resulting database: %s", actual)
        self.assertTrue(len(extra) == 0 and len(missing) == 0, msg)

    def check_equal(self, actual_code, correct_code, msg=None, equal=None):
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
        actual = compile.parse(actual_code)
        correct = compile.parse(correct_code)
        extra = minus(actual, correct)
        # in case EQUAL is asymmetric, always supply actual as the first arg
        missing = minus(correct, actual, invert=True)
        self.output_diffs(extra, missing, msg)
        LOG.debug("** Finished equality: %s **", msg)

    def check_same(self, actual_code, correct_code, msg=None):
        """Checks if ACTUAL_CODE is a variable-renaming of CORRECT_CODE."""
        return self.check_equal(
            actual_code, correct_code, msg=msg,
            equal=lambda x, y: unify.same(x, y) is not None)

    def check_instance(self, actual_code, correct_code, msg=None):
        """Checks if ACTUAL_CODE is an instance of CORRECT_CODE."""
        return self.check_equal(
            actual_code, correct_code, msg=msg,
            equal=lambda x, y: unify.instance(x, y) is not None)

    def check_proofs(self, run, correct, msg=None):
        """Test proofs.

        Check that the proofs stored in runtime RUN are exactly
        those in CORRECT.
        """
        # example
        # check_proofs(run, {'q': {(1,):
        #              Database.ProofCollection([{'x': 1, 'y': 2}])}})

        errs = []
        checked_tables = set()
        for table in run.database.table_names():
            if table in correct:
                checked_tables.add(table)
                for dbtuple in run.database[table]:
                    if dbtuple.tuple in correct[table]:
                        if dbtuple.proofs != correct[table][dbtuple.tuple]:
                            errs.append(
                                "For table {} tuple {}\n  Computed: {}\n  "
                                "Correct: {}".format(
                                    table, str(dbtuple),
                                    str(dbtuple.proofs),
                                    str(correct[table][dbtuple.tuple])))
        for table in set(correct.keys()) - checked_tables:
            errs.append("Table {} had a correct answer but did not exist "
                        "in the database".format(table))
        if len(errs) > 0:
            # LOG.debug("Check_proof errors:\n%s", "\n".join(errs))
            self.fail("\n".join(errs))

    def showdb(self, run):
        LOG.debug("Resulting DB: %s",
                  run.theory[run.CLASSIFY_THEORY].database |
                  run.theory[run.DATABASE] |
                  run.theory[run.ENFORCEMENT_THEORY].database)

    def insert(self, run, alist, target=None):
        if target is None:
            target = MAT_THEORY
        run.insert(tuple(alist))

    def delete(self, run, alist):
        run.delete(tuple(alist))

    def test_remediation(self):
        """Test remediation computation."""
        def check(action_code, classify_code, query, correct, msg):
            run = self.prep_runtime()
            actth = run.ACTION_THEORY
            clsth = run.CLASSIFY_THEORY
            run.insert(action_code, target=actth)
            run.insert(class_code, target=clsth)
            self.showdb(run)
            self.check_equal(run.remediate(query), correct, msg)

        # simple
        action_code = ('action("a")'
                       'p-(x) :- a(x)')
        class_code = ('err(x) :- p(x)'
                      'p(1)')
        check(action_code, class_code, 'err(1)', 'p-(1) :- a(1)', 'Monadic')

        # rules in action theory
        action_code = ('action("a")'
                       'p-(x) :- q(x)'
                       'q(x) :- a(x)')
        class_code = ('err(x) :- p(x)'
                      'p(1)')
        check(action_code, class_code, 'err(1)', 'p-(1) :- a(1)',
              'Monadic, indirect')

        # multiple conditions in error
        action_code = ('action("a")'
                       'action("b")'
                       'p-(x) :- a(x)'
                       'q-(x) :- b(x)')
        class_code = ('err(x) :- p(x), q(x)'
                      'p(1)'
                      'q(1)')
        check(action_code, class_code, 'err(1)',
              'p-(1) :- a(1)  q-(1) :- b(1)',
              'Monadic, two conditions, two actions')

    def test_access_control(self):
        """Test access control: whether a given action is permitted."""
        def create(ac_code, class_code):
            run = self.prep_runtime()

            acth = run.ACCESSCONTROL_THEORY
            permitted, errors = run.insert(ac_code, target=acth)
            self.assertTrue(permitted,
                            "Error in access control policy: {}".format(
                                utility.iterstr(errors)))

            clsth = run.CLASSIFY_THEORY
            permitted, errors = run.insert(class_code, target=clsth)
            self.assertTrue(permitted, "Error in classifier policy: {}".format(
                utility.iterstr(errors)))
            return run

        def check_true(run, query, support='', msg=None):
            result = run.access_control(query, support)
            self.assertTrue(result,
                            "Error in access control test {}".format(msg))

        def check_false(run, query, support='', msg=None):
            result = run.access_control(query, support)
            self.assertFalse(result,
                             "Error in access control test {}".format(msg))

        # Only checking basic I/O interface for the access_control request.
        # Basic inference algorithms are tested elsewhere.

        # Simple
        ac_code = ('action(x) :- q(x)')
        classify_code = 'q(2)'
        run = create(ac_code, classify_code)
        check_true(run, "action(2)", msg="Simple true action")
        check_false(run, "action(1)", msg="Simple false action")

        # Options
        ac_code = ('action(x, y) :- q(x), options:value(y, "name", name), '
                   'r(name)')
        classify_code = 'q(2) r("alice")'
        run = create(ac_code, classify_code)
        check_true(run, 'action(2,18)', 'options:value(18, "name", "alice")',
                   msg="Single option true")
        check_false(run, 'action(2,18)', 'options:value(18, "name", "bob")',
                    msg="Single option false")

        # Multiple Options
        ac_code = ('action(x, y) :- q(x), options:value(y, "name", name), '
                   'r(name), options:value(y, "age", 30)')
        classify_code = 'q(2) r("alice")'
        run = create(ac_code, classify_code)
        check_true(run, 'action(2,18)', 'options:value(18, "name", "alice") '
                   'options:value(18, "age", 30)', msg="Multiple option true")
        check_false(run, 'action(2, 18)', 'options:value(18, "name", "bob") '
                    'options:value(18, "age", 30)',
                    msg="Multiple option false")

    def test_enforcement(self):
        """Test enforcement."""
        def prep_runtime(enforce_theory, action_theory, class_theory):
            run = agnostic.Runtime()
            run.insert(enforce_theory, target=run.ENFORCEMENT_THEORY)
            run.insert(action_theory, target=run.ACTION_THEORY)
            run.insert(class_theory, target=run.CLASSIFY_THEORY)
            return run
        enforce = 'act(x) :- p(x)'
        action = 'action("act")'
        run = prep_runtime(enforce, action, "")
        run.insert('p(1)')
        self.check_equal(run.logger.content(), 'act(1)', 'Insert')
        run.logger.empty()
        run.insert('p(1)')
        self.check_equal(run.logger.content(), '', 'Insert again')
        run.insert('p(2)')
        self.check_equal(run.logger.content(), 'act(2)', 'Insert different')
        run.logger.empty()
        run.delete('p(2)')
        self.check_equal(run.logger.content(), '', 'Delete')

    def test_neutron_actions(self):
        """Test our encoding of the Neutron actions basics by simulation."""
        def check(query, action_sequence, correct, msg):
            actual = run.simulate(query, action_sequence)
            LOG.debug("Simulate results: %s", actual)
            self.check_instance(actual, correct, msg)

        full_path = os.path.realpath(__file__)
        path = os.path.dirname(full_path)
        neutron_path = path + "/../../../examples/neutron.action"
        run = agnostic.Runtime()
        run.debug_mode()
        # load_file does not exist any longer.
        permitted, errs = run.load_file(neutron_path, target=run.ACTION_THEORY)
        if not permitted:
            self.assertTrue(permitted, "Error in Neutron file: {}".format(
                "\n".join([str(x) for x in errs])))
            return

        # Ports
        query = 'neutron:port(x1, x2, x3, x4, x5, x6, x7, x8, x9)'
        acts = 'neutron:create_port("net1", 17), sys:user("tim") :- true'
        correct = ('neutron:port(id, "net1", name, mac, "null",'
                   '"null", z, w, "tim")')
        check(query, acts, correct, 'Simple port creation')

        query = 'neutron:port(x1, x2, x3, x4, x5, x6, x7, x8, x9)'
        # result(uuid): simulation-specific table that holds the results
        #  of the last action invocation
        acts = ('neutron:create_port("net1", 17), sys:user("tim") :- true '
                'neutron:update_port(uuid, 18), sys:user("tim"), '
                '    options:value(18, "name", "tims port") :- result(uuid) ')
        correct = ('neutron:port(id, "net1", "tims port", mac, "null",'
                   '"null", z, w, "tim")')
        check(query, acts, correct, 'Port create, update')

        query = 'neutron:port(x1, x2, x3, x4, x5, x6, x7, x8, x9)'
        # result(uuid): simulation-specific table that holds the results
        #  of the last action invocation
        acts = ('neutron:create_port("net1", 17), sys:user("tim") :- true '
                'neutron:update_port(uuid, 18), sys:user("tim"), '
                '    options:value(18, "name", "tims port") :- result(uuid) '
                'neutron:delete_port(uuid), sys:user("tim")'
                '    :- result(uuid) ')
        correct = ''
        check(query, acts, correct, 'Port create, update, delete')

        # Networks
        query = ('neutron:network(id, name, status, admin_state, shared,'
                 'tenenant_id)')
        acts = 'neutron:create_network(17), sys:user("tim") :- true'
        correct = 'neutron:network(id, "", status, "true", "true", "tim")'
        check(query, acts, correct, 'Simple network creation')

        query = ('neutron:network(id, name, status, admin_state, '
                 'shared, tenenant_id)')
        acts = ('neutron:create_network(17), sys:user("tim") :- true '
                'neutron:update_network(uuid, 18), sys:user("tim"), '
                '  options:value(18, "admin_state", "false") :- result(uuid)')
        correct = 'neutron:network(id, "", status, "false", "true", "tim")'
        check(query, acts, correct, 'Network creation, update')

        query = ('neutron:network(id, name, status, admin_state, shared, '
                 'tenenant_id)')
        acts = ('neutron:create_network(17), sys:user("tim") :- true '
                'neutron:update_network(uuid, 18), sys:user("tim"), '
                '  options:value(18, "admin_state", "false") :- result(uuid)'
                'neutron:delete_network(uuid) :- result(uuid)')
        correct = ''
        check(query, acts, correct, 'Network creation, update')

        # Subnets
        query = ('neutron:subnet(id, name, network_id, '
                 'gateway_ip, ip_version, cidr, enable_dhcp, tenant_id)')
        acts = ('neutron:create_subnet("net1", "10.0.0.1/24", 17), '
                'sys:user("tim") :- true')
        correct = ('neutron:subnet(id, "", "net1", gateway_ip, 4, '
                   '"10.0.0.1/24", "true", "tim")')
        check(query, acts, correct, 'Simple subnet creation')

        query = ('neutron:subnet(id, name, network_id, '
                 'gateway_ip, ip_version, cidr, enable_dhcp, tenant_id)')
        acts = ('neutron:create_subnet("net1", "10.0.0.1/24", 17), '
                'sys:user("tim") :- true '
                'neutron:update_subnet(uuid, 17), sys:user("tim"), '
                '   options:value(17, "enable_dhcp", "false") :- result(uuid)')
        correct = ('neutron:subnet(id, "", "net1", gateway_ip, 4, '
                   '"10.0.0.1/24", "false", "tim")')
        check(query, acts, correct, 'Subnet creation, update')

        query = ('neutron:subnet(id, name, network_id, '
                 'gateway_ip, ip_version, cidr, enable_dhcp, tenant_id)')
        acts = ('neutron:create_subnet("net1", "10.0.0.1/24", 17), '
                'sys:user("tim") :- true '
                'neutron:update_subnet(uuid, 17), sys:user("tim"), '
                '   options:value(17, "enable_dhcp", "false") :- result(uuid)'
                'neutron:delete_subnet(uuid) :- result(uuid)')
        correct = ''
        check(query, acts, correct, 'Subnet creation, update, delete')


def str2form(formula_string):
    return compile.parse1(formula_string)


def str2pol(policy_string):
    return compile.parse(policy_string)


def pol2str(policy):
    return " ".join(str(x) for x in policy)


def form2str(formula):
    return str(formula)
