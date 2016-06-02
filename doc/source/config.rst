.. include:: aliases.rst

.. _config:

=====================
Configuration Options
=====================

In this section we highlight the configuration options that are specific
to Congress.  To generate a sample configuration file that lists all
available options, along with descriptions run the following commands::

    $ cd /path/to/congress
    $ tox -egenconfig

The tox command will create the file ``etc/congress.conf.sample``, which has
a comprehensive list of options.  All options have default values, which
means that even if you specify no options Congress will run.

The options most important to Congress are described below, all of which
appear under the [DEFAULT] section of the configuration file.

``drivers``
    The list of permitted datasource drivers.  Default is the empty list.
    The list is a comma separated list of Python class paths. For example:
    drivers = congress.datasources.neutronv2_driver.NeutronV2Driver,congress.datasources.glancev2_driver.GlanceV2Driver

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

``distributed_architecture``
    Whether to enable the distributed architecture.  Don't set it to true in
    before Newton release since the new architecture is still under
    development as of Newton.  Default is false.  Appears in [DEFAULT] section.

``node_id``
    Unique ID of this Congress instance.  Can be any string.  Useful if
    you want to create multiple, distributed instances of Congress.  Appears
    in the [DSE] section.

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
