"""
Dockenv - Run untrusted python in Docker
"""
import argparse
import os
import sys
import shutil
import tempfile
import subprocess
import logging
import traceback
import shlex
import docker

ROOT_FOLDER = os.path.abspath(os.path.dirname(__file__))
CLIENT = docker.from_env()

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
LOGGER.addHandler(logging.StreamHandler())


def get_posix_path(path):
    """
    If on Windows, convert a windows path to POSIX
    """
    if os.name != "nt":
        return path
    split = os.path.splitdrive(path)
    drive = split[0].replace(":", "").lower()
    posix_path = "/" + drive + split[1].replace("\\", "/")
    return posix_path


def get_venv_name(dockenv_name):
    """
    Helper function to split the user-defined virtual env name
    out of the full name that includes the dockenv tag

    :param dockenv_name: The full name to pull the virtual env name
                         out of
    """
    # Format of tage name if dockenv-**NAME**:latest
    venv_start = len("dockenv-")
    if dockenv_name.endswith(":latest"):
        venv_end = len(":latest") * -1
        return dockenv_name[venv_start:venv_end]
    return dockenv_name[venv_start:]


def local_image_exists(image_name, tagname="latest"):
    """
    Check if we already have an image stored locally.

    :param tagname: The particular tag of the image to get. defaults to 'latest'
    :returns: The Docker container object that matches the name if it
              exists locally, otherwise None.
    """
    for image in CLIENT.images.list():
        for tag in image.tags:
            if tag == f"{image_name}:{tagname}":
                return True
    return False


def get_local_container(venv_name, tagname="latest"):
    """
    Get a Docker container object, but only if we have it locally.
    The Docker API will attempt to call out to the remote registry if we
    do not have the container localy.

    However as Dockenv only operates on the local
    level, calling out to a remote site is reduntant at best, and a potential security
    risk at worst, as the name may contain sensitive information, and would open
    the user to an attack where a malicious user uploads their own container matching
    the name to the registry.

    :param venv_name: The name of the container to attempt to get.
    :param tagname: The particular tag of the image to get. defaults to 'latest'
    :returns: The Docker container object that matches the name if it
              exists locally, otherwise None.
    """
    if local_image_exists(venv_name, tagname=tagname):
        return CLIENT.containers.get(venv_name)
    return None


# pylint: disable=too-many-arguments, too-many-locals
# pylint: disable=too-many-branches, too-many-statements
def run_script(dockenv_name,
               script,
               as_module=False,
               expose_port=None,
               mount=None,
               write_filesystem=False,
               write_mount=False,
               script_args=None):
    """
    Run a script inside a virtual env. This will build the new image that includes
    the the script file. It will then run the script passing in the args

    :param dockenv_name: The full name of the image to create
    :param script_path: The path to the script file to run
    :param as_module: If True, script is not a file on disk, but a python module
                      to run with 'python -m'
    :param expose_port: A port to expose on the docker container, so the host can
                        connect to it
    :param mount: A folder to mount inside the container. This can be used to pass
                  in config files or other data to the script to read
    :param write_filesystem: If True, allow script to write to conainer's filesystem
    :param write_mount: If True, allow script to write to the mounted folder
    :param script_args: If not None, an array of arguments to pass into the script
    """
    # Check venv exists:
    if not local_image_exists(dockenv_name):
        venv_name = get_venv_name(dockenv_name)
        LOGGER.error(f"ERROR: {venv_name!r} doesn't exist")
        return

    if as_module:
        cmd = ["-m", f"{script}"]
    else:
        cmd = [f"./{os.path.split(script)[-1]}"]

    if script_args:
        cmd += script_args
    cmd_quoted = " ".join(shlex.quote(x) for x in cmd)

    expose_script = ""
    if expose_port:
        expose_script = f"echo [***] Exposed port: $(hostname -i):{expose_port} [***]"

    runner_script = f"""
    {expose_script}
    cd ./runner
    python {cmd_quoted}
    """

    with tempfile.TemporaryDirectory() as runner_dir:
        if not as_module:
            shutil.copy(script, runner_dir)
        with open(
                os.path.join(runner_dir, "run.sh"), "w",
                newline="\n") as frunner:
            frunner.write(runner_script)

        # Create new container to run, mounting our temp dir into it
        try:
            args = ["docker", "run", "-ti", "--rm"]
            # mount temp dir into container
            vol_cmd = f"{get_posix_path(runner_dir)}:/usr/src/app/runner"
            if write_filesystem:
                args += ["-v", vol_cmd]
            else:
                args += ["-v", f"{vol_cmd}:ro"]
                args += ["--read-only"]

            if expose_port:
                args += ["--expose", expose_port]

            if mount:
                src_abs = os.path.abspath(mount)
                dest_folder = os.path.split(src_abs)[-1]
                args += ["-v"]
                mount_cmd = f"{get_posix_path(src_abs)}:/usr/src/app/{dest_folder}"
                if write_mount:
                    args += [mount_cmd]
                else:
                    args += [f"{mount_cmd}:ro"]
            args += [dockenv_name]
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            # As long as docker is installed, this is just the same
            # amout of information that is printed out by the running container
            LOGGER.debug(traceback.format_exc())
            LOGGER.error("\nERROR: Script completed with error! "
                         "Use 'dockenv --verbose run' to get more info")


