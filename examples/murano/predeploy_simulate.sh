cd /opt/stack/congress
. ~/devstack/openrc admin demo

echo "Creating datasource murano: user=admin, tenant=demo"
openstack congress datasource create murano "murano" \
    --config username="admin" \
    --config tenant_name="demo" \
    --config password="password" \
    --config auth_url="http://127.0.0.1:5000/v2.0"

echo "Deleting all existing rules of murano_system policy"
rule_ids=(`openstack congress policy rule list murano_system | \
grep "// ID:" | awk '{print $3}'`)
for i in "${rule_ids[@]}"
do
    echo "delete rule ${i}"
    openstack congress policy rule delete murano_system ${i}
done

echo "Deleting murano_system policy if exists"
murano_system_uuid=(`openstack congress policy list | \
    grep murano_system | awk '{print $2}'`)
if [ -n "$murano_system_uuid" ]
then
    echo "Found existing $murano_system_uuid"
    openstack congress policy delete $murano_system_uuid
    echo "$murano_system_uuid deleted"
fi

echo
echo "Create murano_system policy"
openstack congress policy create murano_system

openstack congress policy rule create murano_system '
allowed_flavors(flavor) :-
    nova:flavors(flavor_id, flavor, vcpus, ram, disk, ephemeral, rxtx_factor),
    equal(flavor, "m1.medium")'

openstack congress policy rule create murano_system '
allowed_flavors(flavor) :-
    nova:flavors(flavor_id, flavor, vcpus, ram, disk, ephemeral, rxtx_factor),
    equal(flavor, "m1.small")'

openstack congress policy rule create murano_system '
allowed_flavors(flavor) :-
    nova:flavors(flavor_id, flavor, vcpus, ram, disk, ephemeral, rxtx_factor),
    equal(flavor, "m1.tiny")'

openstack congress policy rule create murano_system '
murano_pending_envs(env_id) :-
    murano:objects(env_id, tenant_id, "io.murano.Environment"),
    murano:states(env_id, env_state),
    equal(env_state, "pending")'

openstack congress policy rule create murano_system '
murano_instances(env_id, instance_id) :-
    murano:objects(env_id, tenant_id, "io.murano.Environment"),
    murano:objects(service_id, env_id, service_type),
    murano:parent_types(service_id, "io.murano.Object"),
    murano:parent_types(service_id, "io.murano.Application"),
    murano:parent_types(service_id, service_type),
    murano:objects(instance_id, service_id, instance_type),
    murano:parent_types(instance_id, "io.murano.resources.Instance"),
    murano:parent_types(instance_id, "io.murano.Object"),
    murano:parent_types(instance_id, instance_type)'

openstack congress policy rule create murano_system '
murano_instance_flavors(instance_id, flavor) :-
    murano:properties(instance_id, "flavor", flavor)'

openstack congress policy rule create murano_system '
predeploy_error(env_id) :-
    murano_pending_envs(env_id),
    murano_instances(env_id, instance_id),
    murano_instance_flavors(instance_id, flavor),
    not allowed_flavors(flavor)'

echo ""
echo "--- simulate policy ---"
echo 'env_id = "env_uuid", flavor = "m1.small"'
openstack congress policy simulate murano_system 'predeploy_error(env_id)' '
    murano:objects+("env_uuid", "tenant_uuid", "io.murano.Environment")
    murano:states+("env_uuid", "pending")

    murano:objects+("service_uuid", "env_uuid", "service_type")
    murano:parent_types+("service_uuid", "io.murano.Object")
    murano:parent_types+("service_uuid", "io.murano.Application")
    murano:parent_types+("service_uuid", "service_type")
    murano:objects+("instance_uuid", "service_uuid", "instance_type")
    murano:parent_types+("instance_uuid", "io.murano.resources.Instance")
    murano:parent_types+("instance_uuid", "io.murano.Object")
    murano:parent_types+("instance_uuid", "instance_type")

    murano:properties+("instance_uuid", "flavor", "m1.small")' action

echo "---"
echo 'env_id = "env_uuid", flavor = "m1.large"'
openstack congress policy simulate murano_system 'predeploy_error(env_id)' '
    murano:objects+("env_uuid", "tenant_uuid", "io.murano.Environment")
    murano:states+("env_uuid", "pending")

    murano:objects+("service_uuid", "env_uuid", "service_type")
    murano:parent_types+("service_uuid", "io.murano.Object")
    murano:parent_types+("service_uuid", "io.murano.Application")
    murano:parent_types+("service_uuid", "service_type")
    murano:objects+("instance_uuid", "service_uuid", "instance_type")
    murano:parent_types+("instance_uuid", "io.murano.resources.Instance")
    murano:parent_types+("instance_uuid", "io.murano.Object")
    murano:parent_types+("instance_uuid", "instance_type")

    murano:properties+("instance_uuid", "flavor", "m1.large")' action
