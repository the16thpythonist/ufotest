"""
A module, which contains the code related to the installation process of the UFO dependencies
"""
import os
import re
import click
import subprocess
from typing import Optional, Tuple

from ufotest.config import CONFIG
from ufotest.util import execute_command, get_repository_name, cprint


def git_clone(path: str, git_url: str, verbose: bool, branch: str = 'master') -> Tuple[str, str]:
    """Clones the repository from *git_url* into the given folder *path*

    The additional arg *verbose* is a boolean which controls whether the output of this operation is being written to
    stdout stream.

    :param path: The path of the folder into which the repository is supposed to be clonedS
    :param git_url: The string url of the git repository from which to clone
    :param verbose: Whether or not to print additional output to the stdout stream
    :param branch: The string name of the branch to be cloned. Default is master branch.

    :return: A tuple of two values, where the first one is the string name of the repository and the second is the
    string of the absolute path of the clones location within the filesystem.
    """
    # Here we are first extracting the name of the git repository, because that will also be the name of the folder
    # into which it was cloned into later on and this that will be important to actually enter this folder
    repository_name = get_repository_name(git_url)
    repository_path = os.path.join(path, repository_name)
    if verbose:
        click.secho('   Cloning git repository "{}"'.format(git_url))

    # Executing the clone command
    clone_command = 'git clone --single-branch --branch {} {}'.format(branch, git_url)
    exit_code = execute_command(clone_command, verbose, cwd=path)
    if not exit_code:
        click.secho('(+) Cloned repository "{}" ({})'.format(repository_name, repository_path), fg='green')

    return repository_name, repository_path


def install_generic_cmake(path: str, git_url: str, verbose: bool, cmake_args: dict):
    """
    Installs the cmake project from the "git_url" into the given folder "path".

    This function first clones the repository which is given by the git url, then it enters this folder locally,
    creates a build folder and attempts to run a cmake installation process within this folder.
    The cmake_args can be used to pass additional options to the cmake build process.
    """
    # Cloning the repository
    name, folder_path = git_clone(path, git_url, verbose)

    arguments = ' '.join(['-D{}={}'.format(key, value) for key, value in cmake_args.items()])
    build_command = 'mkdir build; cd build; cmake {} ..'.format(arguments)
    exit_code = execute_command(build_command, verbose, cwd=folder_path)
    if not exit_code:
        click.secho('Built "{}" sources'.format(name), fg='green')

    install_command = 'cd build; sudo make install'
    exit_code = execute_command(install_command, verbose, cwd=folder_path)
    if not exit_code:
        click.secho('Installed "{}" successfully!'.format(name), bold=True, fg='green')
    else:
        click.secho('Error installing "{}"!'.format(name), bold=True, fg='red')

    return folder_path


def install_package(package_name: str, verbose=True):
    """
    Installs a system package with the given "package_name"
    """
    operating_system = CONFIG['install']['os']
    package_install_command = CONFIG['install'][operating_system]['package_install']

    click.secho('Installing package "{}"...'.format(package_name))

    command = '{} {}'.format(package_install_command, package_name)
    exit_code = execute_command(command, verbose)

    if not exit_code:
        click.secho('Successfully installed "{}"'.format(package_name), fg='green')
        return True
    else:
        click.secho('Encountered an error while installing "{}"'.format(package_name), fg='yellow')
        return False


def install_dependencies(verbose=True):
    """
    Installs all the system packages, which are listed in the config file.
    """
    operating_system = CONFIG['install']['os']
    packages = CONFIG['install'][operating_system]['packages']

    installed_packages = {}

    for package_name in packages:

        success = install_package(package_name, verbose=verbose)
        installed_packages[package_name] = success

    successful_packages = [package_name for package_name, success in installed_packages.items() if success]
    click.secho('Installed {} packages: {}'.format(
        len(successful_packages),
        ', '.join(successful_packages)
    ), fg='green', bold=True)


