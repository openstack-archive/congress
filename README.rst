========================
Team and repository tags
========================

.. image:: https://governance.openstack.org/badges/congress.svg
    :target: https://governance.openstack.org/reference/tags/index.html

.. Change things from this point on

.. include:: aliases.rst

.. _readme:

======================================
Congress Introduction and Installation
======================================

1. What is Congress
===================

Congress is an open policy framework for the cloud.  With Congress, a
cloud operator can declare, monitor, enforce, and audit "policy" in a
heterogeneous cloud environment.  Congress gets inputs from a cloud's
various cloud services; for example in OpenStack, Congress fetches
information about VMs from Nova, and network state from Neutron, etc.
Congress then feeds input data from those services into its policy engine
where Congress verifies that the cloud's actual state abides by the cloud
operator's policies.  Congress is designed to work with **any policy** and
**any cloud service**.

2. Why is Policy Important
==========================

The cloud is a collection of autonomous
services that constantly change the state of the cloud, and it can be
challenging for the cloud operator to know whether the cloud is even
configured correctly.  For example,

* The services are often independent from each other and do not
  support transactional consistency across services, so a cloud
  management system can change one service (create a VM) without also
  making a necessary change to another service (attach the VM to a
  network).  This can lead to incorrect behavior.

* Other times, we have seen a cloud operator allocate cloud resources
  and then forget to clean them up when the resources are no longer in
  use, effectively leaving garbage around the system and wasting
  resources.

* The desired cloud state can also change over time.  For example, if
  a security vulnerability is discovered in Linux version X, then all
  machines with version X that were ok in the past are now in an
  undesirable state.  A version number policy would detect all the
  machines in that undesirable state.  This is a trivial example, but
  the more complex the policy, the more helpful a policy system
  becomes.

Congress's job is to help people manage that plethora of state across
all cloud services with a succinct policy language.

3. Using Congress
=================

Setting up Congress involves writing policies and configuring Congress
to fetch input data from the cloud services.  The cloud operator
writes policy in the Congress policy language, which receives input
from the cloud services in the form of tables.  The language itself
resembles datalog.  For more detail about the policy language and data
format see :ref:`Policy <policy>`.

To add a service as an input data source, the cloud operator configures a Congress
"driver," and the driver queries the service.  Congress already
has drivers for several types of service, but if a cloud operator
needs to use an unsupported service, she can write a new driver
without much effort and probably contribute the driver to the
Congress project so that no one else needs to write the same driver.

Finally, when using Congress, the cloud operator must choose what
Congress should do with the policy it has been given:

* **monitoring**: detect violations of policy and provide a list of those violations
* **proactive enforcement**: prevent violations before they happen (functionality that requires
  other services to consult with Congress before making changes)
* **reactive enforcement**: correct violations after they happen (a manual process that
  Congress tries to simplify)

In the future, Congress
will also help the cloud operator audit policy (analyze the history
of policy and policy violations).

Congress is free software and is licensed with Apache.

* Free software: Apache license

4. Installing Congress
======================

There are 2 ways to install Congress.

* As part of DevStack.  Get Congress running alongside other OpenStack services like Nova
  and Neutron, all on a single machine.  This is a great way to try out Congress for the
  first time.

* Separate install.  Get Congress running alongside an existing OpenStack
  deployment

4.1 Devstack-install
--------------------
For integrating Congress with DevStack:

1. Download DevStack

.. code-block:: console

    $ git clone https://git.openstack.org/openstack-dev/devstack.git
    $ cd devstack

2. Configure DevStack to use Congress and any other service you want.  To do that, modify
   the ``local.conf`` file (inside the DevStack directory).  Here is what
   our file looks like:

.. code-block:: console

    [[local|localrc]]

    enable_plugin congress https://git.openstack.org/openstack/congress
    enable_plugin heat https://git.openstack.org/openstack/heat
    enable_plugin aodh https://git.openstack.org/openstack/aodh
    enable_plugin ceilometer https://git.openstack.org/openstack/ceilometer
    enable_service s-proxy s-object s-container s-account

3. Run ``stack.sh``.  The default configuration expects the passwords to be 'password'
   without the quotes

.. code-block:: console

    $ ./stack.sh


4.2 Separate install
--------------------
Install the following software, if you haven't already.

* python 2.7: https://www.python.org/download/releases/2.7/

* pip: https://pip.pypa.io/en/latest/installing.html

* java: https://java.com  (any reasonably current version should work)
  On Ubuntu:   console apt-get install default-jre
  On Federa:   console yum install jre

* Additionally

.. code-block:: console

  $ sudo apt-get install git gcc python-dev python-antlr3 libxml2 libxslt1-dev libzip-dev build-essential libssl-dev libffi-dev
  $ sudo apt install python-setuptools
  $ sudo pip install --upgrade pip virtualenv pbr tox

Clone Congress

.. code-block:: console

  $ git clone https://github.com/openstack/congress.git
  $ cd congress

Install requirements

.. code-block:: console

 $ sudo pip install .

Install Source code

.. code-block:: console

  $ sudo python setup.py install

