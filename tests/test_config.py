"""
Unittests for the config module of ufotest
"""
import os
import tempfile

from unittest import TestCase

from ufotest._testing import UfotestTestCase
from ufotest.config import get_path, DEFAULT_PATH


class TestGetPath(TestCase):

    # -- TESTS --

    def test_without_arguments(self) -> None:
        """
        If the function generally works
        """
        # Without explicitly setting the environmental variable to specify a different installation path, the call of
        # the function without any arguments should return the default path
        self.assertEqual(DEFAULT_PATH, get_path())

    def test_with_arguments(self) -> None:
        """
        If passing additional arguments (relative paths) results in a correct result
        """
        self.assertEqual(
            os.path.join(DEFAULT_PATH, "archive/test/report.json"),
            get_path('archive', 'test', 'report.json')
        )

    def test_with_custom_installation_path(self) -> None:
        """
        If a correct path is returned when defining a custom installation path with the env variable
        """
        temp_folder = tempfile.TemporaryDirectory()
        os.environ['UFOTEST_PATH'] = temp_folder.name

        self.assertEqual(temp_folder.name, get_path())

        # Cleaning up to not influence other tests
        temp_folder.cleanup()
        del os.environ['UFOTEST_PATH']
