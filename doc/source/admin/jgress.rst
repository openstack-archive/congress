===================================
JGress: policy over JSON data model
===================================


Introduction
============
JGress (JSON data model for Congress) is an experimental framework that allows
an operator to query, monitor, and automate clouds using JSON queries/views.
In short, Congress capabilities over a JSON data model.

JGress is designed to capture the state of a cloud from controllers (Nova,
Neutron, EC2, etc) and alarms (Monasca, Vitrage, Zabbix, etc.) in the form of
a JSON database. The framework enables an operator to perform policy-based
monitoring using queries and views. The framework also allows an operator to
define remedial actions and workflows (Mistral, Heat, etc.) in response to
declarative conditions.

JGress can be thought of as a kind of declarative "glue" layer that helps
different services work together while avoiding the N-squared problem with
1:1 integrations.

For documentation on writing policy in this model, refer to
:ref:`JGress policy<jgress_policy>`
in user documentation.


Data sources
============

One key advantage offered by JGress is the ability for an administrator or
deployer to integrate arbitrary JSON API as a data source, with nothing more
than a simple YAML config file. Many sample config files are provided here:

https://github.com/openstack/congress/tree/master/etc/sample_json_ingesters