def mock_install_repository(path: str):
    """
    Does not actually perform anything, but still returns a result dict like the other install functions. This
    result dict contains the following fields:
    - success: True
    - path: The path passed as parameter
    - git: Github URL

    :return: dict
    """
    return {
        'success':      True,
        'path':         path,
        'git':          'https://github.com'
    }


def install_pcitools(path: str, verbose: bool = True) -> dict:
    """
    Installs the "pcitool" repository into the given *path*. Returns a dict which contains information about the
    installation process.

    The returned dict contains the following items:
    - success: boolean value of whether or not the installation succeeded
    - path: the string path of the file
    - git: the string URL of the git repository from which it was installed

    :param path: The string path of the folder into which to install this dependency
    :param verbose: Whether or not to produce verbose output. DEPRECATED: Uses config field to determine verbosity

    :return: A dict, which contains information about the installation process.
    """
    git_url = CONFIG['install']['pcitools_git']
    folder_path = install_generic_cmake(
        path,
        git_url,
        CONFIG.verbose(),
        {'CMAKE_INSTALL_PREFIX': '/usr'}
    )

    # Also installing the driver!
    driver_path = os.path.join(folder_path, 'driver')
    output = None if verbose else subprocess.DEVNULL

    build_command = 'mkdir build; cd build; cmake -DCMAKE_INSTALL_PREFIX=/usr ..'
    exit_code = execute_command(build_command, CONFIG.verbose(), cwd=driver_path)
    if not exit_code:
        click.secho('Built "pcilib driver" sources', fg='green')

    install_command = 'cd build; sudo make install'
    exit_code = execute_command(install_command, CONFIG.verbose(), cwd=driver_path)
    if not exit_code:
        click.secho('Installed "pcilib driver" successfully!', bold=True, fg='green')

    # Activating the driver after it has been installed...
    activate_driver_command = 'sudo depmod -a'
    exit_code = execute_command(activate_driver_command, CONFIG.verbose())
    if not exit_code:
        click.secho('Activated driver!', bold=True, fg='green')

    return {
        'success':          (not exit_code),
        'path':             folder_path,
        'git':              git_url
    }


def install_fastwriter(path: str, verbose: bool = True) -> dict:
    """
    Installs the "fastwriter" repository into the given *path*. Returns a dict which contains some information about
    the installation process.

    The returned dict contains the following items:
    - success: boolean value of whether or not the installation succeeded
    - path: the string path of the file
    - git: the string URL of the git repository from which it was installed

    :param path: The string path of the folder into which to install this dependency
    :param verbose: Whether or not to produce verbose output. DEPRECATED: Uses config field to determine verbosity

    :return: A dict, which contains information about the installation process.
    """
    git_url = CONFIG['install']['fastwriter_git']
    folder_path = install_generic_cmake(
        path,
        git_url,
        CONFIG.verbose(),
        {'CMAKE_INSTALL_PREFIX': '/usr'}
    )

    # Declare as successful if the folder exists and is not empty
    success = os.path.exists(folder_path) and bool(os.listdir(folder_path))
    return {
        'success': success,
        'path': folder_path,
        'git': git_url
    }


def install_libufodecode(path: str, verbose: bool = True) -> dict:
    """
    Installs the "libufodecode" repository into the given *path*. Returns a dict which contains some information about
    the installation process.

    The returned dict contains the following items:
    - success: boolean value of whether or not the installation succeeded
    - path: the string path of the file
    - git: the string URL of the git repository from which it was installed

    :param path: The string path of the folder into which to install this dependency
    :param verbose: Whether or not to produce verbose output. DEPRECATED: Uses config field to determine verbosity

    :return: A dict, which contains information about the installation process.
    """
    git_url = CONFIG['install']['libufodecode_git']
    folder_path = install_generic_cmake(
        path,
        git_url,
        CONFIG.verbose(),
        {
            'CMAKE_INSTALL_PREFIX': '/usr',
            'IPECAMERA_WIDTH': CONFIG.get_sensor_width(),
            'IPECAMERA_HEIGHT': CONFIG.get_sensor_height()
        }
    )

    # Declare as successful if the folder exists and is not empty
    success = os.path.exists(folder_path) and bool(os.listdir(folder_path))
    return {
        'success':      success,
        'path':         folder_path,
        'git':          git_url
    }


