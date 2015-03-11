
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


