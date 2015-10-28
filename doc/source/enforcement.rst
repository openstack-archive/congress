.. include:: aliases.rst

.. _enforcement:


==========================
Monitoring and Enforcement
==========================

Congress is given two inputs: the other cloud
services in the datacenter and a policy describing the desired state of those
services.  Congress does two things with those inputs: monitoring and
enforcement.  *Monitoring* means passively comparing the actual state of the
other cloud services and the desired state (i.e. policy) and flagging
mismatches. *Enforcement* means actively working
to ensure that the actual state of the other cloud services is also a desired
state (i.e. that the other services obey policy).

1. Monitoring
=============
Recall from :ref:`Policy <policy>` that policy violations are represented with the
table *error*.  To ask Congress for a list of all policy violations, we
simply ask it for the contents of the *error* table.

For example, recall our policy from :ref:`Policy <policy>`: each Neutron port has at
most one IP address.  For that policy, the *error* table is has 1 row for
each Neutron port that has more than 1 IP address.  Each of those rows
specify the UUID for the port, and two different IP addresses.  So if we
had the following mapping of Neutron ports to IP addresses:

====================================== ==========
ID                                     IP
====================================== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1"
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.2"
"73e31d4c-e89b-12d3-a456-426655440000" "10.0.0.3"
"73e31d4c-e89b-12d3-a456-426655440000" "10.0.0.4"
"8caead95-67d5-4f45-b01b-4082cddce425" "10.0.0.5"
====================================== ==========

the *error* table would be something like the one shown below.

====================================== ========== ==========
ID                                     IP 1       IP 2
====================================== ========== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1" "10.0.0.2"
"73e31d4c-e89b-12d3-a456-426655440000" "10.0.0.3" "10.0.0.4"
====================================== ========== ==========

The API would return this table as the following collection of Datalog facts
(encoded as a string)::

    error("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.1", "10.0.0.2")
    error("73e31d4c-e89b-12d3-a456-426655440000", "10.0.0.3", "10.0.0.4")

It is the responsibility of the client to periodically ask the server for the
contents of the error table.


2. Proactive Enforcement
========================
Often we want policy to be enforced, not just monitored.  *Proactive
enforcement* is the term we use to mean preventing policy violations before
they occur.  Proactive enforcement requires having enforcement points in the
cloud that stop changes before they happen.  Cloud services like Nova,
Neutron, and Cinder are good examples of enforcement points.  For example,
Nova could refuse to provision a VM that would cause a policy violation,
thereby proactively enforcing policy.

To enable other cloud services like Nova to check if a proposed change in the
cloud state would violate policy, the cloud service can consult Congress
using its :func:`simulate` functionality. The idea for :func:`simulate` is
that we ask Congress to answer a query after having
temporarily made some changes to data and policies.  Simulation allows us to
explore the effects of proposed changes.  Typically simulation is used to ask:
if I made these changes, would there be any new policy violations?
For example, provisioning a new VM might add rows to several of Nova's tables.
After receiving an API call that requests a new VM be provisioned, Nova could
ask Congress if adding those rows would create any new policy violations.
If new violations arise, Nova could refuse to provision the VM, thereby
proactively enforcing the policy.


In this writeup we assume you are using the python-client.

Suppose you want to know the policy violations after making the following
changes.

  1.  insert a row into the *nova:servers* table with ID uuid1, 2TB of disk,
      and 10GB of memory
  2.  delete the row from *neutron:security_groups* with the ID “uuid2” and name
      “alice_default_group”

(Here we assume the nova:servers table has columns ID, disk-size, and memory
and that neutron:security groups has columns ID, and name.)

To do a simulation from the command line, you use the following command::

    $ openstack congress policy simulate <policy-name> <query> <change-sequence> <action-policy-name>

* <policy-name>: the name of the policy in which to run the query
* <query>: a string representing the query you would like to run after
  applying the change sequence