def build_venv(args, upgrade=False):
    """
    Create a new virtual env or upgrade an existing one.
    If new, this will build a Docker image based on the "Python:3" image,
    and our Image will be named named "dockenv-<envname>".
    If upgrading, we will build from a base image of the same name

    :param args: cli args
    :param upgrade: If True, base image will be the same dockenv image.
                    If False, base image will be "python:3"
    """
    dockenv_name = f"dockenv-{args.envname}"

    image_exists = local_image_exists(dockenv_name)
    # Check if either upgrading and image is missing,
    # or if creating new and image already exists
    if (not upgrade) and image_exists:
        LOGGER.error(f"ERROR: Virtual Env {args.envname!r} already exists! "
                     "Use 'dockenv delete' or 'dockenv run'")
        return
    if upgrade and (not image_exists):
        LOGGER.error(f"ERROR: Virtual Env {args.envname!r} doesn't exist! ")
        return

    if args.package and args.requirements:
        LOGGER.error(f"ERROR: Use only one of '--package' or '--requirements'")
        return

    # If a new env, we need to setup the user permissions
    if upgrade:
        base_script = f"""
        FROM {dockenv_name}
        USER root
        RUN python -m pip install --upgrade pip
        """
    else:
        base_script = """
        FROM python:3
        RUN python -m pip install --upgrade pip
        RUN groupadd -r dockenv && useradd -m -r -g dockenv dockenv
        """

    pip_script = ""
    if args.requirements or args.package:
        pip_script = "RUN pip install --no-cache-dir --user -r requirements.txt"
        if not args.allow_nonbinary:
            pip_script += " --only-binary=:all:"

    if args.extra_pip_arguments:
        pip_script += " " + " ".join(args.extra_pip_arguments)

    dockerfile = f"""
    {base_script}
    USER dockenv
    WORKDIR /usr/src/app
    COPY . .
    {pip_script}
    CMD [ "sh", "./runner/run.sh" ]
    """

    # Put everything inside a temp directory
    with tempfile.TemporaryDirectory() as build_dir:
        # copy required files
        with open(os.path.join(build_dir, "Dockerfile"), "w") as fdockerfile:
            fdockerfile.write(dockerfile)

        # Copy any optional files
        if args.requirements is not None:
            shutil.copy(args.requirements,
                        os.path.join(build_dir, "requirements.txt"))

        if args.package is not None:
            with open(os.path.join(build_dir, "requirements.txt"),
                      "w") as fpackage:
                fpackage.write(args.package)

        # It takes a while to build the base Python3 image if we haven't already
        if not local_image_exists("python", tagname="3"):
            LOGGER.info(
                f"[*] First time using dockenv, may take some extra time")

        # Build the container
        LOGGER.info(f"[*] building virtual env {dockenv_name!r}...")
        # NOTE: I didn't see how to get 'CLIENT.images.build'
        # to actually print what it is doing, leading this to "hang" with no output
        # Switched to calling subprocess so user gets feedback on whats going on
        if args.verbose:
            subprocess.check_call(
                ["docker", "build", "-t", dockenv_name, build_dir])
        else:
            CLIENT.images.build(tag=dockenv_name, path=build_dir)
        LOGGER.info(f"[*] built virtual env {dockenv_name!r}")


