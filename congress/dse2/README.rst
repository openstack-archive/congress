
.. _dse2:

==========================================
Data Services Engine v2 (DSE2) Development
==========================================

1. DSE2 Design Overview
=======================

The work in this folder supports the dist-cross-process-dse blueprint.
In brief, the goal of this work is support Congress components running
across multiple process.  A new DSE framework is being created to
leverage oslo.messaging for component communication.

The distribution work is being done in parallel to the existing DSE.
We aim to create an optional startup flag to select the new framework,
such that existing functionality is preserved during development. When
the new framework is deemed ready, a small commit will change the
default runtime to the new framework, and deprecate the old DSE.


2. Current Development Status
=============================

Since the DSE provides the conduit for Congress component communication,
it is critical that it is robust and well tested.  The core testing
should be focused on the DSE component only, and should not require external
configuration or dependencies.

All DSE2 work is currently being done in a standalone dse2 folder.

* data_service.py:
  * Status:
    * DataServiceInfo created
    * DataService skeleton created
  * Next Steps:
    * Expose DataService RPC endpoints to DataServiceInfo
    * Add table pub/sub to DataService
    * Add policy management methods to DataService
* dse_node.py:
  * Status:
    * DseNode created; supports node and service RPC
  * Next Steps:
    * Integrate control bus and validate peer discovery
* control_bus.py:
  * Status:
    * DseNodeControlBus basic discovery of peers
  * Next Steps:
    * Robustness


3. Running the tests
====================

The current code snapshot is intentionally decoupled from the project
testing framework.  To run, developers can set up a virtual environment
that contains the project dependencies:

Configure Rabbit for testing
----------------------------

* Install rabbitmq (e.g. apt-get install rabbitmq-server)
* Add testing user:
  # rabbitmqctl add_user testing test
  # rabbitmqctl set_permissions -p / testing '.*' '.*' '.*'

Setting up a testing virtual environment
----------------------------------------

 $ virtualenv dsetest
 $ echo <path_to_congress_root> > \
   dsetest/lib/python2.7/site-packages/congress.pth  # Add congress PYTHONPATH
 $ . dsetest/bin/activate
 $ pip install --upgrade pip
 $ pip install -r <path_to_congress_root>/requirements.txt
 $ pip install -r <path_to_congress_root>/test-requirements.txt
 $ pip install oslo.messaging

Running the DSE2 tests
----------------------

* Ensure you are in the virtual env configured above
 $ . dsetest/bin/activate  # Run to join the virtualenv if not already

* Change to the dse2 directory
 $ cd congress/dse2

* Run the data_service tests:
 $ python test_data_service.py

* Run the dse_node test using the 'fake' oslo.messaging driver
 $ python test_dse_node.py --fake

* Run the dse_node test using the 'rabbit' oslo.messaging driver
 $ python test_dse_node.py --rabbit
