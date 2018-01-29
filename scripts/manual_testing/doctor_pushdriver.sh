#!/bin/bash -x

#############################################################################
### doctor push data driver manual testing script                         ###
#
#   Note:
#   The following OpenStack environment variables must set first:
#   OS_USERNAME, OS_PASSWORD, OS_PROJECT_NAME, OS_TENANT_NAME, OS_AUTH_URL
#   For example by running (under a devstack setup)
#     $ . devstack/openrc admin admin
#############################################################################

UUID=`openstack congress datasource create doctor doctor -f value | sed -n '5p'`

openstack congress datasource row update doctor events '[{"id": "0123-4567-89ab", "time": "2016-02-22T11:48:55Z", "type": "compute.host.down", "details": {"hostname": "compute1", "status": "down", "monitor": "zabbix1", "monitor_event_id": "111"}}]'

openstack congress datasource row list doctor events

openstack congress datasource row update $UUID events '[{"id": "1123-4567-89ab", "time": "2016-02-22T11:48:55Z", "type": "compute.host.down", "details": {"hostname": "compute2", "status": "down", "monitor": "zabbix2", "monitor_event_id": "222"}}]'

openstack congress datasource row list doctor events

openstack congress datasource delete doctor
