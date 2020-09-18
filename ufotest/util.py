"""
A module containing various utility functions for usage in other modules.
"""
import os
import click
import subprocess
import importlib.util
from typing import Optional

from ufotest.config import *
from ufotest.scripts import SCRIPTS


VERSION_PATH = os.path.join(PATH, 'VERSION')


def get_version():
    with open(VERSION_PATH) as version_file:
        version = version_file.read()

    return version


def dynamic_import(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


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


def create_folder(folder_path: str):
    if os.path.exists(folder_path):
        os.mkdir(folder_path)
        os.chmod(folder_path, 0o777)


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

    # Also we need to create the tests folder inside of this folder
    test_folder_path = os.path.join(folder_path, 'tests')
    os.mkdir(test_folder_path)
    os.chmod(folder_path, 0o777)
    click.secho('Created the "tests" folder within the ufotest installation', fg='green')

    # Additionally we need to create a folder for the archive of the test runs
    archive_folder_path = os.path.join(folder_path, 'archive')
    os.mkdir(archive_folder_path)
    os.chmod(folder_path, 0o777)
    click.secho('Created the "archive" folder within the ufotest installation', fg='green')


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


def check_path(path: str, is_dir: bool = False):
    exists = os.path.exists(path)
    correct_type = os.path.isdir(path) if is_dir else os.path.isfile(path)

    return exists and correct_type


def check_vivado():
    vivado_path = CONFIG['install']['vivado_path']
    vivado_settings_path = os.path.join(vivado_path, 'settings64.sh')

    vivado_folder_exists = check_path(vivado_path, is_dir=True)
    vivado_settings_exists = check_path(vivado_settings_path, is_dir=False)

    return vivado_folder_exists and vivado_settings_exists


def execute_script(name: str, prefix: str = '', verbose: bool = False):

    if name not in SCRIPTS.keys():
        click.secho('There is no script with the name "{}" registered!'.format(name), fg='red')
        return

    script = SCRIPTS[name]
    script_folder = os.path.dirname(script['path'])
    script_command = prefix + script['path']

    exit_code = execute_command(script_command, verbose=verbose, cwd=script_folder)
    if not exit_code:
        click.secho('Script "{}" executed successfully!'.format(name), fg='green')
    else:
        click.secho('Script "{}" encountered an error!'.format(name), fg='red')

    return exit_code
