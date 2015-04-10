#!/bin/bash
set -xe

env

DEVSTACKDIR=${DEVSTACKDIR:-"devstack"}


if [ ! -d $DEVSTACKDIR ]; then
    echo "Cannot find devstack directory: $DEVSTACKDIR"
    exit 1
fi

wget -O - http://git.openstack.org/cgit/stackforge/congress/plain/contrib/devstack/lib/congress > $DEVSTACKDIR/lib/congress
wget -O - http://git.openstack.org/cgit/stackforge/congress/plain/contrib/devstack/extras.d/70-congress.sh > $DEVSTACKDIR/extras.d/70-congress.sh

if [ -e $DEVSTACKDIR/local.conf ]; then
    echo "enable_service congress" >> $DEVSTACKDIR/local.conf
else
    echo "Cannot find a local.conf. Using localrc instead"
    cat - <<-EOF >> $DEVSTACKDIR/localrc
	enable_service congress
	EOF
fi

set +o xtrace

echo ""
echo "Devstack has been successfully configured with congress."
echo "Run: cd $DEVSTACKDIR; ./stack.sh to setup devstack."
