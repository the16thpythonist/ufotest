import os
import sys
from typing import Optional

import click
import shutil

from ufotest.config import Config, get_path
from ufotest.util import execute_command
from ufotest.install import git_clone, get_repository_name
from ufotest.testing import TestRunner

CONFIG = Config()
UFOTEST_PATH = get_path()


def is_building() -> bool:
    """Returns the boolean value of whether or not a build process for the remote repo is currently running.

    :return: the boolean value of whether a build is currently running or not.
    """
    # So the build process works as follows: The repo folder cloned from the remote location, the new bit file is
    # flashed to the hardware, the test suite is executed and most importantly the afterwards the cloned folder is
    # deleted again! We are using this here to check if a build is currently still running, by checking if this repo
    # folder still exists.
    repository_url = CONFIG.get_ci_repository_url()
    repository_name = get_repository_name(repository_url)
    repository_path = os.path.join(UFOTEST_PATH, repository_name)

    return os.path.exists(repository_path) and os.path.isdir(repository_path)


def build_repository(suite: str, verbose: Optional[bool] = False):
    """Clones the remote repo, flashes the new configuration to the hardware and runs the test *suite*

    :param suite: the string name of the test suite which is supposed to be executed with the camera after the new
    configuration was flashed to the hardware.
    :param verbose: Whether or not additional console output is to be generated.

    :return: void
    """
    repository_path = clone_repository(verbose)

    try:
        # -- FLASHING THE BITFILE TO THE HARDWARE
        # For the flashing process there already exists an CLI command within this very application. So the simplest
        # thing is to just invoke this command to do the flashing process here.
        bitfile_path = os.path.join(repository_path, CONFIG.get_ci_bitfile_path())
        exit_code = execute_command('ufotest flash {}'.format(bitfile_path), True)
        if exit_code:
            # TODO: there seems to be a problem where the flash command does not reurn exit code 1 even with an error.
            click.secho('(+) There was a problem flashing the bitfile!')
            sys.exit(1)
        click.secho('(+) New bitfile flashed to the hardware', fg='green')

        # -- RUNNING THE TEST SUITE
        test_runner = TestRunner()
        test_runner.load()
        click.secho('    Tests have been loaded from memory')

        click.secho('    Running test suite: {}'.format(suite))
        test_report = test_runner.run_suite(suite)
        click.secho('(+) Test report saved to "{}"'.format(test_runner.folder_path), fg='green')

        # -- COPY THE BIT FILE INTO THE ARCHIVE
        bitfile_archive_path = os.path.join(test_runner.folder_path, 'snapshot.bit')
        shutil.copy(bitfile_path, bitfile_archive_path)
        click.secho('(+) Copied the used version of the bitfile: {}'.format(bitfile_archive_path), fg='green')

    except Exception as e:
        click.secho('[!] Exception: {}'.format(str(e)), fg='red')

    finally:
        # At the end it is important that we remove the cloned repo again, so that the next build process can clone the
        # new repo version into the same path.
        shutil.rmtree(repository_path)
        click.secho('(+) deleted repository folder: {}'.format(repository_path), fg='green')


def clone_repository(verbose: Optional[bool] = False):
    """Clones the repository for the camera source code which was specified in the config file.

    The repository is cloned into the base folder of the ufotest installation folder.

    :return: The string of the absolute path for the repository top level folder on the local machine
    """
    # The URL of the git repository is saved in the config file. We will install the repository directly into the folder
    # of the ufotest installation. This will be the same path every time. Due to this fact it is important that we make
    # sure that the installation is deleted at the end of each build process!
    repository_url = CONFIG.get_ci_repository_url()
    branch = CONFIG.get_ci_branch()
    _, repository_path = git_clone(UFOTEST_PATH, repository_url, verbose, branch=branch)

    return repository_path
