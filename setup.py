"""
Dockenv
"""
import os
from setuptools import setup

setup(
    name="dockenv-cli",
    version="1.0.0",
    description="Dockenv - Run untrusted Python scripts inside docker containers",
    author="/path/to/file",
    license="MIT",
    url="http://github.com/pathtofile/dockenv",
    packages=["dockenv"],
    entry_points={"console_scripts": ["dockenv = dockenv.__main__:main"]},
    package_data={
        "dockenv": [
            os.path.join("scripts", "*.py"),
            os.path.join("scripts", "Dockerfile"), "pip_freeze.py"
        ],
    },
    include_package_data=True,
    install_requires=["docker"],
    python_requires=">=3.6"
    )
