===================================
 Kilo Series Release Notes
===================================

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
