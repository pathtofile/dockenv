.. _manage:

Managing Environments
=====================

List existing envs
--------------------------

To list all existing environments:

.. code-block:: bash

    $> dockenv list

List packages inside an env
---------------------------------------

To do run :code:`pip freeze` inside an environment:

.. code-block:: bash

    $> dockenv freeze <env_name>

This will list all the packages installed


Delete env
---------------------

To delete an existing environment:

.. code-block:: bash

    $> dockenv delete <env_name>

Upgrade env
----------------------

To upgrade an environment to add new packages to it:

.. code-block:: bash

    $> dockenv upgrade <env_name> --package new-package
    # Or use a requirements.txt for multiple packages
    $> dockenv upgrade <env_name> -r requirements.txt


Export env
------------------

To export an existing environment into a :code:`.tar.gz`:

.. code-block:: bash

    $> dockenv export <env_name> <output_filename.tar.gz>

Use this to share an environment with others, or move to a different machine


Import env
------------------

To import an existing environment from an exported .tar.gz:

.. code-block:: bash

    $> dockenv import <env_name>  <input_filename.tar.gz>
