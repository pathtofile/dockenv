.. _setup:

Installation
============

1. Install Python >= 3.6 and Docker
-----------------------------------

On Ubuntu/Debian/Kali Linux:

.. code-block:: bash

    apt-get install python3.6 docker


On Centos/Fedora/Redhat Linux:

.. code-block:: bash

    yum install python3.6 docker


On Windows, I recommend using the legacy docker-toolbox: https://docs.docker.com/toolbox/toolbox_install_windows/

Docker Toolbox works on all versions of Windows from Windows 7 to 10,
and won't cause conflicts if you also want to run VMs on VMWare or VirtualBox
without having to reboot.



2. Install DockEnv
------------------

From Pypi:

.. code-block:: bash

    pip install dockenv

Or, From source:

.. code-block:: bash

    git clone git@github.com:pathtofile/dockenv.git
    pip install ./dockenv
