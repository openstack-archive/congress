.. _readme:

======================
 Introducing Congress
======================

Why is Policy Important
=======================

The cloud is a collection of autonomous
services that constantly change the state of the cloud, and it can be
challenging for the cloud operator to know whether the cloud is even
configured correctly.  For example,

* The services are often independent from each other and do not
  support transactional consistency across services, so a cloud
  management system can change one service (create a VM) without also
  making a necessary change to another service (attach the VM to a
  network).  This can lead to incorrect behavior.

* Other times, we have seen a cloud operator allocate cloud resources
  and then forget to clean them up when the resources are no longer in
  use, effectively leaving garbage around the system and wasting
  resources.

* The desired cloud state can also change over time.  For example, if
  a security vulnerability is discovered in Linux version X, then all
  machines with version X that were ok in the past are now in an
  undesirable state.  A version number policy would detect all the
  machines in that undesirable state.  This is a trivial example, but
  the more complex the policy, the more helpful a policy system
  becomes.

Congress's job is to help people manage that plethora of state across
all cloud services with a succinct policy language.

Using Congress
==============

Setting up Congress involves writing policies and configuring Congress
to fetch input data from the cloud services.  The cloud operator
writes policy in the Congress policy language, which receives input
from the cloud services in the form of tables.  The language itself
resembles datalog.  For more detail about the policy language and data
format see :ref:`Policy <policy>`.

To add a service as an input data source, the cloud operator configures a Congress
"driver," and the driver queries the service.  Congress already
has drivers for several types of service, but if a cloud operator
needs to use an unsupported service, she can write a new driver
without much effort and probably contribute the driver to the
Congress project so that no one else needs to write the same driver.

Finally, when using Congress, the cloud operator must choose what
Congress should do with the policy it has been given:

* **monitoring**: detect violations of policy and provide a list of those violations
* **proactive enforcement**: prevent violations before they happen (functionality that requires
  other services to consult with Congress before making changes)
* **reactive enforcement**: correct violations after they happen (a manual process that
  Congress tries to simplify)

In the future, Congress
will also help the cloud operator audit policy (analyze the history
of policy and policy violations).

Installing Congress
===================

Please refer to the
`installation guide <https://docs.openstack.org/congress/latest/install/>`_
