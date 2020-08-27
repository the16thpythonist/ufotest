"""
A module containing various utility functions for usage in other modules.
"""
import os
import click
import subprocess
from typing import Optional

from ufotest.config import *


SCRIPT_AUTHORS = {
    'michele':              'Michele Caselle <michele.caselle@kit.edu>',
    'jonas':                'Jonas Teufel <jonseb1998@gmail.com',
    'timo':                 'Timo Dritschler <timo.dritschler@kit.edu>'
}


SCRIPTS = {
    'reset': {
        'path':             os.path.join(PATH, 'Reset_all.sh'),
        'description':      'Resets the camera parameters to the default state',
        'author':           SCRIPT_AUTHORS['michele']
    },
    'status': {
        'path':             os.path.join(PATH, 'status.sh'),
        'description':      'Reads out the status parameters of the camera',
        'author':           SCRIPT_AUTHORS['michele']
    },

}



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


def init_install():
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


def check_install():
    folder_path = get_path()
    config_path = get_config_path()

    valid_install = True

    if not os.path.exists(folder_path):
        click.secho('ufotest is missing an installation folder!', bold=True, fg='red')
        valid_install = False

    if not os.path.exists(config_path):
        click.secho('ufotest is missing the configuration file at "{}"!'.format(config_path), bold=True, fg='red')
        valid_install = False

    if not valid_install:
        click.secho('A new ufotest installation can be created by typing "ufotest init" into the console...')

    return valid_install


def execute_script(name: str, prefix: str = '', verbose: bool = False):
    if name not in SCRIPTS.keys():
        click.secho('There is no script with the name "{}" registered!'.format(name), fg='red')
        return

    script = SCRIPTS[name]
    script_command = prefix + script['path']

    exit_code = execute_command(script_command, verbose=verbose)
    if not exit_code:
        click.secho('Script "{}" executed successfully!'.format(name), fg='green')
    else:
        click.secho('Script "{}" encountered an error!'.format(name), fg='red')