def func_new_venv(args):
    """
    Create a new virtual env. This will build a Docker image based on the
    "Python:3" image. Our Image will be named named "dockenv-<envname>"

    :param args: cli arguments
    """
    build_venv(args, upgrade=False)


def func_upgrade_venv(args):
    """
    Upgrade a virtual env, installing new packages and creating
    a new version of the virtualenv image

    :param args: cli arguments
    """
    build_venv(args, upgrade=True)


def func_run_script(args):
    """
    Run a script inside a virtual env. This will build and create a container
    based on an image named "dockenv-<envname>"

    :param args: cli arguments
    """
    # Create a new container on top of the virtual env image
    dockenv_name = f"dockenv-{args.envname}"
    run_script(
        dockenv_name,
        args.script,
        as_module=args.as_module,
        expose_port=args.port,
        mount=args.mount,
        write_mount=args.write_mount,
        write_filesystem=args.write_filesystem,
        script_args=args.arguments)


def func_run_shell(args):
    """
    Launch a shell inside a virtual env. This will build and create a container
    based on an image named "dockenv-<envname>"

    :param args: cli arguments
    """
    dockenv_name = f"dockenv-{args.envname}"
    with tempfile.TemporaryDirectory() as runner_dir:
        shell_fname = os.path.join(runner_dir, "shell.py")
        with open(shell_fname, "w", newline="\n") as fshell:
            fshell.write("import pty; pty.spawn('/bin/bash')")
        LOGGER.info(f"[*] Starting shell in {dockenv_name!r}")
        LOGGER.info(
            f"[*] NOTE: ANYTHING you do inside the container will be blown")
        LOGGER.info(f"[*] away once you quit. This is only for debugging!")
        # As this is for debugging, we'll always run with a writable filesystem
        run_script(
            dockenv_name,
            shell_fname,
            expose_port=args.port,
            mount=args.mount,
            write_mount=True,
            write_filesystem=True)


# pylint: disable=W0613
def func_list_venv(args):
    """
    List all virtual envs. This will list all images that
    match the name "dockenv-<envname>"

    :param args: cli arguments, ignored.
    """
    LOGGER.info("Dockenv virtual envs:")
    for image in CLIENT.images.list():
        for tag in image.tags:
            if tag.startswith("dockenv"):
                venv_name = get_venv_name(tag)
                LOGGER.info(f"  {venv_name}")


def func_run_freeze(args):
    """
    This will call "dockenv run" calling a special script that
    will run "pip freeze" inside the container.
    Like "dockenv run" this will create a container based on an
    image named "dockenv-<envname>"

    :param args: cli arguments
    """
    dockenv_name = f"dockenv-{args.envname}"
    with tempfile.TemporaryDirectory() as runner_dir:
        freeze_fname = os.path.join(runner_dir, "freeze.py")
        with open(freeze_fname, "w", newline="\n") as ffreeze:
            ffreeze.write(
                "import subprocess; subprocess.run('pip freeze', shell=True)")
        # Pip freeze needs write access to the container's /tmp for some reason...
        run_script(dockenv_name, freeze_fname, write_filesystem=True)


