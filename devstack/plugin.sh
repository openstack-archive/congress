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
set -o xtrace


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
    iniset $CONGRESS_CONF DEFAULT transport_url rabbit://$RABBIT_USERID:$RABBIT_PASSWORD@$RABBIT_HOST:5672/
    iniset $CONGRESS_CONF database connection `database_connection_url $CONGRESS_DB_NAME`
    if [ "$ENABLE_CONGRESS_JSON" == "True" ]; then
        iniset $CONGRESS_CONF json_ingester enable "True"
        # when the main db is not postgres, the devstack function
        # database_connection_url_postgresql returns URL with wrong prefix,
        # so we do a substitution here
        local db_connection_mysql=`database_connection_url_postgresql $CONGRESS_JSON_DB_NAME`
        CONGRESS_JSON_DB_CONNECTION_URL=${db_connection_mysql/?*:\/\//postgresql:\/\/}
        iniset $CONGRESS_CONF json_ingester db_connection $CONGRESS_JSON_DB_CONNECTION_URL
        iniset $CONGRESS_CONF json_ingester config_path "$CONGRESS_JSON_CONF_DIR"
        iniset $CONGRESS_CONF json_ingester config_reusables_path "$CONGRESS_JSON_CONF_REUSABLES_PATH"

        # setup json ingester config files
        if [[ ! -d $CONGRESS_JSON_CONF_DIR ]]; then
            mkdir $CONGRESS_JSON_CONF_DIR
        fi
        echo "keystone_admin_auth_config:" > "$CONGRESS_JSON_CONF_REUSABLES_PATH"
        echo "  type: keystone" >> "$CONGRESS_JSON_CONF_REUSABLES_PATH"
        echo "  config:" >> "$CONGRESS_JSON_CONF_REUSABLES_PATH"
        echo "    project_name: $OS_PROJECT_NAME" >> "$CONGRESS_JSON_CONF_REUSABLES_PATH"
        echo "    username: $OS_USERNAME" >> "$CONGRESS_JSON_CONF_REUSABLES_PATH"
        echo "    password: $OS_PASSWORD" >> "$CONGRESS_JSON_CONF_REUSABLES_PATH"
        echo "    auth_url: `openstack catalog show keystone -f value -c endpoints | sed -n 's/^\s*public: //p' | sed -n '1p'`" >> "$CONGRESS_JSON_CONF_REUSABLES_PATH"
    fi

    _congress_setup_keystone $CONGRESS_CONF keystone_authtoken
}

function _configure_congress_json_ingester {
    local endpoint=`openstack catalog show $1 -f value -c endpoints | sed -n 's/^\s*public:\s*//p' | sed -n '1p'`
    if [[ ! -z $endpoint ]]; then
        echo "$1_api_endpoint: $endpoint" >> "$CONGRESS_JSON_CONF_REUSABLES_PATH"
        _copy_congress_json_ingester_config $1
    fi
}

function _copy_congress_json_ingester_config {
    cp $CONGRESS_DIR/etc/sample_json_ingesters/$1.yaml $CONGRESS_JSON_CONF_DIR/
}

function configure_congress_datasources {
    if [ "$ENABLE_CONGRESS_JSON" == "True" ]; then
        _configure_congress_json_ingester cinderv3
        _configure_congress_json_ingester glance
        _configure_congress_json_ingester heat
        _configure_congress_json_ingester keystone
        _configure_congress_json_ingester magnum
        _configure_congress_json_ingester masakari
        _configure_congress_json_ingester mistral
        _configure_congress_json_ingester neutron
        _configure_congress_json_ingester nova
        _configure_congress_json_ingester tacker
        _configure_congress_json_ingester zun
        _copy_congress_json_ingester_config monasca
        _copy_congress_json_ingester_config cve
        if [ "$CONGRESS_MULTIPROCESS_DEPLOYMENT" == "False" ]; then
            restart_service devstack@congress.service
            echo "Waiting for Congress to restart..."
            if ! timeout $SERVICE_TIMEOUT sh -c "while ! wget --no-proxy -q -O- http://$CONGRESS_HOST:$CONGRESS_PORT; do sleep 1; done"; then
                die $LINENO "Congress did not restart"
            fi
        else
            restart_service devstack@congress-datasources.service
        fi
    fi
    _configure_service neutron neutronv2
    _configure_service neutron-qos neutronv2_qos
    _configure_service nova nova
    _configure_service key keystonev3
    _configure_service cinder cinder
    _configure_service swift swift
    _configure_service glance glancev2
    _configure_service monasca monasca
    _configure_service murano murano
    _configure_service ironic ironic
    _configure_service heat heat
    _configure_service aodh aodh
    _configure_service mistral mistral
    _configure_service tacker tacker
    if [[ $ENABLE_CONGRESS_AGENT == "True" ]] ; then
        _configure_service congress-agent config
    fi
}

