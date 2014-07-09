===============================
Congress
===============================

Congress: The open policy framework for the cloud.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/congress

1. Compile:

- from the root directory
  make

2. Run the API server:

- from the root directory
  ./bin/congress-server --config-file congress/etc/congress.sample.conf

3. Run the unit tests

- from the root directory

  tox -epy27 or via ./run_test.sh
