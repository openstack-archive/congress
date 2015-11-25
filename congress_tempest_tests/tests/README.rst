====================
Tempest Integration
====================

This directory contains Tempest tests to cover Congress project.

To list all Congress tempest cases, go to tempest directory, then run::

    $ testr list-tests congress

To run only these tests in tempest, go to tempest directory, then run::

    $ ./run_tempest.sh -N -- congress

To run a single test case, go to tempest directory, then run with test case name, e.g.::

    $ ./run_tempest.sh -N -- congress_tempest_tests.tests.scenario.test_congress_basic_ops.TestPolicyBasicOps.test_policy_basic_op

Alternatively, to run congress tempest plugin tests using tox, go to tempest directory, then run::

    $ tox -eall-plugin congress

And, to run a specific test::

    $ tox -eall-plugin congress_tempest_tests.tests.scenario.test_congress_basic_ops.TestPolicyBasicOps.test_policy_basic_op
