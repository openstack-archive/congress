.. include:: aliases.rst

.. _policy:

======
Policy
======

1. What Does a Policy Look Like
===============================

A policy describes how services (either individually or as a whole)
ought to behave.  More specifically, a policy describes which
**states** of the cloud are permitted and which are not.  Or a policy describes
which **actions** to take in each state of the cloud, in order to
transition the cloud to one of those permitted states.  For example
For example,
a policy might simply state that the minimum password length on all
systems is eight characters, or a policy might state that if
the minimum password length on some system is less than 8 that the
minimum length should be reset to 8.

In both cases, the policy relies on knowing the state of the cloud.
The state of the cloud is the amalgamation of the states of all the
services running in the cloud.  In Congress, the state of each service
is represented as a collection of tables (see :ref:`cloudservices`).
The policy language determines whether any violation exists given the
content of the state tables.

For example, one desirable policy is that each Neutron port has at
most one IP address.  That means that the following table mapping port
id to ip address with the schema "port(id, ip)" is permitted by the
policy.

====================================== ==========
ID                                     IP
====================================== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1"
"73e31d4c-e89b-12d3-a456-426655440000" "10.0.0.3"
====================================== ==========

Whereas, the following table is a violation.

====================================== ==========
ID                                     IP
====================================== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1"
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.2"
"73e31d4c-e89b-12d3-a456-426655440000" "10.0.0.3"
====================================== ==========

This is the policy written in Congress's policy language:

error(port_id, ip1, ip2) :-
  port(port_id, ip1),
  port(port_id, ip2),
  not equal(ip1, ip2);

Note that the policy above does not mention specific table content;
instead it describes the general condition of tables.  The policy says
that for every row in the port table, no two rows should have the same
ID and different IPs.

This example verifies a single table within Neutron, but a
policy can use many tables as well.  Those tables
might all come from the same cloud service (e.g. all the tables might be
Neutron tables), or the tables may come from different cloud services (e.g.
some tables from Neutron, others from Nova).

For example, if we have the following table schemas from Nova, Neutron, and
|ad|, we could write a policy that says every network connected to a VM must
either be public or owned by someone in the same group as the VM owner.::

  error(vm, network) :-
    nova:virtual_machine(vm)
    nova:network(vm, network)
    nova:owner(vm, vm_owner)
    neutron:owner(network, network_owner)
    not neutron:public_network(network)
    not same_group(vm_owner, network_owner)

  same_group(user1, user2) :-
    ad:group(user1, group)
    ad:group(user2, group)

And if one of these errors occurs, the right solution is to disconnect
the offending network (as opposed to deleting the VM, changing the owner,
or any of the other feasible options)::

  execute[neutron:disconnectNetwork(vm, network)] :-
    error(vm, network)

The language Congress supports for expressing policy is called Datalog,
a declarative language derived from SQL and first-order logic that has been
the subject of research and development for decades.



.. _datalog:

2. Datalog Policy Language
==========================

As a policy writer, your goal is to define the contents of the *error* table, and
in so doing to describe exactly those conditions that must be true
when policy is being obeyed.

As a policy writer, you can also describe which actions Congress should take when policy
is being violated by using the *execute* operator and thinking of the action
to be executed as if it were a table itself.

Either when defining policy directly or describing the conditions under which
actions should be executed to eliminate policy violations, it is often useful
to use higher-level concepts than
the cloud services provide natively.  Datalog allows us to do this by defining
new tables (higher-level concepts) in terms of existing tables (lower-level
concepts) by writing *rules*.  For example, OpenStack does not tell us directly
which VMs are connected to the internet; rather, it provides a collection of
lower-level API calls from which we can derive that information.  Using Datalog
we can define a table that lists all of the VMs connected to the internet in
terms of the tables that Nova/Neutron support directly.  As another example, if
Keystone stores some collection of user groups and Active Directory stores a
collection of user groups, we might want to create a new table that represents
all the groups from either Keystone or Active Directory.

