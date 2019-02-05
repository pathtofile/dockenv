# :whale: :snake: DockEnv :snake: :whale:

[![CircleCI](https://circleci.com/gh/pathtofile/dockenv/tree/feature%2Finit.svg?style=shield&circle-token=0fbcb1341ca010df70b9977b3ca6176fbf8e34b6)](https://circleci.com/gh/pathtofile/dockenv/tree/feature%2Finit)

------------------------------------------------------------------------

Run untrusted python in Docker, the easy way!

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
pip install dockenv
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

Create a clean virtual environment and install a number of packages into it:
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
dockenv run venv test.py
```


Run script `test.py` with arguments `--testargs foo` inside a virtual environment:
```
dockenv run venv test.py --testargs foo
```


Run the webserver script `test_server.py` inside a virtual environment, exposing port `80` so you can connect
to it from your local machine:
```
dockenv run --expose-port 80 venv test_server.py
## Script will print out the virtual environment's IP address so you can connect to it
```


Run the webserver script `my_script.py` inside a virtual environment, mounting the folder `config_dir` so the
script can read from the files inside it:
```
dockenv run --mount ./config_dir venv my_script.py
## Folder will be mounted in the same root directory as my_script.py
```
*NOTE* On Windows, by default the local folder must be somewhere in your users directory, otherwise
the folder will be empty inside the virtual environment



## Other Commands
List all virtual environments:
```
dockenv list
```


List all pip packages installed into a virtual environment named `venv`
```
dockenv freeze venv
```

Delete a virtual environment named `venv`
```
dockenv delete venv
```

# IMPORTANT NOTES
Dockenv is a tool for developers and hackers who want to either try out untrusted code,
or don't have the resources to create a full environment. But it is not a replacement
for a proper production environment, and should not be treated as such.



## Environments are ephemeral
Each time you run `dockenv run` you are getting a brand new envionment. This means state does
not carry over from one `run` to the next.

If you wish to preserve state, create your own docker containers and go from there, as dockenv is
no longer for your use-case.




## Malicious code can see what you pass into it
If you install a malicious package, it will be able to see any files you put into it using `--mount`, or
anything else you type or pass into it. However, the malicious code will not be able to see anything outside the
environment, and it will only run for the lifetime of `dockenv run`.




## Containers aren't compleltly infaliable
Unlike Virtual Machines, docker containers share parts of your host's operating system in order to do some low-level things. But there is a strong sepearation between the Container and the Host, that will prevent the majority of malicious code from being able to breach the gap and read or alter data on your host machine.

However, a particularly nasty and persistant actor could still find a way to break out of the container, so be warned if you feel you may be targeted by such theats.
