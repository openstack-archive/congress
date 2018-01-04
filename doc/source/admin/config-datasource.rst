.. _config_datasource:

#####################
The config datasource
#####################

Overview
========

The config datasource is a Congress datasource that let you
access the definition of configuration options of Openstack
services on the nodes of the cloud.

Its main purpose is to let administrator check the coherence
of a deployment by defining constraints on the value of those
options.

To retrieve the configuration files, the datasource uses an agent that must be configured on the various nodes.

Agent configuration options
===========================

Please refer to :ref:`config` for the generation of a sample configuration file (``etc/congress-agent.conf.sample``).

The options most important to the agent are described below. They all appear under the ``[agent]`` section of the configuration file.

``host``
    The name of the host as it will appear in the Congress
    tables.

``version``
    This is the Openstack version used on the host. It can be
    used for rules that only apply to a given version of a service. Standard version names in lowercase should be used (e.g. ``ocata``, ``pike``).

``services``
    This is a dictionary that associates to each service
    (use standard service names in lowercase), a description
    of its configuration file. The description is itself
    a dictionary. Keys are the paths to the configuration
    files and values are the path to the template
    definitions of the configuration files for oslo-config
    generator.

The agent also requires a valid configuration of the message bus as it uses it to communicate with the datasource driver.

An example of configuration file is the following:

.. code-block:: text

    [DEFAULT]
    transport_url = rabbit://...

    [cfg_validator]
    host = compute-node-001
    version = pike
    services = nova: { /etc/nova/nova.conf:/opt/stack/nova/etc/nova/nova-config-generator.conf },neutron: { /etc/neutron/neutron.conf:/opt/stack/neutron/etc/oslo-config-generator/neutron.conf },congress: { /etc/congress/congress.conf:/opt/stack/congress/etc/congress-config-generator.conf }
