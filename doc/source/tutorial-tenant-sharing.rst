Congress Tutorial - Tenant Sharing Policy
=========================================

Overview
--------
This tutorial illustrates how to create a Congress monitoring policy
that detects when one Openstack tenant shares a network with another
Openstack tenant, and then flags that sharing as a policy violation.

Data Sources
------------
Neutron networks: list of each network and its owner tenant.

Neutron ports: list of each port and its owner tenant.

Nova servers: list of each server, and its owner tenant.

Policy Detailed Description
---------------------------

This policy collects the owner information for each server, any ports
that server is connected to, and each network those ports are part of.
It then verifies that the owner (tenant_id) is the same for the
server, ports, and networks.  If the tenant_id does not match, the
policy will insert the server's name to the Congress error table.

Setting up Devstack
-------------------

The first step is to install and configure Devstack + Congress:

1) Install Devstack and Congress using the directions in the following
   README.  When asked for a password, type "password" without the quotes.

   https://github.com/stackforge/congress/blob/master/contrib/devstack/README.rst

2) Change OS_USERNAME to "admin" in both nova and neutron::

     /etc/congress/datasources.conf

3) Change auth_strategy from "keystone" to "noauth" in /etc/congress/congress.conf

4) Restart congress-server::

     $ screen -x stack
     switch to congress window <Ctrl-A> ' 23 <Enter>
     <Ctrl-C>
     <Up>
     <Enter>
     <Ctrl-A> d

Setting up an Openstack VM and network
--------------------------------------

At this point, Devstack and Congress are running and ready to accept
API calls.  Now you can setup the Openstack environment, including a
network and subnet owned by the "admin" tenant, a port owned by the
"demo" tenant, and a VM owned by the "demo" tenant.

5) Change to the congress directory::

     $ cd /opt/stack/congress

6) Login as the admin tenant.::

     $ source ~/devstack/openrc admin admin

7) Create a network called "network-admin". Note this is owned by the admin tenant. ::

     $ neutron net-create network-admin
     Created a new network:
     +-----------------------+--------------------------------------+
     | Field                 | Value                                |
     +-----------------------+--------------------------------------+
     | admin_state_up        | True                                 |
     | id                    | a4130b34-81b4-46df-af3a-f133b277592e |
     | name                  | network-admin                        |
     | port_security_enabled | True                                 |
     | shared                | False                                |
     | status                | ACTIVE                               |
     | subnets               |                                      |
     | tenant_id             | 7320f8345acb489e8296ddb3b1ad1262     |
     +-----------------------+--------------------------------------+

8) Create a subnet called "subnet-admin".  Noce this is owned by the admin tenant.::

     $ neutron subnet-create network-admin 2.2.2.0/24 --name subnet-admin
     Created a new subnet:
     +-------------------+------------------------------------------+
     | Field             | Value                                    |
     +-------------------+------------------------------------------+
     | allocation_pools  | {"start": "2.2.2.2", "end": "2.2.2.254"} |
     | cidr              | 2.2.2.0/24                               |
     | dns_nameservers   |                                          |
     | enable_dhcp       | True                                     |
     | gateway_ip        | 2.2.2.1                                  |
     | host_routes       |                                          |
     | id                | 6ff5faa3-1752-4b4f-b744-2e0744cb9208     |
     | ip_version        | 4                                        |
     | ipv6_address_mode |                                          |
     | ipv6_ra_mode      |                                          |
     | name              | subnet-admin                             |
     | network_id        | a4130b34-81b4-46df-af3a-f133b277592e     |
     | tenant_id         | 7320f8345acb489e8296ddb3b1ad1262         |
     +-------------------+------------------------------------------+

