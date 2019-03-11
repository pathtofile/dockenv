🐳 🐍 DockEnv 🐍 🐳
====================


Virtual Environments for Python, using Docker
---------------------------------------------

DockEnv makes it easy to safely run untrusted python code and packages.

The nature of modern software development means even the simplest of projects can depend
on a complex web of package dependencies. This web can be abused to execute malicious code,
particularly at install time.


Example Usage:
--------------

.. code-block:: bash

    # Step 1: Create a new virtual enviroment
    $> dockenv new my_env --package djrongo==0.0.1
    # Step 2: Run the script
    $> dockenv run my_env djrongo_example.py --run-demo
        this is output from djrongo_example.py



Table of Contents
-----------------
.. toctree::
   :maxdepth: 2

   setup
   create
   run
   manage
   advanced
   notes