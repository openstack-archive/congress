.. include:: aliases.rst

.. _enforcement:

Monitoring and Enforcement
===========================

Congress can monitor and enforce the Classification policy and enables cloud administrators to control which portions of the policy are monitored and which are enforced.  Monitoring policy would ideally involve a dashboard that helps the cloud administrator understand the state of the cloud and what portions of the cloud fail to comply with the policy (if any).  At the time of writing, Congress does not have a dashboard; however, it implements the APIs required for one.

Monitoring
-----------
The most important information that a dashboard would display for monitoring the Classification policy is a list of all the current policy violations.  Recall from :ref:`policy` that the policy violations are represented with the table *error*.  To ask Congress for a list of all policy violations, we can simply ask it for the contents of the *error* table.

Congress provides the API call :func:`select` to request the contents of any table.  :func:`select` also allows you to request all rows of a table where the columns meet certain conditions.  You can also request answers to a query posed over a combination of tables.

.. function:: select(formula)
    :noindex:

    FORMULA is either a Datalog rule or atom.  If it is an atom, SELECT returns a string representing all instances of FORMULA that are true.  If it is a rule, it returns all instances of that rule where the body is true.

:func:`select` takes either an atom or a rule as an argument.  If it is an atom, Congress returns all instances of the atom that are true.  For example, suppose we have the following instance of the table *neutron:port*.

====================================== ==========
ID                                     IP
====================================== ==========
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.1"
"66dafde0-a49c-11e3-be40-425861b86ab6" "10.0.0.2"
"73e31d4c-a49c-11e3-be40-425861b86ab6" "10.0.0.3"
====================================== ==========

If the argument to :func:`select` is::

    'neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", x)'

then Congress would return the following statements encoded as a string::

    neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.1")
    neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.2")


If the argument to :func:`select` is a rule then Congress finds all instances of the body of the rule that are true and instantiates the variables in the head accordingly.  For example, if the rule argument were the string::

    multi_port(port) :- neutron:port(port, ip1), neutron:port(port, ip2), not equal(ip1, ip2)

then Congress would return the following string.  Notice that there are two results because there are two different reasons that "66dafde0-a49c-11e3-be40-425861b86ab6" belongs to *multi_port*::

    multi_port("66dafde0-a49c-11e3-be40-425861b86ab6") :-
        neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.1"),
        neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.2"),
        not equal("10.0.0.1", "10.0.0.2")
    multi_port("66dafde0-a49c-11e3-be40-425861b86ab6") :-
        neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.2"),
        neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.1"),
        not equal("10.0.0.2", "10.0.0.1")

We can also ask Congress for an explanation as to why a row belongs to a particular table.  This allows us to ask Congress to list the rows from the original cloud-service tables that cause a particular error.  Explaining the causes of an error is another important piece of functionality for a policy dashboard.

.. function:: explain(atom, tablenames=None, find_all=False)
    :noindex:

    At the time of writing, this function needs an overhaul.  In theory it should return a rule describing why ATOM is true.  The head of the rule is ATOM.  The body of the rule has tables only from TABLENAMES (which if not supplied Congress is free to choose) that constitute the causes of ATOM being true.  If FIND_ALL is True, then the result is a list of all such rules.

.. todo: fix up explanation routine and expand discussion here.


Another piece of functionality useful for building a dashboard is simulating the effects of changes.  If an administrator is contemplating the addition of several policy statements, she could temporarily add those policy statements and check the resulting state to see if any new violations were created or old violations were eliminated.  Similarly, if the administrator wanted to understand how a change in the state of several cloud services would impact policy, she could simulate the effects of those changes.

.. function:: simulate(query, sequence)
    :noindex:

    QUERY is any :func:`select` query.  SEQUENCE is a sequence Datalog rules, described in more detail below.  SIMULATE returns select(QUERY) after applying the updates described by SEQUENCE.  The current implementation locks the state data structures, applies the updates, answers the query, and then applies the inversion of those updates; in short, it is not thread safe.

Each Datalog rule in SEQUENCE is one of the following types. (There are near-terms plans for improving the syntax.)

* Data update.  q+(1) means that q(1) should be inserted.  q-(1) means that q(1) should be deleted.
* Policy update.   p+(x) :- q(x) means that p(x) :- q(x) should be inserted.  p-(x) :- q(x) means that p(x) :- q(x) should be deleted.

For example, we could ask for contents of the *error* table after::

    inserting neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.10")
    deleting neutron:port("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.3")

