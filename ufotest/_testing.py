import tempfile
import os

from unittest import TestCase

from ufotest.util import init_install, get_path
from ufotest.config import CONFIG, reload_config, load_config, Config


class UfotestTestCase(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        # So here I somehow have to setup a new config file etc. I guess I would do this with a temp folder?
        cls.temp_folder = tempfile.TemporaryDirectory()
        cls.folder_path = cls.temp_folder.name

        # Now we need to set a custom path for the installation folder of ufotest, which is inside this temporary
        # folder.
        os.environ['UFOTEST_PATH'] = cls.folder_path
        # After that we can install ufotest into this folder
        init_install()
        # After the installation we also need to reload the config dictionary for the whole system
        cls.config = Config()
        cls.config.reload()

    @classmethod
    def tearDownClass(cls) -> None:
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
