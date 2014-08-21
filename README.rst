.. include:: aliases.rst

.. _readme:

======================================
Congress Introduction and Installation
======================================

1. What is Congress
===================

Congress is an open policy framework for the cloud.  With Congress, a
cloud operator can declare, monitor, enforce, and audit "policy" in a
heterogeneous cloud environment.  Congress get inputs from a cloud's
various cloud services; for example in Openstack, Congress fetches
information about VMs from Nova, and network state from Neutron, etc.
Congress then feeds input data from those services into its policy engine where Congress
verifies that the cloud's actual state abides by the cloud operator's
policies.  Congress is designed to work with **any policy** and
**any cloud service**.

2. Why is Policy Important
==========================

The cloud is a collection of autonomous
services that constantly change the state of the cloud, and it can be
challenging for the cloud operator to know whether the cloud is even
configured correctly.  For example,

* The services are often independent from each other, and do not
  support transactional consistency across services, so a cloud
  management system can change one service (create a VM) without also
  making a necessary change to another service (attach the VM to a
  network).  This can lead to incorrect behavior.

* Other times, we have seen a cloud operator allocate cloud resources
  and then forget to clean them up when the resources are no longer in
  use, effectively leaving garbage around the system and wasting
  resources.

* The desired cloud state can also change over time.  For example, if
  a security vulnerability appears in Linux version X, then all
  machines with version X that were ok in the past are now in an
  undesirable state.  A version number policy would detect all the
  machines in that undesirable state.  This is a trivial example, but
  the more complex the policy, the more helpful a policy system
  becomes.

Congress's job is to help people manage that plethora of state across
all cloud services with a susinct policy language.

3. Using Congress
---------------------

Setting up Congress involves writing policies and configuring Congress
to fetch input data from the cloud services.  The cloud operator
writes policy in the Congress policy language, which receives input
from the cloud services in the form of tables.  The language itself
resembles datalog.  For more detail about the policy language and data
format see policy.rst.

To add a service as an input data source, the cloud operator configures a Congress
"driver", and the driver queries the service.  Congress already
has drivers for several types of service, but if a cloud operator
needs to use an unsupported service, she can write a new driver
without much effort, and probably contribute the driver to the
Congress project so that no one else needs to write the same driver.
(See :ref:`Cloud Services <cloudservices>`)

Finally, when using Congress, the cloud operator will need to address
violations that Congress detects.  Usually, this means fixing the
cloud configuration to abide by the policy.  In the future Congress
will also provide mechanisms to enforce policy (by preventing
violations before they occur or correcting violations after the fact)
and to audit policy (analyze the history of policy and policy
violations).

* Free software: Apache license
* Documentation: http://docs.openstack.org/developer/congress

4. Installing Congress
======================

There are 2 ways to install Congress.

* As part of devstack.  This allows you to run Congress alongside
  live instances of other OpenStack projects like Nova and Neutron.

* Standalone. This allows you to write code and run unit tests,
  without requiring a full devstack installation.

4.1 Devstack-install
--------------------
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


4.2 Standalone-install
----------------------
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


