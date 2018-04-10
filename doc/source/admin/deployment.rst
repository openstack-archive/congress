
.. _deployment:

==========
Deployment
==========
Congress has two modes for deployment: single-process and multi-process.
If you are interested in test-driving Congress or are not concerned
about high-availability, the single-process deployment is best because it
is easiest to set up.  If you are interested in making Congress highly-available
you want the multi-process deployment.

In the single-process version, you run Congress as a single operating-system
process on one node (i.e. container, VM, physical machine).

In the multi-process version, you start with the 3 components of Congress
(the API, the policy engine, and the datasource drivers).  You choose how many
copies of each component you want to run, how you want to distribute those
components across processes, and how you want to distribute those processes
across nodes.

Section :ref:`config` describes the common configuration options for both
single-process and multi-process deployments.  After that :ref:`ha_overview`
and :ref:`ha_deployment` describe how to set up the multi-process deployment. Section :ref:`config_datasource`
describes how to configure agents on the various nodes to use the ``config`` datasource.

.. _config:

---------------------
Configuration Options
---------------------

In this section we highlight the configuration options that are specific
to Congress.  To generate a sample configuration file that lists all
available options, along with descriptions, run the following commands::

    $ cd /path/to/congress

Install tox::

    $ pip install tox

Generate config::

    $ tox -egenconfig

The tox command will create the file ``etc/congress.conf.sample``, which has
a comprehensive list of options.  All options have default values, which
means that even if you specify no options Congress will run.

The options most important to Congress are described below, all of which
appear under the [DEFAULT] section of the configuration file.

``datasource_sync_period``
    The number of seconds to wait between synchronizing datasource config
    from the database.  Default is 0.

``enable_execute_action``
    Whether or not congress will execute actions.  If false, Congress will
    never execute any actions to do manual reactive enforcement, even if there
    are policy statements that say actions should be executed and the
    conditions of those actions become true.  Default is True.

One of Congress's new experimental features is distributing its services
across multiple services and even hosts.  Here are the options for using
that feature.

``bus_id``
    Unique ID of DSE bus.  Can be any string. Defaults to 'bus'.
    ID should be same across all the processes of a single congress instance
    and should be unique across different congress instances.
    Used if you want to create multiple, distributed instances of Congress and
    can be ignored if only one congress instance is deployed as single process
    in rabbitMQ cluster. Appears in the [dse] section.

Here are the most often-used, but standard OpenStack options.  These
are specified in the [DEFAULT] section of the configuration file.

``auth_strategy``
    Method for authenticating Congress users.
    Can be assigned to either 'keystone' meaning that the user must provide
    Keystone credentials or to 'noauth' meaning that no authentication is
    required.  Default is 'keystone'.

``verbose``
    Controls whether the INFO-level of logging is enabled.  If false, logging
    level will be set to WARNING.  Default is true.  Deprecated.

``debug``
    Whether or not the DEBUG-level of logging is enabled. Default is false.

``transport_url``
    URL to the shared messaging service. It is not needed in a single-process
    Congress deployment, but must be specified in a multi-process Congress
    deployment.

.. code-block:: text

    [DEFAULT]
    transport_url = rabbit://<rabbit-userid>:<rabbit-password>@<rabbit-host-address>:<port>

-------------
HA Deployment
-------------

.. toctree::
   :maxdepth: 2

   ha-overview
   ha-deployment

---------------------
The Config Datasource
---------------------

.. toctree::
   :maxdepth: 2

   config-datasource