def func_delete_venv(args):
    """
    Delete a virtual environment.
    This will remove both containers and images that match the
    name "dockenv-<envname>"

    :param args: cli arguments
    """
    dockenv_name = f"dockenv-{args.envname}"

    # Check env exists:
    if not local_image_exists(dockenv_name):
        LOGGER.error(f"ERROR: Virtual Env {args.envname!r} doesn't exist")
        return

    # First force-stop any running containers that start with venv_name
    for container in CLIENT.containers.list():
        for tag in container.image.tags:
            if tag.startswith(dockenv_name):
                LOGGER.info(f"[*] deleting container {dockenv_name!r}")
                container.remove(force=True)

    # Then delete the image
    LOGGER.info(f"[*] deleting image {dockenv_name!r}")
    CLIENT.images.remove(dockenv_name, force=True)


def func_export_venv(args):
    """
    Exports a virtual environment to a .tar file

    :param args: cli arguments
    """
    dockenv_name = f"dockenv-{args.envname}"

    # Check env exists:
    if not local_image_exists(dockenv_name):
        LOGGER.error(f"ERROR: Virtual Env {args.envname!r} doesn't exist")
        return

    image = CLIENT.images.get(dockenv_name)
    LOGGER.info(f"Exporting env {args.envname!r}, this can take 5-10 minutes")
    with open(args.filename, "wb") as fimage:
        for chunk in image.save(chunk_size=209715, named=True):
            fimage.write(chunk)
    LOGGER.info(f"Exported env {args.envname!r} to {args.filename!r}")


def func_import_venv(args):
    """
    Imports a virtual environment from a saved a .tar file

    :param args: cli arguments
    """
    LOGGER.info(
        f"Attempting to import from {args.filename!r}, this can take 5 minutes"
    )
    with open(args.filename, "rb") as fimage:
        image = CLIENT.images.load(fimage.read())[0]
    # Get the new env name
    for tag in image.tags:
        if tag.startswith("dockenv"):
            LOGGER.info(f"Imported env {get_venv_name(tag)!r}")
            break
    else:
        # Wasn't a dockenv image, remove it an error out
        CLIENT.images.remove(image.id)
        LOGGER.error(
            "Imported Docker image from {args.filename!r} wasn'y a dockenv env"
        )


