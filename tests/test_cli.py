import os
import unittest
import shutil
import json
from typing import Optional

from click.testing import CliRunner
from ufotest._testing import UfotestTestMixin

from ufotest.util import get_version
from ufotest.cli import (cli,
                         install)


# https://click.palletsprojects.com/en/8.0.x/testing/
class UfotestCliTestMixin(UfotestTestMixin):

    def setUp(self):
        super(UfotestTestMixin, self).setUp()

        self.cli_runner = CliRunner()

    def assertExitCodeZero(self, result) -> None:
        self.assertEqual(0, result.exit_code)

    def assertExitCodeNotZero(self, result) -> None:
        self.assertNotEqual(0, result.exit_code)

    def strip(self, value: str) -> str:
        return value.replace('\n', '').replace(' ', '')


# == THE ACTUAL TESTS ==

class TestBaseCommand(UfotestCliTestMixin, unittest.TestCase):

    def test_can_be_invoked_without_sub_command(self):
        """
        If the basic cli command group can be invoked without a specific sub command, as it should be able to
        """
        result = self.cli_runner.invoke(cli, [])
        self.assertExitCodeZero(result)

    def test_help_is_displayed(self):
        """
        If the --help option works and actually displays the docstring
        """
        result = self.cli_runner.invoke(cli, ['--help'])
        self.assertExitCodeZero(result)

        self.assertIn(self.strip(cli.__doc__),
                      self.strip(result.output))

    def test_version_option(self):
        """
        If the --version option prints the correct version string
        """
        result = self.cli_runner.invoke(cli, ['--version'])
        self.assertExitCodeZero(result)

        version = get_version()
        self.assertIn(self.strip(version),
                      self.strip(result.output))

    def test_setting_verbosity_option(self):
        """
        If the --verbose option appropriately sets the verbose flag in the config object
        """
        result = self.cli_runner.invoke(cli, ['--verbose'])
        self.assertExitCodeZero(result)

        self.assertTrue(self.config.verbose())


class TestInstallCommands(UfotestCliTestMixin, unittest.TestCase):

    # Since this class tests the installation, it will have a heavy requirement for a temporary folder into which it
    # can actually install the stuff. "UfotestCliTestMixin" does already provide a temporary folder, but it is only
    # "refreshed" on a per class basis. So the idea is to use a sub folder in this temp folder as the installation
    # target folder and just delete all contents before a new test starts

    def setUp(self):

        super(TestInstallCommands, self).setUp()

        self.install_folder_path = os.path.join(self.folder_path, 'installs')

        # Delete the old folder
        shutil.rmtree(self.install_folder_path, ignore_errors=True)

        # Create a new folder
        os.mkdir(self.install_folder_path)

    # -- test methods for "install"

    def test_invoking_without_arguments_causes_error(self):
        """
        If the exit code indicates an error when attempting to invoke command without positional arguments
        """
        result = self.cli_runner.invoke(cli, ['install'])
        self.assertExitCodeNotZero(result)

    def test_install_pcitool_skip(self):
        """
        If the install command can be invoked with the option "pcitool". Not actually performing the installation
        """
        result = self.cli_runner.invoke(cli, ['install', '--skip', 'pcitool', self.install_folder_path])
        self.assertExitCodeZero(result)

    def test_install_pcitool_with_json_flag(self):
        """
        If calling the "install" command with the --save-json flag actually creates the json result file in the cwd
        """
        os.chdir(self.install_folder_path)
        # This should create a "install.json" file in the current working directory
        result = self.cli_runner.invoke(cli, ['install', '--skip', '--save-json', 'pcitool', self.install_folder_path])
        self.assertExitCodeZero(result)

        # Does the JSON file exist?
        json_file_path = os.path.join(self.install_folder_path, 'install.json')
        self.assertTrue(os.path.exists(json_file_path))

        # Does it contain the right content
        with open(json_file_path, mode='r') as json_file:
            content = json.load(json_file)
            self.assertIn('success', content.keys())
            self.assertTrue(content['success'])

    def test_install_pcitool_without_json_flag(self):
        """
        If calling the "install" command without the --save-json flag does not create the json file.
        """
        os.chdir(self.install_folder_path)
        result = self.cli_runner.invoke(cli, ['install', '--skip', 'pcitool', self.install_folder_path])
        self.assertExitCodeZero(result)

        json_file_path = os.path.join(self.install_folder_path, 'install.json')
        self.assertFalse(os.path.exists(json_file_path))

    # -- test methods for "install-all"

    def test_install_all_skip(self):
        """
        If the "install-all" command basically works with exit code 0 when using the --skip option
        """
        result = self.cli_runner.invoke(cli, ['install-all', '--skip', self.install_folder_path])
        self.assertExitCodeZero(result)

    def test_install_all_with_save_json_flag(self):
        """
        If the "install-all" command actually produces a json result file if the --save-json flag is being passed
        """
        os.chdir(self.install_folder_path)
        result = self.cli_runner.invoke(cli, ['install-all', '--skip', '--save-json', self.install_folder_path])
        self.assertExitCodeZero(result)

        # Does the JSON file exist?
        json_file_path = os.path.join(self.install_folder_path, 'install.json')
        self.assertTrue(os.path.exists(json_file_path))

        # Does it contain the empty dict as it should?
        with open(json_file_path, mode='r') as json_file:
            content = json.load(json_file)
            self.assertIn('mock', content.keys())

    def test_install_all_without_save_json_flag(self):
        """
        If the "install-all" properly does not create a json file if the --save-json flag is not set
        """
        os.chdir(self.install_folder_path)
        result = self.cli_runner.invoke(cli, ['install-all', '--skip', self.install_folder_path])

        json_file_path = os.path.join(self.install_folder_path, 'install.json')
        self.assertFalse(os.path.exists(json_file_path))
