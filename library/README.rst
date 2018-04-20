==============
Policy Library
==============

Congress bundles a library of useful policies to help users get started.

For example, the ``library/volume_encryption/servers_unencrypted_volume.yaml``
identifies and warns on servers with unencrypted volumes attached.

.. literalinclude:: ../../../library/volume_encryption/servers_unencrypted_volume.yaml

The latest collection library policies can be found here:
https://github.com/openstack/congress/tree/master/library

To import a library policy YAML file into Congress, use the following CLI
command (python-congressclient version 1.8.0 or higher
https://pypi.org/project/python-congressclient/).

.. code-block:: console

  $ openstack congress policy create-from-file <path-to-policy-yaml>
