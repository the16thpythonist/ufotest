"""
A module containing various utility functions for usage in other modules.
"""
import string
import click
import random
import re
import subprocess
import importlib.util
from typing import Optional, List
from abc import ABC, abstractmethod

from jinja2 import Template

from ufotest.config import *
from ufotest.scripts import SCRIPTS


VERSION_PATH = os.path.join(PATH, 'VERSION')


# FUNCTIONS
# =========

def get_repository_name(repository_url: str) -> str:
    """Returns the name of a git repository if the *repository_url* for it is given.

    :param repository_url: the string url of the remote repository

    :return: the string name of the repo, which does NOT include the username it is just the name of the top level
    folder of that repo.
    """
    repository_name = re.findall(r'/([^/]*)\.git', repository_url)[0]
    return repository_name


def markdown_to_html(input_path: str, output_path: str, header_lines: List[str] = []):
    """Converts the markdown file at *input_path* to html file at *output_path*

    The functionality of this function is provided by the command line tool 'md-to-html' provided by the python
    package of the same name.
    This function also offers the additional possibility to add custom string lines to the head section of the created
    html file to potentially insert additional styles.

    :param input_path: The path to the original markdown file
    :param output_path: The path to be created for the html file
    :param header_lines: A list of strings to be included as separate lines into the head of the html
    """
    # The command md-to-html should be pretty self explanatory, it takes a markdown file as the input and produces a
    # corresponding html file from it. We can assume that this command generally works because it is provided by a
    # python module with the same name which is listed as one of the dependencies of this project. So when the ufotest
    # package is installed, this will be installed as well automatically.
    command = 'md-to-html --input {} --output {}'.format(
        input_path,
        output_path
    )
    execute_command(command, False)

    # This plain html file which was created looks pretty plain, so additionally there should be the possibility to
    # add stylesheets to the header of the document. This will be realized by being able to generally insert any kind
    # of string to the header section of the html file. Luckily this will be a rather simple string operation since
    # the previous conversion creates a html file which is very well structured by new lines.
    with open(output_path, mode='r+') as read_file:
        lines = read_file.readlines()

    for line in header_lines:
        lines.insert(lines.index(' </head>'), line)

    with open(output_path, mode='w+') as write_file:
        write_file.write('\n'.join(lines))


def get_version():
    with open(VERSION_PATH) as version_file:
        version = version_file.read()
        version = version.replace(' ', '').replace('\n', '')

    return version


def dynamic_import(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def get_command_output(command: str, cwd: Optional[str] = None):
    """
    Executes the given "command" and returns the output of the command as string

    The additional "cwd" option can be used to pass a string path description, which is supposed to be used as the
    current working directory for the command execution.

    :param command: The command which is to be executed
    :type command: str

    :param cwd: The path string of the current working directory to be assumed for the command execution
    :type cwd: Optional[str]
    """
    completed_process = subprocess.run(command, cwd=cwd, shell=True, stdout=subprocess.PIPE)
    byte_output = completed_process.stdout
    return byte_output.decode('utf-8')


def execute_command(command: str, verbose: bool, cwd: Optional[str] = None, foreground=True):
    """
    Executes the given system "command"

    The "verbose" flag controls whether or not the output of the command is written to stdout or not. With the "cwd"
    string a path can be passed, which is supposed to be used as the current working directory from which the command
    is to be executed.
    """
    output = None if verbose else subprocess.DEVNULL
    completed_process = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        stdout=output,
        stderr=output,
        close_fds=not foreground
    )
    return completed_process.returncode


def setup_environment():
    """
    Sets up all the environmental variables defined in the config file
    """
    for key, value in CONFIG['environment'].items():
        # Is this enough?
        os.environ[key] = value


def create_folder(folder_path: str):
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
        os.chmod(folder_path, 0o777)


def init_install(verbose=False) -> str:
    """Initializes the installation folder for the ufotest app.

    :param verbose: whether or not to print additional info to the console.

    :return: The string absolute path to the top level installation folder which has been created.
    """
    # First we check if the installation folder already exists.
    # "get_path" returns the path to where the config file is supposed to be installed to.
    folder_path = get_path()
    if os.path.exists(folder_path):
        raise IsADirectoryError('An ufotest installation already exists!')
    else:
        # In case it does not exist we will create it
        os.mkdir(folder_path)
        os.chmod(folder_path, 0o777)
        if verbose:
            click.secho('    Created new folder: {}'.format(folder_path))

    # -- CREATE CONFIG FILE
    # Then we need to copy the default template for the config file into this folder, if it is not already there
    config_path = get_config_path()
    if not os.path.exists(config_path):
        shutil.copyfile(CONFIG_TEMPLATE_PATH, config_path)
        if verbose:
            click.secho('    Created default config: {}'.format(folder_path))

    # -- TESTS FOLDER
    # Also we need to create the tests folder inside of this folder
    test_folder_path = os.path.join(folder_path, 'tests')
    os.mkdir(test_folder_path)
    os.chmod(folder_path, 0o777)
    if verbose:
        click.secho('    Created the "tests" folder for ufotest')

    # -- ARCHIVE FOLDER
    # Additionally we need to create a folder for the archive of the test runs
    archive_folder_path = os.path.join(folder_path, 'archive')
    os.mkdir(archive_folder_path)
    os.chmod(folder_path, 0o777)
    if verbose:
        click.secho('    Created the "archive" folder for ufotest')

    # -- BUILDS FOLDER
    # This folder will contain the build reporst which are created when a new version of the hardware configuration
    # is built from the source repository
    builds_folder_path = get_builds_path()
    os.mkdir(builds_folder_path)
    if verbose:
        click.secho('    Created the "builds" folder for ufotest')

    return folder_path


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


def get_template(name: str):
    template_path = os.path.join(TEMPLATE_PATH, name)
    with open(template_path, mode='r+') as file:
        return Template(file.read())


def random_string(length: int):
    letters = string.ascii_letters + ' '
    return ''.join(random.choice(letters) for i in range(length))


def clean_pci_read_output(output: str):
    """
    Cleans the output from the "pci_read" function.

    This essentially only means, that all the newlines and the leading whitespaces are being removed.

    :param output: The output message of the "pci_read" function
    :type output: str

    :return:
    """
    # Removing the newlines
    cleaned = output.replace('\n', '')
    # Removing the whitespaces in the front
    cleaned = cleaned.lstrip(' ')

    return cleaned


# CLASSES
# =======

class AbstractRichOutput(ABC):

    # TO BE IMPLEMENTED
    # -----------------

    @abstractmethod
    def to_markdown(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def to_latex(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def to_string(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def to_html(self) -> str:
        raise NotImplementedError()
