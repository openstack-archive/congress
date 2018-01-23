
.. _ha_deployment:

#############
HA Deployment
#############

Overview
========

This section shows how to deploy Congress with High Availability (HA). For an
architectural overview, please see the :ref:`HA Overview <ha_overview>`.

An HA deployment of Congress involves five main steps.

#. Deploy messaging and database infrastructure to be shared by all the
   Congress nodes.
#. Prepare the hosts to run Congress nodes.
#. Deploy N (at least 2) policy-engine nodes.
#. Deploy one datasource-drivers node.
#. Deploy a load-balancer to load-balance between the N policy-engine nodes.

The following sections describe each step in more detail.


Shared Services
===============

All the Congress nodes share a database backend. To setup a database backend
for Congress, please follow the database portion of
`separate install instructions`__.

__ https://docs.openstack.org/congress/latest/install/index.html#separate-install

Various solutions exist to avoid creating a single point of failure with the
database backend.

Note: If a replicated database solution is used, it must support table
locking. Galera, for example, would not work. This limitation is expected to
be removed in the Ocata release.

A shared messaging service is also required. Refer to `Shared Messaging`__ for
instructions for installing and configuring RabbitMQ.

__ https://docs.openstack.org/ha-guide/shared-messaging.html


Hosts Preparation
=================

Congress should be installed on each host expected to run a Congress node.
Please follow the directions in `separate install instructions`__ to install
Congress on each host, skipping the local database portion.

__ https://docs.openstack.org/congress/latest/install/index.html#separate-install

In the configuration file, a ``transport_url`` should be specified to use the
RabbitMQ messaging service configured in step 1.

For example:

.. code-block:: text

    [DEFAULT]
    transport_url = rabbit://<rabbit-userid>:<rabbit-password>@<rabbit-host-address>:5672

In addition, the ``replicated_policy_engine`` option should be set to ``True``.

.. code-block:: text

    [DEFAULT]
    replicated_policy_engine = True

All hosts should be configured with a database connection that points to the
shared database deployed in step 1, not the local address shown in
`separate install instructions`__.

__ https://docs.openstack.org/congress/latest/install/index.html#separate-install

For example:

.. code-block:: text

    [database]
    connection = mysql+pymysql://root:<database-password>@<shared-database-ip-address>/congress?charset=utf8


Datasource Drivers Node
=======================

In this step, we deploy a single datasource-drivers node in warm-standby style.

The datasource-drivers node can be started directly with the following command:

.. code-block:: console

   $ python /usr/local/bin/congress-server --datasources --node-id=<unique_node_id>

A unique node-id (distinct from all the policy-engine nodes) must be specified.

For warm-standby deployment, an external manager is used to launch and manage
the datasource-drivers node. In this document, we sketch how to deploy the
datasource-drivers node with `Pacemaker`_ .

See the `OpenStack High Availability Guide`__ for general usage of Pacemaker
and how to deploy Pacemaker cluster stack. The guide also has some HA
configuration guidance for other OpenStack projects.

__ https://docs.openstack.org/ha-guide/index.html
.. _Pacemaker: http://clusterlabs.org/

Prepare OCF resource agent
----------------------------

You need a custom Resource Agent (RA) for DataSoure Node HA. The custom RA is
located in Congress repository, ``/path/to/congress/script/ocf/congress-datasource``.
Install the RA with following steps.

.. code-block:: sh

  $ cd /usr/lib/ocf/resource.d
  $ mkdir openstack
  $ cd openstack
  $ cp /path/to/congress/script/ocf/congress-datasource ./congress-datasource
  $ chmod a+rx congress-datasource

Configuring the Resource Agent
-------------------------------

You can now add the Pacemaker configuration for Congress DataSource Node resource.
Connect to the Pacemaker cluster with the *crm configure* command and add the
following cluster resources. After adding the resource make sure *commit*
the change.

.. code-block:: sh

  primitive ds-node ocf:openstack:congress-datasource \
     params config="/etc/congress/congress.conf" \
     node_id="datasource-node" \
     op monitor interval="30s" timeout="30s"

Make sure that all nodes in the cluster have same config file with same name and
path since DataSource Node resource, ``ds-node``, uses config file defined at
*config* parameter to launch the resource.

The RA has following configurable parameters.

* config: a path of Congress's config file
* node_id(Option): a node id of the datasource node. Default is "datasource-node".
* binary(Option): a path of Congress binary Default is "/usr/local/bin/congress-server".
* additional_parameters(Option): additional parameters of congress-server


Policy Engine Nodes
===================

In this step, we deploy N (at least 2) policy-engine nodes, each with an
associated API server. This step should be done only after the
`Datasource Drivers Node`_ is deployed. Each node can be started as follows:

.. code-block:: console

   $ python /usr/local/bin/congress-server --api --policy-engine --node-id=<unique_node_id>

Each node must have a unique node-id specified as a commandline option.

For high availability, each node is usually deployed on a different host. If
multiple nodes are to be deployed on the same host, each node must have a
different port specified using the ``bind_port`` configuration option in the
congress configuration file.


Load-balancer
=============

A load-balancer should be used to distribute incoming API requests to the N
policy-engine (and API service) nodes deployed in step 3.
It is recommended that a sticky configuration be used to avoid exposing a user
to out-of-sync artifacts when the user hits different policy-engine nodes.

`HAProxy <http://www.haproxy.org/>`_ is a popular load-balancer for this
purpose. The HAProxy section of the `OpenStack High Availability Guide`__
has instructions for deploying HAProxy for high availability.

__ https://docs.openstack.org/ha-guide/index.html
