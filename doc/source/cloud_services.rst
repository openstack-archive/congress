.. include:: aliases.rst

.. _cloudservices:

Configuring Cloud Services
===========================

A Congress policy describes how the services running in the cloud ought to
behave--how the users, scripts, and services running in the cloud are allowed
to change the *state* of the cloud.  The *state* of the cloud is the
amalgamation of the states of all the services running in the cloud.  In order
for Congress to compare the desired state of the cloud (policy) against the
actual state of the cloud, it must be able to figure out what the actual state
of the cloud is--what the actual states of the services running in the cloud
actually are.

To extract the state of a cloud service, Congress needs some basic connection
details about a service, e.g. its IP address and the username/password to use
when communicating.  In addition, Congress needs to know what API calls to
make to extract the state of that service and how to represent that state in a
way that Congress understands.  Thus when you configure a cloud service, you do
two things: send a few API calls to give Congress the necessary connection
details and choose (or in some cases write) a *datasource driver* that makes
API calls and converts the results into the format that Congress understands.

Congress expects the state of any cloud service to be represented as a
collection of *tables* of simple data.  *Tables* are familiar to anyone
who has used Excel, HTML, or a relational database.  A *table* is a
collection of rows, each of which has the same number of columns.  Each
row-column entry in the table must be either a number or a string.   For
example, part of the state of Neutron is a mapping between IP addresses
and the ports they are assigned to, which can be represented in the
following table.

====================================== ==========
ID                                     IP
====================================== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1"
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.2"
"73e31d4c-a49c-11e3-be40-425861b86ab6" "10.0.0.3"
====================================== ==========

Currently, every datasource driver is a piece of Python code that invokes
some number of API calls on a service (whose connection details are provided
as parameters), converts the results of those API calls into tables, and
returns the tables (as a list of tuples).

Datasource drivers are typically (but not necessarily) stored in ::

  congress/congress/datasources/

Once a Python driver is in place, you can use it to create a service whose
data you can refer to in policy.  To create a service, you use the API and
provide a name (the name you will use in policy to refer to the service) and
additional connection details needed by your service (e.g. an IP and a
username/password).  The same driver can be used to create multiple services
(e.g. if you have 2 instances of Neutron, you can create 2 services named say
'neutron_dev' and 'neutron_prod' using the same Python driver).

To configure datasources, you will create a standard Python configuration
file and include a section for each datasource you would like to reference
in policy.  For example, the following config file will create an instance
of Nova and an instance of Neutron::

  [neutron]
  module: datasources/neutron_driver.py
  username: demo
  password: password
  auth_url: http://127.0.0.1:5000/v2.0
  tenant_name: demo

  [nova]
  module: datasources/nova_driver.py
  username: demo
  password: password
  auth_url: http://127.0.0.1:5000/v2.0
  tenant_name: demo

This particular sample is included in the source code and is installed into
/etc/congress/datasources.conf when using the devstack installation procedure.
The original can be found at::

  congress/congress/etc/datasources.conf.sample

In a future release, it will be possible to add new datasources at run-time,
but in the current release, adding a new datasource or changing and existing
datasource's configuration requires restarting the server.


Out of the box datasources
---------------------------
The datasources currently shipping with Congress expose the following tables.
Each table is listed in the form :code:`<tablename>(column1, ... columnm)`.
Roughly, there is one table for each object (e.g. network, virtual machine),
and the columns of that table correspond to the attributes of that object
as returned by the API call for that element.
The value of each row-column entry is either a (Python) string or number. If
the attribute as returned by the API call is a complex object, that object
is flattened into its own table (or tables).  See the comments for more
information.



**Nova**::

  // The virtual machines.
  servers(id, name, host_id, status, tenant_id, user_id, image_id, flavor_id)

  // Flavors
  flavors(id, name, vcpus, ram, disk, ephemeral, rxtx_factor)

  // Hosts
  hosts(host_name, service, zone)

  // Floating IPs
  floating_IPs(fixed_ip, id, ip, host_id, pool)


**Neutron**

There are tables representing networks::

    // networks
    //   SUBNETS field is an ID representing a list of subnets
    //   stored in the networks.subnets table
    networks(status, name, subnet_group_id, provider_physical_network,
             admin_state_up, tenant_id, provider_network_type, router_external,
             shared, id, provider_segmentation_id)

    // Names for lists of subnets.  Join SUBNET_GROUP_ID with SUBNET_GROUP_ID
    //    from NETWORKS table.
    networks.subnets(subnet_group_id, subnet_id)

There are also tables representing ports::

    // ports
    // Just as the SUBNETS field of a network is represented in a separate
    //    table, so too several of the fields of a port are represented
    //    in separate tables.
    // All of the following COLUMN -> TABLENAME mean that column COLUMN
    //   is an ID referencing one or more rows in table TABLENAME.
    // allowed_address_pairs -> ports.address_pairs
    // security_groups -> ports.security_groups
    // binding_capabilities -> ports.binding_capabilities
    // fixed_ips_group -> ports.fixed_ips_groups
    // extra_dhcp_opts -> ports.extra_dhcp_opts
    ports(allowed_address_pairs, security_groups, extra_dhcp_opts,
          binding_capabilities, status, name, admin_state_up, network_id,
          tenant_id, binding_vif_type, device_owner, mac_address,
          fixed_ips_group, id, device_id, binding_host_id)

    // lists of port addresses
    //  There may be 0, 1, or more port addresses per group id
    ports.address_pairs(group_id, port_address)

    // lists of security group IDs
    //  There may be 0, 1, or more port security groups per group id
    ports.security_groups(group_id, security_group_id)

    // dictionaries of key/value pairs representing binding capabilities
    ports.binding_capabilities(id, key, value)

    // lists of fixed_ip IDs
    //  There may be 0, 1, or more fixed_ips per id
    ports.fixed_ips_groups(id, fixed_ip_id)

    // dictionaries of key/value pairs representing fixed_ips
    ports.fixed_ips(id, key, value)

    // lists of extra dhcp options
    //  There may be 0, 1, or more options per id
    ports.extra_dhcp_opts(id, option)

