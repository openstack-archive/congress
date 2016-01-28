Congress Dashboard
------------------

Congress Dashboard is an extension for OpenStack Dashboard that provides a UI
for Congress. With congress-dashboard, a user is able to easily write the
policies and rules for governance of cloud.

Setup Instructions
------------------

This instruction assumes that Horizon is already installed and its
installation folder is <horizon>. Detailed information on how to install
Horizon can be found at
http://docs.openstack.org/developer/horizon/quickstart.html#setup.

To integrate congress with horizon, copy the files in
<congress_dashboard>/enabled to <horizon>/openstack_dashboard/local/enabled/

$ cp -b <congress_dashboard>/enabled/_50_policy.py <horizon>/openstack_dashboard/local/enabled/
$ cp -b <congress_dashboard>/enabled/_60_policies.py <horizon>/openstack_dashboard/local/enabled/
$ cp -b <congress_dashboard>/enabled/_70_datasources.py <horizon>/openstack_dashboard/local/enabled/

Restart Apache server
sudo service apache2 restart

