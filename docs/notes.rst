.. _notes:

Inportant Notes
===============

DockEnv is a tool for developers and hackers who want to either
try out untrusted code, or don't have the time or resources to
create a full environment.

But it is not a replacement for a proper production environment, and should not be treated as such.

Environments are ephemeral
--------------------------
Each time you run :code:`dockenv run` you are getting a brand new environment.
This means state does not carry over from one :code:`run` to the next.

If you wish to preserve state, either use :code:`--writable-mount --mount /a/folder` and write state to the folder, or create your own docker containers and go from there, as DockEnv is no longer for your use-case.

Malicious code can see what you pass into it
--------------------------------------------

If you install a malicious package, it will be able to see any files
you put into it using :code:`--mount`, or anything else you type or
pass into it.

However, the malicious code will not be able to see anything outside the environment, and it will only run for the lifetime of :code:`dockenv run`.


Containers aren't completely infallible
---------------------------------------
Unlike Virtual Machines, docker containers share parts of your host's operating system in order to do some low-level things. But there is a strong separation between the Container and the Host, that will prevent the majority of malicious code from being able to breach the gap and read or alter data on your host machine.

However, a particularly nasty and persistent actor could still
find a way to break out of the container.
Care has been taken to mitigate most factors that can lead to an escape,
but the possibility is still there.

