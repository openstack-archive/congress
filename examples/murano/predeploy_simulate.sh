cd /opt/stack/congress
source ~/devstack/openrc admin admin

echo "Deleting all existing rules of murano_system policy"
rule_ids=(`openstack congress policy rule list murano_system | grep "// ID:" | awk '{print $3}'`)
for i in "${rule_ids[@]}"
do
    echo "delete rule ${i}"
    openstack congress policy rule delete murano_system ${i}
done

echo "Rule deleting done."

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
murano.environments(env_id, env_name) :-
    murano.objects(env_id, owner_id, "io.murano.Environment"),
    murano.properties(env_id, "name", env_name)'

openstack congress policy rule create murano_system '
murano.instances(env_id, obj_id) :-
    murano.objects(obj_id, service_id, instance_type),
    murano.objects(service_id, env_id, service_type),
    murano.parent_types(obj_id, "io.murano.resources.Instance")'

openstack congress policy rule create murano_system '
predeploy_error(env_id) :-
    murano.environments(env_id, env_name),
    murano.instances(env_id, obj_id),
    murano.properties(obj_id, "flavor", flavor),
    murano.states(env_id, env_state),
    equal(env_state, "pending"),
    not allowed_flavors(flavor)'

openstack congress policy rule create murano_system '
untyped_predeploy_error(env_id) :-
    murano.objects(env_id, tenant_id, "io.murano.Environment"),
    murano.objects(instance_id, service_id, instance_type),
    murano.objects(service_id, env_id, service_type),
    murano.parent_types(instance_id, "io.murano.resources.Instance"),
    murano.properties(instance_id, "flavor", flavor),
    murano.states(env_id, env_state),
    equal(env_state, "pending"),
    not allowed_flavors(flavor)'

echo "Define rules using murano datasource"
openstack congress policy rule create murano_system '
untyped_predeploy_error2(env_id) :-
    murano:objects(env_id, tenant_id, "io.murano.Environment"),
    murano:objects(instance_id, service_id, instance_type),
    murano:objects(service_id, env_id, service_type),
    murano:parent_types(instance_id, "io.murano.resources.Instance"),
    murano:properties(instance_id, "flavor", flavor),
    murano:states(env_id, env_state),
    equal(env_state, "pending"),
    not allowed_flavors(flavor)'

echo ""
echo "--- simulate policy ---"
echo 'env_id = "env_uuid", flavor = "m1.small"'
openstack congress policy simulate murano_system 'untyped_predeploy_error(env_id)' '
    murano.objects+("env_uuid", "env_owner_uuid", "io.murano.Environment")
    murano.objects+("svc_uuid", "env_uuid", "service_type")
    murano.objects+("inst_uuid", "svc_uuid", "instance_type")
    murano.parent_types+("inst_uuid", "io.murano.resources.Instance")
    murano.properties+("inst_uuid", "flavor", "m1.small")
    murano.states+("env_uuid", "pending")' action

echo "---"
echo 'env_id = "env_uuid", flavor = "m1.large"'
openstack congress policy simulate murano_system 'untyped_predeploy_error(env_id)' '
    murano.objects+("env_uuid", "env_owner_uuid", "io.murano.Environment")
    murano.objects+("svc_uuid", "env_uuid", "service_type")
    murano.objects+("inst_uuid", "svc_uuid", "instance_type")
    murano.parent_types+("inst_uuid", "io.murano.resources.Instance")
    murano.properties+("inst_uuid", "flavor", "m1.large")
    murano.states+("env_uuid", "pending")' action

echo "---"
echo 'Simulate using datasource tables. env_id = "env_uuid", flavor = "m1.large"'
openstack congress policy simulate murano_system 'untyped_predeploy_error2(env_id)' '
    murano:objects+("env_uuid", "env_owner_uuid", "io.murano.Environment")
    murano:objects+("svc_uuid", "env_uuid", "service_type")
    murano:objects+("inst_uuid", "svc_uuid", "instance_type")
    murano:parent_types+("inst_uuid", "io.murano.resources.Instance")
    murano:properties+("inst_uuid", "flavor", "m1.large")
    murano:states+("env_uuid", "pending")' action

echo "---"
echo 'env_id = "env_uuid", flavor = "m1.large"'
openstack congress policy simulate murano_system 'predeploy_error(env_id)' '
    murano.objects+("env_uuid", "env_owner_uuid", "io.murano.Environment")
    murano.properties+("env_uuid", "name", "second_env")
    murano.objects+("svc_uuid", "env_uuid", "service_type")
    murano.objects+("inst_uuid", "svc_uuid", "instance_type")
    murano.parent_types+("inst_uuid", "io.murano.resources.Instance")
    murano.properties+("inst_uuid", "flavor", "m1.large")
    murano.states+("env_uuid", "pending")' action
