.. include:: aliases.rst

.. _ha_deployment:


=============
HA Deployment
=============

Overview
--------

This section shows how to deploy Congress with High Availability (HA).
Congress is divided to 2 parts in HA. First part is API and PolicyEngine
Node which is replicated with Active-Active style. Another part is
DataSource Node which is deployed with warm-standby style. Please see the
:ref:`HA Overview <ha_overview>` for details.

.. code-block:: text

  +-------------------------------------+      +--------------+
  |       Load Balancer (eg. HAProxy)   | <----+ Push client  |
  +----+-------------+-------------+----+      +--------------+
       |             |             |
  PE   |        PE   |        PE   |        all+DSDs node
  +---------+   +---------+   +---------+   +-----------------+
  | +-----+ |   | +-----+ |   | +-----+ |   | +-----+ +-----+ |
  | | API | |   | | API | |   | | API | |   | | DSD | | DSD | |
  | +-----+ |   | +-----+ |   | +-----+ |   | +-----+ +-----+ |
  | +-----+ |   | +-----+ |   | +-----+ |   | +-----+ +-----+ |
  | | PE  | |   | | PE  | |   | | PE  | |   | | DSD | | DSD | |
  | +-----+ |   | +-----+ |   | +-----+ |   | +-----+ +-----+ |
  +---------+   +---------+   +---------+   +--------+--------+
       |             |             |                 |
       |             |             |                 |
       +--+----------+-------------+--------+--------+
          |                                 |
          |                                 |
  +-------+----+   +------------------------+-----------------+
  |  Oslo Msg  |   | DBs (policy, config, push data, exec log)|
  +------------+   +------------------------------------------+


HA for API and Policy Engine Node
---------------------------------

New config settings for setting the DSE node type:

- N (>=2 even okay) nodes of PE+API node

  .. code-block:: console

    $ python /usr/local/bin/congress-server --api --policy-engine --node-id=<api_unique_id>

- One single DSD node

  .. code-block:: console

    $ python /usr/local/bin/congress-server --datasources --node-id=<datasource_unique_id>

HA for DataSource Node
----------------------

Nodes which DataSourceDriver runs on takes warm-standby style. Congress assumes
cluster manager handles the active-standby cluster. In this document, we describe
how to make HA of DataSourceDriver node by `Pacemaker`_ .

See the `OpenStack High Availability Guide`__ for general usage of Pacemaker
and how to deploy Pacemaker cluster stack. The guide has some HA configuration
for other OpenStack projects.

__ http://docs.openstack.org/ha-guide/index.html
.. _Pacemaker: http://clusterlabs.org/

Prepare OCF resource agent
==========================

You need a custom Resource Agent (RA) for DataSoure Node HA. The custom RA is
located in Congress repository, ``/path/to/congress/script/ocf/congress-datasource``.
Install the RA with following steps.

.. code-block:: sh

  $ cd /usr/lib/ocf/resource.d
  $ mkdir openstack
  $ cd openstack
  $ cp /path/to/congress/script/ocf/congress-datasource ./congress-datasource
  $ chmod a+rx congress-datasource

Configure RA
============

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