"""
Unittests for the testing functionality of ufotest.
"""
import inspect

from ufotest._testing import UfotestTestCase
from ufotest.util import random_string
from ufotest.testing import (TestRunner,
                             TestContext,
                             AbstractTest,
                             TestReport,
                             MessageTestResult,
                             TestMetadata,
                             AssertionTestResult)


# HELPER FUNCTIONS
# ================

def get_message_test_result(exit_code: int = 0):
    return MessageTestResult(
        exit_code=exit_code,
        message=random_string(20)
    )


# TESTCASES
# =========

class TestTestRunner(UfotestTestCase):

    def test_construction(self):
        """
        Simply tests if the construction of a new instance does not produce errors
        """
        # self.config is a special config object, which was especially constructed for the test. It makes sure that the
        # test cases run within their own "testing" environment and do not use the global environment, which may or may
        # may not be already installed on the PC.
        with TestContext(config=self.config) as test_context:
            test_runner = TestRunner(test_context)
            self.assertIsInstance(test_runner, TestRunner)

    def test_module_loading_working_at_all(self):
        """
        Tests if the dynamic loading of the modules from the test folder works at all. That does not imply that it
        tests for the correct amount of tests.
        """
        with TestContext(config=self.config) as test_context:
            test_runner = TestRunner(test_context)
            test_runner.load()

            self.assertNotEqual(0, len(test_runner.modules))
            for module in test_runner.modules.values():
                self.assertTrue(inspect.ismodule(module))

    def test_test_loading_working_at_all(self):
        """
        Tests if any tests have been loaded from the test modules and also tests if these are only valid subclasses
        of the AbstractTest base class.
        """
        with TestContext(config=self.config) as test_context:
            test_runner = TestRunner(test_context)
            test_runner.load()

            self.assertNotEqual(0, len(test_runner.tests))
            for test in test_runner.tests.values():
                self.assertTrue(inspect.isclass(test))
                self.assertTrue(issubclass(test, AbstractTest))

    def test_run_mock_test(self):
        """
        Tests if the "mock" test is being run correctly
        """
        with TestContext(config=self.config) as test_context:
            test_runner = TestRunner(test_context)
            test_runner.load()

            test_runner.run_test('mock')
            test_report = TestReport(test_context)
            self.assertIsInstance(test_report, TestReport)
            self.assertEqual(1, test_report.test_count)
            self.assertEqual(1, test_report.successful_count)
            self.assertEqual(0, test_report.error_count)

    def test_run_mock_suite(self):
        """
        Tests if the "mock" test suite is being run correctly
        """
        with TestContext(config=self.config) as test_context:
            test_runner = TestRunner(test_context)
            test_runner.load()

            test_runner.run_suite('mock')
            test_report = TestReport(test_context)
            self.assertIsInstance(test_report, TestReport)
            self.assertEqual(1, test_report.test_count)
            self.assertEqual(1, test_report.successful_count)
            self.assertEqual(0, test_report.error_count)


class TestTestReport(UfotestTestCase):

    def test_construction(self):
        """
        If an instance can be constructed without errors
        """
        with TestContext(config=self.config) as test_context:
            # To be able to actually construct a test report, we first need to actually run at least one test!
            test_runner = TestRunner(test_context)
            test_runner.load()
            test_runner.run_test('mock')

            test_report = TestReport(test_context)
            self.assertIsInstance(test_report, TestReport)

    def test_construction_with_unfinished_context(self):
        """
        The test context cannot be passed to the test report right away, it usually first needs to run some actual
        tests, which will set some important properties that are needed by the test context.
        """
        with TestContext(config=self.config) as test_context:
            with self.assertRaises(AssertionError):
                test_report = TestReport(test_context)


class TestAssertionTestResult(UfotestTestCase):

    def test_construction(self):
        """
        If the construction of an instance generally works
        """
        test_result = AssertionTestResult()
        self.assertIsInstance(test_result, AssertionTestResult)

    def test_adding_assertions(self):
        """
        If the adding of new assertions works and causes the object to update internal state properly
        """
        test_result = AssertionTestResult()

        test_result.assert_equal(1, 1)
        test_result.assert_equal(2, 2)

        self.assertEqual(2, len(test_result.assertions))
        self.assertEqual(0, test_result.error_count)
        self.assertEqual(0, test_result.exit_code)

    def test_adding_false_assertions(self):
        """
        If adding a false assertion gets registered correctly
        """
        test_result = AssertionTestResult()

        test_result.assert_equal(1, 1)
        test_result.assert_equal(1, 2)

        self.assertEqual(2, len(test_result.assertions))
        self.assertEqual(1, test_result.error_count)
        self.assertNotEqual(0, test_result.exit_code)

    def test_markdown_conversion(self):
        """
        If the conversion to markdown works
        """
        test_result = AssertionTestResult()

        test_result.assert_equal(1, 1)
        test_result.assert_equal(1, 2)
        test_result.assert_equal("hello", "bello")

        markdown_string = test_result.to_markdown()
        print(markdown_string)

        self.assertIsInstance(markdown_string, str)
        self.assertIn('NOT EQUAL', markdown_string)

    def test_pci_read_assertion(self):
        """
        if the custom assertion for the output of a pci_read function works properly
        """
        test_result = AssertionTestResult()

        correct_pci_read = '9010:  000fdf00'
        test_result.assert_pci_read_ok(correct_pci_read)

        error_pci_read = '9010:  000bef00'
        test_result.assert_pci_read_ok(error_pci_read)

        # Now it needs to have one correct assertion and one error!
        self.assertEqual(2, len(test_result.assertions))
        self.assertEqual(1, test_result.error_count)