Datalog has a collection of core features for manipulating tables, and it
has a collection of more advanced features that become important when you
go beyond toy examples.


2.1 Core Datalog Features
-------------------------

Since Datalog is entirely concerned with tables, it's not surprising that
Datalog allows us to represent concrete tables directly in the language.

**Concrete tables.**  Suppose we want to use Datalog to represent a Neutron
table that lists which ports have been assigned which IPs, such as the one
shown below.

Table: neutron:port_ip

====================================== ==========
ID                                     IP
====================================== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1"
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.2"
"73e31d4c-e89b-12d3-a456-426655440000" "10.0.0.3"
====================================== ==========

To represent this table, we write the following Datalog::

    neutron:port_ip("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.1")
    neutron:port_ip("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.2")
    neutron:port_ip("73e31d4c-e89b-12d3-a456-426655440000", "10.0.0.3")

Each of the Datalog statements above is called a *ground atom* (or *ground
fact*).  A ground atom takes the form ``<tablename>(arg1, ..., argn)``,
where each ``argi`` is either a double-quoted Python string or a Python
number.

**Basic rules** The real power of Datalog is that it allows you to write recipes
for constructing new tables out of existing tables, regardless which rows are
in those existing tables.

To create a new table out of an existing table, we write Datalog *rules*.
A *rule* is a simple if-then statement, where the *if* part is called the
*head* and the *then* part is called the *body*.  The head is always a single
Datalog atom.  The body is an AND of several possibly negated Datalog atoms.
OR is accomplished by writing multiple rules with the same table in the head.

Suppose we want to create a new table ``has_ip`` that is just a list of
the Neutron ports that have been assigned at least one IP address.  We want
our table to work regardless what IDs and IPs appear in the neutron:port_ip
table so we use variables in place of strings/numbers.  Variables have the
same meaning as in algebra: they are placeholders for any value.
(Syntactically, a variable is any symbol other than a number or a string.)::

    has_ip(x) :- neutron:port_ip(x, y)

This rule says that a port *x* belongs to the *has_ip* table if there exists
some IP *y* such that row *<x,y>* belongs to the *neutron:port* table.
Conceptually, this rule says to look at all of the ground atoms for the
neutron:port_ip table, and for each one assign *x* to the port UUID and *y*
to the IP.  Then create a row in the *has_ip* table for *x*.  This rule when
applied to the neutron:port_ip table shown above would generate the following
table::

    has_ip("66dafde0-a49c-11e3-be40-425861b86ab6")
    has_ip("73e31d4c-e89b-12d3-a456-426655440000")

Notice here that there are only 2 rows in *has_ip* despite there being 3 rows
in *neutron:port_ip*.  That happens because one of the ports in
neutron:port_ip has been assigned 2 distinct IPs.

**AND operator** As a slightly more complex example, we could define a table
*same_ip* that lists all the pairs of ports that are assigned the same IP.::

    same_ip(port1, port2) :- neutron:port_ip(port1, ip), neutron:port_ip(port2, ip)

This rule says that the row <port1, port2> must be included in the
*same_ip* table if there exists some *ip* where both *<port1, ip>* and *<port2, ip>*
are rows in the *neutron:port* table (where notice that *ip* is the same in the two
rows).  Notice here the variable *ip* appears in two different places in the body,
thereby requiring the value assigned to that variable be the same in both cases.
This is called a *join* in the realm of relational databases and SQL.

**NOT operator** As another example, suppose we want a list of all the ports
that have NOT been assigned any IP address.  We can use the *not* operator to
check if a row fails to belong to a table.

    no_ip(port) :- neutron:port(port), not has_ip(port)

There are special restrictions that you must be aware of when using *not*.
See the next section for details.

**OR operator**. Some examples require an OR, which in Datalog means writing
multiple rules with the same table in the head.   Imagine we have two tables
representing group membership information from two different services:
Keystone and Active Directory.  We can create a new table *group* that says a
person is a member of a group if she is a member of that group either according
to Keystone or according to Active Directory.  In Datalog we create this table
by writing two rules.::

    group(user, grp) :- ad:group(user, grp)
    group(user, grp) :- keystone:group(user, grp)

