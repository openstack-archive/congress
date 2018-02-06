#!/bin/bash -x

#############################################################################
### exercise all the congress CLI commands                                ###
#   except datasource push update command
#
#   Note:
#   The following OpenStack environment variables must set first:
#   OS_USERNAME, OS_PASSWORD, OS_PROJECT_NAME, OS_TENANT_NAME, OS_AUTH_URL
#   For example by running (under a devstack setup)
#     $ . devstack/openrc admin admin
#############################################################################

openstack congress version list
UUID=`openstack congress datasource create --config username=admin --config tenant_name=admin  --config auth_url=http://127.0.0.1/identity --config password=password --config poll_time=5 nova nova2 -f value | sed -n '5p'`
openstack congress datasource actions show nova2
openstack congress datasource actions show $UUID
openstack congress datasource list
openstack congress datasource request-refresh nova2
openstack congress datasource request-refresh $UUID
openstack congress datasource schema show nova2
openstack congress datasource schema show $UUID
openstack congress datasource status show nova2
openstack congress datasource status show $UUID
openstack congress datasource table list nova2
openstack congress datasource table list $UUID
openstack congress datasource table schema show nova2 flavors
openstack congress datasource table schema show $UUID flavors
openstack congress datasource table show nova2 flavors
openstack congress datasource table show $UUID flavors
openstack congress driver config show nova
openstack congress driver list
openstack congress driver schema show nova
openstack congress datasource row list nova flavors
openstack congress datasource row list nova2 flavors
openstack congress datasource row list $UUID flavors
openstack congress datasource delete nova2

PUUID=`openstack congress policy create policy1 -f value | sed -n '3p'`
openstack congress policy show policy1
openstack congress policy show $PUUID
openstack congress policy list
UUID=`openstack congress policy rule create policy1 'temp(1,2)' -f value | sed -n '2p'`
openstack congress policy rule show policy1 $UUID
openstack congress policy rule delete policy1 $UUID
# UUID=`openstack congress policy rule create $PUUID 'temp(1,2)' -f value | sed -n '2p'`
# openstack congress policy rule show $PUUID $UUID
# openstack congress policy rule delete $PUUID $UUID
openstack congress policy rule create policy1 'q(1,2)'
openstack congress policy rule list policy1  # 1 rules
# openstack congress policy rule list $PUUID  # 1 rules
openstack congress policy rule create policy1 'q(2,3)'
openstack congress policy rule create policy1 'p(x,y) :- q(x,y), r(y,x)'
openstack congress policy row list policy1 q  # 2 tuples
# openstack congress policy row list $PUUID q  # 2 tuples
openstack congress policy row list policy1 p  # should be empty
openstack congress policy rule create policy1 'r(2,1)'
openstack congress policy rule create policy1 'r(3,2)'
openstack congress policy rule create policy1 'r(5,7)'
openstack congress policy rule create policy1 'r(9,9)'
openstack congress policy rule create policy1 'q(5,7)'

openstack congress policy table list policy1
# openstack congress policy table list $PUUID
openstack congress policy table show policy1 'p'
# openstack congress policy table show $PUUID 'p'
openstack congress policy row list policy1 q  # 3 tuples
openstack congress policy row list policy1 r  # 4 tuples
openstack congress policy row list policy1 p  # 2 tuples
openstack congress policy rule create policy1 'p(x,y) :- r(x,y), NOT equal(x,9)'
openstack congress policy row list policy1 p  # 5 tuples
openstack congress policy rule create policy1 's(x) :- nova:flavors(vcpus=x), p(x,y)'
openstack congress policy rule create policy1 't(x) :- nova:flavors(vcpus=x), NOT s(x)'
openstack congress policy row list policy1 s  # (2),(1) env dep 
openstack congress policy row list policy1 t  # (4), (8) env dep
openstack congress policy create policy2
openstack congress policy rule create policy2 'a(1,2)'
openstack congress policy row list policy2 a
openstack congress policy table list policy2
openstack congress policy rule create policy1 'u(x,y) :- q(x,y), NOT policy2:a(x,y)'
openstack congress policy row list policy1 u  # 2 tuples
openstack congress policy delete policy2

# restart openstack congress
openstack congress policy row list policy1 q  # 3 tuples
openstack congress policy row list policy1 r  # 4 tuples
openstack congress policy row list policy1 p  # 5 tuples
openstack congress policy row list policy1 s  # (2),(1) env dep 
openstack congress policy row list policy1 t  # (4), (8) env dep

# test execute
openstack congress policy rule create policy1 'execute[nova:flavors.delete(id)] :- nova:flavors(id=id,vcpus=x),s(x), q(10,10)'  # change to action
openstack congress policy row list policy1 s
# TODO make action undoable. undo.

openstack congress datasource delete nova
UUID=`openstack congress datasource create --config username=admin --config tenant_name=admin  --config auth_url=http://127.0.0.1/identity --config password=password --config poll_time=5 nova nova -f value | sed -n '5p'`
openstack congress datasource row list nova flavors
openstack congress policy rule create policy1 'q(10,10)'
sleep 5  # wait to make sure execution takes effect
openstack congress policy row list policy1 s  # 0 tuples, could take a little time to realize
openstack congress datasource row list $UUID flavors  # removed all entries with vcpus 1,2

# test simulate
openstack congress policy rule create policy1 'simA(x) :- simB(x)'
openstack congress policy simulate policy1 "simA(x)" "simB+(1)" action  # 1 tuple
# openstack congress policy simulate $PUUID "simA(x)" "simB+(1)" action  # 1 tuple

openstack congress policy delete $PUUID
openstack congress policy list  # action, classification
