"""
A module containing various utility functions for usage in other modules.
"""
import string
import click
import random
import re
import subprocess
import shutil
import importlib.util
from typing import Optional, Tuple, Dict, List
from abc import ABC, abstractmethod

from jinja2 import Template, FileSystemLoader, Environment

from ufotest.config import *

# GLOBAL VARIABLES
VERSION_PATH = os.path.join(PATH, 'VERSION')

TEMPLATE_LOADER = FileSystemLoader(TEMPLATE_PATH)
TEMPLATE_ENVIRONMENT = Environment(loader=TEMPLATE_LOADER)
TEMPLATE_ENVIRONMENT.globals['config'] = Config()

SCRIPTS = {}


# FUNCTIONS
# =========

def cerror(message: str) -> None:
    """Outputs the *message* as an error to the console.

    :param message: The message to be printed
    """
    click.secho(f'[!] {message}', fg='red')


def cresult(message: str) -> None:
    """Outputs the *message* as progress to the console

    :param message: The message to be printed
    """
    click.secho(f'(+) {message}', fg='green')


def ctitle(message: str) -> None:
    """Outputs the *message* as a title to the console

    :param message: The message to be printed
    """
    click.secho(f'\n| | {message.upper()} | |', bold=True)


def csubtitle(message: str) -> None:
    """Outputs the *message* as a subtitle to the console

    :param message: The message to be printed
    """
    click.secho(f'\n==| {message} |==', bold=True)


def cparams(parameters: Dict[str, str]) -> None:
    """Outputs a dictionary of parameters as key value pairs to the console

    :param parameters: A dict of string keys and string values.
    """
    for key, value in parameters.items():
        click.secho(f'--| {key}: {value}')
    click.secho('')


def cprint(message: str) -> None:
    """Outputs the *message* to the console

    :param message: The message to be printed
    """
    click.secho(f'... {message}')


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


def get_version() -> str:
    """
    Returns the version string for the ufotest project. The version scheme of ufotest loosely follows the
    technique of `Semantic Versioning <https://semver.org/>`_. Where a minor version change may introduce backward
    incompatible changes, due to the project still being in active development with many features being subject to
    change.

    The return value of this function is subject to the "get_version" filter hook, which is able to modify the version
    string *after* it has been loaded from the file and sanitized.

    *EXAMPLE*

    .. code-block:: python

        version = get_version() # "1.2.1"

    :returns: The version string without any additional characters or whitespaces.
    """
    with open(VERSION_PATH) as version_file:
        version = version_file.read()
        version = version.replace(' ', '').replace('\n', '')

    # Here we actually need to check if the plugin management system is actually initialized (this is what the boolean
    # return of is_prepared indicates) because the version function needs to be functional even when the ufotest
    # installation folder and thus the config file does not yet exist.
    if CONFIG.is_prepared():
        version = CONFIG.pm.apply_filter('get_version', value=version)

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

    :deprecated:
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


def run_command(command: str, cwd: Optional[str] = None) -> Tuple[int, str]:
    """Runs a terminal command and returns it's exit code and console output

    :param command: The command string to execute
    :param cwd: Optionally a string path, which is to be used as the current working directory for the execution of the
        command.
    :return: A tuple, where the first value ist the int exit code of the command execution and the second value is the
        string of all the output the command produced on the stdout pipe.
    """
    completed_process = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    output = completed_process.stdout.decode()
    exit_code = completed_process.returncode

    if CONFIG.verbose():
        click.secho(f'[#] {command}', fg='cyan')
        if output:
            click.secho(f' >  {output}', fg='cyan')

    return exit_code, output


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
            click.secho('    Created default config: {}'.format(config_path))

    # -- BUILD QUEUE FILE
    queue_path = os.path.join(folder_path, 'build.queue')
    with open(queue_path, mode='w') as file:
        file.write('[]')
        if verbose:
            click.secho('    Created empty build queue: {}'.format(queue_path))

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
    # This folder will contain the build reports which are created when a new version of the hardware configuration
    # is built from the source repository
    builds_folder_path = get_builds_path()
    os.mkdir(builds_folder_path)
    if verbose:
        click.secho('    Created the "builds" folder for ufotest')

    # -- STATIC FOLDER
    # This folder contains all the static assets which are required for the internal CI web server. This folder already
    # exists within the ufotest package, it simply needs to be copied into the installation folder...
    static_path = os.path.join(folder_path, 'static')
    shutil.copytree(STATIC_PATH, static_path)
    if verbose:
        click.secho('    Copied the "static" folder into ufotest installation')

    return folder_path


def update_install(folder_path: str) -> None:
    # ~ replacing the static folder
    static_path = os.path.join(folder_path, 'static')
    shutil.rmtree(static_path)
    shutil.copytree(STATIC_PATH, static_path)
    if CONFIG.verbose():
        cprint('Updated ufotest static folder to new version')


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


def run_script(script_name: str, prefix: str = '') -> Tuple[int, str]:
    """Runs the script which is identified by *script_name*.

    :param script_name: The string name, which identifies the script within the ufotest application.
    :param prefix: A string which is prepended to the command string for the execution of the script. This mainly
        exists to possibly supply the "sudo" prefix to the execution of a script, if it needs it. Default is empty str.

    :raises FileNotFoundError: If the given script name does not refer to a valid script, which is registered with
        the ufotest application.

    :returns: A tuple, where the first element is the integer exit code of the script command and the second the str
        of the output, which the command generated on stdout.
    """
    if script_name not in SCRIPTS.keys():
        raise FileNotFoundError(f'The script "{script_name}" is not known to the application')

    script_data = SCRIPTS[script_name]
    script_folder = os.path.dirname(script_data['path'])
    script_command = prefix + script_data['path']

    # This perhaps needs explanation: The script command in itself would work fine. Since it contains the absolute path
    # to an executable file, that is fine. But we set the current working dir to the script folder anyways since some
    # of the scripts call other scripts and the way they call them, they expect them to be in the cwd...
    exit_code, stdout = run_command(script_command, cwd=script_folder)
    if CONFIG.verbose():
        if exit_code:
            cerror(f'The script "{script_name}" terminated with exit code 1')
            cerror(stdout)
        else:
            cerror(f'The script "{script_name}" terminated successfully')

    return exit_code, stdout


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


def get_template(name: str) -> Template:
    """
    Returns the jinja2 template with the given file name *name* within the static templates folder of this project

    :param name: The file name of the template to be loaded

    :returns: The template object for the specified template
    """
    return TEMPLATE_ENVIRONMENT.get_template(name)


def random_string(length: int, additional_letters: str = ' '):
    letters = string.ascii_letters + additional_letters
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
