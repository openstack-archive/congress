..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==============
API Validation
==============

https://blueprints.launchpad.net/congress/+spec/api-validation

Users (and programs) sometimes provide invalid inputs to APIs.  The API should
be resilient to this, and deny bad requests.

Problem description
===================

Any request that does not conform to the form expected by the API is deemed
invalid.  Invalid requests should be rejected by the API, along with
information to aid in correcting the problem.

The following features are desirable in an API validation solution:

* Validation should enforce a declarative model that is visible external to
  the validation implementation.

  * The declarative model should follow standard formatting and conventions
    that are understood in the API caller's context.

  * For cross-platform APIs, the model should be consumable without knowledge
    of a particular programming language.

  * The model should provide sufficient information for generation of
    resource documentation in associated API reference material.

* Validation should be performed by a common framework which facilitates
  binding the declarative models with the API implementation.

  * The API implementation may assume trusted inputs by relying on the
    framework to offload validation.

* Validation may be selectively enabled on API outputs to facilitate
  development and testing.


Proposed change
===============

We will introduce JSON schemas to model the expected inputs and outputs of
each API call.

The API resource manager will be updated to support binding of schemas to
each handler.

When dispatching API calls, the framework will validate the call body using
the 'jsonschema' python validator.

If an optional flag is provided, the dispatcher will validate the API handler
response body before passing the response up the stack.


Alternatives
------------

Other components, such as neutron, have created custom validation utilities.
These utilities are often not as rich as JSON schema, and do not address
many of the desirable features described above.

The nova project is currently retrofitting their API to utilize JSON Schema
validation: https://blueprints.launchpad.net/nova/+spec/v3-api-schema


Data model impact
-----------------

None.



REST API impact
---------------

The current API provides very minimal validation.  This change will add
validation to all existing API calls.


Security impact
---------------

Adding validation to the API should increase security of the system by
protecting the API implementation from unexpected inputs.


Notifications impact
--------------------

None.


Other end user impact
---------------------

None.


Performance Impact
------------------

Validation of inputs will have a negative performance impact on latency and
throughput of API calls.  JSON schema does not necessarily impose larger
performance impacts than other validation solutions, despite its increased
power and flexibility.


Other deployer impact
---------------------

None.


Developer impact
----------------

After introduction of API validation, new API calls will need to introduce an
associated schema.


Implementation
==============

Assignee(s)
-----------

Primary assignee:
  pballand

Other contributors:
  None

Work Items
----------

* Create JSON schemas for each API resource (This is already done in the API
  design, and simply needs to be translated to the source tree.)

* Add support to the API resource manager to bind schemas with resource
  endpoints.

* Add jsonschema as a runtime dependency.

* Use jsonschema to validate requests before dispatching to API implementation.

* Expose flag to support output validation.  Optionally use jsonschema to
  validate body of API result before returning to the wsgi server.


Dependencies
============

None.


Testing
=======

The schema validator is assumed to be thoroughly tested.  We will test that
validation is being performed by issuing requests that should and should not
validate against the schema.


Documentation Impact
====================

This change itself does not impact documentation.  The addition of schemas
for each API call should be included in the documentation.


References
==========

JSON Schema definition:
  http://json-schema.org/

Python jsonschema validator:
  https://python-jsonschema.readthedocs.org/en/latest/

Nova spec for updating validation to use JSON Schema:
  https://blueprints.launchpad.net/nova/+spec/v3-api-schema
