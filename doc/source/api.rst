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


1. Policy (/)
=============

There is currently exactly 1 policy provided by the system, called
*classification*.  Eventually we will support the creation/deletion of policies
to enable multitenancy.


======= ============================ ================================
Op       URL                         Result
======= ============================ ================================
GET     .../policies                 List policies
GET     .../policies/<policy-id>     Read policy properties
======= ============================ ================================


2. Policy Rules (/policies/<policy-id>/...)
===========================================

Each policy is a collection of rules.  Congress supports the usual CRUD
operations for changing that collection.  Eventually a rule will have
meta-properties like *comments*, but for now the only field a
rule contains is *rule*, which is a string containing a single statement
from the policy language described in :ref:`policy`.

======= ======================= ======================
Op      URL                     Result
======= ======================= ======================
GET     .../rules               List policy rules
POST    .../rules               Create policy rule
GET     .../rules/<rule-id>     Read policy rule
DELETE  .../rules/<rule-id>     Delete policy rule
======= ======================= ======================


3. Policy Tables (/policies/<policy-id>/...)
============================================

All the tables mentioned in the rules of a policy can be queried
via the API.

======= ========================== =========================
Op      URL                        Result
======= ========================== =========================
GET     .../tables                 List tables
GET     .../tables/<table-id>      Read table properties
======= ========================== =========================


4. Policy Table Rows (/policies/<policy-id>/tables/<table-id>/...)
==================================================================

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


5. Data sources (/)
===================

Data sources (e.g. Nova/Neutron) can be queried via the API.  Each data source
is effectively a collection of tables.

======= ================================ ======================================
Op      URL                              Result
======= ================================ ======================================
GET     .../data-sources                 List data sources
GET     .../data-sources/<ds-id>         Read data source properties
======= ================================ ======================================


6. Data source Tables (/data-sources/<ds-id>/...)
=================================================

Each data source maintains a collection of tables (very similar to a Policy).
The list of available tables for each data source is available via the API.

======= ========================== =========================================
Op      URL                        Result
======= ========================== =========================================
GET     .../tables                 List data sources
GET     .../tables/<table-id>      Read data source properties
======= ========================== =========================================


7. Data source Table Rows (/data-sources/<ds-id>/tables/<table-id/...)
======================================================================

The contents of each data source table (the rows of each table) can be queried
via the API as well.

======= ========================== =================================
Op      URL                        Result
======= ========================== =================================
GET     .../rows                   List rows
======= ========================== =================================






