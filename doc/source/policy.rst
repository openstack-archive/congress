.. |ad| replace:: ActiveDirectory

.. _policy:

Policy
=======

There are several policies that control how Congress behaves.  The one we will focus on in this section is called the **Classification policy**.  The Classification Policy describes how cloud services are will to relate to one another in an ideal world. As described in :ref:`cloud-services`, each cloud service is conceptualized as a collection of tables.  Those tables represent the state of the cloud, as Congress sees it.  The Classification policy allows us to describe exactly which states of the cloud are in compliance and which are not.  In other words, the Classification policy describes which combinations of tables are permitted and which are not.

For example, we might want to enforce a policy where every Neutron port is assigned at most one IP address.  That would mean that the following table is permitted by the policy.

====================================== ==========
ID                                     IP
====================================== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1"
"73e31d4c-a49c-11e3-be40-425861b86ab6" "10.0.0.3"
====================================== ==========

The following table would *not* be permitted.

====================================== ==========
ID                                     IP
====================================== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1"
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.2"
"73e31d4c-a49c-11e3-be40-425861b86ab6" "10.0.0.3"
====================================== ==========

The example above puts restrictions on a single table within Neutron, but the Classification policy is permitted to put restrictions on any collection of tables.  Those tables might all come from the same cloud service (e.g. all the tables might be Neutron tables), or the tables may come from different cloud services (e.g. some tables come from Neutron, others come from Nova).

For example, if we have the following tables from Nova, Neutron, and |ad|, we could write a policy that says every network connected to a VM must either be public or owned by someone in the same group as the VM owner.::

    nova:virtual_machine(vm)
    nova:network(vm, network)
    nova:owner(vm, owner)
    neutron:public_network(network)
    neutron:owner(network, owner)
    ad:group(user, group)

The key observation about this example is that policies are often complex, and we need a rich language to explain to Congress which combinations of tables are permitted and which are not.  The basic language Congress supports for expressing policy is called Datalog, a declarative language derived from SQL and first-order logic that has been around for decades.

The next section is a Datalog primer, and the section after that describes how  Congress uses Datalog.




.. _datalog:

Datalog Primer
---------------

Datalog is a language that describes how to compute new tables from existing tables.  In Congress, the existing tables are the ones derived from the cloud services Congress is managing.  The new tables represent combinations and abstractions of the cloud service tables, similar to subroutines or helper functions in traditional programming languages.  These new tables are useful for expressing real-world policies because those policies are typically written at a higher-level of abstraction (e.g. users, applications) than the cloud services that Congress can actually manage (e.g. networking, compute, storage).

For example, if Keystone stores some collection of user groups and Active Directory stores a collection of user groups, we might want to create a new table that represents all the groups from either Keystone or Active Directory.  Or maybe that table represents only the managerial groups of Keystone and Active Directory.

In Datalog, there is a syntactic entity for each row of a table.  That syntactic entity looks like a function invocation from a traditional programming language.  The "function" is the table name, and the "arguments" are the values for each of the columns.  Each column is allowed to either be a string or a number.

For example, the following table is represented by the Datalog that follows it.

====================================== ==========
ID                                     IP
====================================== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1"
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.2"
"73e31d4c-a49c-11e3-be40-425861b86ab6" "10.0.0.3"
====================================== ==========

::

    neutron:port_ip("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.1")
    neutron:port_ip("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.2")
    neutron:port_ip("73e31d4c-a49c-11e3-be40-425861b86ab6", "10.0.0.3")

Each of these Datalog statements is called an *atom*.  Each Datalog statement that creates a new table from several existing tables is called a *rule* and embodies if-then logic.  The "if" part is an AND of conditions on the existing tables, and the "then" part describes the rows that are part of the new table.  The *then* part of the rule is called the *head*, and the *if* part is called the *body*.  We use *:-* for *if*, Datalog atoms as conditional tests, the comma for AND, and *not* for negation.  OR is accomplished by writing multiple rules with the same table in the head.

For example, we could create a new table *has_ip* that is just a list of the Neutron ports that have been assigned at least one IP address.::

    has_ip("66dafde0-a49c-11e3-be40-425861b86ab6") :-
        neutron:port_ip("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.1")
    has_ip("66dafde0-a49c-11e3-be40-425861b86ab6") :-
        neutron:port_ip("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.2")
    has_ip("73e31d4c-a49c-11e3-be40-425861b86ab6") :-
        neutron:port_ip("73e31d4c-a49c-11e3-be40-425861b86ab6", "10.0.0.3")

The rules above work for the neutron:port_id table shown earlier, but we would like our definition of *has_ip* to work for any instance of neutron:port_id.  To that end, Datalog allows us to use variables in place of the constants (strings/numbers).  Conceptually, these variables are similar to iterator variables in traditional programming languages that implicitly loop over all possible rows of the table.  Syntactically, a variable is any non-string and non-number identifier.  A Datalog rule or atom that contains no variables is called *ground*.

The proper way to define the table that lists all the ports that have been assigned IPs is shown below.::

    has_ip(x) :- neutron:port_ip(x, y)

