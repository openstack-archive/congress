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

.. _datasource_driver:

Data Source Driver
------------------

Introduction
~~~~~~~~~~~~
Congress acts on the data exposed by various data sources. This could be
OpenStack components like Neutron, Nova, Keystone or non OpenStack components
like Active Directory, LDAP.

Data Source Base Class
~~~~~~~~~~~~~~~~~~~~~~
All the Data Source drivers extend from the base class
:code:`congress.server.service_pluggins.DataSourceDriver`. It consists of
following methods which need to be overriden.

.. class:: DataSourceDriver

      Base class for all the drivers to implement

      .. function:: __init__(**creds):

         Initialize the driver with appropriate parameter ``creds``

      .. function:: get_all(type):

         Get all the tuples exposed by the driver for a ``type``

      .. function:: boolean_to_congress(self, bool):

         Converts :code:`bool` into a :code:`string` as Congress does not
         support boolean type.

Implement the DataSource Driver
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To implement a data source driver following steps need to be executed

1. Extend :code:`DataSource` class::

        class MyDriver(DataSource)

2. Implement the following methods

   Intialize the driver by implementing :func:`__init__`::

        def __init__(**creds):

   Implement :func:`get_all` where `type` is the type of tuples that can be
   returned. Convert all lists, dictionaries into tuples::

        def get_all(self, type):

   Update the last time updated by implementing the following function::

        def get_last_updated_time(self)

3. Test your driver using a unit test as well as with a real integration


Converting Data into Tuples
~~~~~~~~~~~~~~~~~~~~~~~~~~
Since Congress only supports tuples, each dictionary element and its nested
lists/dictionaries need to be converted into one or more tuples


- A List of dictionary converted to a tuple

    Original data::

        [{'key1':'value1','key2':'value2'},
         {'key1':'value3','key2':'value4'}
        ]

    Tuple::

        [('value1', 'value2'),
         ('value3', 'value4')
        ]

- List of Dictionary with a nested List

    Original data::

        [{'key1':'value1','key2':['v1','v2']},
         {'key1':'value2','key2':['v3','v4']}
        ]

    Tuple::

        [('value1', 'uuid1'),
         ('value1', 'uuid2'),
         ('value2', 'uuid3'),
         ('value2', 'uuid4')
        ]

        [('uuid1', 'v1'),
         ('uuid2', 'v2'),
         ('uuid3', 'v3'),
         ('uuid4', 'v4')
        ]

    *Note* : uuid* are congress generated uuids

- List of Dictionary with a nested dictionary

   Original data::

        [{'key1':'value1','key2':{'k1':'v1'}},
         {'key1':'value2','key2':{'k1':'v2'}}
        ]

   Tuple::

        [('value1', 'uuid1'),
         ('value2', 'uuid2')
        ]

        [('uuid1', 'k1', 'v1'),
         ('uuid2', 'k1', 'v2'),
        ]

   *Note* : uuid* are congress generated uuids
