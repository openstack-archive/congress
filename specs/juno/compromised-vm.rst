..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

==========================================
Compromised VM
==========================================

https://blueprints.launchpad.net/congress/+spec/compromised-vm

Security policy use case

Problem description
===================

IDS service notices malicious traffic originating from an insider VM trying to
send packets to hosts inside and outside of the tenant perimeter.  As this is
detected, some reactive response would need to be taken, such as isolating the
offending VM from the rest of the network.  This policy would facilitate one of
the reactive responses to be invoked when a compromise is reported by an IDS
service.


Proposed change
===============

An IDS will need to monitor traffic in and out of virtual machines. The IDS
will maintain the blacklist of known bad destinations. The patterns will need
to maintained in the IDS. While the IDS is monitoring for traffic patterns and
blacklist, it will need to notify Congress of the event through the Congress
IDS plugin. Through the Congress Neutron plugin, Neutron API will need to be
updated blocked IP. Congress-client and Horizon to alert the operator of
changes.

Alternatives
------------

(sarob)
Instead of a blacklist maintained by the IDS, use an real time check of a
public blacklist.

(thinrichs)
Would it be simpler to flag an error anytime a VM was identified by IDS?
error(vm) :- ids:ip_blacklist(ip), neutron:port(vm, ip)

(thinrichs)
We should try to work out how the reactive bit would work. The way we'll do
that for the beta is to write another policy that dictates which action to take
under certain conditions. Imagine the policy above but instead of error(vm), we
write something like neutron:block_ip(secgrp, ip) :- ids:ip_blacklist(ip),
neutron:port(vm, ip), neutron:security_group(vm, secgrp)
I'm sure not all the details there are right. But ideally the thing in the head
of the rule would be a Neutron API call. In the worst case it can just the name
of a script that we write.

Policy
----------------
error(vm) :-
    nova:virtual_machine(vm),
    ids:ip_packet(src_ip, dst_ip),
    neutron:port(vm, src_ip),	//finds out the port that has the VM’s IP
    ids:ip_blacklist(dst_ip).

Policy Actions
-----------------

* Monitoring: report/log the incident including the VM’s IP address, external
    IP, etc.
* Reactive: Invoke the nova API to add the VM to IDS security group restricting
    access to make changes. Invoke neutron to block all traffic to/from the
    VM’s IP address. Alternatives are to restart the VM on a nova IDS
    schedule filter (limiting traffic chaos while maintaining the ability to
    access the VM) and/or a no route network or removing the VM network
    interface(s).

Data Sources
-----------------

* IDS (intrusion detection service VM): IP address of the offending VM
* neutron: network details, IP details
* nova: VM details; instance ID, interface(s) status, instance state, security
    group

Data Model Impact
------------------

none


REST API impact
---------------

Needs explanation

Security impact
---------------

* DoS

Notifications impact
--------------------

* IDS API
* congress-client
* horizon

Other end user impact
---------------------

Unknown at this time


Performance Impact
------------------

Unknown at this time


Other deployer impact
---------------------

Unknown at this time


Developer impact
----------------

Unknown at this time



Implementation
==============

Assignee(s)
-----------

Unknown at this time


Work Items
----------

* Congress IDS plugin
* Compromised VM policy
* Congress client notification
* Horizon notification


Dependencies
============

Neutron really needs to provide port allow/deny primitive. Today it blocks
everything and we can only poke pin holes what's allowed out -- this makes it
complex to implement policy

(thinrichs)
Need to understand more about these limitations.

(sarob)



Testing
=======

TBD


Documentation Impact
====================

TBD


References
==========

https://docs.google.com/document/d/1ExDmT06vDZjzOPePYBqojMRfXodvsk0R8nRkX-zrkSw/edit#
https://wiki.openstack.org/wiki/Congress
