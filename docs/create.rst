.. _create:

Creating Environments
=====================

To create a virtual environment, simply call: :code:`dockenv new <name_of_env>`,
where :code:`<name_of_env>` is a unique name for the environment. e.g:

.. code-block:: bash

    $> dockenv new my_env

Creating with packages
----------------------
The power of DockEnv is the ability to create a new environment with
packages pre-installed into it.

This will run all install scripts inside the container, preventing any malicious :code:`setup.py`
from being able to see or alter you local machine. e.g.:

.. code-block:: bash

    $> dockenv new my_env --package djrongo

Then, every time you run :code:`dockenv run my_env`, the script will be able to use the djrongo
package, while preventing both the script and djrongo from being able to reach your local machine.

If you have multiple packages you want to install, create a :code:`requirements.txt`, similarly
to what you would do with pip:

.. code-block:: bash

    # $> cat requirements.txt
    #    djrongo==0.0.1
    #    requests
    #    lxml
    $> dockenv new my_env -r requirements.txt


