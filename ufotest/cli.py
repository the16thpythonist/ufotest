"""Console script for ufotest."""
import sys
import os
import click

from ufotest.config import CONFIG, get_config_path
from ufotest.install import (install_dependencies,
                             install_fastwriter,
                             install_pcitools,
                             install_libufodecode,
                             install_libuca,
                             install_uca_ufo)


@click.group()
def cli():
    pass


@click.command('install')
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True))
@click.option('--verbose', '-v', is_flag=True)
@click.option('--no-dependencies', '-d', is_flag=True)
@click.option('--no-libuca', '-l', is_flag=True)
def install(path, verbose, no_dependencies, no_libuca):
    """Installing the project"""
    path = os.path.realpath(path)
    if not no_dependencies:
        click.secho('\n=====| Installing the Dependencies |=====', bold=True)
        click.secho('Reading configuration...')
        click.secho('- Configured OS: {}'.format(CONFIG['install']['os']))
        click.secho('- Configured package install: {}'.format(CONFIG['install']['package_install']))
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

        click.secho('\n=====| Installing pcilib plugin |=====', bold=True)
        # tbd

    else:
        click.secho('\n=====| Skipping Libuca |=====', bold=True)

    # The exit code
    return 0


@click.command('config')
def config():
    """Edit the config for the ufotest CLI"""
    config_path = get_config_path()
    click.edit(filename=config_path)

    return 0


cli.add_command(config)
cli.add_command(install)


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
