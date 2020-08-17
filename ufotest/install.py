import click
import subprocess
from ufotest.config import CONFIG


PACKAGES = {
    'ubuntu': [
        'swig',
        'cmake',
        'libxml'
    ],
    'suse': [
        'cmake',
        'python2',
        'python2-devel',
        'swig',
        'uthash-devel',
        'libxml',
        'libxml-devel',
        'uuid-devel',
        'xfsprogs-devel'
    ]
}


def install_package(package_name: str, verbose=True):
    package_install_command = CONFIG['install']['package_install']

    click.secho('Installing package "{}"...'.format(package_name))

    command = '{} {}'.format(package_install_command, package_name)
    output = None if verbose else subprocess.DEVNULL
    completed_process = subprocess.run(command, shell=True, stdout=output, stderr=output)

    if completed_process.returncode == 0:
        click.secho('Successfully installed "{}"'.format(package_name), fg='green')
        return True
    else:
        click.secho('Encountered an error while installing "{}"'.format(package_name), fg='yellow')
        return False


def install_dependencies(verbose=True):
    operating_system = CONFIG['install']['os']
    packages = PACKAGES[operating_system]

    installed_packages = {}

    for package_name in packages:

        success = install_package(package_name, verbose=verbose)
        installed_packages[package_name] = success

    successful_packages = [package_name for package_name, success in installed_packages.items() if success]
    click.secho('Installed {} packages: {}'.format(
        len(successful_packages),
        ', '.join(successful_packages)
    ), fg='green', bold=True)
