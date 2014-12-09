
.. include:: aliases.rst

.. _codeoverview:

==============
Code Overview
==============
This page gives a brief overview of the code structure that implements
Congress.


1. External information
=======================

The main source of information is the Congress wiki.  There are two separate
codebases that implement Congress: the server and the python client bindings.

* wiki: https://wiki.openstack.org/wiki/Congress
* server: https://git.openstack.org/cgit/stackforge/congress
* client: https://git.openstack.org/cgit/stackforge/python-congressclient

The structure of the client code is the same as that for other recent
OpenStack python clients. The bulk of the Congress code is contained
within the server.  The remainder of this page describes the layout
of the server code.


2. Server directory structure
===============================

Here are the most important components of the code, described by how they are
laid out in the repository.

* ``congress/harness.py``: instantiates message bus and installs datasource
  drivers and policy engine onto the bus
* ``congress/policy``: policy engine (datalog interpreter, monitoring,
  enforcement)
* ``congress/datasources``: datasource drivers: thin wrappers/adapters for
  integrating services like Nova, Neutron
* ``congress/dse``: message bus that the policy engine and datasources use to
  communicate
* ``congress/api``: API data models (entry points into the system from the API)
* ``contrib``: code for integrating into other services, e.g. devstack,
  horizon, tempest


3. Policy Engine
====================

First is a description of the files and folders in congress/policy.

* ``congress/policy/Congress.g``: Antlr3 grammar defining the syntax of policies.
  ``make`` uses Congress.g to generate CongressLexer.py and CongressParser.py,
  which are used to convert strings into Python datastructures.
* ``congress/policy/compile.py``:

  * Convert policy strings into Python datastructures that represent those
    strings.
  * Includes datastructures for individual policy statements.
  * Also includes additional syntax checks that are not handled by the grammar.

* ``congress/policy/runtime.py``:

  * Policy datastructures
  * Reasoning algorithms
  * Toplevel class for policy engine: Runtime

* ``congress/policy/unify.py``: unification routines used at the heart of the
  policy reasoning algorithms.
* ``congress/policy/dsepolicy.py``: code that implements the Runtime class as
  a member of the DSE message bus.  Handles publishing/subscribing to the
  tables exported by the datasources.

Second is a brief overview of the fundamental datastructures used to represent individual policy statements.

* ``congress/policy/compile.py:Rule``: represents a single rule of the form
  ``head1, ..., headn :- body1, ..., bodym``.  Each headi and bodyi are
  Literals.
* ``congress/policy/compile.py:Literal``: represents a possibly negated atom of
  the form ``[not] table(arg1, ..., argn)``.  Each argi is a term.
* ``congress/policy/compile.py:Term``: represents an argument to a Literal.  Is
  either a Variable or an ObjectConstant.
* ``congress/policy/compile.py:ObjectConstant``: special kind of Term that
  represents a fixed string or number.
* ``congress/policy/compile.py:Variable``: special kind of Term that is a
  placeholder used in a rule to represent an ObjectConstant.

Third is an overview of the datastructures used to represent entire policies.
There are several different kinds of policies that you can choose from when
creating a new policy. Each makes different tradeoffs in terms of time/space
or in terms of the kind of policy statements that are permitted.  Internally
these are called 'theories'.


* ``congress/policy/runtime.py:NonrecursiveRuleTheory``: represents an
  arbitrary collection of rules (without recursion).  No precomputation of
  table contents is performed.  Small memory footprint, but query time can be
  large.  (A Prolog implementation of rules.)  This is the default
  datastructure used when creating a new policy.

* ``congress/policy/runtime.py:MaterializedViewTheory``: represents an
  arbitrary collection of rules (even allows recursion).  Contents of all
  tables are computed and stored each time policy changes.  Large memory
  footprint, but query time is small when asking for the contents of any
  table.  Not actively maintained.

* ``congress/policy/runtime.py:Database``: represents a collection of
  non-negated Literals without variables, e.g. ``p(1, "alice")``.  A standard
  DB table.

Last we give a list of the top-level entry points to the Runtime class, which
is basically the top-level class for the policy engine.

* ``create_policy``, ``delete_policy``: implement multiple policies
* ``select``: ask for the answer to a standard database query
  (e.g. the contents of a table) for a specified policy
* ``insert``, ``delete``: insert or delete a single policy statement
  into a specified policy
* ``update``: batch of inserts/deletes into multiple policies
* ``simulate``: apply a sequence of updates (temporarily), answer a
  query, and roll-back the updates.