Configure Congress  (Assume you put config files in /etc/congress)

.. code-block:: console

  $ sudo mkdir -p /etc/congress
  $ sudo mkdir -p /etc/congress/snapshot
  $ sudo cp etc/api-paste.ini /etc/congress
  $ sudo cp etc/policy.json /etc/congress

Set-up Policy Library [optional]
  This step copies the bundled collection Congress policies into the Congress
  policy library for easy activation by an administrator. The policies in the
  library do not become active until explicitly activated by an administrator.
  The step may be skipped if you do not want to load the bundled policies into
  the policy library.

.. code-block:: console

  $ sudo cp -r library /etc/congress/.

Generate a configuration file as outlined in the Configuration Options section
of the :ref:`Deployment <deployment>` document. Note: you may have to run the command with sudo.

There are several sections in the congress/etc/congress.conf.sample file you may want to change:

* [DEFAULT] Section
    - drivers
    - auth_strategy
* "From oslo.log" Section
    - log_file
    - log_dir (remember to create the directory)
* [database] Section
    - connection

Add drivers:

.. code-block:: text

  drivers = congress.datasources.neutronv2_driver.NeutronV2Driver,congress.datasources.glancev2_driver.GlanceV2Driver,congress.datasources.nova_driver.NovaDriver,congress.datasources.keystone_driver.KeystoneDriver,congress.datasources.ceilometer_driver.CeilometerDriver,congress.datasources.cinder_driver.CinderDriver,congress.datasources.swift_driver.SwiftDriver,congress.datasources.plexxi_driver.PlexxiDriver,congress.datasources.vCenter_driver.VCenterDriver,congress.datasources.murano_driver.MuranoDriver,congress.datasources.ironic_driver.IronicDriver


The default auth_strategy is keystone. To set Congress to use no authorization strategy:

.. code-block:: text

    auth_strategy = noauth

If you use noauth, you might want to delete or comment out the [keystone_authtoken] section.

Set the database connection string in the [database] section (adapt MySQL root password):

.. code-block:: text

    connection = mysql+pymysql://root:password@127.0.0.1/congress?charset=utf8

To use RabbitMQ with Congress, set the transport_url in the "From oslo.messaging" section according to your setup:

.. code-block:: text

    transport_url = rabbit://$RABBIT_USERID:$RABBIT_PASSWORD@$RABBIT_HOST:5672

A bare-bones congress.conf is as follows:

.. code-block:: text

  [DEFAULT]
  auth_strategy = noauth
  drivers = congress.datasources.neutronv2_driver.NeutronV2Driver,congress.datasources.glancev2_driver.GlanceV2Driver,congress.datasources.nova_driver.NovaDriver,congress.datasources.keystone_driver.KeystoneDriver,congress.datasources.ceilometer_driver.CeilometerDriver,congress.datasources.cinder_driver.CinderDriver,congress.datasources.swift_driver.SwiftDriver,congress.datasources.plexxi_driver.PlexxiDriver,congress.datasources.vCenter_driver.VCenterDriver,congress.datasources.murano_driver.MuranoDriver,congress.datasources.ironic_driver.IronicDriver
  log_file=congress.log
  log_dir=/var/log/congress
  [database]
  connection = mysql+pymysql://root:password@127.0.0.1/congress?charset=utf8


When you are finished editing congress.conf.sample, copy it to the /etc/congress directory.

.. code-block:: console

    sudo cp etc/congress.conf.sample /etc/congress/congress.conf


Create database

.. code-block:: console

  $ mysql -u root -p
  $ mysql> CREATE DATABASE congress;
  $ mysql> GRANT ALL PRIVILEGES ON congress.* TO 'congress'@'localhost' IDENTIFIED BY 'CONGRESS_DBPASS';
  $ mysql> GRANT ALL PRIVILEGES ON congress.* TO 'congress'@'%' IDENTIFIED BY 'CONGRESS_DBPASS';


Push down schema

.. code-block:: console

  $ sudo congress-db-manage --config-file /etc/congress/congress.conf upgrade head


Set up Congress accounts
  Use your OpenStack RC file to set and export required environment variables:
  OS_USERNAME, OS_PASSWORD, OS_PROJECT_NAME, OS_TENANT_NAME, OS_AUTH_URL.

  (Adapt parameters according to your environment)


.. code-block:: console

  $ ADMIN_ROLE=$(openstack role list | awk "/ admin / { print \$2 }")
  $ SERVICE_TENANT=$(openstack project list | awk "/ service / { print \$2 }")
  $ CONGRESS_USER=$(openstack user create --password password --project service --email "congress@example.com" congress | awk "/ id / {print \$4 }")
  $ openstack role add $ADMIN_ROLE --user $CONGRESS_USER --project  $SERVICE_TENANT
  $ CONGRESS_SERVICE=$(openstack service create policy --name congress --description "Congress Service" | awk "/ id / { print \$4 }")


Create the Congress Service Endpoint
  Endpoint creation differs based upon the Identity version. Please see the `endpoint <https://docs.openstack.org/developer/python-openstackclient/command-objects/endpoint.html>`_ documentation for details.


