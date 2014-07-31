.. include:: aliases.rst

.. _readme:

===============================
Congress
===============================

Congress: The open policy framework for the cloud.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/congress


0. Install requirements
=========================
Install the following software, if you haven't already.

* python 2.7 or above: https://www.python.org/download/releases/2.7/

* pip: https://pip.pypa.io/en/latest/installing.html

* java: http://java.com


1. Setup Congress
===================
Clone Congress and run the setup script::

   git clone https://github.com/stackforge/congress.git
   cd congress
   sudo python setup.py develop


2. Run the unit tests (optional)
=================================

Starting from the congress directory, you run all the unit tests in one of two ways: with the run_tests.sh script (which is a little faster) or with the tox script (which runs tests in a virtual environment, which avoids problems with operating system environments)::

    cd /path/to/congress
    ./run_tests.sh -N

OR::

    cd /path/to/congress
    tox -epy27


3. Run the API server
======================

Currently, all the OpenStack services that are connected to Congress must use the same userID and password.  Set the userID and password by editing the file::

    /path/to/congress/congress/datasources/settings.py

To start congress running so that you can send commands over HTTP, execute::

    cd /path/to/congress
    ./bin/congress-server --config-file etc/congress.conf.sample



4. Read docs
======================

Use a web browser to open the file::

    /path/to/congress/doc/html/index.html in a browser

