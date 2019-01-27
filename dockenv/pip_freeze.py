"""
Helper script to call pip freeze inside a container
"""
import subprocess

subprocess.run("pip freeze", shell=True)
