# congress.sh - Devstack extras script to install Congress

# congress service
CONGRESS_REPO=${CONGRESS_REPO:-${GIT_BASE}/stackforge/congress.git}
CONGRESS_BRANCH=${CONGRESS_BRANCH:-master}

# congress client library test
CONGRESSCLIENT_REPO=${CONGRESSCLIENT_REPO:-${GIT_BASE}/stackforge/python-congressclient.git}
CONGRESSCLIENT_BRANCH=${CONGRESSCLIENT_BRANCH:-master}


if is_service_enabled congress; then
    if [[ "$1" == "source" ]]; then
        # Initial source
        source $TOP_DIR/lib/congress
    elif [[ "$1" == "stack" && "$2" == "install" ]]; then
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
fi
