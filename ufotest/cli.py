"""Console script for ufotest."""
import sys
import click

from ufotest.install import print_hello


@click.group()
def cli():
    pass


@click.command('install')
def install(args=None):
    """Console script for ufotest."""
    print_hello()
    return 0


cli.add_command(install)


if __name__ == "__main__":
    sys.exit(cli())  # pragma: no cover
