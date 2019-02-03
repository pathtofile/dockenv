"""
Dockeenv - Run untrusted python in Docker
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
CONTAINER_ROOT = os.path.join(ROOT_FOLDER, "scripts")
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


def run_script(dockenv_name,
               script_path,
               expose_port=None,
               mount=None,
               script_args=None):
    """
    Run a script inside a virtual env. This will build the new image that includes
    the the script file. It will then run the script passing in the args

    :param dockenv_name: The full name of the image to create
    :param script_path: The path to the script file to run
    :param expose_port: A port to expose on the docker container, so the host can
                        connect to it
    :param mount: A folder to mount inside the container, so
    :param script_args: If not None, an array of arguments to pass into the script
    """
    # Check venv exists:
    if not local_image_exists(dockenv_name):
        venv_name = get_venv_name(dockenv_name)
        LOGGER.error(f"ERROR: {venv_name} doesn't exist")
        return

    cmd = [f"./{os.path.split(script_path)[-1]}"]

    if script_args:
        cmd += script_args
    expose_script = ""
    if expose_port:
        expose_script = f"echo [***] Exposed port: $(hostname -i):{expose_port} [***]"

    cmd_quoted = " ".join(shlex.quote(x) for x in cmd)
    runner_script = f"""
    {expose_script}
    cd ./runner
    python {cmd_quoted}
    """
    print(runner_script)

    with tempfile.TemporaryDirectory() as runner_dir:
        shutil.copy(script_path, runner_dir)
        # Write as bytes so we can force unix endings
        with open(
                os.path.join(runner_dir, "run.sh"), "w",
                newline="\n") as frunner:
            frunner.write(runner_script)

        # Create new container to run, mounting our temp dir into it
        try:
            args = ["docker", "run", "-ti", "--rm"]
            # mount temp dir into container
            args += ["-v", f"{get_posix_path(runner_dir)}:/usr/src/app/runner"]
            if expose_port:
                args += ["--expose", expose_port]

            if mount:
                src_abs = os.path.abspath(mount)
                dest_folder = os.path.split(src_abs)[-1]
                args += [
                    "-v",
                    f"{get_posix_path(src_abs)}:/usr/src/app/runner/{dest_folder}"
                ]
            args += [dockenv_name]
            subprocess.check_call(args)
        except subprocess.CalledProcessError:
            # As long as docker is installed, this is just the same
            # amout of information that is printed out by the running container
            LOGGER.debug(traceback.format_exc())
            LOGGER.error("\nERROR: Script completed with error! "
                         "Use `dockenv run --verbose` to get more info")


def func_new_venv(args):
    """
    Create a new virtual env. This will build a Docker image based on the
    "Python:3" image. Our Image will be named named "dockenv-<envname>"

    :param args: cli arguments
    """
    dockenv_name = f"dockenv-{args.envname}"
    # Check env doesn't already exist:
    if local_image_exists(dockenv_name):
        LOGGER.error(f"ERROR: Virtual Env `{args.envname}` already exists! "
                     "Use `dockenv delete` or `dockenv run`")
        return

    # Put everything inside a temp directory
    with tempfile.TemporaryDirectory() as build_dir:
        # copy required files
        shutil.copy(os.path.join(CONTAINER_ROOT, "Dockerfile"), build_dir)
        shutil.copy(os.path.join(CONTAINER_ROOT, "build.py"), build_dir)

        # Copy any optional files
        if args.requirements is not None:
            shutil.copy(args.requirements,
                        os.path.join(build_dir, "requirements.txt"))

        if args.package is not None:
            with open(os.path.join(build_dir, "package.txt"), "w") as fpackage:
                fpackage.write(args.package)

        # It takes a while to build the base Python3 image if we haven't already
        if not local_image_exists("python", tagname="3"):
            LOGGER.info(
                f"[*] First time using dockenv, may take some extra time")

        # Build the container
        LOGGER.info(f"[*] building virtual env {dockenv_name}...")
        CLIENT.images.build(tag=dockenv_name, path=build_dir)
        LOGGER.info(f"[*] built virtual env {dockenv_name}")


def func_run_script(args):
    """
    Run a script inside a virtual env. This will build and create a container
    based on an image named "dockenv-<envname>"

    :param args: cli arguments
    """
    # Create a new container on top of the virtual env one
    dockenv_name = f"dockenv-{args.envname}"
    run_script(
        dockenv_name,
        args.script,
        expose_port=args.port,
        mount=args.mount,
        script_args=args.arguments)


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


def func_freeze_venv(args):
    """
    This will call "dockenv run" calling a special script that
    will run "pip freeze" inside the container.
    Like "dockenv run" this will create a container based on an
    image named "dockenv-<envname>"

    :param args: cli arguments
    """
    # Create a new container on top of the virtual env one
    dockenv_name = f"dockenv-{args.envname}"
    freeze_script = os.path.join(ROOT_FOLDER, "pip_freeze.py")
    run_script(dockenv_name, freeze_script)


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
        LOGGER.error(f"ERROR: Virtual Env `{args.envname}` doesn't exist")
        return

    # First force-stop any running containers that start with venv_name
    for container in CLIENT.containers.list():
        for tag in container.image.tags:
            if tag.startswith(dockenv_name):
                LOGGER.info(f"[*] deleting container {dockenv_name}")
                container.remove(force=True)

    # Then delete the image
    LOGGER.info(f"[*] deleting image {dockenv_name}")
    CLIENT.images.remove(dockenv_name)


def main():
    """
    Main entry function
    """
    parser = argparse.ArgumentParser(description="Run python inside docker")
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
        "-v", "--verbose", action="store_true", help="print verbose output")
    new_parser.set_defaults(func=func_new_venv)

    # --- Run Script ---
    run_parser = subparsers.add_parser(
        "run", help="run script inside an existing virtual env")
    run_parser.add_argument(
        "envname", help="name of the virtualenv to run script in")
    run_parser.add_argument("script", help="script to run")
    run_parser.add_argument(
        "-v", "--verbose", action="store_true", help="print verbose output")
    run_parser.add_argument(
        "-e",
        "--expose-port",
        type=int,
        dest="port",
        help="Expose a network port on the container")
    run_parser.add_argument(
        "-m",
        "--mount",
        help="Mount a folder into the working directory of the container")
    run_parser.add_argument(
        "arguments",
        nargs=argparse.REMAINDER,
        help="arguments to pass into script")
    run_parser.set_defaults(func=func_run_script)

    # --- List Virtual Envs ---
    list_parser = subparsers.add_parser(
        "list", help="list all virtual environments")
    list_parser.add_argument(
        "-v", "--verbose", action="store_true", help="print verbose output")
    list_parser.set_defaults(func=func_list_venv)

    # --- List packages inside a Virtual Env ---
    freeze_parser = subparsers.add_parser(
        "freeze", help="list packages inside an environment")
    freeze_parser.add_argument(
        "envname", help="name of the virtualenv to list packges in")
    freeze_parser.add_argument(
        "-v", "--verbose", action="store_true", help="print verbose output")
    freeze_parser.set_defaults(func=func_freeze_venv)

    # --- Delete Virtual Env ---
    del_parser = subparsers.add_parser(
        "delete", help="delete a virtual environment")
    del_parser.add_argument("envname", help="name of the virtualenv to enter")
    del_parser.add_argument(
        "-v", "--verbose", action="store_true", help="print verbose output")
    del_parser.set_defaults(func=func_delete_venv)

    if len(sys.argv) == 1:
        parser.print_help()
    else:
        args = parser.parse_args()
        if args.verbose:
            LOGGER.setLevel(logging.DEBUG)
        args.func(args)


if __name__ == "__main__":
    main()
