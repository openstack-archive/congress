..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
Keystone integration
==========================================

https://blueprints.launchpad.net/congress/+spec/keystone-integration

This blueprint is to add keystone integration to congress just as the
other openstack projects do.

Problem description
===================

A detailed description of the problem:

    * All of the openstack projects leverage keystone for authorization, etc
      so we should add support for this in congress as well.


Proposed change
===============

Integrate the python-keystoneclient middleware.


Alternatives
------------

None

Data model impact
-----------------

None

REST API impact
---------------

Deployers of congress will now be able to use keystone with congress if they
choose.

Security impact
---------------

None

Notifications impact
--------------------

None

Other end user impact
---------------------

None

Performance Impact
------------------

None

Other deployer impact
---------------------

Congress will still continue to work without keystone if a deployer chooses.

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

Integrate keystone middleware with congress


Dependencies
============

None

Testing
=======

Unit tests will be added.

Documentation Impact
====================

We'll need to document how to add the keystone endpoint for congress which
would be:

$ keystone service-create --name=congress --type=policy \
     --description="Openstack Policy Service"

$ keystone endpoint-create \
     --service-id the_service_id_above \
     --publicurl http://controller:port \
     --adminurl http://controller:port \
     --internalurl http://controller:port

References
==========

None
