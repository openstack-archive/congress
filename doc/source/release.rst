.. include:: aliases.rst

.. _release:

=============
Release Notes
=============

Liberty
-------
**Main updates**

* Added datasource driver for Heat
* Designed and began implementation of new distributed architecture
* Added API call to list available actions for manual reactive enforcement
* Refactored all datasource drivers for improved consistency
* Extended grammar to include insert and delete events
* Improved tempest/devstack support for running in gate
* Added version API
* Improved support for python3
* Reduced debug log volume by reducing messages sent on message bus
* Enabled action execution for all datasources
* Eliminated busy-loop in message bus for reduced cpu consumption
* Improved unit test coverage for API
* Added experimental vm-migration policy enforcement engine


Kilo
----

**Main features**

* Datalog: basic rules, column references, multiple policies,
  action-execution rules
* Monitoring: check for policy violations by asking for the rows of
  the ``error`` table
* Proactive enforcement: prevent violations by asking Congress before making
  changes using the ``simulate`` API call
* Manual reactive enforcement: correct violations by writing Datalog
  statements that say which actions to execute to eliminate violations
* Datasource drivers for Ceilometer, Cinder, CloudFoundry, Glance, Ironic,
  Keystone, Murano, Neutron, Nova, Plexxi, Swift, vCenter

**Known issues**

* ``GET /v1/policies/<policy-name>/rules`` fails to return 404 if the policy name
  is not found.  There are similar issues for other
  ``/v1/policies/<policy-name>/rules`` API calls.

* Within a policy, you may not use both ``execute[<table>(<args>)]`` and
  ``<table>(<args>)`` in the heads of rules.