def install_libuca(path: str, verbose: bool = True) -> dict:
    """
    Installs the libuca repository into the given *path*. Returns a dict which contains some information about
    the installation process.

    The returned dict contains the following items:
    - success: boolean value of whether or not the installation succeeded
    - path: the string path of the file
    - git: the string URL of the git repository from which it was installed

    :param path: The string path of the folder into which to install this dependency
    :param verbose: Whether or not to produce verbose output. DEPRECATED: Uses config field to determine verbosity

    :return: A dict, which contains information about the installation process.
    """
    git_url = CONFIG['install']['libuca_git']
    folder_path = install_generic_cmake(
        path,
        git_url,
        CONFIG.verbose(),
        {'CMAKE_INSTALL_PREFIX': '/usr'}
    )

    # Declare as successful if the folder exists and is not empty
    success = os.path.exists(folder_path) and bool(os.listdir(folder_path))
    return {
        'success': success,
        'path': folder_path,
        'git': git_url
    }


def install_uca_ufo(path: str, verbose: bool = True) -> dict:
    """
    Installs the uca-ufo repository into the given *path*. Returns a dict which contains some information about the
    installation process.

    The returned dict contains the following items:
    - success: boolean value of whether or not the installation succeeded
    - path: the string path of the file
    - git: the string URL of the git repository from which it was installed

    :param path: The string path of the folder into which to install this dependency
    :param verbose: Whether or not to produce verbose output. DEPRECATED: Uses config field to determine verbosity

    :return: A dict, which contains information about the installation process.
    """
    git_url = CONFIG['install']['ucaufo_git']
    folder_path = install_generic_cmake(
        path,
        git_url,
        CONFIG.verbose(),
        {
            'CMAKE_INSTALL_PREFIX': '/usr',
            'CMOSIS_SENSOR_WIDTH': CONFIG.get_sensor_width(),
            'CMOSIS_SENSOR_HEIGHT': CONFIG.get_sensor_height()
        }
    )

    # Declare as successful if the folder exists and is not empty
    success = os.path.exists(folder_path) and bool(os.listdir(folder_path))
    return {
        'success': success,
        'path': folder_path,
        'git': git_url
    }


def install_ipecamera(path: str, verbose: bool = True) -> dict:
    """
    Installs the "ipecamera" repository into the given *path*. Returns a dict which contains information about the
    installation process.

    The returned dict contains the following items:
    - success: boolean value of whether or not the installation succeeded
    - path: the string path of the file
    - git: the string URL of the git repository from which it was installed

    :param path: The string path of the folder into which to install this dependency
    :param verbose: Whether or not to produce verbose output. DEPRECATED: Uses config field to determine verbosity

    :return: A dict, which contains information about the installation process.
    """
    git_url = CONFIG['install']['ipecamera_git']
    folder_path = install_generic_cmake(
        path,
        git_url,
        CONFIG.verbose(),
        {
            'CMAKE_INSTALL_PREFIX': '/usr',
        }
    )

    # Declare as successful if the folder exists and is not empty
    success = os.path.exists(folder_path) and bool(os.listdir(folder_path))
    return {
        'success': success,
        'path': folder_path,
        'git': git_url
    }


def install_vivado(path: str, verbose=True):
    # Downloading the zip file

    # Unzipping the file into a folder

    # Going into the folder and starting the installation process

    # Returning the path to the folder
    pass


# ====================================================================================================================
# THE NEW HOOK BASED VERSION OF INSTALLATIONS
# ====================================================================================================================
# Right now, the old code simply uses the