These rules happen to have only one atom in each of their bodies, but there is
no requirement for that.

2.2 Extended Datalog Features
-----------------------------
In addition writing basic rules with and/or/not, the version of Datalog used
by Congress includes the features described in this section.

**Builtins**. Often we want to write rules that are conditioned on things that
are difficult or impossible to define within Datalog.  For example, we might
want to create a table that lists all of the virtual machines that have at
least 100 GB of memory.  To write that rule, we would need a way to check
if the memory of a given machine is greater-than 100 or not.
Basic arithmetic, string manipulation, etc. are operations
that are built into Datalog, but they look as though they are just ordinary
tables.  Below the *gt* is a builtin table implementing greater-than::

    plenty_of_memory(vm) :- nova:virtual_machine.memory(vm, mem), gt(mem, 100)

In a later section we include the list of available builtins.

**Column references**. Some tables have 5+ columns, and
when tables have that many columns writing rules can be awkward.  Typically when
we write a rule, we only want 1 or 2 columns, but if there are 10 columns, then
we end up needing to invent variable names to fill all the unneeded columns.

For example, Neutron's *ports* table has 10 columns.  If you want to create a
table that includes just the port IDs (as we used above), you would write the
following rule::

  port(id) :-
    neutron:ports(id, tenant_id, name, network_id, mac_address, admin_state_up,
                  status, device_owner, fixed_ips, security_groups)

To simplify such rules, we can write rules that reference only those columns
that we care about by using the column's name.  Since the name of the first
column of the *neutron:ports* table is "ID", we can write the rule above as
follows::

  port(x) :- neutron:ports(id=x)

You can only use these column references for tables provided by cloud services
(since Congress only knows the column names for the cloud service tables).
Column references like these are translated automatically to the version
without column-references, which is something you may notice from time to
time.

**Table hierarchy**.   The tables in the body of rules can either be the
original cloud-service tables or tables that are defined by other rules
(with some limitations, described in the next section).  We can think of a
Datalog policy as a hierarchy of tables, where each table is defined in
terms of the tables at a lower level in the hierarchy.  At the bottom of that
hierarchy are the original cloud-service tables representing the state of the
cloud.

**Order irrelevance**.  One noteworthy feature of Datalog is that the order
in which rules appear is irrelevant.  The rows that belong to a table are
the minimal ones required by the rules if we were to compute their contents
starting with the cloud-service tables (whose contents are given to us) and
working our way up the hierarchy of tables.  For more details, search the web
for the term *stratified Datalog semantics*.

**Execute modal**.  To write a policy that tells Congress the conditions
under which it should execute a certain action, we write rules that utilize
the *execute* modal in the head of the rule.

For example, to dictate that Congress should ask Nova to pause() all of the
servers whose state is ACTIVE, we would write the following policy statement::

  execute[nova:servers.pause(x)] :- nova:servers(id=x, status="ACTIVE")

We discuss this modal operator in greater detail in Section 3.

**Grammar**. Here is the grammar for Datalog policies::

    <policy> ::= <rule>*
    <rule> ::= <head> COLONMINUS <literal> (COMMA <literal>)*
    <head> ::= <atom>
    <head> ::= EXECUTE[<atom>]
    <literal> ::= <atom>
    <literal> ::= NOT <atom>
    <atom> ::= TABLENAME LPAREN <arg> (COMMA <arg>)* RPAREN
    <arg> ::= <term>
    <arg> ::= COLUMNNAME=<term>
    <term> ::= INTEGER | FLOAT | STRING | VARIABLE


2.3 Datalog Syntax Restrictions
-------------------------------

There are a number of syntactic restrictions on Datalog that are, for the most
part, common sense.

**Head Safety**: every variable in the head of a rule must appear in the body.

