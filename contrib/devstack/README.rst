The contrib/devstack/ directory contains the files necessary to integrate Congress with devstack.

To install::

    $ git clone https://git.openstack.org/openstack-dev/devstack
     (Or set env variable DEVSTACKDIR to the location to your devstack code)
    $ wget http://git.openstack.org/cgit/stackforge/congress/plain/contrib/devstack/prepare_devstack.sh
    $ ./prepare_devstack.sh

Run devstack as normal::

    $ ./stack.sh

Note: If the miminum localrc file required to run congress with keystone requires:
ENABLED_SERVICES=congress,key,mysql
