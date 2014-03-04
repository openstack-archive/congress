
.. include:: aliases.rst

.. _introduction:

Introduction
============

Congress is a policy-based management framework for the cloud. It is a cloud service whose main responsibility is to enforce a single, consistent policy across the cloud.  The policy language includes abstractions like groups that make it easy to express policies over large numbers of users, files, etc.  It enforces policy either by preventing violations before they happen or correcting violations after the fact.

The user documentation is broken into 3 conceptual pieces: hooking cloud services up to Congress, writing policies within Congress, and enforcing policy with Congress.  For those of you familiar with |ad|, it is such a useful point of comparison that we include it below.  Those not familar with |ad| can safely skip it.

Comparison to |ad|
-------------------

In many ways Congress is similar to |ad| (AD).

* Both Congress and AD are cloud services whose main responsibility is policy enforcement.
* Both Congress and AD enforce a single, consistent policy across the cloud.  That policy is concerned primarily with qualitative, as opposed to quantitative, properties of the cloud.
* Both Congress and AD support a policy language that includes abstractions like groups that make it easy to express policies over large numbers of users, files, etc.

Congress generalizes |ad| in several dimensions.

* AD is primarily used for managing a collection of servers.  Congress is designed to manage any collection of cloud services (that reasonably fit within the relational data model).
* AD's policy language provides a list of several thousand actions that the policy controls (e.g. changing the screen saver).  Congress provides a high-level, general-purpose policy language where a policy controls which states of the cloud are permitted (independent of which actions were executed to achieve that state).  Congress has an auxiliary policy for controlling the actions that are executed, but the hope is that such a policy is unnecessary.
* AD enforces policy by relying on the OS to prevent violations before they occur.  Congress makes no assumptions about the enforcement points it has available; rather, it prevents policy violations when possible and corrects them when not.  And Congress enables administrators to control the extent to which enforcement is automatic.



