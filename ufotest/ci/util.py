import os
import sys
from typing import Optional

import click
import shutil

from ufotest.config import Config, get_path
from ufotest.util import execute_command
from ufotest.install import git_clone
from ufotest.testing import TestRunner

CONFIG = Config()
UFOTEST_PATH = get_path()


def build_repository(suite: str, verbose: Optional[bool] = False):
    repository_path = clone_repository(verbose)

    try:
        # -- FLASHING THE BITFILE TO THE HARDWARE
        bitfile_path = os.path.join(repository_path, CONFIG.get_ci_bitfile_path())
        exit_code = execute_command('ufotest flash {}'.format(bitfile_path), True)
        if exit_code:
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

    except Exception as e:
        click.secho('[!] Exception: {}'.format(str(e)), fg='red')

    finally:
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
