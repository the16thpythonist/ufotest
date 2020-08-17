"""Console script for ufotest."""
import sys
import click

from ufotest.config import CONFIG, get_config_path
from ufotest.install import install_dependencies


@click.group()
def cli():
    pass


@click.command('install')
@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True, writable=True))
@click.option('--verbose', '-v', is_flag=True)
def install(path, verbose):
    """Installing the project"""
    click.echo(verbose)
    click.secho('=====| Installing the Dependencies |=====', bold=True)
    click.secho('Reading configuration...')
    click.secho('- Configured OS: {}'.format(CONFIG['install']['os']))
    click.secho('- Configured package install: {}'.format(CONFIG['install']['package_install']))

    install_dependencies(verbose=verbose)

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
