.. include:: aliases.rst

.. _concepts:


============
Architecture
============

Congress consists of the Congress policy engine and a driver for each
of the cloud services acting as a data source.::

                  Policy Engine
                        |
      ------------------+------------------
      |                 |                 |
  Nova Driver    Neutron Driver    Keystone Driver
      |                 |                 |         ....
     Nova            Neutron          Keystone


1. Cloud Services, Drivers, and State
---------------------------

A service is anything that manages cloud state.  For example,
OpenStack components like Nova, Neutron, Cinder, Swift, Heat, and
Keystone are all services.  Software like |ad|, inventory management
systems, anti-virus scanners, intrusion detection systems, and
relational databases are also services.

Congress uses a driver to connect each service to the policy engine.
A driver fetches cloud state from its respective cloud service, and
then feeds that state to the policy engine as table data.  For
example, the Nova driver periodically makes API calls to Nova to fetch
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


2. Policy Language
------------------

Congress uses Datalog as its policy language.  Datalog is table-based
and is similar in many ways to SQL, Prolog, and first-oreder logic.
Congress uses Datalog and a table-based data model to leverage 50
years of research and development into the language and its
implementations.  

Once the cloud operator gives Congress a policy (a description of the
permitted states of the cloud), Congress will monitor the actual state
of the cloud, compare it to policy, and warn the cloud operator about
policy violations (when the cloud's actual state is one that a policy
does not permit).  In the future, Congress will go farther and take
action to change the state of the cloud (enforcement) and help us
understand the history of policy and its violations (auditing).  The
:ref:`Policy <policy>` section describes policies in more detail.


3. Congress Server and API
--------------------------

Congress runs as a standalone server process and presents a RESTful
API for clients; drivers run as part of the server.  The API allows
clients to create policies, read policies, read input data sources,
and read state tables (including policy violation tables).
Instructions for starting the Congress server can be found in the
:ref:`Readme <readme>` file.  The API section describves the API in
more detail.




