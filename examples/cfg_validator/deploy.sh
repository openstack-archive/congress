#!/bin/bash
#
# Renew the policy validator policy and its default rules

DIR="$(cd $(dirname "$0") && pwd)"
RULES_DIR="${DIR}/rules"

cd /opt/stack/congress
. ~/devstack/openrc admin admin

echo
echo "Creating datasource config"
echo
openstack congress datasource create config "config"

echo
echo "Deleting existing rules of validatorpo policy if any"
echo
rule_ids=$(openstack congress policy rule list validatorpo \
    | grep "// ID:" | awk '{print $3}')
for i in $rule_ids; do
    echo "delete rule ${i}"
    openstack congress policy rule delete validatorpo ${i}
done

echo
validatorpo_uuid=$(openstack congress policy list -c id -c name \
    | awk '/validatorpo/ {print $2}')
if [[ -n "$validatorpo_uuid" ]]; then
    echo "Deleting existing validatorpo policy"
    openstack congress policy delete $validatorpo_uuid
    echo "$validatorpo_uuid deleted"
fi

echo
echo "Create validatorpo policy"
echo
openstack congress policy create validatorpo


echo
echo "Create default validatorpo rules"
echo

openstack congress policy rule create validatorpo --name derive_deprecateds \
    "deprecated(hostname, template, namespace, group, name, value)
    :-
    config:option(id=option_id, namespace=ns_id, group=group, name=name),
    config:binding(option_id=option_id, file_id=file_id, val=value),
    config:file(id=file_id, host_id=host_id, template=template_id),
    config:host(id=host_id, name=hostname),
    config:template_ns(template=template_id, namespace=ns_id),
    config:template(id=template_id, name=template),
    config:namespace(id=ns_id, name=namespace),
    config:option_info(option_id=option_id, deprecated='True')"

echo
openstack congress policy rule create validatorpo --name value_defined_in_file \
    "defined_in(option_id, file_id)
    :-
    config:binding(option_id=option_id, file_id=file_id)"

echo
openstack congress policy rule create validatorpo \
    "value(hostname, file, group, name, value)
    :-
    config:option(id=option_id, group=group, name=name),
    config:file(id=file_id, host_id=host_id, name=file),
    config:host(id=host_id, name=hostname),
    config:binding(option_id=option_id, file_id=file_id, val=value)"

echo
openstack congress policy rule create validatorpo \
    "value_or_default(option_id, file_id, value)
    :-
    config:binding(option_id, file_id, value)"
openstack congress policy rule create validatorpo \
    "value_or_default(option_id, file_id, value)
    :-
    default_value(option_id, file_id, value)"

echo
openstack congress policy rule create validatorpo --name default \
    "default_value(option_id, file_id, default)
    :-
    config:option(id=option_id, namespace=ns_id),
    config:file(id=file_id, template=template_id),
    config:template_ns(template=template_id, namespace=ns_id),
    config:option_info(option_id=option_id, default=default),
    not builtin:equal('', default),
    not defined_in(option_id, file_id)"

echo
openstack congress policy rule create validatorpo --name missing_mandatories \
    "missing_mandatory(hostname, template, namespace, group, name)
    :-
    config:option(id=option_id, namespace=ns_id, group=group, name=name),
    config:option_info(option_id=option_id, required='True'),
    config:file(id=file_id, host_id=host_id, template=template_id),
    config:host(id=host_id, name=hostname),
    config:template_ns(template=template_id, namespace=ns_id),
    config:template(id=template_id, name=template),
    config:namespace(id=ns_id, name=namespace),
    not defined_in(option_id, file_id)"

echo
openstack congress policy rule create validatorpo --name validate_int \
    "invalid_int(option_id, min, max, choices, value, error)
    :-
    config:binding(option_id=option_id, val=value),
    config:int_type(option_id=option_id, min=min, max=max, choices=choices),
    builtin:validate_int(min, max, choices, value, error),
    not equal('', error)"

echo
openstack congress policy rule create validatorpo --name validate_float \
    "invalid_float(option_id, min, max, value, error)
    :-
    config:binding(option_id=option_id, val=value),
    config:float_type(option_id=option_id, min=min, max=max),
    builtin:validate_float(min, max, error),
    not equal('', error)"

echo
openstack congress policy rule create validatorpo --name validate_strings \
    "invalid_string(option_id, regex, max_length, quotes, ignore_case, choices, value, error)
    :-
    config:binding(option_id=option_id, val=value),
    config:string_type(option_id=option_id, regex=regex, max_length=max_length, quotes=quotes, ignore_case=ignore_case, choices=choices),
    builtin:validate_string(regex, max_length, quotes, ignore_case, choices, value, error),
    not equal('', error)"

echo
openstack congress policy rule create validatorpo \
    "invalid_value(option_id, value, errro)
    :-
    invalid_int(option_id, x2, x3, x4, value, errro)"
openstack congress policy rule create validatorpo \
    "invalid_value(option_id, value, errro)
    :-
    invalid_string(option_id, x2, x3, x4, x5, x6, value, errro)"

echo
openstack congress policy rule create validatorpo \
    "warn('Wrongly typed option value(s)', 'invalid_value')
    :-
    invalid_value(x1, x2, x3)"
openstack congress policy rule create validatorpo \
    "warn('Mandatory option(s) missing', 'missing_mandatory')
    :-
    missing_mandatory(x1, x2, x3, x4, x5)"
openstack congress policy rule create validatorpo \
    "warn('Deprecated option(s) used', 'deprecated')
    :-
    deprecated(x1, x2, x3, x4, x5, x6)"

echo
echo "Adding business rules"
echo

if [[ -d $RULES_DIR ]]; then
    for rule_file in $RULES_DIR/*.rule ; do
        content=$(awk '/^[^#]/ {print}' <$rule_file)
        IFS=';' read -ra rules <<< $content
        for rule in "${rules[@]}"; do
            openstack congress policy rule create validatorpo "${rule}"
        done
    done
fi
