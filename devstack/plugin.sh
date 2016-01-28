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
    [[ ,${ENABLED_SERVICES} =~ ,"congress" ]] && return 0
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
    CONGRESS_POLICY_FILE=$CONGRESS_CONF_DIR/policy.json

    cp $CONGRESS_DIR/etc/api-paste.ini $CONGRESS_API_PASTE_FILE
    cp $CONGRESS_DIR/etc/policy.json $CONGRESS_POLICY_FILE

    # Update either configuration file
    iniset $CONGRESS_CONF DEFAULT verbose True
    iniset $CONGRESS_CONF DEFAULT debug $ENABLE_DEBUG_LOG_LEVEL
    iniset $CONGRESS_CONF oslo_policy policy_file $CONGRESS_POLICY_FILE
    iniset $CONGRESS_CONF DEFAULT auth_strategy $CONGRESS_AUTH_STRATEGY
    iniset $CONGRESS_CONF DEFAULT distributed_architecture $CONGRESS_DISTRIBUTED_ARCHITECTURE

    CONGRESS_DRIVERS="congress.datasources.neutronv2_driver.NeutronV2Driver,"
    CONGRESS_DRIVERS+="congress.datasources.glancev2_driver.GlanceV2Driver,"
    CONGRESS_DRIVERS+="congress.datasources.nova_driver.NovaDriver,"
    CONGRESS_DRIVERS+="congress.datasources.keystone_driver.KeystoneDriver,"
    CONGRESS_DRIVERS+="congress.datasources.ceilometer_driver.CeilometerDriver,"
    CONGRESS_DRIVERS+="congress.datasources.cinder_driver.CinderDriver,"
    CONGRESS_DRIVERS+="congress.datasources.swift_driver.SwiftDriver,"
    CONGRESS_DRIVERS+="congress.datasources.plexxi_driver.PlexxiDriver,"
    CONGRESS_DRIVERS+="congress.datasources.vCenter_driver.VCenterDriver,"
    CONGRESS_DRIVERS+="congress.datasources.cloudfoundryv2_driver.CloudFoundryV2Driver,"
    CONGRESS_DRIVERS+="congress.datasources.murano_driver.MuranoDriver,"
    CONGRESS_DRIVERS+="congress.datasources.ironic_driver.IronicDriver,"
    CONGRESS_DRIVERS+="congress.datasources.heatv1_driver.HeatV1Driver,"
    CONGRESS_DRIVERS+="congress.tests.fake_datasource.FakeDataSource"

    iniset $CONGRESS_CONF DEFAULT drivers $CONGRESS_DRIVERS

    iniset $CONGRESS_CONF database connection `database_connection_url $CONGRESS_DB_NAME`

    _congress_setup_keystone $CONGRESS_CONF keystone_authtoken

    if is_service_enabled horizon; then
        _congress_setup_horizon
    fi
    _congress_setup_third_party_requirements
}

function _congress_setup_third_party_requirements {
    pip_install -r $CONGRESS_DIR/thirdparty-requirements.txt
}

function configure_congress_datasources {
    _configure_service neutron neutronv2
    _configure_service nova nova
    _configure_service key keystone
    _configure_service ceilometer ceilometer
    _configure_service cinder cinder
    _configure_service swift swift
    _configure_service glance glancev2
    _configure_service murano murano
    _configure_service ironic ironic
    _configure_service heat heat


}

function _configure_service {
    if is_service_enabled $1; then
        openstack congress datasource create $2 "$2" \
            --config poll_time=10 \
            --config username=$OS_USERNAME \
            --config tenant_name=$OS_PROJECT_NAME \
            --config password=$OS_PASSWORD \
            --config auth_url=http://$SERVICE_HOST:5000/v2.0
    fi
}



function configure_congressclient {
    setup_develop $CONGRESSCLIENT_DIR
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

        if [[ "$KEYSTONE_CATALOG_BACKEND" = 'sql' ]]; then

            local congress_service=$(get_or_create_service "congress" \
                "policy" "Congress Service")
            get_or_create_endpoint $congress_service \
                "$REGION_NAME" \
                "http://$SERVICE_HOST:$CONGRESS_PORT/" \
                "http://$SERVICE_HOST:$CONGRESS_PORT/" \
                "http://$SERVICE_HOST:$CONGRESS_PORT/"
        fi
    fi
}

