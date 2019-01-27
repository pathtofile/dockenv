🐳 🐍 DockEnv 🐍 🐳
====================


Virtual Environments for Python, using Docker
---------------------------------------------

DockEnv makes it easy to safely run untrusted python code and packages.

The nature of modern software development means even the simplest of projects can depend
on a complex web of package dependencies. The opacity of this web makes it hard to know what
code you should trust to run on your machine, and what you shouldn't. Outdated packages can create
security holes, and malicious users can inject their own code into the dependency chain.

But you might not have the time, or expertise, to fully audit a dependency chain, particularly if
just trying out new apps, or using a project to solve a one-time problem. This is where DockEnv
can help.

DockEnv uses Docker to create a virtual environment image that you can pre-load with one or mode
packages into. Then, you can execute scripts inside this environment, passing in and out only
text, whilst all code (including the package installation) is only executed inside the container.


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