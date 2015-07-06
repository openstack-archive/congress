Data Services Engine
====================

The DSE is a lightweight variation of a Data Stream Management System.  The
purpose of the DSE is to retrieve, or receive, data from external sources, then
format and present the data on a message bus.

Overview
--------

The DSE consists of a Python "cage" (see d6cage.py) which contains one or more
module instances.  These are instances of an eventlet subclass called "deepsix"
(see deepsix.py).  Each eventlet has an "inbox" queue.  All eventlets share an
"outbox" queue called the "datapath".

A lightweight AMQP router in the cage (see amqprouter.py) routes messages from
the datapath to the appropriate eventlet inbox.  In this way, the deepsix
instances are able to communicate with each other.

A deepsix instance may listen to multiple AMQP addresses.  However, every
deepsix instance must have at least one unique non-wildcard AMQP address.
Subsequent addresses do not have to be unique.  AMQP wildcards are supported
for these additional addresses.

Deepsix
-------

Publisher
~~~~~~~~~

A publishing deepsix instance will either pull data from an external source, or
have data pushed to it.  The nature of how this is achieved is dependent on the
external data source and the libraries used to access it.  For example, a
deepsix module might use the pyVmomi to periodically poll a VMware vSphere
instance to retrieve meta-data for all VM instances on a particular host.

A developer using deepsix will write code to periodically poll vSphere, extract
the data from the pyVmomi response object, and format it into a JSON data
structure.  Next, the "self.publish" method provided by deepsix will be used to
publish the data on the DSE message bus.

Invoking "self.publish" results in calls to the "prepush_processor" and "push"
methods.  For example, if a list of VMs on a host is retrieved from a vSphere
instance, this list is formatted in JSON and the results stored locally in the
instance.  Before sending out any updates, the prepush_processor method is
called.  Here data is groomed before sending out.  Using the prepush_processor
method, a delta of the data can be sent out to known subscribers, instead of
all the data every time it is retrieved from vSphere.  Finally, the "push"
method is called, and a list of known subscribers is iterated over, sending the
update to each.

Incoming subscription requests are processed by the "self.insub" method within
deepsix.py.

Published data is stored in a dictionary called "pubData".

Subscriber
~~~~~~~~~~

A subscribing deepsix instance will use the "self.subscribe" method to announce
it's interest in data being published on the DSE bus.  This announcement is
transmitted periodically, at an interval specified by the developer.  When
"self.subscribe" is called, a callback is provided by the developer as an
argument.  When new data is received by the subscriber, the callback is invoked
with the published data message passed as an argument.

A subscriber may need data from multiple sources.  There are two ways this can
happen:  (1) Multiple invocations of "self.subscribe" to publishers of
different types of data, or (2) A single invocation of "self.subscribe" which
is received by multiple publishers listening to the same AMQP address.

In the former case a unique UUID, used as a subscription ID, is generated for
each call to "self.subscribe".  This UUID is used internally by deepsix to
differentiate between subscriptions.  A unique callback can be provided for
each subscription.

If a UUID is not provided, one is automatically generated.  This UUID is sent
to the publisher within the periodic "subscribe" message.  When the publisher
sends an update, the subscription UUID is included with the update.

Let's consider the case of multiple publishers listening to the same AMQP
address for subscriptions.  For example, you may have two vSphere deepsix
instances:  "vSphere.Boston" and "vSphere.Chicago".  Those are the unique names
for those instances, however, both of those instances may also be listening to
the address "vSphere.node.list".

A subscribing instance might send a subscription announcement to
"vSphere.node.list".  In this case, both "vSphere.Boston" and "vSphere.Chicago"
will receive this subscription request and start publishing data back to the
subscriber.  The subscriber maintains a nested dictionary "subData" which is a
dictionary, indexed by subscription ID.  Each subscription ID, in turn, is a
dictionary indexed by the unique AMQP addresses of the publishers providing
that data.

Incoming published data is processed by the "self.inpubrep" method within
deepsix.py.  It is from this method that the developer provided callback is
invoked.

Request/Reply
~~~~~~~~~~~~~

Another way to retrieve data is with "self.request". This is a one-off
asynchronous request for data.

d6cage
------

The d6cage is itself a deepsix instance.  It listens to the AMQP addresses
"local.d6cage" and "local.router".  When a deepsix instance within d6cage is
created, it registers it's AMQP addresses by invoking "self.subscribe" and
sending the subscription to "local.router".  The d6cage will then add the AMQP
address to it's AMQP route table with the instance inbox thread as a
destination.


Miscellaneous/TO-DO
-------------------

Need to modify d6cage.py/deepsix.py to support dynamic
loading/reloading/stopping of modules.

Need to write a module to proxy external mq bus.  For instance, there may be
multiple OpenStack instances.  If a developer wants to receive updates from
Nova on "compute.instance.update", then they will need to disambiguate between
instances of Nova.  A proxy module would be loaded for each OpenStack instance.
Subscriptions would be sent to "openstack1.compute.instance.update" and/or
"openstack2.compute.instance.update"

