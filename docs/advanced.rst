.. _advanced:

Advanced Guide
==============

Short param names
-----------------

Every param and flag has a short name. run :code:`dockenv -h` or  :code:`dockenv <command> -h`
to get the list.

Configuring pip install
-----------------------

When running :code:`dockenv new`, anything after the env name is passed into the
:code:`pip install` script. This can be used to point to alternate pypi repos, e.g:

.. code-block:: bash

    $> dockenv new my_env --package djrongo --index-url https://test.pypi.org/simple/


Interactive debug shell
-----------------------

You can enter an interactive bash shell inside the env using:

.. code-block:: bash

    $> dockenv shell my_env
    # You can also use '--mount' or '--expose-port', see 'dockenv run'

**NOTE**: Anything you do in this shell will be blown away once you quit.
For more information see :ref:`notes`. This can be useful for debugging.

Container security notes:
-------------------------

By default, DockEnv does the following to help prevent code from being able to escape the container:
 * A new env will always build off the latest python3 
 * All python code, including pip, runs as a container-specific low-privileged user.
 * After the pip install, code is unable to write to the filesystem, unless explicitly allowed
 * After the pip install, code is unable to connect to any network, unless explicitly allowed

