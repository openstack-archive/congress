#!/bin/sh

target=$1

if [ -e '.testr.conf' ] ; then
    rm .testr.conf
fi
ln -s $target .testr.conf