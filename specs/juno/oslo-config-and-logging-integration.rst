..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
Integreate oslo.config and oslo-incubator logging
==========================================

https://blueprints.launchpad.net/congress/+spec/integrate-oslo-config-and-logging

All openstack projects integrate with a library called oslo.config and
oslo-incubator for config and logging management. This blueprint is to
to integrate these two libries into congress.

Problem description
===================

* In order to avoid code duplication all openstack projects leverage
  a common library for config management (oslo.config) and log management
  (oslo-incubator). To avoid reinviting the wheel here we should use these
  libraries as well.

Proposed change
===============

Integrate:
  https://github.com/openstack/oslo-incubator/
  https://github.com/openstack/oslo.config

with congrss.

Alternatives
------------

None

Data model impact
-----------------

None

REST API impact
---------------

None

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

This blueprint provides integration to common libraries that all openstack
deployers are already used to using and configuring.

Performance Impact
------------------

None

Other deployer impact
---------------------

None

Developer impact
----------------

None

Implementation
==============

Assignee(s)
-----------

Primary assignee:
  arosen

Work Items
----------

None

Dependencies
============

None

Testing
=======

Unit tests will be added

Documentation Impact
====================

None

References
==========

None
