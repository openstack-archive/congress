.. Congress documentation master file, created by
   sphinx-quickstart on Tue Jul  9 22:26:36 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

===================
Welcome to Congress
===================

Congress is an open policy framework for the cloud.  With Congress, a
cloud operator can declare, monitor, enforce, and audit "policy" in a
heterogeneous cloud environment.  Congress gets inputs from a cloud's
various cloud services; for example in OpenStack, Congress fetches
information about VMs from Nova, and network state from Neutron, etc.
Congress then feeds input data from those services into its policy engine
where Congress verifies that the cloud's actual state abides by the cloud
operator's policies.

.. toctree::
   :maxdepth: 2

   Introduction <user/readme>
   User Documentation <user/index>
   Installation Documentation <install/index>
   Configuration Documentation <configuration/index>
   Administrator Documentation <admin/index>
   CLI Documentation <cli/index>
   Contributor Documentation <contributor/index>

.. toctree::
   :hidden:

   api/modules


* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
