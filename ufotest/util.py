"""
A module containing various utility functions for usage in other modules.
"""
import os
import click
import subprocess
from typing import Optional

from ufotest.config import *


def pci_write(addr: str, value: str):
    pci_command = 'pci -w {} {}'.format(addr, value)
    exit_code = execute_command(pci_command, False)
    if exit_code:
        click.secho('Command "{}" failed!'.format(pci_command), fg='red')


def pci_read(addr: str, size):
    pci_command = 'pci -r {} -s {}'.format(addr, str(size))
    value = get_command_output(pci_command)
    return value


def get_command_output(command: str, cwd: Optional[str] = None):
    completed_process = subprocess.run(command, cwd=cwd, shell=True)
    return completed_process.stdout


def execute_command(command: str, verbose: bool, cwd: Optional[str] = None):
    """
    Executes the given system "command"

    The "verbose" flag controls whether or not the output of the command is written to stdout or not. With the "cwd"
    string a path can be passed, which is supposed to be used as the current working directory from which the command
    is to be executed.
    """
    output = None if verbose else subprocess.DEVNULL
    completed_process = subprocess.run(command, cwd=cwd, shell=True, stdout=output, stderr=output)
    return completed_process.returncode


def setup_environment():
    """
    Sets up all the environmental variables defined in the config file
    """
    for key, value in CONFIG['environment'].items():
        # Is this enough?
        os.environ[key] = value


def init_config():
    # First we check if the installation folder already exists.
    # "get_path" returns the path to where the config file is supposed to be installed to.
    folder_path = get_path()
    if os.path.exists(folder_path):
        # Maybe check for folder?
        pass
    else:
        # In case it does not exist we will create it
        os.mkdir(folder_path)
        os.chmod(folder_path, 0o777)
        click.secho('Created new ufotest installation folder "{}"'.format(folder_path), fg='green')

    # Then we need to copy the default template for the config file into this folder, if it is not already there
    config_path = get_config_path()
    if not os.path.exists(config_path):
        shutil.copyfile(CONFIG_TEMPLATE_PATH, config_path)
        click.secho('Copied config template to installation folder', fg='green')




