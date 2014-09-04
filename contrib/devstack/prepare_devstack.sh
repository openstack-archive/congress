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
cat - <<-EOF >> $DEVSTACKDIR/localrc
enable_service congress
EOF

set +o xtrace

echo ""
echo "Devstack has been successfully configured with congress."
echo "Run: cd $DEVSTACKDIR; ./stack.sh to setup devstack."
