"""
This file contains utility code, which is used for the unit testing of the actual ufotest code. It is not concerned
with the testing functionality implemented *for* ufotest.
"""
import tempfile
import os
import unittest

from unittest import TestCase

from ufotest.util import init_install, get_path
from ufotest.config import Config


class UfotestTestMixin(object):
    """
    This is a custom base class for UnitTest specifically constructed to provide a mock environment for ufotest. To
    be more specific: Before any tests are actually executed, this class constructs a temporary folder in the /tmp
    folder of the system, where it makes a fresh install of ufotest and changes all references to point to this
    installation. If any of the tests interfaces with any files of the installation, those temporary fresh ones are
    being used instead of messing with the users system installation of ufotest.

    **USAGE**

    It is recommended to employ this mixin for every test class which in any capacity interfaces with the ufotest
    config file or any other file. To use it simply define a test class with mutliple inheritance that uses this
    mixin and the standard unittest.TestCase. *It is important that this class is actually listed first!*

    .. code-block:: python

        import unittest
        from ufotest._testing import UfotestTestMixin

        class TestMyStuff(UfotestTestMixin, unittest.TestCase):

            # ... the test methods

    **INHERITANCE VS. MIXIN**

    https://stackoverflow.com/questions/1323455/python-unit-test-with-base-and-sub-class
    As you might have noticed this class is a "mixin" which is intended to be used in a multiple inheritance scenario
    for those test cases which actually need the ufotest environment. Such a test class would have to inherit from this
    mixin first and from the basic unittest.TestCase second. This is a design choice, where the alternative would have
    been to make this a child class of the basic TestCase class and then have all the actual test classes only inherit
    from this extended test class. But that actually causes problems, because that was the way I had it before. The
    issue ist the following: The pytest test discovery automatically runs every class which inherits from TestCase and
    contains at least one method which starts with "test_" this would then also discover the "raw" base class which is
    present in the namespace of all the test files because it was imported. This causes the base class which is only
    supposed to be a base class for further inheritance and not actually executed as a test itself to be actually
    executed as exactly that multiple times: Once per test file where it is imported. This does not happen with the
    mixin implementation because the mixin obviously does not inherit from TestCase directly...
    """

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
        """
        If the installation path is correct
        """
        print(self.__class__)
        installation_path = get_path()
        expected_path = self.folder_path
        self.assertEqual(installation_path, expected_path)

    def test_config(self):
        """
        If the config object is generally correctly loaded
        """
        self.assertIn('install', self.config)
        self.assertIn('camera', self.config)

        # This is actually quite relevant. The context field is being set in the constructor of the config class and is
        # not an intrinsic field of the config file. So it could be that this field gets overwritten or deleted somehow.
        # That would be important to catch
        self.assertIn('context', self.config)