function _configure_tempest {
    # NOTE(gmann): Every service which are required by congress
    # CI/CD has to be explicitly set here on Tempest. Devstack
    # only set the Tempest in-tree configured service only which
    # are - [nova, keystone, cinder, glance, swift, glance, neutron].
    # service_available from Tempest plugin is not guaranteed to be
    # set correctly due to different env setup scenario, so it is
    # better to set it explicitly here.
    local service
    local required_services="heat,ironic,aodh,murano,mistral,monasca,neutron-qos,tacker"
    for service in ${required_services//,/ }; do
        if is_service_enabled $service ; then
            iniset $TEMPEST_CONFIG service_available $service "True"
        else
            iniset $TEMPEST_CONFIG service_available $service "False"
        fi
    done
    iniset $TEMPEST_CONFIG service_available congress "True"
    # Notify tempest if z3 is enabled.
    if [[ $ENABLE_CONGRESS_Z3 == "True" ]] ; then
        iniset $TEMPEST_CONFIG congressz3 enabled "True"
    fi

    # Set feature flags
    # (remove when Queens no longer supported)
    iniset $TEMPEST_CONFIG congress-feature-enabled monasca_webhook "True"
    iniset $TEMPEST_CONFIG congress-feature-enabled vitrage_webhook "True"
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

function _install_z3 {
    if [[ $USE_Z3_RELEASE != None ]]; then
        mkdir -p $CONGRESS_Z3_DIR
        pushd $CONGRESS_Z3_DIR
        z3rel="z3-${USE_Z3_RELEASE}"
        z3file="${z3rel}-x64-${os_VENDOR,,}-${os_RELEASE}"
        # binary not available for ubuntu-18, so use ubuntu-16 binary instead
        if [ ${os_VENDOR,,} == "ubuntu" ] && [ ${os_RELEASE} == "18.04" ]; then
            z3file="${z3rel}-x64-ubuntu-16.04"
            echo "WARNING: Using ${z3file} binary on ${os_VENDOR,,}-${os_RELEASE} because ${z3rel}-x64-${os_VENDOR,,}-${os_RELEASE} is not available."
        fi
        url="https://github.com/Z3Prover/z3/releases/download/${z3rel}/${z3file}.zip"
        if [ ! -f "${z3file}.zip" ]; then
            wget "${url}" || true
        fi
        if [ ! -f "${z3file}.zip" ]; then
            echo "Failed to download z3 release ${USE_Z3_RELEASE} for ${os_VENDOR}-${os_RELEASE}"
            exit 1
        fi
        unzip -o "${z3file}.zip" "${z3file}/bin/python/z3/*" "${z3file}/bin/libz3.so"
        dist_dir=$($PYTHON -c "import site; print(site.getsitepackages()[0])")
        sudo cp -r "${z3file}/bin/python/z3" "${dist_dir}"
        sudo mkdir -p "${dist_dir}/z3/lib"
        sudo cp "${z3file}/bin/libz3.so" /usr/lib
        sudo ln -s /usr/lib/libz3.so "${dist_dir}/z3/lib/libz3.so"
        popd
    else
        git_clone $CONGRESS_Z3_REPO $CONGRESS_Z3_DIR $CONGRESS_Z3_BRANCH
        pushd $CONGRESS_Z3_DIR
        ${PYTHON} scripts/mk_make.py --python
        cd build
        make
        sudo make install
        popd
    fi
}

function _uninstall_z3 {
    if [[ $USE_Z3_RELEASE != None ]]; then
        sudo rm /usr/lib/libz3.so
        dist_dir=$($PYTHON -c "import site; print(site.getsitepackages()[0])")
        # Double check we are removing what we must remove.
        if [ -f "${dist_dir}/z3/z3core.py" ]; then
            sudo rm -rf "${dist_dir}/z3"
        fi
    else
        pushd $CONGRESS_Z3_DIR
        cd build
        sudo make uninstall
        popd
    fi
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
    if [ "$ENABLE_CONGRESS_JSON" == "True" ]; then
        if [ ${DATABASE_TYPE,,} != "postgresql" ]; then
            # setup separate postgres db if main is not already postgres
            install_database_postgresql
            install_database_python_postgresql
            configure_database_postgresql
        fi
        recreate_database_postgresql $CONGRESS_JSON_DB_NAME utf8
        psql --set=ingester_role="$CONGRESS_JSON_INGESTER_ROLE" \
             --set=user_role="$CONGRESS_JSON_USER_ROLE" \
             --set=db_name="$CONGRESS_JSON_DB_NAME" \
             $CONGRESS_JSON_DB_CONNECTION_URL \
             -f $CONGRESS_DIR/scripts/jgress/setup_permissions.sql
    fi
    # Run Congress db migrations
    congress-db-manage --config-file $CONGRESS_CONF upgrade head
}

function install_congress_pythonclient() {
# For using non-released client from git branch, need to add
# LIBS_FROM_GIT=python-congressclient parameter to localrc.
# Otherwise, congress will install python-congressclient from requirements.
    if use_library_from_git "python-congressclient"; then
        git_clone_by_name "python-congressclient"
        setup_dev_lib "python-congressclient"
    fi
}

# install_congress() - install dependency, collect client source and prepare
function install_congress {
    install_congress_pythonclient

    if is_service_enabled horizon; then
        _install_congress_dashboard
    fi

    if [[ $ENABLE_CONGRESS_Z3 == "True" ]] ; then
        _install_z3
    fi
}

# Start running processes, including screen
function start_congress_service_and_check {
    # build config-file options
    local cfg_file
    local CFG_FILE_OPTIONS="--config-file $CONGRESS_CONF"

    # Start the congress services in separate processes
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

function _wait_for_congress {
    echo "Waiting for Congress to start..."
    if ! timeout $SERVICE_TIMEOUT sh -c "while ! wget --no-proxy -q -O- http://$CONGRESS_HOST:$CONGRESS_PORT; do sleep 1; done"; then
        die $LINENO "Congress did not start"
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
        if [[ $ENABLE_CONGRESS_Z3 == "True" ]] ; then
            _uninstall_z3
        fi
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
        elif [[ "$2" == "test-config" ]]; then
            if is_service_enabled tempest; then
                # Configure Tempest for Congress
                _configure_tempest
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
