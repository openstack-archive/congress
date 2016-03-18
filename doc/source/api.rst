.. include:: aliases.rst

.. _api:

===
API
===

The design document for the API can be found below.  This document contains
the API as of the current release::

    https://docs.google.com/document/d/14hM7-GSm3CcyohPT2Q7GalyrQRohVcx77hxEx4AO4Bk/edit#

There are two top-level concepts in today's API: Policies and Data-sources.

* Policies have *rules* that describe the permitted states of the cloud,
  along with *tables* representing abstractions of the cloud state.
* Data-sources have *tables* representing the current state of the cloud.
* The *tables* of both policies and data-sources have rows that describe
  their contents.


1. Policy (/v1/)
================

You can create and delete policies.  Two policies are provided by
the system, and you are not permitted to delete them: *classification*
and *action*.  A policy has the following fields:

* name: a unique name that is human-readable
* abbreviation: a shorter name that appears in traces
* description: an explanation of this policy's purpose
* kind: kind of policy. Supported kinds are -
        a) nonrecursive,
        b) action,
        c) database,
        d) materialized
        The default is *nonrecursive* and unless you are writing action
        descriptions for use with ``simulate`` you should always use the
        default.


======= ============================ ================================
Op       URL                         Result
======= ============================ ================================
GET     .../policies                 List policies
GET     .../policies/<policy-id>     Read policy properties
POST    .../policies/<policy-id>     Create new policy
DELETE  .../policies/<policy-id>     Delete policy
======= ============================ ================================

You can also utilize the simulation API call, which answers hypothetical
questions: if we were to change the state of the cloud in this way,
what would the answer to this query be?  See :ref:`enforcement` for
more details and examples::

    POST .../policies/<policy-id>
      ?action=simulate
      [&delta=true]                    # return just change in <query>
      [&trace=true]                    # also return explanation of result

    Request Body
    {
      "query" : "<query>",                 # string query like: 'error(x)'
      "sequence": "<sequence>",            # changes to state like: 'p+(1) p-(2)'
      "action_policy" : "<action_policy>"  # name of a policy: 'action'
    }

2. Policy Rules (/v1/policies/<policy-id>/...)
==============================================

Each policy is a collection of rules.  Congress supports the usual CRUD
operations for changing that collection.  A rule has the following fields:

* ID: a unique identifier
* name: a human-friendly identifier
* rule: a string representing the actual rule as described in :ref:`policy`
* comment: description or comment related to the rule

======= ======================= ======================
Op      URL                     Result
======= ======================= ======================
GET     .../rules               List policy rules
POST    .../rules               Create policy rule
GET     .../rules/<rule-id>     Read policy rule
DELETE  .../rules/<rule-id>     Delete policy rule
======= ======================= ======================


3. Policy Tables (/v1/policies/<policy-id>/...)
===============================================

All the tables mentioned in the rules of a policy can be queried
via the API.  They have only an ID field.

======= ========================== =====================================
Op      URL                        Result
======= ========================== =====================================
GET     .../tables                 List tables
GET     .../tables/<table-id>      Read table properties
======= ========================== =====================================


4. Policy Table Rows (/v1/policies/<policy-id>/tables/<table-id>/...)
=====================================================================

Rules are used to instruct Congress how to create new tables from existing
tables.  Congress allows you to query the actual contents of tables
at any point in time.  Congress will also provide a trace of how
it computed a table, to help policy authors understand why
certain rows belong to the table and others do not.

======= ====================== =====================================================
Op      URL                    Result
======= ====================== =====================================================
GET     .../rows               List rows
GET     .../rows?trace=true    List rows with explanation (use 'printf' to display)
======= ====================== =====================================================


5. DEPRECATED: Drivers (/v1/system/)
====================================
A driver is a piece of code that once instantiated and configured interacts
with a specific cloud service like Nova or Neutron.  A driver has the following
fields.

* ID: a human-friendly unique identifier
* description: an explanation of which type of cloud service this driver
  interacts with

======= ======================== ==============================================
Op      URL                      Result
======= ======================== ==============================================
GET     .../drivers              List drivers
GET     .../drivers/<driver-id>  Read driver properties
======= ======================== ==============================================

Drivers are deprecated as of liberty.  The upcoming distributed architecture
replaces API-level datasource management with configuration-level datasource
management.


6. Data sources (/v1/)
======================

A data source is an instantiated and configured driver that interacts with a
particular instance of a cloud service (like Nova or Neutron).  You can
construct multiple datasources using the same driver.  For example, if you have
two instances of Neutron running, one in production and one in test and you
want to write policy over both of them, you would create two datasources using
the Neutron driver and give them different names and configuration options. For
example, you might call one datasource 'neutron_prod' and the other
'neutron_test' and configure them with different IP addresses.

A datasource has the following fields.

* ID: a unique identifier
* name: a human-friendly unique that is unique across datasources and policies
* driver: the name of the driver code that this datasource is running
* config: a dictionary capturing the configuration of this datasource
* description: an explanation of the purpose of this datasource
* enabled: whether or not this datasource is functioning (which is always True)


======= ================================ ======================================
Op      URL                              Result
======= ================================ ======================================
GET     .../data-sources                 List data sources
POST    .../data-sources                 Create data source
DELETE  .../data-sources/<ds-id>         Delete data source
GET     .../data-sources/<ds-id>/schema  Show schema (tables and table-columns)
GET     .../data-sources/<ds-id>/status  Show data source status
GET     .../data-sources/<ds-id>/actions List supported data source actions
======= ================================ ======================================

Datasource creation and deletion via the API will be deprecated in future. The
upcoming distributed architecture replaces API-level datasource management with
configuration-level datasource management.



7. Data source Tables (/v1/data-sources/<ds-id>/...)
====================================================

Each data source maintains a collection of tables (very similar to a Policy).
The list of available tables for each data source is available via the API.
A table just has an ID field.

======= ========================== =========================================
Op      URL                        Result
======= ========================== =========================================
GET     .../tables                 List data sources
GET     .../tables/<table-id>      Read data source properties
GET     .../tables/<table-id>/spec Show a table schema
======= ========================== =========================================



8. Data source Table Rows (/v1/data-sources/<ds-id>/tables/<table-id>/...)
==========================================================================

The contents of each data source table (the rows of each table) can be queried
via the API as well.  A row has just a Data field, which is a list of values.

======= ========================== =================================
Op      URL                        Result
======= ========================== =================================
GET     .../rows                   List rows
======= ========================== =================================



9. Versions (/)
===============

You can see the supported API versions.

======= ========================== =================================
Op      URL                        Result
======= ========================== =================================
GET     .../                       List supported versions
GET     .../<version-id>           Read version
======= ========================== =================================



