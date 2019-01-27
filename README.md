# :whale: :snake: DockEnv :snake: :whale:

[![CircleCI](https://circleci.com/gh/pathtofile/dockenv/tree/master.svg?style=shield&circle-token=0fbcb1341ca010df70b9977b3ca6176fbf8e34b6)](https://circleci.com/gh/pathtofile/dockenv/tree/master) [![Documentation Status](https://readthedocs.org/projects/dockenv/badge/?version=latest)](https://dockenv.readthedocs.io/en/latest/?badge=latest) [![Liscence](https://img.shields.io/github/license/pathtofile/dockenv.svg)]()

------------------------------------------------------------------------

Run untrusted python in Docker, the easy way!

Full Documentation: https://dockenv.readthedocs.io

# Overview
This project aims to make it easy to test and run untrusted python code safely.


# Installation
## 1. Install docker and Python >= 3.6
On Ubuntu/Debian:
```
apt-get install python3.6 docker
```

On Centos/Fedora/Redhat:
```
yum install python3.6 docker
```

On Windows, I reccomend using the legacy docker-toolbox: https://docs.docker.com/toolbox/toolbox_install_windows/
docker toolbox works on all versions of Windows from Windows 7, and won't cause problems if you
also want to run VMs on VMWare or VirtualBox without having to reboot.


## 2. Install dockenv
## From pypi:
```
pip install dockenv-cli
```

## From source
```
git clone git@github.com:pathtofile/dockenv.git
pip install ./dockenv
```

# How To use examples

## 1. Create a new virtual environment
Create a clean virtual environment named `venv`:
```
dockenv new venv
```


Create a clean virtual environment and install the `requests` pip package into it:
```
dockenv new venv -p requests
```

OR, create a clean virtual environment and install a number of packages into it:
```
# > cat requirements.txt
#     dodgy-package
#     urllib3==1.24.1
#     wrapt==1.11.1
dockenv new venv -r requirements.txt
```


## 2. Run a script inside the virtual environment
Run script `test.py` inside a created virtual environment named `venv`:
```
dockenv run venv test.py --testargs foo
```



Full Documentation: https://dockenv.readthedocs.io