by running the following API call::

    simulate('error(x)',
             'neutron:port+("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.10")
              neutron:port-("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.3")')

In the near future, we will provide an alternate version of :func:`simulate`.  Instead of returning the entire contents of QUERY after applying the updates, it will return a list of the changes to the query caused by the updates.

.. todo: Add version of simulate that computes deltas on query caused by updates.

.. todo: Change impl so that these are insert[...] and delete[...].  Update docs.


Proactive Enforcement 1
------------------------

Often we want policy to be enforced, not just monitored.  *Proactive enforcement* is the term we use to mean preventing policy violations before they occur.  Proactive enforcement requires having enforcement points in the cloud that stop changes before they happen.  Cloud services like Nova, Neutron, and Cinder are good examples of enforcement points.  For example, Nova could refuse to provision a VM that would cause a policy violation, thereby proactively enforcing policy.

To enable other cloud services like Nova to check if a proposed change in the cloud state would violate policy, the cloud service can consult Congress using the :func:`simulate` function call described in the previous section.  For example, provisioning a new VM might add rows to several of Nova's tables.  After receiving an API call that requests a new VM be provisioned, Nova could ask Congress if adding those rows would create any new policy violations.  If new violations arise, Nova could refuse to provision the VM, thereby proactively enforcing the policy.

Actions
----------
The downside to the form of proactive enforcement just described is that the cloud service wanting to prevent policy violations would need to compute the proposed changes in terms of the *tables* that Congress uses to represent its internal state.  Ideally a cloud service would have no idea which tables Congress uses to represent its internals.  But even if each cloud service knew which tables Congress was using, it would still need convert each API call into a collection of changes on its internal tables.  For example, an API call for Nova to provision a new VM might change several tables.  An API call to Heat to provision a new app might change tables in several different cloud services.  Translating each API call exposed by a cloud service into the collection of Congress table changes is sometimes impractical.

It would be preferable if an external cloud service could simply ask Congress if the API call it is about to execute is permitted by the policy.  To do that, we must tell Congress what each of those actions do in terms of the cloud-service tables.  Each of these *action descriptions* describe which rows are inserted/deleted from which tables if the action were to be executed in the current state of the cloud.  Those action descriptions are written in Datalog and are stored in the **Action** policy.  (If this seems overly complex, it may help to know that the Action policy is used for purposes other than proactive enforcement.)

Action description policy statements are regular Datalog rules with one main exception: they use + and - to adorn the table in the head of a rule to indicate whether a row is inserted or deleted, respectively.

For example, the API call *neutron:setPort* assigns an IP to a port in Neutron only when the tenant executing the API call is the owner of the port.  To describe this action, we write two things: a declaration to Congress that *neutron:setPort* is indeed an action using the reserved table name *action* and rules that declare which table rows are inserted and deleted if *neutron:setPort* were executed::

    // declare "neutron:setPort" as an action
    action("neutron:setPort")

    // insert new port ID
    neutron:port+(uuid, newport) :-
        neutron:setPort(uuid, newport),
        username(caller),                // ID of API caller
        neutron:owner(uuid, caller)

    // delete the old ID
    neutron:port-(uuid, oldport) :-
        neutron:setPort(uuid, newport),
        username(caller),
        neutron:owner(uuid, caller),
        neutron:port(uuid, oldport)

Insertion takes precedence over deletion, which means that if a row is both inserted and deleted, the row will be inserted.

Modifying the Action policy within Congress is done using the same :func:`insert` and :func:`delete` functions that are used to modify the Classification policy but providing an additional argument: the policy target.

.. function:: insert(formula[, target])
    :noindex:

    Inserts Datalog rule FORMULA into the TARGET policy.  Possible values for TARGET are: ``classification``, ``action``, ``enforcement``, ``database`` and ``service``.  If TARGET is not supplied, the default is ``classification``.

.. function:: delete(formula[, target])
    :noindex:

    Deletes Datalog rule FORMULA from the TARGET policy.  Possible values for TARGET are: ``classification``, ``action``, ``enforcement``, ``database`` and ``service``.  If TARGET is not supplied, the default is ``classification``.


Proactive Enforcement 2
------------------------
With the proper Action policy, external cloud services can ask Congress whether an API call that it is about to execute will cause any policy violations using the :func:`simulate` function described earlier.  Recall that :func:`simulate` takes a query and a sequence of updates.  Action invocations are also permitted updates that can be included in that sequence.

An action invocation is sometimes more than the action name and its arguments.  It typically has supporting information that is necessary as well, such as the name of the user invoking the action or optional parameters for the invocation.  And sometimes it is useful to describe the action that will be taken using information from the current state of the cloud.

An action invocation is described using a slightly extended Datalog syntax where multiple atoms, separated by commas, can be in the head of the rule.  The head of the rule describes action invocation and its supporting information; the body of the rule helps fill in missing information from the head using the current state.  If the action invocation does not depend on the current state, use *true* for the body.

For example, if Neutron were about to execute::

    setPort("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.3")

on behalf of user ``alice`` and wanted to consult with Congress before doing so, it would construct a Datalog rule describing the invocation::

    neutron:setPort("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.3"), username("alice") :- true

and then pose the following query to Congress::

    simulate('error(x)', 'neutron:setPort("66dafde0-a49c-11e3-be40-425861b86ab6", "10.0.0.3"), username("alice") :- true')

The framework for update sequences supported by :func:`simulate` also allows an action to return a value (such as a UUID when a new object is created) and for subsequent action invocations to have their arguments derived from the return value of a previous action.  In short, the update sequence is written in a mini-programming language for describing changes to apply to the current state, and each statement in that language is a Datalog rule.

.. :todo: Support multiple heads throughout prototype.  When done, modify Datalog primer.


Reactive Enforcement
----------------------
There's no requirement that a cloud service consult with Congress before changing the cloud (and even if it does, the cloud could change between the time Congress is consulted and when the service actually makes the changes).  So Congress expects that sometimes the Classification policy will be violated and attempts to take action that brings the cloud back into compliance when that happens.  We call this *reactive enforcement*.

Congress's ability to monitor policy violations is the key to its ability to reactively enforce that policy.  Every time a cloud service sends an update for one of its tables (or Congress polls the cloud service and finds an update), Congress checks if that update caused any new policy violations and if so attempts to find actions that when executed will eliminate them.

For example, recall the Classification policy "every network connected to a VM must either be public or owned by someone in the same group as the VM owner," written below in Datalog::

    error(vm) :- nova:virtual_machine(vm),
        nova:network(vm, network),
        not neutron:public_network(network),
        neutron:owner(network, netowner),
        nova:owner(vm, vmowner),
        not same_group(netowner, vmowner)

    same_group(user1, user2) :- ad:group(user1, group), ad:group(user2, group)

If this policy is violated, it means there is a network connected to a VM whose owners are not in the same group.  After identifying this violation, Congress could attempt to eliminate it by executing an action that disconnects the offending network from the VM.

To find actions that eliminate violations, Congress combines information from the Classification theory, which explains why the error exists in terms of the cloud-service tables, and information from the Action theory, which explains how each API call can be used to change the cloud-service tables.  Conceptually, Congress tries to match up the actions it has available with the changes in cloud-service tables that would eliminate a given violation.

One important observation is that there are sometimes multiple ways of eliminating a violation, and not all of them are equally preferred.  Congress is currently ultra-conservative about making changes to the cloud and does not enforce policy reactively without guidance from an administrator; however, in the future we expect to provide administrators with the ability to let Congress sometimes enforce policy reactively without guidance.

In the example above, there are several ways of eliminating the violation:

* Disconnect the network from the VM
* Delete the VM.
* Make the network public
* Change the owner of the VM.
* Change the owner of the network.
* Change the group membership of the VM owner and/or network owner.

In this case, disconnecting the network is a far better choice than destroying the VM, but without additional guidance from an administrator, there is not enough information contained in the Classification and Action policies for Congress to figure that out.

Until we provide a mechanism that enables administrators to give Congress proper guidance for choosing among options for eliminating a violation, Congress supports two of the crucial building blocks for reactive enforcement: a way to enumerate remediation options and a cache of remediation decisions.

To ask Congress for actions that will eliminate a policy violation (or more generally cause any row from any table defined in the Classification policy to be deleted), we can use the function :func:`remediate`.

.. function:: remediate(atom)
    :noindex:

    ATOM is a string representing a Datalog atom.  :func:`remediate` returns a string representing a list of action sequences that will cause ATOM to become false.

Once a decision is made about which remediation action to take, an administrator (or other process) can choose to have Congress make the same decision for future violations.  To do so, she modifies Congress's **Enforcement Policy**.  The Enforcement policy is a Datalog policy that dictates which actions to take under what circumstances.  Each rule in the policy has an action (as declared in the Action policy) in the head.  Every time an update from a cloud-service tables arrives at Congress, Congress executes any actions that the update caused to become true.

For example, to execute the *disconnectNetwork* action each time a network is connected to a VM where the owners are not in the same group, we would insert the following statement into the Enforcement policy::

    disconnectNetwork(vm, network) :-
        nova:virtual_machine(vm),
        nova:network(vm, network),
        not neutron:public_network(network),
        neutron:owner(network, netowner),
        nova:owner(vm, vmowner),
        not same_group(netowner, vmowner)


In this example, the statement added to the Enforcement policy is identical to the one in the Classification policy, except in the head we use *disconnectNetwork* instead of *error*.  But in other examples, the administrator might decide to apply an action in broader or narrower circumstances.  See :ref:`other-enforcement` for a discussion of how Congress's policies relate to one another and how they relate to other approaches to policy-based management.


.. warning: The functionality in this section is the least tested.

.. todo: Add mechanism for admins to control when actions are taken automatically.