def main():
    """
    Main entry function
    """
    parser = argparse.ArgumentParser(description="Run python inside docker")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="print verbose output")
    subparsers = parser.add_subparsers(help="options")

    # --- New virtual Env ---
    new_parser = subparsers.add_parser(
        "new", help="create a new virtual environment")
    new_parser.add_argument("envname", help="name of the virtualenv to create")
    new_parser.add_argument(
        "--requirements", "-r", help="requirements.txt file to install first")
    new_parser.add_argument(
        "--package", "-p", help="name of a packge to install from pip first")
    new_parser.add_argument(
        "-anb",
        "--allow-nonbinary",
        action="store_true",
        dest="allow_nonbinary",
        help="If not set, pip will be run with '--only-binary=:all:'")
    new_parser.add_argument(
        "extra_pip_arguments",
        nargs=argparse.REMAINDER,
        help="after envname, any extra arguments to pass to pip")
    new_parser.set_defaults(func=func_new_venv)

    # --- Upgrade virtual Env ---
    upgrade_parser = subparsers.add_parser(
        "upgrade", help="upgrade an existing virtual environment")
    upgrade_parser.add_argument(
        "envname", help="name of the virtualenv to upgrade")
    upgrade_parser.add_argument(
        "--requirements",
        "-r",
        help="requirements.txt file to install into virtualenv")
    upgrade_parser.add_argument(
        "--package", "-p", help="name of a packge to install into virtualenv")
    upgrade_parser.add_argument(
        "-anb",
        "--allow-nonbinary",
        action="store_true",
        dest="allow_nonbinary",
        help="If not set, pip will be run with '--only-binary=:all:'")
    upgrade_parser.add_argument(
        "extra_pip_arguments",
        nargs=argparse.REMAINDER,
        help="after envname, any extra arguments to pass to pip")
    upgrade_parser.set_defaults(func=func_upgrade_venv)

    # --- Run Script ---
    run_parser = subparsers.add_parser(
        "run", help="run script inside an existing virtual env")
    run_parser.add_argument(
        "envname", help="name of the virtualenv to run script in")
    run_parser.add_argument("script", help="path to script to run")
    run_parser.add_argument(
        "-am",
        "--as-module",
        action="store_true",
        dest="as_module",
        help=("If set, script is not a file on disk, "
              "but a name of a python module"))
    run_parser.add_argument(
        "-e",
        "--expose-port",
        type=int,
        dest="port",
        help="Expose a network port on the container")
    run_parser.add_argument(
        "-m",
        "--mount",
        help=("Mount a folder inside the container "
              "to '/usr/src/app/<folder_name>'"))
    run_parser.add_argument(
        "-wm",
        "--writeable-mount",
        action="store_true",
        dest="write_mount",
        help="Allow script to write data into the mount")
    run_parser.add_argument(
        "-wf",
        "--writeable-fs",
        action="store_true",
        dest="write_filesystem",
        help="Allow script to write data anywhere in the env's own filesystem")
    run_parser.add_argument(
        "arguments",
        nargs=argparse.REMAINDER,
        help="arguments to pass into script")
    run_parser.set_defaults(func=func_run_script)

    # --- List Virtual Envs ---
    list_parser = subparsers.add_parser(
        "list", help="list all virtual environments")
    list_parser.set_defaults(func=func_list_venv)

    # --- List packages inside a Virtual Env ---
    freeze_parser = subparsers.add_parser(
        "freeze", help="list packages inside an environment")
    freeze_parser.add_argument(
        "envname", help="name of the virtualenv to list packges in")
    freeze_parser.set_defaults(func=func_run_freeze)

    # --- Delete Virtual Env ---
    del_parser = subparsers.add_parser(
        "delete", aliases=['del'], help="delete a virtual environment")
    del_parser.add_argument("envname", help="name of the virtualenv to enter")
    del_parser.set_defaults(func=func_delete_venv)

    # --- Export Virtual Env ---
    export_parser = subparsers.add_parser(
        "export", help="Exports a virtual environment into a .tar file")
    export_parser.add_argument(
        "envname", help="name of the virtualenv to export")
    export_parser.add_argument(
        "filename", help="file to save the virtualenv to")
    export_parser.set_defaults(func=func_export_venv)

    # --- Import Virtual Env ---
    import_parser = subparsers.add_parser(
        "import", help="imports a virtual environment from a .tar file")
    import_parser.add_argument(
        "filename", help="file to save the virtualenv to")
    import_parser.set_defaults(func=func_import_venv)

    # --- Debug Shell Script ---
    shell_parser = subparsers.add_parser(
        "shell",
        help="FOR ADVANCED USERS ONLY! Start a debug shell inside the env. "
        "Anything you do in this shell will be blown away once you quit")
    shell_parser.add_argument(
        "envname", help="name of the virtualenv to start the shell in")
    shell_parser.add_argument(
        "-e",
        "--expose-port",
        type=int,
        dest="port",
        help="Expose a network port on the container")
    shell_parser.add_argument(
        "-m",
        "--mount",
        help="Mount a folder into the working directory of the container")
    shell_parser.set_defaults(func=func_run_shell)

    if len(sys.argv) == 1:
        parser.print_help()
    else:
        args = parser.parse_args()
        if args.verbose:
            LOGGER.setLevel(logging.DEBUG)
        args.func(args)


if __name__ == "__main__":
    main()
