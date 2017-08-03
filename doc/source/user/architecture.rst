
.. _concepts:


============
Architecture
============

Congress consists of the Congress policy engine and a driver for any number of
other cloud services that act as sources of information about the cloud::

                  Policy Engine
                        |
      ------------------+------------------
      |                 |                 |
  Nova Driver    Neutron Driver    Keystone Driver
      |                 |                 |         ....
     Nova            Neutron          Keystone


1. Cloud Services, Drivers, and State
-------------------------------------

A service is anything that manages cloud state.  For example,
OpenStack components like Nova, Neutron, Cinder, Swift, Heat, and
Keystone are all services.  Software like ActiveDirectory, inventory management
systems, anti-virus scanners, intrusion detection systems, and
relational databases are also services.

Congress uses a driver to connect each service to the policy engine.
A driver fetches cloud state from its respective cloud service, and
then feeds that state to the policy engine in the form of tables.
A table is a collection of rows; each row is a collection of columns;
each row-column entry stores simple data like numbers or strings.

For example, the Nova driver periodically makes API calls to Nova to fetch
the list of virtual machines in the cloud, and the properties
associated with each VM.  The Nova driver then populates a table in
the policy engine with the Nova state.  For example, the Nova driver
populates a table like this:::

  ---------------------------------------------
  | VM id | Name | Status | Power State | ... |
  ---------------------------------------------
  | 12345 | foo  | ACTIVE | Running     | ... |
  | ...   |      |        |             |     |
  ---------------------------------------------


The state for each service will be unique to that service.  For
Neutron, the existing logical networks, subnets, and ports make up
that state.  For Nova, the existing VMs along with their disk and
memory space make up that state.  For an anti-virus scanner, the
results of all its most recent scans are the state.  The
:ref:`Services <cloudservices>` section describes services and drivers in
more detail.


2. Policy
---------

A Congress policy defines all those states of the cloud that are permitted:
all those combinations of service tables that are possible when the cloud is
behaving as intended.  Since listing the permitted states explicitly is an
insurmountable task, policy authors describe the permitted states implicitly
by writing a collection of if-then statements that are always true when the
cloud is behaving as intended.

More precisely, Congress uses Datalog as its policy language.  Datalog is a
declarative language and is similar in many ways to SQL, Prolog, and
first-order logic.  Datalog has been the subject of research and
development for the past 50 years, which means there is
a wealth of tools, algorithms, and deployment experience surrounding it.
The :ref:`Policy <policy>` section describes policies in more detail.

3. Capabilities
---------------

Once Congress is given a policy, it has three
capabilities:

* monitoring the cloud for policy violations
* preventing violations before they occur
* correcting violations after they occur

In the future, Congress will also record the history of policy and its
violations for the purpose of audit.
The :ref:`Monitoring and Enforcement <enforcement>` section describes
these capabilities in more detail.


4. Congress Server and API
--------------------------

Congress runs as a standalone server process and presents a RESTful
API for clients; drivers run as part of the server.
Instructions for installing and starting the Congress server can be
found in the :ref:`Readme <readme>` file.


The API allows clients to perform the following operations:

* insert and delete policy statements
* check for policy violations
* ask hypothetical questions: if the cloud were to undergo these changes,
  would that cause any policy violations?
* execute actions

The :ref:`API <api>` section describes the API in more detail.

