"""
Module containing all the actual console scripts of the project.
"""
import sys
import os
from pathlib import Path

import click
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')

from ufotest.config import PATH, CONFIG, get_config_path
from ufotest.scripts import SCRIPTS, SCRIPTS_PATH
from ufotest.util import (execute_command,
                          setup_environment,
                          init_install,
                          check_install,
                          execute_script,
                          get_version,
                          check_vivado,
                          check_path)
from ufotest.install import (install_dependencies,
                             install_fastwriter,
                             install_pcitools,
                             install_libufodecode,
                             install_libuca,
                             install_uca_ufo,
                             install_ipecamera)
from ufotest.camera import save_frame, import_raw, set_up_camera, tear_down_camera


@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='Print the version of the program')
def cli(version):
    if version:
        version = get_version()
        click.secho('UFOTEST VERSION')
        click.secho(version, bold=True)
        return 0


@click.command('install', short_help='Install the project and its dependencies')
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True))
@click.option('--verbose', '-v', is_flag=True, help='Show additional console output')
@click.option('--no-dependencies', '-d', is_flag=True, help='Skip installation of required repositories')
@click.option('--no-libuca', '-l', is_flag=True, help='Skip installation of libuca')
@click.option('--no-vivado', is_flag=True, help='Skip installation of vivado')
def install(path, verbose, no_dependencies, no_libuca, no_vivado):
    """
    Installing the Project into PATH

    PATH will be the system path, which will then contain subfolders with all the required repositories and
    dependencies
    """
    if not check_install():
        return 1

    path = os.path.realpath(path)

    click.secho('\n')
    click.secho(' +-------------------------+', bold=True, fg='green')
    click.secho(' |  STARTING INSTALLATION  |', bold=True, fg='green')
    click.secho(' +-------------------------+', bold=True, fg='green')

    click.secho('\nReading configuration...')
    click.secho('- Configured OS: {}'.format(CONFIG['install']['os']))
    click.secho('- Configured package install: {}'.format(CONFIG['install']['package_install']))
    click.secho('- Camera dimensions: {} x {}'.format(
        CONFIG['camera']['sensor_width'],
        CONFIG['camera']['sensor_height']
    ))

    if not no_dependencies:
        click.secho('\n=====| Installing System Packages |=====', bold=True)
        install_dependencies(verbose=verbose)

        click.secho('\n=====| Installing fastwriter |=====', bold=True)
        install_fastwriter(path, verbose=verbose)

        click.secho('\n=====| Installing pcitools |=====', bold=True)
        install_pcitools(path, verbose=verbose)

        click.secho('\n=====| Installing libufodecode |=====', bold=True)
        install_libufodecode(path, verbose=verbose)
    else:
        click.secho('\n=====| Skipping Dependencies |=====', bold=True)

    if not no_libuca:
        click.secho('\n=====| Installing Libuca |=====', bold=True)
        install_libuca(path, verbose=verbose)

        click.secho('\n=====| Installing uca-ufo |=====', bold=True)
        install_uca_ufo(path, verbose=verbose)

        click.secho('\n=====| Installing ipecamera plugin |=====', bold=True)
        install_ipecamera(path, verbose)
    else:
        click.secho('\n=====| Skipping Libuca |=====', bold=True)

    # if not no_vivado:
    #     click.secho('\n=====| Installing Vivado |=====', bold=True)
    #     click.secho('not yet implemented')
    #
    #     click.secho('\n=====| Installing Vivado Programmer drivers |=====', bold=True)
    #     click.secho('not yet implemented')
    # else:
    #     click.secho('\n=====| Skipping Vivado |=====', bold=True)

    # The exit code
    return 0


@click.command('init', short_help='initializes the config files for ufotest')
def init():
    """
    Initializes the config files for ufotest
    """
    init_install()
    click.secho('Ufotest is initialized!', bold=True, fg='green')

    return 0


@click.command('config', short_help='Edit the config for ufotest')
@click.option('--editor', '-e', type=click.STRING, help='Specify the editor command to be used to open the config file')
def config(editor):
    """
    Edit the configuration file for this project
    """
    if not check_install():
        return 1

    config_path = get_config_path()
    click.edit(filename=config_path, editor=editor)

    return 0