Head Safety is natural because if a variable appears in the head of the rule
but not the body, we have not given a prescription for which strings/numbers
to use for that variable when adding rows to the table in the head.

**Body Safety**: every variable occurring in a negated atom or in the input
of a built-in table must appear in a non-negated, non-builtin atom in the body.

Body Safety is important for ensuring that the sizes of our tables are always
finite.  There are always infinitely many rows that DO NOT belong to a table,
and there are often infinitely many rows that DO belong to a builtin
(like equal).  Body safety ensures that the number of rows belonging to
the table in the head is always finite.

**No recursion**: You are not allowed to define a table in terms of itself.

A classic example starts with a table that tells us which network nodes
are directly adjacent to which other nodes (by a single network hop).  Then you
want to write a policy about which nodes are connected to which other nodes
(by any number of hops).  Expressing such a policy requires recursion, which
is not allowed.

**Modal safety**: The *execute* modal may only appear in the heads of rules.

The Datalog language is we have is called a condition-action language, meaning
that action-execution depends on conditions on the state of the cloud.  But
it is not an event-condition-action language, which would enable
action-execution to depend on the conditions of the cloud plus the action
that was just executed.  An event-condition-action language would allow
the *execute* modal to appear in the body of rules.

**Schema consistency**: Every time a rule references one of the cloud service
tables, the rule must use the same (number of) columns that the cloud service
provides for that table.

This restriction catches mistakes in rules that use the wrong number of columns
or the wrong column names.



.. **Stratification [Recursion is not currently supported]**
..    No table may be defined in terms of its negation.

.. In Datalog, a table may be defined in terms of itself.  These are called
   *recursive* tables.  A classic example is defining all pairs of nodes that
   are connected in a network given a table that records which nodes are adjacent
   to which other nodes (i.e. by a single network hop).::

..    connected(x,y) :- adjacent(x,y)
..    connected(x,y) :- connected(x,z), connected(z,y)

.. The Stratification restriction says that we cannot define a table in terms of
   its *negation*.  For example, the following rule is disallowed.::

..    p(x) :- not p(x)   // NOT valid Datalog

.. More precisely, the Stratification restriction says that there is no cycle
   through the dependency graph of a Datalog policy that includes an edge
   labeled with *negation*.  The dependency graph of a Datalog policy has
   one node for every table.  It has an edge from table u to table v if
   there is a rule with u in the head and v in the body; that edge is labeled
   with *negation* if NOT is applied to the atom for v.



2.4 Datalog builtins
--------------------

Here is a list of the currently supported builtins.  A builtin that has
N inputs means that the leftmost N columns are the inputs, and the
remaining columns (if any) are the outputs.  If a builtin has no outputs,
, starting with arithmetic.

====================================== ======= =============================
Arithmetic Builtin                     Inputs  Description
====================================== ======= =============================
lt(x, y)                               2       True if x < y
lteq(x, y)                             2       True if x <= y
gt(x, y)                               2       True if x > y
gteq(x, y)                             2       True if x >= y
max(x, y, z)                           2       z = max(x, y)
plus(x, y, z)                          2       z = x + y
minus(x, y, z)                         2       z = x - y
mul(x, y, z)                           2       z = x * y
div(x, y, z)                           2       z = x / y
float(x, y)                            1       y = float(x)
int(x, y)                              1       y = int(x)
====================================== ======= =============================


Next are the string builtins.

====================================== ======= =============================
String Builtin                         Inputs  Description
====================================== ======= =============================
concat(x, y, z)                        2       z = concatenate(x, y)
len(x, y)                              1       y = number of characters in x
====================================== ======= =============================

Last are the builtins for manipulating dates and times.  These builtins
are based on the Python DateTime object.

