===================================
JGress: policy over JSON data model
===================================


Introduction
============
JGress (JSON data model for Congress) is an experimental framework that allows
an operator to query, monitor, and automate clouds using JSON queries/views.
In short, Congress capabilities over a JSON data model.

JGress is designed to capture the state of a cloud from controllers (Nova,
Neutron, EC2, etc) and alarms (Monasca, Vitrage, Zabbix, etc.) in the form of
a JSON database. The framework enables an operator to perform policy-based
monitoring using queries and views. The framework also allows an operator to
define remedial actions and workflows (Mistral, Heat, etc.) in response to
declarative conditions.

JGress can be thought of as a kind of declarative "glue" layer that helps
different services work together while avoiding the N-squared problem with
1:1 integrations.

.. _jgress_policy:

Examples
========
This brief introduction demonstrates the capabilities through a series of
simple examples. For reference on the data used in the examples,
please see the `data representation`_ section.

Example 1: ad-hoc query
-----------------------
Suppose there has been some significant outage and many hosts are down.
Auto evacuation either was not configured or partially failed. An admin wants
to find out which hosts have the most affected VMs.

The admin can use the following query to list the host by number of VMs
affected.

.. code-block:: sql

    SELECT d ->> 'hostId' AS host_id,
           Count(*)       AS down
    FROM   _compute.servers
    WHERE  d ->> 'host_status' = 'DOWN'
    GROUP  BY host_id
    ORDER  BY down DESC
    LIMIT  5;

Note:
The ``->>`` operator accesses the content of a JSON object field and returns
the result as text.

Example result:

::

     host_id | down
    ---------+------
     host-13 |   11
     host-57 |   10
     host-08 |   10
     host-74 |   10
     host-22 |    9

Example 2: ad-hoc query
-----------------------
Continuing from the above example, perhaps the admin is interested only in the
production workloads. Then a simple addition to the filtering condition finds
the results. (Production workloads are indicated by tag: ``production`` in this
example, but can be replaced by filtering on any available metadata).

.. code-block:: sql

    SELECT   d->>'hostId' AS host_id,
             Count(*)     AS down
    FROM   _compute.servers
    WHERE    d->>'host_status' = 'DOWN'
    AND      d->'tags' ? 'production'
    GROUP BY host_id

    ORDER BY down DESC
    LIMIT  5;

Note:
The ``->`` operator accesses the content of a JSON object field and returns the
result as JSON. In this example, ``d->'tags'`` returns the array of tags
associated with each server.
The ``?`` operator checks that a string is a top-level key/element in a JSON
structure. In this example, the ``d->'tags' ? 'production'`` condition checks
that the string ``'production'`` is in the array of tags retrieved by
``d->'tags'``.

Example result:

::

     host_id | down
    ---------+------
     host-75 |    4
     host-19 |    4
     host-39 |    4
     host-63 |    3
     host-27 |    3

Example 3: Monitoring
---------------------
The system can also be used for ongoing monitoring to identify problematic
situations. For example, we may expect all critical workloads VMs are protected
by Masakari instance HA. We can monitor for any exceptions by defining the
following view for JGress or another tool to monitor.

.. code-block:: sql

    CREATE VIEW critical_vm_ha.problem AS
    SELECT d->>'id' AS server_id
    FROM   _compute.servers
    WHERE  d->'tags' ? 'critical'
    AND    NOT d->'metadata' @> '{"HA_Enabled": true}';

Note:
The ``@>`` operator checks that the left JSON value contain the right JSON
value. In this example, the ``d->'metadata' @> '{"HA_Enabled": true}'``
condition checks that the metadata contains the ``'HA_Enabled'`` field and the
field is set to true.

Example result:

::

     server_id
    ------------
     server-536
     server-556
     server-939
     server-517
     server-811

Example 4: Remediation
----------------------

Going one step further, we can create a view that defines which APIs to call
(for example a Mistral workflow) to rectify the problem of the non-HA critical
VM. JGress monitors the view and makes the REST API calls as defined by the
view.

.. code-block:: sql

    CREATE VIEW critical_vm_ha._exec_api AS
    SELECT '_mistral'                    AS endpoint,
           '/executions'                 AS path,
           'POST'                        AS method,
           Format('{
                     "workflow_name": "make_server_ha",
                     "params": {"server_id": "%s"}}', server_id)
                                         AS body,
           NULL                          AS parameters,
           NULL                          AS headers,
    FROM   critical_vm_ha.problem;

Note:
``_mistral`` is the name of the endpoint configured to accept requests for
API executions to OpenStack Mistral service.

Example 5: combining multiple sources of data
---------------------------------------------
Here’s a slightly more complex example to demonstrate that the queries can span
multiple cloud services. In this case, we want to identify the problematic
situation where production workloads use images considered unstable. The
following view accomplishes the goal by combining server information from Nova
and image information from Glance, then filtering on the tag information.

.. code-block:: sql

    CREATE SCHEMA production_stable;
    CREATE VIEW production_stable.problem AS
    SELECT server.d->>'id'                AS server_id,
           image.d->>'id'                 AS image_id
    FROM   _compute.servers server
    JOIN   _image.images image
    ON     server.d->'image'->'id' = image.d->'id'
    WHERE  (server.d->'tags' ? 'production')
    AND    (image.d->'tags' ? 'unstable');

