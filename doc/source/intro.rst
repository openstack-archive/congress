
.. include:: aliases.rst

.. _introduction:

Introduction
============

Congress is a system for declaring, monitoring, enforcing, and auditing
policy in heterogeneous cloud environments.   Users typically perform three
tasks when using Congress.

* **Write policy.**  A policy describes how the cloud services installed in
  the cloud ought to behave, both individually and as a whole.  This information
  allows Congress to compare how the cloud is actually behaving with how policy
  says the cloud should behave.
* **Configure cloud services.**  A policy is only useful if there are cloud
  services that Congress can use to monitor/enforce/audit that policy.  For
  example, a policy that requires a minimum password length is only useful if
  there is a service that can examine the minimum password lengths on all the
  virtual machines, mobile devices, web applications, routers, etc.  Out of the
  box, Congress has support for a number of different cloud services, which
  must be configured for each installation.  If the services supported out of
  the box are inadequate, the user will connect additional cloud services
  (a task that was designed to be as simple as we could make it).
* **Make decisions about policy violations.**  When Congress identifies a
  policy violation (a mismatch between the cloud's intended behavior described
  in policy and the cloud's actual behavior), a user must decide what to do.
  Currently, Congress only monitors violations, but in the future Congress
  will provide mechanisms to enforce policy (by preventing violations before
  they occur or correcting violations after the fact) and to audit policy
  (analyze the history of policy and policy  violations).

In short, Congress was designed to work with **any policy** and
**any cloud service**.

The user documentation is broken into 4 pieces:

* :ref:`Concepts <concepts>`: Understanding the core ideas of Congress
* :ref:`Services <cloudservices>`: Configuring cloud services in Congress
* :ref:`Policy <policy>`: Writing Congress policies
* :ref:`API <api>`: Interacting with Congress