* <change-sequence>: a string codifying a sequence of insertions and deletions
  of data and rules.  Insertions are denoted by '+' and deletions by '-'
* <action-policy-name>: the name of another policy of type 'action' describing
  the effects of any actions occurring in <change-sequence>.  Actions are not
  necessary and are explained later.  Without actions, this argument can be
  anything (and will in the future be optional).

For our nova:servers and neutron:security_groups example, we would run the
following command to find all of the policy violations after inserting a row
into nova:servers and then deleting a row out of neutron:security_groups::

    $ openstack congress policy simulate classification
        'error(x)’
        'nova:servers+(“uuid1”, “2TB”, “10 GB”)
         neutron:security_groups-(“uuid2”, “alice_default_group”)'
        action

**More examples**

Suppose the table 'p' is a collection of key-value pairs:  p(key, value).
Let's begin by creating a policy and adding some key/value pairs for 'p'::

    $ openstack congress policy create alice
    $ openstack congress policy rule create alice 'p(101, 0)'
    $ openstack congress policy rule create alice 'p(202, "abc")'
    $ openstack congress policy rule create alice 'p(302, 9)'

Let's also add a statement that says there's an error if a single key has
multiple values or if any value is assigned 9::

    $ openstack congress policy rule create alice
        'error(x) :- p(x, val1), p(x, val2), not equal(val1, val2)'
    $ openstack congress policy rule create alice 'error(x) :- p(x, 9)'


Each of the following is an example of a simulation query you might want to run.

a) **Basic usage**. Simulate adding the value 5 to key 101 and ask for the contents of p::

    $ openstack congress policy simulate alice 'p(x,y)' 'p+(101, 5)' action
    p(101, 0)
    p(101, 5)
    p(202, "abc")
    p(302, 9)

b) **Error table**. Simulate adding the value 5 to key 101 and ask for the contents of error::

    $ openstack congress policy simulate alice 'error(x)' 'p+(101, 5)' action
    error(101)
    error(302)

c) **Inserts and Deletes**. Simulate adding the value 5 to key 101 and deleting 0 and ask for the contents of error::

    $ openstack congress policy simulate alice 'error(x)'
        'p+(101, 5) p-(101, 0)' action
    error(302)


d) **Error changes**. Simulate changing the value of key 101 to 9 and query the **change** in the error table::

    $ openstack congress policy simulate alice 'error(x)'
        'p+(101, 9) p-(101, 0)' action --delta
    error+(101)


f) **Multiple error changes**. Simulate changing 101:9, 202:9, 302:1 and query the *change* in the error table::

    $ openstack congress policy simulate alice 'error(x)'
        'p+(101, 9) p-(101, 0) p+(202, 9) p-(202, "abc") p+(302, 1) p-(302, 9)'
        action --delta
    error+(202)
    error+(101)
    error-(302)


g) **Order matters**. Simulate changing 101:9, 202:9, 302:1, and finally 101:15 (in that order).  Then query the *change* in the error table::

    $ openstack congress policy simulate alice 'error(x)'
        'p+(101, 9) p-(101, 0) p+(202, 9) p-(202, "abc") p+(302, 1) p-(302, 9)
         p+(101, 15) p-(101, 9)' action --delta
    error+(202)
    error-(302)


h) **Tracing**. Simulate changing 101:9 and query the *change* in the error table, while asking for a debug trace of the computation::

    $ openstack congress policy simulate alice 'error(x)'
        'p+(101, 9) p-(101, 0)' action --delta --trace
    error+(101)
    RT    : ** Simulate: Querying error(x)
    Clas  : Call: error(x)
    Clas  : | Call: p(x, 9)
    Clas  : | Exit: p(302, 9)
    Clas  : Exit: error(302)
    Clas  : Redo: error(302)
    Clas  : | Redo: p(302, 9)
    Clas  : | Fail: p(x, 9)
    Clas  : Fail: error(x)
    Clas  : Found answer [error(302)]
    RT    : Original result of error(x) is [error(302)]
    RT    : ** Simulate: Applying sequence [set(101, 9)]
    Action: Call: action(x)
    ...