.. code-block:: console

  Identity v2:
  $ openstack endpoint create $CONGRESS_SERVICE --region RegionOne --publicurl https://127.0.0.1:1789/  --adminurl https://127.0.0.1:1789/ --internalurl https://127.0.0.1:1789/


.. code-block:: console

  Identity v3:
  $ openstack endpoint create --region $OS_REGION_NAME  $CONGRESS_SERVICE public https://$SERVICE_HOST:1789
  $ openstack endpoint create --region $OS_REGION_NAME  $CONGRESS_SERVICE admin https://$SERVICE_HOST:1789
  $ openstack endpoint create --region $OS_REGION_NAME  $CONGRESS_SERVICE internal https://$SERVICE_HOST:1789



Start Congress
  The default behavior is to start the Congress API, Policy Engine, and
  Datasource in a single node. For HAHT deployment options, please see the
  :ref:`HA Overview <ha_overview>` document.

.. code-block:: console

  $ sudo /usr/local/bin/congress-server --debug


Install the Congress Client
  The command line interface (CLI) for Congress resides in a project called python-congressclient.
  Follow the installation instructions on the `GitHub page <https://github.com/openstack/python-congressclient>`_.


Configure datasource drivers
  For this you must have the Congress CLI installed. Run this command for every
  service that Congress will poll for  data.
  Please note that the service name $SERVICE should match the ID of the
  datasource driver, e.g. "neutronv2" for Neutron and "glancev2" for Glance;
  $OS_USERNAME, $OS_TENANT_NAME, $OS_PASSWORD and $SERVICE_HOST are used to
  configure the related datasource driver so that congress knows how to
  talk with the service.

.. code-block:: console

  $ openstack congress datasource create $SERVICE $"SERVICE" \
    --config username=$OS_USERNAME \
    --config tenant_name=$OS_TENANT_NAME
    --config password=$OS_PASSWORD
    --config auth_url=https://$SERVICE_HOST:5000/v2.0


Install the Congress Dashboard in Horizon
  Clone congress-dashboard repo, located here https://github.com/openstack/congress-dashboard
  Follow the instructions in the README file located in https://github.com/openstack/congress-dashboard/blob/master/README.rst
  for further installation.

  Note: After you install the Congress Dashboard and restart apache, the OpenStack Dashboard may throw
  a "You have offline compression enabled..." error, follow the instructions in the error message.
  You may have to:

.. code-block:: console

  $ cd /opt/stack/horizon
  $ python manage.py compress
  $ sudo service apache2 restart


Read the HTML documentation
  Install python-sphinx and the oslosphinx extension if missing and build the docs.
  After building, open congress/doc/html/index.html in a browser.

.. code-block:: console

  $ sudo pip install sphinx
  $ sudo pip install oslosphinx
  $ make docs


Test Using the Congress CLI
  If you are not familiar with using the OpenStack command-line clients, please read the `OpenStack documentation <https://docs.openstack.org/user-guide/cli.html>`_ before proceeding.

  Once you have set up or obtained credentials to use the OpenStack command-line clients, you may begin testing Congress. During installation a number of policies are created.

  To view policies: $ openstack congress policy list

  To view installed datasources: $ openstack congress datasource list

  To list available commands: $ openstack congress --help

4.3 Unit Tests
------------------------

Run unit tests in the Congress directory

.. code-block:: console

  $ tox -epy27

In order to break into the debugger from a unit test we need to insert
a break point to the code:

.. code-block:: python

  import pdb; pdb.set_trace()

Then run ``tox`` with the debug environment as one of the following::

  tox -e debug
  tox -e debug test_file_name.TestClass.test_name

For more information see the `oslotest documentation
<https://docs.openstack.org/developer/oslotest/features.html#debugging-with-oslo-debug-helper>`_.

4.4 Upgrade
-----------

Here are the instructions for upgrading to a new release of the
Congress server.

1. Stop the Congress server.

2. Update the Congress git repo

.. code-block:: console

  $ cd /path/to/congress
  $ git fetch origin

3. Checkout the release you are interested in, say Mitaka.  Note that this
step will not succeed if you have any uncommitted changes in the repo.

.. code-block:: console

  $ git checkout origin/stable/mitaka


If you have changes committed locally that are not merged into the public
repository, you now need to cherry-pick those changes onto the new
branch.

4. Install dependencies

.. code-block:: console

 $ sudo pip install

5. Install source code

.. code-block:: console

  $ sudo python setup.py install

6. Migrate the database schema

.. code-block:: console

  $ sudo congress-db-manage --config-file /etc/congress/congress.conf upgrade head

7. (optional) Check if the configuration options you are currently using are
   still supported and whether there are any new configuration options you
   would like to use.  To see the current list of configuration options,
   use the following command, which will create a sample configuration file
   in ``etc/congress.conf.sample`` for you to examine.

.. code-block:: console

   $ tox -egenconfig

8. Restart Congress, e.g.

.. code-block:: console

  $ sudo /usr/local/bin/congress-server --debug
