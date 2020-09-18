import inspect

from ufotest._testing import UfotestTestCase
from ufotest.testing import TestRunner, AbstractTest


class TestTestRunner(UfotestTestCase):

    def test_construction(self):
        """
        Simply tests if the construction of a new instance does not produce errors
        """
        test_runner = TestRunner(config=self.config)
        self.assertIsInstance(test_runner, TestRunner)

    def test_module_loading_working_at_all(self):
        """
        Tests if the dynamic loading of the modules from the test folder works at all. That does not imply that it
        tests for the correct amount of tests.
        """
        test_runner = TestRunner(config=self.config)
        test_runner.load()

        self.assertNotEqual(0, len(test_runner.modules))
        for module in test_runner.modules.values():
            self.assertTrue(inspect.ismodule(module))

    def test_test_loading_working_at_all(self):
        """
        Tests if any tests have been loaded from the test modules and also tests if these are only valid subclasses
        of the AbstractTest base class.
        """
        test_runner = TestRunner(config=self.config)
        test_runner.load()

        self.assertNotEqual(0, len(test_runner.tests))
        for test in test_runner.tests.values():
            self.assertTrue(inspect.isclass(test))
            self.assertTrue(issubclass(test, AbstractTest))