9) Create port owned by the demo tenant::

     $ source ~/devstack/openrc admin demo
     $ neutron port-create network-admin | tee port-create.log
     Created a new port:
     +-----------------------+--------------------------------------------------------------------------------+
     | Field                 | Value                                                                          |
     +-----------------------+--------------------------------------------------------------------------------+
     | admin_state_up        | True                                                                           |
     | allowed_address_pairs |                                                                                |
     | binding:host_id       |                                                                                |
     | binding:profile       | {}                                                                             |
     | binding:vif_details   | {}                                                                             |
     | binding:vif_type      | unbound                                                                        |
     | binding:vnic_type     | normal                                                                         |
     | device_id             |                                                                                |
     | device_owner          |                                                                                |
     | fixed_ips             | {"subnet_id": "6ff5faa3-1752-4b4f-b744-2e0744cb9208", "ip_address": "2.2.2.2"} |
     | id                    | 066c5cfc-949e-4d56-ad76-15528c68c8b8                                           |
     | mac_address           | fa:16:3e:e9:f8:2a                                                              |
     | name                  |                                                                                |
     | network_id            | a4130b34-81b4-46df-af3a-f133b277592e                                           |
     | security_groups       | dd74db4f-fe35-4a51-b920-313fd36837f2                                           |
     | status                | DOWN                                                                           |
     | tenant_id             | 81084a94769c4ce0accb6968c397a085                                               |
     +-----------------------+--------------------------------------------------------------------------------+

     $ PORT_ID=`grep " id " port-create.log | awk '{print $4}'`

10) Create vm named "vm-demo" with the newly created port.  The vm is owned by the demo tenant::

     $ nova boot --image cirros-0.3.2-x86_64-uec --flavor 1 vm-demo --nic port-id=$PORT_ID
     +--------------------------------------+----------------------------------------------------------------+
     | Property                             | Value                                                          |
     +--------------------------------------+----------------------------------------------------------------+
     | OS-DCF:diskConfig                    | MANUAL                                                         |
     | OS-EXT-AZ:availability_zone          | nova                                                           |
     | OS-EXT-SRV-ATTR:host                 | Ubuntu1204Server                                               |
     | OS-EXT-SRV-ATTR:hypervisor_hostname  | Ubuntu1204Server                                               |
     | OS-EXT-SRV-ATTR:instance_name        | instance-00000001                                              |
     | OS-EXT-STS:power_state               | 0                                                              |
     | OS-EXT-STS:task_state                | networking                                                     |
     | OS-EXT-STS:vm_state                  | building                                                       |
     | OS-SRV-USG:launched_at               | -                                                              |
     | OS-SRV-USG:terminated_at             | -                                                              |
     | accessIPv4                           |                                                                |
     | accessIPv6                           |                                                                |
     | adminPass                            | js6ZnNjX82rQ                                                   |
     | config_drive                         |                                                                |
     | created                              | 2014-08-15T00:08:11Z                                           |
     | flavor                               | m1.tiny (1)                                                    |
     | hostId                               | 930764f06a4a5ffb8e433b24efce63fd5096ddaee5e62b439169fbdf       |
     | id                                   | 19b6049e-fe69-416a-b6f1-c02afaf54a34                           |
     | image                                | cirros-0.3.2-x86_64-uec (e8dc8305-c9de-42a8-b3d1-6b1bc9869f32) |
     | key_name                             | -                                                              |
     | metadata                             | {}                                                             |
     | name                                 | vm-demo                                                        |
     | os-extended-volumes:volumes_attached | []                                                             |
     | progress                             | 0                                                              |
     | security_groups                      | default                                                        |
     | status                               | BUILD                                                          |
     | tenant_id                            | 81084a94769c4ce0accb6968c397a085                               |
     | updated                              | 2014-08-15T00:08:12Z                                           |
     | user_id                              | 3d6c6119e5c94c258a26ab246cdcac12                               |
     +--------------------------------------+----------------------------------------------------------------+

11) Get tenant ids::

     $ keystone tenant-list | tee tenant-list.log
     +----------------------------------+--------------------+---------+
     |                id                |        name        | enabled |
     +----------------------------------+--------------------+---------+
     | 7320f8345acb489e8296ddb3b1ad1262 |       admin        |   True  |
     | 81084a94769c4ce0accb6968c397a085 |        demo        |   True  |
     | 315d4a5892ed4da1bdf717845e8959df | invisible_to_admin |   True  |
     | b590e27c87fa40c18c850954dca4c879 |      service       |   True  |
     +----------------------------------+--------------------+---------+

     $ ADMIN_ID=`grep " admin " tenant-list.log | awk '{print $2}'`
     $ DEMO_ID=`grep " demo " tenant-list.log | awk '{print $2}'`