@click.command('frame', short_help='Acquire and display a frame from the camera')
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
@click.option('--output', '-o', type=click.STRING,
              help='Specify the output file path for the frame', default='/tmp/frame.raw')
@click.option('--display', '-d', is_flag=True, help='display the frame in seperate window')
def frame(verbose, output, display):
    """
    Capture a frame from the camera and display it to the user
    """
    if not check_install():
        return 1

    # Setup all the important environment variables and stuff
    setup_environment()

    execute_command('rm /tmp/frame*', verbose)
    if verbose:
        click.secho('Removed the previous frame buffer', fg='green')

    # Call the necessary pci commands
    save_frame(output, verbose=verbose)

    # Display the file using matplot lib
    if display:
        images = import_raw(
            path=output,
            n=1,
            sensor_height=CONFIG['camera']['sensor_height'],
            sensor_width=CONFIG['camera']['sensor_width']
        )

        plt.imshow(images[0])
        plt.show()

    return 0


@click.command('script', short_help="Execute one of the known (bash) scripts")
@click.argument('name', type=click.STRING)
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
def script(name, verbose):
    """
    Executes a registered script with the given NAME
    """
    if not check_install():
        return 1

    exit_code = execute_script(name, verbose=verbose)
    if not exit_code:
        click.secho('Script "{}" succeeded'.format(name), bold=True, fg='green')
    else:
        click.secho('Script "{}" failed'.format(name), bold=True, fg='red')


@click.command('list-scripts', short_help='List all available scripts')
def list_scripts():
    if not check_install():
        return 1

    click.secho('The following scripts are available:\n', fg='green', bold=True)

    for script_id, script_data in SCRIPTS.items():
        click.secho(script_id, bold=True)
        click.secho('   Path: {}\n   Description: {}\n   Author: {}\n'.format(
            script_data['path'],
            script_data['description'],
            script_data['author']
        ))


@click.command('setup', short_help="Enable the camera")
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
def setup(verbose):
    if not check_install():
        return 1

    set_up_camera(verbose=verbose)


@click.command('teardown', short_help="Disable the camera. DO NOT USE")
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
def teardown(verbose):
    if not check_install():
        return 1

    tear_down_camera(verbose)


@click.command('flash', short_help='Flash a new .BIT file to the FPGA memory')
@click.option('--verbose', '-v', is_flag=True, help='print additional console messages')
@click.argument('file', type=click.STRING)
def flash(verbose, file: str):
    if not check_install():
        return 1

    click.secho('FLASHING THE FPGA MEMORY', bold=True)

    # -- CHECKING IF THE GIVEN FILE EVEN EXISTS
    file_path = os.path.abspath(file)
    file_exists = check_path(file_path, is_dir=False)
    if not file_exists:
        click.secho('The given path does not exist!', fg='red')
        return 1

    # -- CHECKING IF THE FILE EVEN IS A BIT FILE
    file_extension = file_path.split('.')[-1].lower()
    is_bit_file = file_extension == 'bit'
    if not is_bit_file:
        click.secho('The given file is not a .BIT file', fg='red')
        return 1
    elif verbose:
        click.secho('Flashing bit file "{}"'.format(file))

    # -- CHECKING IF VIVADO IS INSTALLED
    vivado_installed = check_vivado()
    if not vivado_installed:
        click.secho('Vivado is not installed, please install Vivado to be able to flash the fpga!', fg='red')
        return 1
    elif verbose:
        click.secho('Vivado installation found!', fg='green')

    # -- FLASHING THE BIT FILE
    flash_command = "{command} -nolog -nojournal -mode batch -source fpga_conf_bitprog.tcl -tclargs {file}".format(
        command=CONFIG['install']['vivado_command'],
        file=file_path
    )
    exit_code = execute_command(flash_command, verbose, cwd=SCRIPTS_PATH)
    if not exit_code:
        click.secho('SUCCESSFULLY FLASHED FPGA WITH "{}"'.format(file_path))
        return 0
    else:
        return 1


# Registering the commands within the click group
cli.add_command(init)
cli.add_command(config)
cli.add_command(install)
cli.add_command(script)
cli.add_command(frame)
cli.add_command(setup)
cli.add_command(teardown)
cli.add_command(list_scripts)
cli.add_command(flash)


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
