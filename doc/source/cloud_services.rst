.. include:: aliases.rst

.. _cloud-services:

Cloud Services
==============

Congress is designed to manage a collection of cloud services by enforcing a policy that dictates how those cloud services are supposed to relate to one another.  The assumption is that Congress can interact with those cloud services so that, at the very least, it can identify when the cloud service ecosystem does not comply with policy.

So that Congress can interact with *any* cloud service, it defines a simple interface that all cloud services must implement in order to be managed by Congress.  The interface requires the information within a cloud service to be conceptualized as a collection of tables of data.  Each table is a collection of rows, each of which have the same number of columns.  Each entry in the table must be either a number or a string (e.g. not a dictionary or list).

For example, one of the Neutron tables might describe which IP addresses are assigned to which ports.

====================================== ==========
ID                                     IP
====================================== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1"
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.2"
"73e31d4c-a49c-11e3-be40-425861b86ab6" "10.0.0.3"
====================================== ==========

The interface that a cloud service must support, at a minimum, is a request for all of the tuples in a given table.  In addition, it is beneficial if each cloud service can publish updates to its tables as it learns of them.  If these updates are not sent by the service, Congress will simulate them by polling the service periodically and computing the changes since the last poll.

Also, many cloud services have API calls that change the state of the service, e.g. Neutron has an API call that assigns an IP address to a port.  This aspect of cloud services is covered in TODO(Section ref).

.. todo:: provide details about hooking up cloud services for reading tables
