"""
This file contains utility code, which is used for the unit testing of the actual ufotest code. It is not concerned
with the testing functionality implemented *for* ufotest.
"""
import tempfile
import os

from unittest import TestCase

from ufotest.util import init_install, get_path
from ufotest.config import CONFIG, reload_config, load_config, Config


class UfotestTestCase(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        # So the main problem with testing the ufotest application is that the test cases are obviously not meant to
        # modify the already existing installation on the PC, which is why a new installation has to be created for
        # just for testing. The "tempfile" module is perfect for this.
        cls.temp_folder = tempfile.TemporaryDirectory()
        cls.folder_path = os.path.join(cls.temp_folder.name, '.ufotest')

        # The installation path for the project can be controlled by using the content
        os.environ['UFOTEST_PATH'] = cls.folder_path
        init_install()

        # After the installation we also need to reload the config dictionary for the whole system
        cls.config = Config()
        cls.config.reload()

    @classmethod
    def tearDownClass(cls) -> None:
        # Cleaning up the modification of environmental variables.
        del os.environ['UFOTEST_PATH']

        # We need to properly close the temporary folder here
        cls.temp_folder.cleanup()

    # DEFAULT TESTS
    # -------------

    def test_installation_path(self):
        installation_path = get_path()
        expected_path = self.folder_path
        self.assertEqual(installation_path, expected_path)

    def test_config(self):
        self.assertIn('install', self.config)
        self.assertIn('camera', self.config)