Creating a Congress Policy
--------------------------

At this point, demo's vm exists and its port is connected to an
network belonging to admin.  This is a violation of the policy.  Now
you will add the congress policy to detect the violation.

12) Add a rule that detects when a VM is connected to a port belonging to a different group::

     $ curl -X POST localhost:1789/policies/classification/rules -d '{"rule": "error(name2) :- neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p), nova:servers(device_id, name2, c2, d2, tenant_id2, f2, g2, h2), neutron:networks(a3, b3, c3, d3, e3, tenant_id3, g3, h3, i3, network_id, k3), not same_group(tenant_id, tenant_id2) "}'

     {"comment": null, "id": "869e6a85-43ed-49fd-9fd7-f649d9c06fc2", "rule": "error(name2) :- neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p), nova:servers(device_id, name2, c2, d2, tenant_id2, f2, g2, h2), neutron:networks(a3, b3, c3, d3, e3, tenant_id3, g3, h3, i3, network_id, k3), not same_group(tenant_id, tenant_id2)"}


13) Add a rule that detects when a port is connected to a network belonging to a different group::

     $ curl -X POST localhost:1789/policies/classification/rules -d '{"rule": "error(name2) :- neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p), nova:servers(device_id, name2, c2, d2, tenant_id2, f2, g2, h2), neutron:networks(a3, b3, c3, d3, e3, tenant_id3, g3, h3, i3, network_id, k3) , not same_group(tenant_id2, tenant_id3) "}'

     {"comment": null, "id": "6871ef89-4bec-4b47-ad2f-b71788e9d400", "rule": "error(name2) :- neutron:ports(a, b, c, d, e, f, g, network_id, tenant_id, j, k, l, m, n, device_id, p), nova:servers(device_id, name2, c2, d2, tenant_id2, f2, g2, h2), neutron:networks(a3, b3, c3, d3, e3, tenant_id3, g3, h3, i3, network_id, k3), not same_group(tenant_id2, tenant_id3)"}

14) Define a table mapping a tenant_id to any other tenant in the same group::

     $ curl -X POST localhost:1789/policies/classification/rules -d '{"rule": "same_group(x, y) :- group(x, g), group(y, g) "}'

     {"comment": null, "id": "9165ab44-ef9e-4561-af55-3d29b9da0bfe", "rule": "same_group(x, y) :- group(x, g), group(y, g)"}

15) Create a table mapping tenant_id to a group name.  admin and demo
are in two separate groups called "IT" and "Marketing" respectively.
In practice, this "group" table would receive group membership
information from a system like Keystone or ActiveDirectory.  In this
tutorial, we'll populate the group table with membership information
manually::

     $ curl -X POST localhost:1789/policies/classification/rules -d "{\"rule\": \"group(\\\"$ADMIN_ID\\\", \\\"IT\\\") :- true \"}"

     {"comment": null, "id": "1554e108-adc5-40e1-870a-dda3b877f2bc", "rule": "group(\"7320f8345acb489e8296ddb3b1ad1262\", \"IT\") :- true()"}

     $ curl -X POST localhost:1789/policies/classification/rules -d "{\"rule\": \"group(\\\"$DEMO_ID\\\", \\\"Marketing\\\") :- true \"}"

     {"comment": null, "id": "810c2217-0161-4ba6-ab29-a822bfca0f99", "rule": "group(\"81084a94769c4ce0accb6968c397a085\", \"Marketing\") :- true()"}

Listing Policy Violations
-------------------------

Finally, we can print the error table to see if there are any
violations (which there are).

16) List the errors.  You should see one entry for "vm-demo".::

      $ curl -X GET localhost:1789/policies/classification/tables/error/rows

      [
         {
           "data": [
             "vm-demo"
           ]
         }
       ]

Fix the Policy Violation
------------------------

17) To fix the policy violation, we'll remove the demo's port from admin's network.::

     $ neutron port-delete $PORT_ID
     Deleted port: 066c5cfc-949e-4d56-ad76-15528c68c8b8

Relisting Policy Violations
---------------------------

18) Now, when print the error table it will be empty because there are
no violations.::

     $ curl -X GET localhost:1789/policies/classification/tables/error/rows
     []
