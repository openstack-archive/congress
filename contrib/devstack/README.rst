The contrib/devstack/ directory contains the files necessary to integrate Congress with devstack.

To install::

    $ git clone https://git.openstack.org/stackforge/congress /opt/stack/congress
    $ git clone https://git.openstack.org/openstack-dev/devstack /opt/stack/devstack

    $ cd /opt/stack/congress
    $ ./contrib/devstack/prepare_devstack.sh

Run devstack as normal::

    $ ./stack.sh

Note: If the miminum localrc file required to run congress with keystone requires:
ENABLED_SERVICES=congress,key,mysql