It says that a port *x* belongs to the *has_ip* table if there exists some IP *y* such that row *<x,y>* belongs to the *neutron:port* table.
We could also define a table *same_ip* that lists all the pairs of ports that are assigned the same IP.::

    same_ip(port1, port2) :- neutron:port_ip(port1, ip), neutron:port(port2, ip)

In this case we use multiple atoms in the body of the rule.  We use the same variable *ip* in both tables (called a *join* for those of you familiar with relational databases and SQL).  The pair <port1, port2> is included in *same_ip* if there exists some *ip* where both *<port1, ip>* and *<port2, ip>* both belong to the *neutron:port* table.

As a final example, we imagine that we have two tables representing group membership information from two different services: Keystone and Active Directory.  We can create a new table *group* that says a person is a member of a group if she is a member of that group either according to Keystone or according to Active Directory.  In Datalog we do so by writing two rules.::

    group(user, grp) :- ad:group(user, grp)
    group(user, grp) :- keystone:group(user, grp)

These rules happen to have only one atom in each of their bodies, but there is no requirement for that.  Moreover, the tables in the body of rules can either be the original cloud-service tables or tables that are defined by other rules (with some limitations, described later).  We can think of a Datalog policy as a hierarchy of tables, where each table is defined in terms of the tables at a lower level in the hierarchy.  At the bottom of that hierarchy are the original cloud-service tables representing the state of the cloud.

One noteworthy feature of Datalog is that the order in which rules appear is irrelevant.  The rows that belong to a table are the minimal ones required by the rules if we were to compute their contents starting with the cloud-service tables (whose contents are given to us) and working our way up the hierarchy of tables.  For more details, search the web for the term *stratified Datalog semantics*.

Here is the grammar for Datalog policies::

    <policy> ::= <rule>*
    <rule> ::= <atom> COLONMINUS <literal> (COMMA <literal>)*
    <literal> ::= <atom>
    <literal> ::= NOT <atom>
    <atom> ::= TABLENAME LPAREN <term> (COMMA <term>)* RPAREN
    <term> ::= INTEGER | FLOAT | STRING | VARIABLE


Datalog Restrictions
-----------------------

There are a number of syntactic restrictions on Datalog that are, for the most part, common sense.

Head Safety
    every variable in the head of a rule must appear in the body.

Head Safety is natural because if a variable appears in the head of the rule but not the body, we have not given a prescription for which constants (strings/numbers) to use for that variable.

Body Safety
    every variable in a negated atom or in a built-in table must appear in a non-negated, non-builtin atom in the body.

Body Safety is important for ensuring that the sizes of our tables are always finite.  There are always infinitely many rows that DO NOT belong to a table, and there are often infinitely many rows that DO belong to a builtin (like equal).  For some builtin tables, the Body Safety restriction is overly strong, but having the restriction in place ensures that the Datalog engine can treat all built-in tables the same.

Stratification
    No table may be defined in terms of its negation.

In Datalog, a table may be defined in terms of itself.  These are called *recursive* tables.  A classic example is defining all pairs of nodes that are connected in a network given a table that records which nodes are adjacent to which other nodes (i.e. by a single network hop).::

    connected(x,y) :- adjacent(x,y)
    connected(x,y) :- connected(x,z), connected(z,y)

The Stratification restriction says that we cannot define a table in terms of its *negation*.  For example, the following rule is disallowed.::

    p(x) :- not p(x)   // NOT valid Datalog

More precisely, the Stratification restriction says that there is no cycle through the dependency graph of a Datalog policy that includes an edge labeled with *negation*.  The dependency graph of a Datalog policy has one node for every table.  It has an edge from table u to table v if there is a rule with u in the head and v in the body; that edge is labeled with *negation* if NOT is applied to the atom for v.

The Classification Policy
-------------------------
The Classification policy of Congress describes which cloud states are in compliance and which ones are not.  It says which combinations of cloud-service tables are in compliance and which are not.  A Congress Classification policy is a Datalog policy that defines the reserved table *error*.  Every row in the *error* table represents a policy violation.

For example, below is the Classification policy that encodes the restriction "every network connected to a VM must either be public or owned by someone in the same group as the VM owner."::

    error(vm) :- nova:virtual_machine(vm),
        nova:network(vm, network),
        not neutron:public_network(network),
        neutron:owner(network, netowner),
        nova:owner(vm, vmowner),
        not same_group(netowner, vmowner)

    same_group(user1, user2) :- ad:group(user1, group), ad:group(user2, group)

The columns of *error* are largely unimportant, and different rules can use different numbers of columns for the *error* table.  One reasonable approach is to use no columns for *error*.

Setting Policy in Congress
--------------------------

To set the Classification within Congress, you use the methods :func:`insert` and :func:`delete` (which are exposed via the API and are implemented as methods of the class congress.runtime.Runtime).

.. function:: insert(formula)
    :noindex:

    Inserts FORMULA into the Classification policy.  FORMULA is a string encoding a single Datalog rule.

.. function:: delete(formula)
    :noindex:

    Deletes FORMULA from the Classification policy.  FORMULA is a string encoding a single Datalog rule.


Formulas may be inserted and deleted at any time.