Note: see image document format in the `Glance API documentation
<https://developer.openstack.org/api-ref/image/v2/index.html?expanded=list-images-detail#id11>`_.

Example result:

::

     server_id    | image_id
    --------------+-----------
     server-386   | image-6
     server-508   | image-0
     server-972   | image-3
     server-746   | image-3
     server-999   | image-0

Example 6: using helper views
-----------------------------

It’s not always convenient to write queries directly on the source data. For
example, a query to determine which servers have internet connectivity is
rather complex and would be cumbersome to repeat in every query requiring that
information. This is where helper views are useful. Suppose we have defined the
view internet_access.servers which is the subset of _compute.servers with
security group configuration that allows internet connectivity. Then we can use
the view to define the following view which identifies internet connected
servers running on an image not tagged as approved by the security team.

.. code-block:: sql

    CREATE SCHEMA internet_security;
    CREATE VIEW internet_security.problem AS
    SELECT server.d->>'id'                AS server_id,
           image.d->>'id'                 AS image_id
    FROM   internet_access.servers server
    JOIN   _image.images image
    ON     server.d->'image'->'id' = image.d->'id'
    WHERE  NOT image.d->'tags' ? 'security-team-approved';

Note: see image document format in the `Glance API documentation
<https://developer.openstack.org/api-ref/image/v2/index.html?expanded=list-images-detail#id11>`_.

Example result:

::

      server_id   | image_id
    --------------+-----------
      server-705  | image-1
      server-264  | image-0
      server-811  | image-0
      server-224  | image-4
      server-508  | image-0

Example 7: using webhook alarm notification
-------------------------------------------
Some cloud services supports sending webhook notifications. For example, the
Monasca monitoring service can be configured to send webhook notifications of
alarm updates. JGress can be configured to received these webhook notifications
and insert the new data into the database (replacing old entries as needed).
Here is an example of using such webhook notification data from Monasca to flag
critical workloads running on hypervisors where the CPU load is too high for
comfort.

.. code-block:: sql

    CREATE VIEW host_cpu_high.problem AS
    SELECT server.d->>'id'            AS server_id,
           server.d->>'hostId'        AS host_id
    FROM   _compute.servers server
    JOIN   _monasca.webhook_alarms alarm
    ON     server.d->'OS-EXT-SRV-ATTR:hypervisor_hostname' IN
           (SELECT value->'dimensions'->'hostname'
            FROM   Jsonb_array_elements(alarm.d->'metrics'))
    WHERE  alarm.d->>'alarm_name' = 'high_cpu_load'
    AND    alarm.d->>'state' = 'ALARM';


Data representation
===================
The examples above use OpenStack Nova (compute service)
`API response data <https://developer.openstack.org/api-ref/compute/?expanded=list-servers-detailed-detail#id22>`_ on
servers, stored in a PostgreSQL
`JSONB <https://blog.2ndquadrant.com/nosql-postgresql-9-4-jsonb/>`_ column.

Each server is represented as a JSON document as provided by the Nova API.

Sample server data (simplified):

.. code-block:: json

    {
       "id":"server-134",
       "name":"server 134",
       "status":"ACTIVE",
       "tags":[
          "production",
          "critical"
       ],
       "hostId":"host-05",
       "host_status":"ACTIVE",
       "metadata":{
          "HA_Enabled":false
       },
       "tenant_id":"tenant-52",
       "user_id":"user-830"
    }

The ``_compute.servers`` table is the collection of all the JSON documents
representing servers, each document in a row with a column ``d`` containing the
document.

The content of each JSON document is accessible using the JSON operators
provided by PostgreSQL.

Additional data sources are available, each in the original format of the
source JSON API representation. To see all data sources available, use the
``\dn`` command in a ``psql`` console to list the schemas.


Sample policies
===============

Additional sample policies can be found here:

https://github.com/openstack/congress/tree/master/doc/source/user/jgress_sample_policies

Each policy can be imported using:

.. code-block:: console

    $ psql <connection_url> -f <policy_file.sql>


Connecting to PostgreSQL
========================
To interact with JGress data, connect to the JGress PostgreSQL database using
any compatible client. Examples include the command-line client ``psql``
and the browser-based client `pgweb <https://pgweb-demo.herokuapp.com/>`_.

For example, here is how to connect using psql:

.. code-block:: console

    $ psql postgresql://<user>:<password>@<host>/<jgress_database>

If on the controller node of a :ref:`devstack installation <devstack_install>`,
the default values are as follows:

.. code-block:: console

    $ psql postgresql://jgress_user:<password>@127.0.0.1/congress_json


Language reference
==================

* `PostgreSQL JSON syntax cheat sheet
  <https://hackernoon.com/how-to-query-jsonb-beginner-sheet-cheat-4da3aa5082a3>`_

* `PostgreSQL JSON operators and functions
  <https://www.postgresql.org/docs/9.6/functions-json.html>`_

* `PostgreSQL language reference
  <https://www.postgresql.org/docs/9.6/sql.html>`_
