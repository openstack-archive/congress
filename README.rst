.. include:: aliases.rst

.. _readme:

===============================
Congress
===============================

Congress: The open policy framework for the cloud.

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/congress

There are 2 ways to install Congress.

* As part of devstack.  This allows you to run Congress alongside
  live instances of other OpenStack projects like Nova and Neutron.

* Standalone. This allows you to write code and run unit tests,
  without requiring a full devstack installation.


1. Devstack-install
=========================
The contrib/devstack/ directory contains the files necessary to integrate
Congress with devstack.

To install, make sure you have *git* installed.  Then::

    $ git clone https://git.openstack.org/openstack-dev/devstack
     (Or set env variable DEVSTACKDIR to the location to your devstack code)

    $ wget http://git.openstack.org/cgit/stackforge/congress/plain/contrib/devstack/prepare_devstack.sh

    $ chmod u+x prepare_devstack.sh

    $ ./prepare_devstack.sh

Run devstack as normal.  Note: the default data source configuration assumes
the admin password is 'password'::

    $ ./stack.sh


Note: If the miminum localrc file required to run congress with keystone requires:
ENABLED_SERVICES=congress,key,mysql



2. Standalone-install
======================
Install the following software, if you haven't already.

* python 2.7 or above: https://www.python.org/download/releases/2.7/

* pip: https://pip.pypa.io/en/latest/installing.html

* java: http://java.com

* git


Clone Congress::

  $ git clone https://github.com/stackforge/congress.git
  $ cd congress

Run unit tests::

  $ tox -epy27

Read the HTML documentation::

  $ make docs
  Open doc/html/index.html in a browser