There are tables representing routers and security groups::

    // routers
    // If EXTERNAL_GATEWAY_INFO is non-None, it is populated
    //   with <Placeholder>.  (Obviously this is a temporary hack.)
    routers(status, external_gateway_info, networks, name, admin_state_up,
            tenant_id, id)


    // security groups
    security_groups(tenant_id, name, description, id)


.. _datasource_driver:

Writing a Datasource Driver
----------------------------

This section is a tutorial for those of you interested in writing your own
datasource driver.  It can be safely skipped otherwise.

Implementing a Datasource Driver
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All the Datasource drivers extend the code found in
:code:`congress/datasources/datasource_driver.py`.  Typically, you will create
a subclass of DataSourceDriver; each instance of that class will correspond to
a different service using that driver.

The following steps detail how to implement a datasource driver.

1. Create a new Python module and include 1 static method

  :code:`d6service(name, keys, inbox, datapath, args)`

  When a service is created, Congress calls ``d6service`` on the appropriate
  driver module to construct an instance of DataSourceDriver tailored for that
  service.

  ``name``, ``keys``, ``inbox``, and ``datapath`` are all arguments that
  should be passed unaltered to the constructor of the DataSourceDriver
  subclass.

2. Create a subclass of :code`DataSourceDriver`.

  :code:`from congress.datasources.datasource_driver import DataSourceDriver`

  :code:`class MyDriver(DataSourceDriver)`

3. Implement the constructor :func:`MyDriver.__init__`

  :code:`def __init__(name, keys, inbox, datapath, args)`

  You must call the DataSourceDriver's constructor.

  :code:`super(NeutronDriver, self).__init__(name, keys, inbox=inbox,
  datapath=datapath, poll_time=poll_time, creds`

4. Implement the function :func:`MyDriver.update_from_datasource`

  :code:`def update_from_datasource(self)`

  This function is called to update :code:`self.state` to reflect the new
  state of the service.  :code:`self.state` is a dictionary that maps a
  tablename (as a string) to a set of tuples (to a collection of tables).
  Each tuple element must be either a number or string.  This function
  implements the polling logic for the service.

5. By convention, it is useful for debugging purposes to include a
:code:`main` that calls update_from_datasource, and prints out the raw
API results along with the tables that were generated.

Converting API results into Tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Since Congress requires the state of each dataservice to be represented as
tables, we must convert the results of each API call (which may be comprised
of dictionaries, lists, dictionaries embedded within lists, etc.) into tables.

While this translation is more of an art than a science, we have a
few recommendations.

**Recommendation 1: Row = object.** Typically an API call will return a
collection of objects (e.g. networks, virtual machines, disks).  Conceptually
it is convenient to represent each object with a row in a table.  The columns
of that row are the attributes of each object.  For example, a table of all
virtual machines will have columns for memory, disk, flavor, and image.

Table: virtual_machine

====================================== ====== ==== ====== =====================================
ID                                     Memory Disk Flavor Image
====================================== ====== ==== ====== =====================================
66dafde0-a49c-11e3-be40-425861b86ab6   256GB  1TB  1      83e31d4c-a49c-11e3-be40-425861b86ab6
73e31d4c-a49c-11e3-be40-425861b86ab6   10GB   2TB  2      93e31d4c-a49c-11e3-be40-425861b86ab6
====================================== ====== ==== ====== =====================================


**Recommendation 2. Avoid wide tables.**  Wide tables (i.e. tables with many
columns) are hard to use for a policy-writer.  Breaking such tables up into
smaller ones is often a good idea.  In the above example, we could create 4
tables with 2 columns instead of 1 table with 5 columns.

Table: virtual_machine.memory

====================================== ======
ID                                     Memory
====================================== ======
66dafde0-a49c-11e3-be40-425861b86ab6   256GB
73e31d4c-a49c-11e3-be40-425861b86ab6   10GB
====================================== ======

Table: virtual_machine.disk

====================================== ======
ID                                     Disk
====================================== ======
66dafde0-a49c-11e3-be40-425861b86ab6   1TB
73e31d4c-a49c-11e3-be40-425861b86ab6   2TB
====================================== ======

Table: virtual_machine.flavor

====================================== ======
ID                                     Flavor
====================================== ======
66dafde0-a49c-11e3-be40-425861b86ab6   1
73e31d4c-a49c-11e3-be40-425861b86ab6   2
====================================== ======

Table: virtual_machine.image

====================================== =====================================
ID                                     Image
====================================== =====================================
66dafde0-a49c-11e3-be40-425861b86ab6   83e31d4c-a49c-11e3-be40-425861b86ab6
73e31d4c-a49c-11e3-be40-425861b86ab6   93e31d4c-a49c-11e3-be40-425861b86ab6
====================================== =====================================


**Recommendation 3. Try these design patterns.** Below we give a few design
patterns.  Notice that when an object has an attribute whose value is a
structured object itself (e.g. a list of dictionaries), we must recursively
flatten that subobject into tables.

- A List of dictionary converted to tuples

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