i) **Changing rules**.  Simulate adding 101: 5 (which results in 101 having 2 values) and deleting the rule that says each key must have at most 1 value. Then query the error table::

    $ openstack congress policy simulate alice 'error(x)'
        'p+(101, 5)   error-(x) :- p(x, val1), p(x, val2), not equal(val1, val2)'
        action
    error(302)

The syntax for inserting/deleting rules is a bit awkward since we just afix
a + or - to the head of the rule.  Ideally we would afix the +/- to the rule
as a whole.  This syntactic sugar will be added in a future release.

There is also currently the limitation that you can only insert/delete rules
from the policy you are querying.  And you cannot insert/delete action
description rules.


2.1 Simulation with Actions
---------------------------

The downside to the simulation functionality just described is that the
cloud service wanting to prevent policy violations would need to compute the
proposed changes in terms of the *tables* that Congress uses to represent its
internal state.  Ideally a cloud service would have no idea which tables
Congress uses to represent its internals.  But even if each cloud service
knew which tables Congress was using, it would still need convert each API
call into a collection of changes on its internal tables.

For example, an API call for Nova to provision a new VM might change several
tables.  An API call to Heat to provision a new app might change tables in
several different cloud services.  Translating each API call exposed by a
cloud service into the collection of Congress table changes is sometimes
impractical.

In the key/value examples above, the caller needed to know the current
state of the key/value store in order to accurately describe the changes
she wanted to make.  Setting the key 101 to value 9 meant knowing that its
current value was 0 so that during the simulation we could say to delete the
assignment of 101 to 0 and add the assignment of 101 to 9.

It would be preferable if an external cloud service could simply ask Congress
if the API call it is about to execute is permitted by the policy.
To do that, we must tell Congress what each of those actions do in terms of
the cloud-service tables.  Each of these *action descriptions* describe which
rows are inserted/deleted from which tables if the action were to be executed
in the current state of the cloud.  Those action descriptions are written in
Datalog and are stored in a policy of type 'action'.

Action description policy statements are regular Datalog rules with one main
exception: they use + and - to adorn the table in the head of a rule to indicate
whether they are describing how to *insert* table rows or to *delete* table rows,
respectively.

For example in the key-value store, we can define an action 'set(key, value)'
that deletes the current value assigned to 'key' and adds 'value' in its place.
To describe this action, we write two things: a declaration to Congress that
*set* is indeed an action using the reserved table name *action* and
rules that describe which table rows *set* inserts and which rows it deletes::

    action("set")
    p+(x,y) :- set(x,y)
    p-(x,oldy) :- set(x,y), p(x,oldy)

Note: Insertion takes precedence over deletion, which means that if a row is
both inserted and deleted by an action, the row will be inserted.

To insert these rows, we create a policy of type 'action' and then insert
these rules into that policy::

    $ openstack congress policy create aliceactions --kind 'action'
    $ openstack congress policy rule create aliceactions 'action("set")'
    $ openstack congress policy rule create aliceactions 'p+(x,y) :- set(x,y)'
    $ openstack congress policy rule create aliceactions 'p-(x,oldy) :- set(x,y), p(x,oldy)'

Below we illustrate how to use *set* to simplify the simulation queries
shown previously.

a) **Inserts and Deletes**. Set key 101 to value 5 and ask for the contents of error::

    $ openstack congress policy simulate alice 'error(x)' 'set(101, 5)' aliceactions
    error(302)


b) **Multiple error changes**. Simulate changing 101:9, 202:9, 302:1 and query the *change* in the error table::

    $ openstack congress policy simulate alice 'error(x)'
        'set(101, 9) set(202, 9) set(302, 1)' aliceactions --delta
    error+(202)
    error+(101)
    error-(302)


