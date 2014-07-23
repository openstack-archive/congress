===============================
Congress
===============================

Congress: The open policy framework for the cloud.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/congress


0. Install requirements.

- python 2.7 or above
https://www.python.org/download/releases/2.7/

- pip
https://pip.pypa.io/en/latest/installing.html

- java
http://java.com


1. Setup Congress

cd /path/to/congress
sudo python setup.py develop


2. Run the unit tests

cd /path/to/congress

./run_tests.sh -N

OR

tox -epy27

3. Run the API server:

cd /path/to/congress
./bin/congress-server --config-file etc/congress.conf.sample


4. Read docs

Open /path/to/congress/doc/html/index.html in a browser

