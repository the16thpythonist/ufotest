"""
A module, which contains the code related to the installation process of the UFO dependencies
"""
import os
import re
import click
import subprocess
from typing import Optional

from ufotest.config import CONFIG


def install_package(package_name: str, verbose=True):
    """
    Installs a system package with the given "package_name"
    """
    package_install_command = CONFIG['install']['package_install']

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


def install_fastwriter(path: str, verbose=True):
    """
    Installs the fastwriter repository into the given "path"
    """
    git_url = CONFIG['install']['fastwriter_git']
    install_generic_cmake(
        path,
        git_url,
        verbose,
        {'CMAKE_INSTALL_PREFIX': '/usr'}
    )


def install_pcitools(path:str, verbose=True):
    """
    Installs the pcitool repository into the given "path"
    """
    git_url = CONFIG['install']['pcitools_git']
    folder_path = install_generic_cmake(
        path,
        git_url,
        verbose,
        {'CMAKE_INSTALL_PREFIX': '/usr'}
    )

    # Also installing the driver!
    driver_path = os.path.join(folder_path, 'driver')
    output = None if verbose else subprocess.DEVNULL

    build_command = 'mkdir build; cd build; cmake -DCMAKE_INSTALL_PREFIX=/usr ..'
    exit_code = execute_command(build_command, verbose, cwd=driver_path)
    if not exit_code:
        click.secho('Built "pcilib driver" sources', fg='green')

    install_command = 'cd build; sudo make install'
    exit_code = execute_command(install_command, verbose, cwd=driver_path)
    if not exit_code:
        click.secho('Installed "pcilib driver" successfully!', bold=True, fg='green')

    # Activating the driver after it has been installed...
    activate_driver_command = 'sudo depmod -a'
    exit_code = execute_command(activate_driver_command, verbose)
    if not exit_code:
        click.secho('Activated driver!', bold=True, fg='green')


def install_libufodecode(path:str, verbose=True):
    """
    Installs the libufodecode repository into the given "path"
    """
    git_url = CONFIG['install']['libufodecode_git']
    camera_width = CONFIG['camera']['camera_width']
    install_generic_cmake(
        path,
        git_url,
        verbose,
        {'CMAKE_INSTALL_PREFIX': '/usr', 'IPECAMERA_WIDTH': camera_width}
    )


def install_libuca(path: str, verbose=True):
    """
    Installs the libuca repository into the given "path"
    """
    git_url = CONFIG['install']['libuca_git']
    install_generic_cmake(
        path,
        git_url,
        verbose,
        {'CMAKE_INSTALL_PREFIX': '/usr'}
    )


def install_uca_ufo(path: str, verbose=True):
    """
    Installs the uca-ufo repository into the given "path"
    """
    git_url = CONFIG['install']['ucaufo_git']
    install_generic_cmake(
        path,
        git_url,
        verbose,
        {
            'CMAKE_INSTALL_PREFIX': '/usr',
            'CMOSIS_SENSOR_WIDTH': CONFIG['camera']['camera_width'],
            'CMOSIS_SENSOR_HEIGHT': CONFIG['camera']['camera_height']
        }
    )


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


def git_clone(path: str, git_url: str, verbose: bool):
    """
    Clones the repository from "git_url" into the given folder "path"
    """
    # Here we are first extracting the name of the git repository, because that will also be the name of the folder
    # into which it was cloned into later on and this that will be important to actually enter this folder
    repository_name = re.findall(r'/(\b*)\.git', git_url)[0]
    repository_path = os.path.join(path, repository_name)
    if verbose:
        click.secho('~ Cloning git repository "{}"'.format(git_url))

    # Executing the clone command
    clone_command = 'git clone {}'.format(git_url)
    exit_code = execute_command(clone_command, verbose, cwd=path)
    if not exit_code:
        click.secho('Cloned repository "{}" ({})'.format(repository_name, repository_path), fg='green')

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

    return folder_path