c) **Order matters**. Simulate changing 101:9, 202:9, 302:1, and finally 101:15 (in that order).  Then query the *change* in the error table::

    $ openstack congress policy simulate alice 'error(x)'
        'set(101, 9) set(202, 9) set(302, 1) set(101, 15)' aliceactions --delta
    error+(202)
    error-(302)

d) **Mixing actions and state-changes**.  Simulate changing 101:9 and adding value 7 for key 202.  Then query the *change* in the error table::

    $ openstack congress policy simulate alice 'error(x)'
        'set(101, 9) p+(202, 7)' aliceactions --delta
    error+(202)
    error+(101)


3. Manual Reactive Enforcement
==============================
Not all policies can be enforced proactively on all clouds, which means that sometimes
the cloud will violate policy.  Once policy violations happen, Congress can take action
to transition the cloud back into one of the states permitted by policy.  We call this
*reactive enforcement*.  Currently, to reactively enforce policy,
Congress relies on people to tell it which actions to execute and when to execute them,
hence we call it *manual* reactive enforcement.

Of course, Congress tries to make it easy for people to tell it how to react to policy
violations.  People write policy statements
that look almost the same as standard Datalog rules, except the rules use the modal *execute* in
the head.  For more information about the Datalog language and how to write these rules,
see :ref:`Policy <policy>`.

Take a simple example that is easy and relatively safe to try out.  The policy we want is
that no server should have an ACTIVE status.  The policy we write tells Congress
how to react when this policy is violated: it says to ask Nova to execute ``pause()``
every time it sees a server with ACTIVE status::

    $ openstack congress policy create reactive
    $ openstack congress policy rule create reactive
        'execute[nova:servers.pause(x)] :- nova:servers(id=x, status="ACTIVE")'

The way this works is that everytime Congress gets new data about the state of the cloud,
it figures out whether that new data causes any new rows to be added to the
``nova:servers.pause(x)`` table.  (While policy writers know that nova:servers.pause isn't a table
in the usual sense, the Datalog implementation treats it like a normal table and computes
all the rows that belong to it in the usual way.)  If there are new rows added to the
``nova:servers.pause(x)`` table, Congress asks Nova to execute ``servers.pause`` for every row
that was newly created.  The arguments passed to ``servers.pause`` are the columns in each row.

For example, if two servers have their status set to ACTIVE, Congress receives the following
data (in actuality the data comes in with all the columns set, but here we use column references
for the sake of pedagogy)::

    nova:servers(id="66dafde0-a49c-11e3-be40-425861b86ab6", status="ACTIVE")
    nova:servers(id="73e31d4c-a49c-11e3-be40-425861b86ab6", status="ACTIVE")

Congress will then ask Nova to execute the following commands::

    nova:servers.pause("66dafde0-a49c-11e3-be40-425861b86ab6")
    nova:servers.pause("73e31d4c-a49c-11e3-be40-425861b86ab6")

Congress will not wait for a response from Nova.  Nor will it change the status of the two servers that it
asked Nova to pause in its ``nova:servers`` table.  Congress will simply execute the pause() actions and
wait for new data to arrive, just like always.
Eventually Nova executes the pause() requests, the status of
those servers change, and Congress receives another data update::

    nova:servers(id="66dafde0-a49c-11e3-be40-425861b86ab6", status="PAUSED")
    nova:servers(id="73e31d4c-a49c-11e3-be40-425861b86ab6", status="PAUSED")

At this point, Congress updates the status of those servers in its ``nova:servers`` table to PAUSED.
But this time, Congress will find that no new rows were **added** to the ``nova:servers.pause(x)``
table and so will execute no actions.  (Two rows were deleted, but Congress ignores deletions.)

In short, Congress executes actions exactly when new rows are inserted into a table augmented
with the *execute* modal.

