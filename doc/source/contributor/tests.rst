Unit Tests
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
<https://docs.openstack.org/oslotest/latest/user/features.html#debugging-with-oslo-debug-helper>`_.
