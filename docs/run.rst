.. _run:

Running Scripts
===============

Run a python file
-----------------

Once you've created an environment, its simple to run a script inside the environment:

.. code-block:: bash

    $> dockenv run <env_name> <script.py>
    Output from <script.py>

You can also pass in arguments to the script:

.. code-block:: bash

    $> dockenv run <env_name> <script.py> --do-thing foo


Run a module
------------
If instead of running a script from a file, you wish to run
an installed python module, like you would with :code:`python -m`,
then simply use the :code:`--as-module` flag:

.. code-block:: bash

    $> dockenv run --as-module <env_name> pylint --version



Networking
----------
By default, the env has no networking ability, preventing code from reaching the internet.

However, there may be times you want to connect to the script, e.g.
if script is running a web server.
DockEnv enables you to expose a port on the env, allowing you to connect to it:

.. code-block:: bash

    $> dockenv run --expose-port 80 <env_name> <webserver_script.py>
    # Script will print out the virtual environment's IP address so you can connect to it


Sharing a folder
----------------
If you have files you wish to use with the script, you can mount a folder inside the env:

.. code-block:: bash

    $> dockenv run --mount /my/config/folder <env_name> <script.py>

This folder will be mounted in the same root folder as :code:`<script.py>`.

This folder will be read-only, however if you wish to enable the script to write data back into the folder use the flag :code:`--writeable-mount`:

.. code-block:: bash

    $> dockenv run --mount /my/config/folder --writeable-mount <env_name> <script.py>


**NOTE:** On Windows, by default the local folder must be somewhere in your :code:`users` directory, otherwise the folder will be empty inside the virtual environment


Writable filesystem
-------------------
By default scripts cannot write any file to disk. You can change this by using the flag :code:`--writeable-filesystem`:
    
.. code-block:: bash

    $> dockenv run --writeable-filesystem <env_name> <script.py>

