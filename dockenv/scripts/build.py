"""
Setup dockenv environment
"""
import os
import subprocess


def main():
    """
    Setup dockenv environment
    """
    if os.path.exists('requirements.txt'):
        subprocess.check_call(
            ['pip', 'install', '--no-cache-dir', '-r', 'requirements.txt'])

    if os.path.exists('package.txt'):
        subprocess.check_call(
            ['pip', 'install', '--no-cache-dir', '-r', 'package.txt'])


if __name__ == "__main__":
    main()
