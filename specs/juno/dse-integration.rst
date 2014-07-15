..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
Integrate DSE with Policy Engine
==========================================

https://blueprints.launchpad.net/congress/+spec/dse-integration

Currently the data sources integrated into Congress cannot send their data to
the policy engine.  DSE is a message bus aimed at providing the functionality
for that communication.  We need to integrate DSE, the policy engine, and
the data sources so that they can all communicate with each other.


Problem description
===================

So that the policy engine and the data sources can interact, we must
instantiate them with the DSE message bus.  Some examples.

* Every time the data source learns of a change in a cloud service
table it must communicate that change to the policy engine.

* Whenever the policy engine computes an action that must be
executed it must communicate that request to an execution engine,
which at this point is a data source.  This use case will not be
covered by this change, but illustrates the multi-directional
nature of the problem.


Proposed change
===============


DSE implements a deepSix class.
* All data sources will inherit from deepSix.
* The policy engine will inherit from deepSix.

DSE also implements d6cage, which is the control structure for managing
a collection of deepSix instances.  We must create an instance of
d6cage, properly instantiate it with data sources and the policy engine,
and create a driver file that is called to launch Congress.

DSE utilizes a publish/subscribe message protocol.
Each time policy changes (via API calls), the policy engine
must change its subscriptions on the DSE bus so that it is subscribed
to exactly those tables that its policy depends upon.


Alternatives
------------

Another option is to write such integration code without a pub/sub message
bus, but the message bus gives us the option of integrating data sources
that are stored on different servers.  Moreover, we believe that the more
manual integration would end up implementing a poor approximation of pub/sub.


Data model impact
-----------------

No data model changes are expected.


REST API impact
---------------

We do not yet have an API implemented.  This change does not impact the API
we have designed.  But it does enable a simple implementation of that API
where API calls are sent on the DSE bus.

Security impact
---------------

None.


Notifications impact
--------------------

None.

Other end user impact
---------------------

None.

Performance Impact
------------------

We expect DSE's performance to be fairly good.  It uses Python queues to
communicate between components.  The cost of the queueing we believe
will be negligible compared to the cost of policy evaluation, polling
for data, and computing deltas on that data.

This change puts each data source and the policy engine into their
own threads.  The message bus is the only state those components
share, so there is no need for any additional locking to be put in place.


Other deployer impact
---------------------

None.

Developer impact
----------------

None.

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  Tim Hinrichs (thinrichs@vmware.com)

Other contributors:
  None

Work Items
----------

* Make datasources inherit from deepSix
* Create object that inherits from both policy engine and deepSix
* Write main() method that properly instantiates policy engine
* Write event-handlers (within policy engine) that properly creates data
sources
* Write event-handlers (within policy engine) that properly change its
subscriptions to reflect the current datasources and tables
required to evaluate policy.

Dependencies
============

None.

Testing
=======

We will add tests for DSE as well as DSE when instantiated as described above.

* We will start with unit tests for DSE: instantiate two data sources, have
one subscribe to the other, and check that publications are seen by the
subscriber.

* We will simulate changes in the underlying data sources and check that the
policy engine receives those updates.

* We will change policy and check that policy engine receives data for all
the right tables.

* We will change the data sources and check that they are properly
instantiated in the framework.

* We will simulate changes in those new data sources and check that the
policy engine receives the proper updates.



Documentation Impact
====================

Docs for external consumption will be unchanged.

We don't yet have developer docs.


References
==========

None.
