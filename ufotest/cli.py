"""
Module containing all the actual console scripts of the project.
"""
import sys
import os
from pathlib import Path

import click
import matplotlib.pyplot as plt

from ufotest.config import CONFIG, get_config_path
from ufotest.util import execute_command, setup_environment, init_install, check_install, execute_script
from ufotest.install import (install_dependencies,
                             install_fastwriter,
                             install_pcitools,
                             install_libufodecode,
                             install_libuca,
                             install_uca_ufo,
                             install_ipecamera)
from ufotest.camera import get_frame, set_up_camera, tear_down_camera


@click.group()
def cli():
    pass


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
        CONFIG['camera']['camera_width'],
        CONFIG['camera']['camera_height']
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

    if not no_vivado:
        click.secho('\n=====| Installing Vivado |=====', bold=True)
        click.secho('not yet implemented')

        click.secho('\n=====| Installing Vivado Programmer drivers |=====', bold=True)
        click.secho('not yet implemented')
    else:
        click.secho('\n=====| Skipping Vivado |=====', bold=True)

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
@click.option('--output', '-o', type=click.Path(file_okay=False, dir_okay=True, writable=True),
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

    # Call the necessary pci commands
    frame_data = get_frame(path=output, verbose=verbose)

    # Display the file using matplot lib
    if display:
        plt.imshow(frame_data)
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


cli.add_command(init)
cli.add_command(config)
cli.add_command(install)
cli.add_command(script)
cli.add_command(frame)

if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