# init_congress() - Initialize databases, etc.
function init_congress {
    recreate_database $CONGRESS_DB_NAME utf8
    # Run Congress db migrations
    congress-db-manage --config-file $CONGRESS_CONF upgrade head
}

# install_congress() - Collect source and prepare
function install_congress {
    git_clone $CONGRESS_REPO $CONGRESS_DIR $CONGRESS_BRANCH
    # congress requires java so we install it here
    install_package default-jre
}

# install_congressclient() - Collect source and prepare
function install_congressclient {
    git_clone $CONGRESSCLIENT_REPO $CONGRESSCLIENT_DIR $CONGRESSCLIENT_BRANCH
    setup_develop $CONGRESSCLIENT_DIR
}

# Start running processes, including screen
function start_congress_service_and_check {
    # build config-file options
    local cfg_file
    local CFG_FILE_OPTIONS="--config-file $CONGRESS_CONF"

    # Start the Congrss service
    screen_it congress "cd $CONGRESS_DIR && python $CONGRESS_BIN_DIR/congress-server $CFG_FILE_OPTIONS"
    echo "Waiting for Congress to start..."
    # FIXME(arosen): using curl right now to check if congress is alive once we implement version use check below.
    if ! timeout $SERVICE_TIMEOUT sh -c "while ! curl --noproxy $CONGRESS_HOST http://$CONGRESS_HOST:$CONGRESS_PORT; do sleep 1; done"; then
        die $LINENO "Congress did not start"
    fi
#    if ! timeout $SERVICE_TIMEOUT sh -c "while ! wget --no-proxy -q -O- http://$CONGRESS_HOST:$CONGRESS_PORT; do sleep 1; done"; then
#        die $LINENO "Congress did not start"
#    fi
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
    cp -r $CONGRESS_HORIZON_DIR/datasources $HORIZON_DIR/openstack_dashboard/dashboards/admin/
    cp -r $CONGRESS_HORIZON_DIR/policies $HORIZON_DIR/openstack_dashboard/dashboards/admin/
    cp -r $CONGRESS_HORIZON_DIR/static $HORIZON_DIR/openstack_dashboard/dashboards/admin/
    cp -r $CONGRESS_HORIZON_DIR/templates $HORIZON_DIR/openstack_dashboard/dashboards/admin/
    cp $CONGRESS_HORIZON_DIR/congress.py $HORIZON_DIR/openstack_dashboard/api/
    cp $CONGRESS_HORIZON_DIR/_50_policy.py $HORIZON_DIR/openstack_dashboard/local/enabled/
    cp $CONGRESS_HORIZON_DIR/_60_policies.py $HORIZON_DIR/openstack_dashboard/local/enabled/
    cp $CONGRESS_HORIZON_DIR/_70_datasources.py $HORIZON_DIR/openstack_dashboard/local/enabled/

    # For unit tests
    echo "python-congressclient" >> $HORIZON_DIR/requirements.txt
    echo -e \
"\n# Load the pluggable dashboard settings"\
"\nimport openstack_dashboard.local.enabled"\
"\nfrom openstack_dashboard.utils import settings"\
"\n\nINSTALLED_APPS = list(INSTALLED_APPS)"\
"\nsettings.update_dashboards(["\
"\n    openstack_dashboard.local.enabled,"\
"\n], HORIZON_CONFIG, INSTALLED_APPS)" >> $HORIZON_DIR/openstack_dashboard/test/settings.py

    # Setup alias for django-admin which could be different depending on distro
    local django_admin
    if type -p django-admin > /dev/null; then
        django_admin=django-admin
    else
        django_admin=django-admin.py
    fi

    # Collect and compress static files (e.g., JavaScript, CSS)
    DJANGO_SETTINGS_MODULE=openstack_dashboard.settings $django_admin collectstatic --noinput
    DJANGO_SETTINGS_MODULE=openstack_dashboard.settings $django_admin compress --force

    # Restart Horizon
    restart_apache_server
}

# Main dispatcher
#----------------

if is_service_enabled congress; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing Congress"
        install_congress
        install_congressclient
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring Congress"
        configure_congressclient
        configure_congress

        if is_service_enabled key; then
            create_congress_accounts
        fi

    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        # Initialize Congress
        init_congress

        # Start the congress API and Congress taskmgr components
        echo_summary "Starting Congress"
        start_congress_service_and_check
        configure_congress_datasources
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
