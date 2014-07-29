#!/bin/bash
set -xe

env

CONGRESSDIR=$(realpath $(dirname $0)/../..)
INSTALLDIR=${INSTALLDIR:-/opt/stack}

cp $CONGRESSDIR/contrib/devstack/extras.d/70-congress.sh $INSTALLDIR/devstack/extras.d/
cp $CONGRESSDIR/contrib/devstack/lib/congress $INSTALLDIR/devstack/lib/

cat - <<-EOF >> $INSTALLDIR/devstack/localrc
ENABLED_SERVICES+=,congress
EOF
