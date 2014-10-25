The contrib/devstack/ directory contains the files necessary to integrate Congress with devstack.

To install, make sure you have *git* installed.  Then::

    $ git clone https://git.openstack.org/openstack-dev/devstack
     (Or set env variable DEVSTACKDIR to the location to your devstack code)

    $ wget http://git.openstack.org/cgit/stackforge/congress/plain/contrib/devstack/prepare_devstack.sh

    $ chmod u+x prepare_devstack.sh

    $ ./prepare_devstack.sh

Run devstack as normal::

    $ ./stack.sh

Note: The recommended ENABLED_SERVICES one should use contains the following options
so that congress can interface with nova, neutron, and ceilometer:
ENABLED_SERVICES=g-api,g-reg,key,n-api,n-crt,n-obj,n-cpu,n-sch,n-cauth,horizon,mysql,rabbit,sysstat,cinder,c-api,c-vol,c-sch,n-cond,quantum,q-svc,q-agt,q-dhcp,q-l3,q-meta,q-lbaas,n-novnc,n-xvnc,q-lbaas,ceilometer-acompute,ceilometer-acentral,ceilometer-anotification,ceilometer-collector,ceilometer-alarm-evaluator,ceilometer-alarm-notifier,ceilometer-api