====================================== ======= ===============================
Datetime Builtin                       Inputs  Description
====================================== ======= ===============================
now(x)                                 0       The current date-time
unpack_date(x, year, month, day)       1       Extract year/month/day
unpack_time(x, hours, minutes, secs)   1       Extract hours/minutes/seconds
unpack_datetime(x, y, m, d, h, i, s)   1       Extract date and time
pack_time(hours, minutes, seconds, x)  3       Create date-time with date
pack_date(year, month, day, x)         3       Create date-time with time
pack_datetime(y, m, d, h, i, s, x)     6       Create date-time with date/time
extract_date(x, date)                  1       Extract date obj from date-time
extract_time(x, time)                  1       Extract time obj from date-time
datetime_to_seconds(x, secs)           1       secs from 1900 to date-time x
datetime_plus(x, y, z)                 2       z = x + y
datetime_minus(x, y, z)                2       z = x - y
datetime_lt(x, y)                      2       True if x is before y
datetime_lteq(x, y)                    2       True if x is no later than y
datetime_gt(x, y)                      2       True if x is later than y
datetime_gteq(x, y)                    2       True if x is no earlier than y
datetime_equal(x, y)                   2       True if x == y
====================================== ======= ===============================




3. Multiple Policies
====================

One of the goals of Congress is for several different people in an organization
to collaboratively define a single, overarching policy that governs a cloud.
The example, the compute admin might some tables that are good building blocks
for writing policy about compute.  Similarly the network and storage admins
might create tables that help define policy about networking and storage, respectively.
Using those building blocks, the cloud administrator might then write
policy about compute, storage, and networking.

To make it easier for several people to collaborate (or for a single person
to write more modular policies) Congress allows you organize your Datalog
statements using policy modules. Each policy module is simply a collection of
Datalog statements.  You create and delete policy modules using the API,
and the you insert/delete Datalog statements into a particular policy module also
using the API.

The rules you insert into one policy module can reference tables defined in
other policy modules.  To do that, you prefix the name of the table with
the name of the policy and separate the policy module and table name with
a colon.

For example, if the policy module *compute* has a table that lists all the
servers that have not been properly secured *insecure(server)*
and the policy module *network* has a table of all devices connected to
the internet *connected_to_internet*, then as a
cloud administrator, you might write a policy that says there is an error
whenever a server is insecure and connected to the internet.

  error(x) :- compute:insecure(x), network:connected_to_internet(x)

Notice that this is exactly the same syntax you use to reference tables exported
directly by cloud services::

    has_ip(x) :- neutron:port_ip(x, y)

In fact, the tables exported by cloud services are stored in a policy module
with the same name as the service.

While the term *policy module* is accurate, we usually abbreviate it to *policy*,
and say that Congress supports multiple policies. Note, however, that supporting
multiple policies is not the same thing as supporting multi-tenancy.
Currently, all of
the policies are visible to everyone using the system, and everyone using
the system has the same view of the tables the cloud services export.  For
true multi-tenancy, you would expect different tenants to have different
sets of policies and potentially a different view of the data exported
by cloud services.

See section :ref:`API <api>` for details about creating, deleting, and
populating policies.


3.1 Syntactic Restrictions for Multiple Policies
------------------------------------------------
There are a couple of additional syntactic restrictions imposed when using
multiple policies.

**No recursion across policies**.  Just as there is no recursion permitted
within a single policy, there is no recursion permitted across policies.

For example, the following is prohibited::

  # Not permitted because of recursion
  Module compute:  p(x) :- storage:q(x)
  Module storage:  q(x) :- compute:p(x)

**No policy name may be referenced in the head of a rule**.  A rule may
not mention any policy in the head (unless the head uses the modal *execute*).

This restriction prohibits one policy from changing the tables
defined within another policy.  The following example is prohibited
(in all policy modules, including 'compute')::

  # Not permitted because 'compute' is in the head
  compute:p(x) :- q(x)

The following rule is permitted, because it utilizes *execute* in the
head of the rule::

  # Permitted because of execute[]
  execute[nova:pause(x)] :- nova:servers(id=x, status="ACTIVE")

Congress will stop you from inserting rules that violate these restrictions.

