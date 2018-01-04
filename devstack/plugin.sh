#!/usr/bin/env bash
# Plugin file for congress services
#----------------------------------

# Dependencies:
# ``functions`` file
# ``DEST`` must be defined
# ``STACK_USER`` must be defined

# Functions in this file are classified into the following categories:
#
# - entry points (called from stack.sh or unstack.sh)
# - internal functions
# - congress exercises


# Save trace setting
XTRACE=$(set +o | grep xtrace)
set +o xtrace


# Functions
# ---------

# Test if any Congress services are enabled
# is_congress_enabled
function is_congress_enabled {
    [[ ,${ENABLED_SERVICES//congress-agent/} =~ ,"congress" ]] && return 0
    return 1
}

# configure_congress()
# Set common config for all congress server and agents.
function configure_congress {
    setup_develop $CONGRESS_DIR
    # Put config files in ``CONGRESS_CONF_DIR`` for everyone to find
    if [[ ! -d $CONGRESS_CONF_DIR ]]; then
        sudo mkdir -p $CONGRESS_CONF_DIR
    fi
    sudo chown $STACK_USER $CONGRESS_CONF_DIR

    touch $CONGRESS_CONF
    sudo chown $STACK_USER $CONGRESS_CONF

    # Format logging
    if [ "$LOG_COLOR" == "True" ] && [ "$SYSLOG" == "False" ]; then
        setup_colorized_logging $CONGRESS_CONF DEFAULT project_id
    fi
    CONGRESS_API_PASTE_FILE=$CONGRESS_CONF_DIR/api-paste.ini

    cp $CONGRESS_DIR/etc/api-paste.ini $CONGRESS_API_PASTE_FILE
    if [[ ! -d $CONGRESS_LIBRARY_DIR ]]; then
        mkdir $CONGRESS_LIBRARY_DIR
    fi
    cp -r $CONGRESS_DIR/library/* $CONGRESS_LIBRARY_DIR

    # Update either configuration file
    iniset $CONGRESS_CONF DEFAULT debug $ENABLE_DEBUG_LOG_LEVEL
    iniset $CONGRESS_CONF DEFAULT auth_strategy $CONGRESS_AUTH_STRATEGY
    iniset $CONGRESS_CONF DEFAULT datasource_sync_period 30
    iniset $CONGRESS_CONF DEFAULT replicated_policy_engine "$CONGRESS_REPLICATED"
    iniset $CONGRESS_CONF DEFAULT transport_url rabbit://$RABBIT_USERID:$RABBIT_PASSWORD@$RABBIT_HOST:5672

    CONGRESS_DRIVERS="congress.datasources.neutronv2_driver.NeutronV2Driver,"
    CONGRESS_DRIVERS+="congress.datasources.neutronv2_qos_driver.NeutronV2QosDriver,"
    CONGRESS_DRIVERS+="congress.datasources.glancev2_driver.GlanceV2Driver,"
    CONGRESS_DRIVERS+="congress.datasources.nova_driver.NovaDriver,"
    CONGRESS_DRIVERS+="congress.datasources.keystonev3_driver.KeystoneV3Driver,"
    CONGRESS_DRIVERS+="congress.datasources.cinder_driver.CinderDriver,"
    CONGRESS_DRIVERS+="congress.datasources.swift_driver.SwiftDriver,"
    CONGRESS_DRIVERS+="congress.datasources.plexxi_driver.PlexxiDriver,"
    CONGRESS_DRIVERS+="congress.datasources.vCenter_driver.VCenterDriver,"
    CONGRESS_DRIVERS+="congress.datasources.murano_driver.MuranoDriver,"
    CONGRESS_DRIVERS+="congress.datasources.ironic_driver.IronicDriver,"
    CONGRESS_DRIVERS+="congress.datasources.heatv1_driver.HeatV1Driver,"
    CONGRESS_DRIVERS+="congress.datasources.doctor_driver.DoctorDriver,"
    CONGRESS_DRIVERS+="congress.datasources.aodh_driver.AodhDriver,"
    CONGRESS_DRIVERS+="congress.tests.fake_datasource.FakeDataSource,"
    CONGRESS_DRIVERS+="congress.datasources.cfgvalidator_driver.ValidatorDriver"

    iniset $CONGRESS_CONF DEFAULT drivers $CONGRESS_DRIVERS

    iniset $CONGRESS_CONF database connection `database_connection_url $CONGRESS_DB_NAME`

    _congress_setup_keystone $CONGRESS_CONF keystone_authtoken

}

function configure_congress_datasources {
    _configure_service neutron neutronv2
    _configure_service neutron neutronv2_qos
    _configure_service nova nova
    _configure_service key keystonev3
    _configure_service cinder cinder
    _configure_service swift swift
    _configure_service glance glancev2
    _configure_service murano murano
    _configure_service ironic ironic
    _configure_service heat heat
    _configure_service aodh aodh
    _configure_service congress-agent config

}

function _configure_service {
    if is_service_enabled $1; then
        if [ "$2" == "config" ] ; then
            openstack congress datasource create $2 "$2" \
                --config poll_time=10
        else
            openstack congress datasource create $2 "$2" \
                --config poll_time=10 \
                --config username=$OS_USERNAME \
                --config tenant_name=$OS_PROJECT_NAME \
                --config password=$OS_PASSWORD \
                --config auth_url=http://$SERVICE_HOST/identity
        fi
    fi
}

function create_predefined_policy {
    if [ -n "$CONGRESS_PREDEFINED_POLICY_FILE" ] ; then
        python $CONGRESS_DIR/scripts/preload-policies/output_policy_command.py \
            $CONGRESS_PREDEFINED_POLICY_FILE | while read CONGRESS_CMD
        do
            $CONGRESS_CMD
        done
    fi
}

function _install_congress_dashboard {
    git_clone $CONGRESSDASHBOARD_REPO $CONGRESSDASHBOARD_DIR $CONGRESSDASHBOARD_BRANCH
    setup_develop $CONGRESSDASHBOARD_DIR
    _congress_setup_horizon
}

# create_congress_cache_dir() - Part of the _congress_setup_keystone() process
function create_congress_cache_dir {
    # Create cache dir
    sudo mkdir -p $CONGRESS_AUTH_CACHE_DIR
    sudo chown $STACK_USER $CONGRESS_AUTH_CACHE_DIR
    rm -f $CONGRESS_AUTH_CACHE_DIR/*
}

# create_congress_accounts() - Set up common required congress accounts

# Tenant               User       Roles
# ---------------------------------------------------------------------
# service              congress    admin        # if enabled

# Migrated from keystone_data.sh
function create_congress_accounts {
    if [[ "$ENABLED_SERVICES" =~ "congress" ]]; then

        create_service_user "congress"

        local congress_service=$(get_or_create_service "congress" \
            "policy" "Congress Service")
        get_or_create_endpoint $congress_service \
            "$REGION_NAME" \
            "http://$SERVICE_HOST:$CONGRESS_PORT/" \
            "http://$SERVICE_HOST:$CONGRESS_PORT/" \
            "http://$SERVICE_HOST:$CONGRESS_PORT/"
    fi
}

# init_congress() - Initialize databases, etc.
function init_congress {
    recreate_database $CONGRESS_DB_NAME utf8
    # Run Congress db migrations
    congress-db-manage --config-file $CONGRESS_CONF upgrade head
}

# install_congress() - install dependency, collect client source and prepare
function install_congress {
    # congress requires java so we install it here
    if is_ubuntu; then
        install_package default-jre
    elif is_fedora; then
        install_package jre
    else
        die $LINENO "Congress devstack only supports Debian and Red Hat-based"
    fi
    git_clone $CONGRESSCLIENT_REPO $CONGRESSCLIENT_DIR $CONGRESSCLIENT_BRANCH
    setup_develop $CONGRESSCLIENT_DIR

    if is_service_enabled horizon; then
        _install_congress_dashboard
    fi
}

# Start running processes, including screen
function start_congress_service_and_check {
    # build config-file options
    local cfg_file
    local CFG_FILE_OPTIONS="--config-file $CONGRESS_CONF"

    # Start the congress services in seperate processes
    echo_summary "Installing congress services"

    if [ "$CONGRESS_MULTIPROCESS_DEPLOYMENT" == "False" ]; then
        echo "Installing congress as single process"
        run_process congress "$CONGRESS_BIN_DIR/congress-server --node-id=allinonenode $CFG_FILE_OPTIONS"
    else
        echo "Installing congress as multi process"
        run_process congress-api "$CONGRESS_BIN_DIR/congress-server --api --node-id=apinode $CFG_FILE_OPTIONS"
        run_process congress-engine "$CONGRESS_BIN_DIR/congress-server --policy-engine --node-id=enginenode $CFG_FILE_OPTIONS"
        run_process congress-datasources "$CONGRESS_BIN_DIR/congress-server --datasources --node-id=datanode $CFG_FILE_OPTIONS"
    fi

    # Start multiple PE's
    if [ "$CONGRESS_REPLICATED" == "True" ]; then
        run_process congress-engine "$CONGRESS_BIN_DIR/congress-server --policy-engine --node-id=enginenode-2 $CFG_FILE_OPTIONS"
        run_process congress-engine "$CONGRESS_BIN_DIR/congress-server --policy-engine --node-id=enginenode-3 $CFG_FILE_OPTIONS"
    fi

    echo "Waiting for Congress to start..."
    if ! timeout $SERVICE_TIMEOUT sh -c "while ! wget --no-proxy -q -O- http://$CONGRESS_HOST:$CONGRESS_PORT; do sleep 1; done"; then
        die $LINENO "Congress did not start"
    fi

    # Expose encryption key to tempest test launched replica instances
    # WARNING: this setting deploys an insecure setup meant for gate-test only
    # Explanation: congress_tempest_tests/tests/scenario/congress_ha/test_ha.py
    #    launches replica congress instances from a different user than the
    #    original devstack-launched instance. Hence, the encryption keys need
    #    to be exposed to additional users for the test to work as intended.
    # Note: This works correctly only for default encryption key location
    # /etc/congress/keys
    # If needed in future, this script can read custom key location from
    # $CONGRESS_CONF and adjust accordingly
    if [ "$CONGRESS_EXPOSE_ENCRYPTION_KEY_FOR_TEST" == "True" ]; then
        # Datasource service starts later than api service, so wait until datasource service fully started.
        if ! timeout $SERVICE_TIMEOUT sh -c "while [ ! -f /etc/congress/keys/aes_key ]; do sleep 1; done"; then
            die $LINENO "Unexpected error in key file creation"
        fi
        chmod a+rx /etc/congress/keys
        chmod a+r /etc/congress/keys/aes_key
    fi
}


# stop_congress() - Stop running processes (non-screen)
function stop_congress {
    :
}

# cleanup_congress() - Remove residual data files, anything left over from previous
# runs that would need to clean up.
function cleanup_congress {
        sudo rm -rf $CONGRESS_AUTH_CACHE_DIR $CONGRESS_CONF_DIR
}


# Configures keystone integration for congress service
function _congress_setup_keystone {
    local conf_file=$1
    local section=$2
    local use_auth_url=$3

    if [[ -z $skip_auth_cache ]]; then
        iniset $conf_file $section signing_dir $CONGRESS_AUTH_CACHE_DIR
        # Create cache dir
        create_congress_cache_dir
    fi

    configure_auth_token_middleware $conf_file $CONGRESS_ADMIN_USERNAME  $CONGRESS_AUTH_CACHE_DIR $section
}

# Set up Horizon integration with Congress
function _congress_setup_horizon {
    # Dashboard panels
    ln -fs $CONGRESSDASHBOARD_DIR/congress_dashboard/enabled/_50_policy.py $HORIZON_DIR/openstack_dashboard/local/enabled/
    ln -fs $CONGRESSDASHBOARD_DIR/congress_dashboard/enabled/_60_policies.py $HORIZON_DIR/openstack_dashboard/local/enabled/
    ln -fs $CONGRESSDASHBOARD_DIR/congress_dashboard/enabled/_70_datasources.py $HORIZON_DIR/openstack_dashboard/local/enabled/
    ln -fs $CONGRESSDASHBOARD_DIR/congress_dashboard/enabled/_75_monitoring.py $HORIZON_DIR/openstack_dashboard/local/enabled/
    ln -fs $CONGRESSDASHBOARD_DIR/congress_dashboard/enabled/_80_library.py $HORIZON_DIR/openstack_dashboard/local/enabled/

    # Restart Horizon
    restart_apache_server
}

function start_cfg_validator_agent {
    echo "Launching congress config agent"
    run_process congress-agent "$CONGRESS_BIN_DIR/congress-cfg-validator-agt --config-file $CONGRESS_AGT_CONF"
}

function configure_cfg_validator_agent {
    if ! is_service_enabled congress; then
        setup_develop $CONGRESS_DIR
    fi
    if [[ ! -d $CONGRESS_CONF_DIR ]]; then
        sudo mkdir -p $CONGRESS_CONF_DIR
    fi

    sudo chown $STACK_USER $CONGRESS_CONF_DIR
    touch $CONGRESS_AGT_CONF
    sudo chown $STACK_USER $CONGRESS_AGT_CONF

    iniset_rpc_backend cfg-validator $CONGRESS_AGT_CONF
    iniset $CONGRESS_AGT_CONF DEFAULT debug $ENABLE_DEBUG_LOG_LEVEL

    iniset $CONGRESS_AGT_CONF agent host $(hostname)
    iniset $CONGRESS_AGT_CONF agent version pike

    if is_service_enabled nova; then
        VALIDATOR_SERVICES+="nova: { ${NOVA_CONF}:${NOVA_DIR}/etc/nova/nova-config-generator.conf },"
    fi

    if is_service_enabled neutron; then
        VALIDATOR_SERVICES+="neutron: { ${NEUTRON_CONF}:${NEUTRON_DIR}/etc/oslo-config-generator/neutron.conf },"
    fi

    if is_service_enabled congress; then
        VALIDATOR_SERVICES+="congress: { ${CONGRESS_CONF}:${CONGRESS_DIR}/etc/congress-config-generator.conf },"
    fi

    if [[ ! -z VALIDATOR_SERVICES ]]; then
        iniset $CONGRESS_AGT_CONF agent services "${VALIDATOR_SERVICES%?}"
    fi
}

# Main dispatcher
#----------------

if is_service_enabled congress || is_service_enabled congress-agent; then
    if [[ "$1" == "stack" ]]; then
        if [[ "$2" == "install" ]]; then
            echo_summary "Installing Congress"
            install_congress

        elif [[ "$2" == "post-config" ]]; then
            if is_service_enabled congress; then
                echo_summary "Configuring Congress"
                configure_congress

                if is_service_enabled key; then
                    create_congress_accounts
                fi
            fi

            if is_service_enabled congress-agent; then
                echo_summary "Configuring Validator agent"
                configure_cfg_validator_agent
            fi

        elif [[ "$2" == "extra" ]]; then
            if is_service_enabled congress; then
                # Initialize Congress
                init_congress

                 # Start the congress API and Congress taskmgr components
                echo_summary "Starting Congress"
                start_congress_service_and_check
                configure_congress_datasources
                create_predefined_policy
            fi

            if is_service_enabled congress-agent; then
                echo_summary "Starting Validator agent"
                start_cfg_validator_agent
            fi
        fi
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_congress
    fi

    if [[ "$1" == "clean" ]]; then
        cleanup_congress
    fi
fi

# Restore xtrace
$XTRACE
