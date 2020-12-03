import os
import re
import inspect
import platform
import datetime
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Dict, List, Type, Any

from ufotest.config import PATH, Config
from ufotest.util import (markdown_to_html,
                          dynamic_import,
                          create_folder,
                          get_template,
                          get_version,
                          AbstractRichOutput)


class TestRunner(object):

    # STATIC LOGGER CONFIG

    def __init__(self, config: Config = Config()):
        self.config = config
        self.modules = {}
        self.tests = {}

        self.archive_folder_path = self.config.get_archive_path()
        # So here I have added a separate step/attribute, which adds the pure folder name string to be saved separately
        # instead of directly assembling it into the absolute path. This value will be needed for example to
        # construct the url to the file server which can be used to view the reports online.
        self.start_time = datetime.datetime.now()
        self.name = self.start_time.strftime('test_run_%d_%m_%Y__%H_%M_%S')
        self.folder_path = os.path.join(
            self.archive_folder_path,
            self.name
        )

        create_folder(self.folder_path)

        # Initializing the logging
        self.logger = logging.Logger('TestRunner')

        # "test_folders" was originally a class attribute and the static and dynamic folder paths where global
        # variables for this folder, but then during testing I realized that CONFIG might not be loaded at that point
        # thus producing a key error for "tests"...
        static_test_folder = os.path.join(PATH, 'tests')
        dynamic_test_folder = self.config['tests']['folder']
        self.test_folders = [
            static_test_folder,
            dynamic_test_folder
        ]

    def load(self):
        for test_folder in self.test_folders:
            # Dynamically import all the modules in this folder and then use inspect to extract all the classes.
            self.load_test_folder_modules(test_folder)

        # Loading the tests from the modules
        for module_name, module in self.modules.items():
            self.load_tests_from_module(module)

    def run_test(self, test_name: str):
        assert test_name in self.tests.keys(), 'Test with the name "{}" does not exists!'.format(test_name)

        test_class = self.tests[test_name]
        test = test_class(self)
        result = test.execute()

        test_report = TestReport({test_name: result}, TestMetadata())
        test_report.save(self.folder_path)
        return test_report

    def run_suite(self, suite_name: str):
        test_suite = self.load_test_suite(suite_name)
        results = test_suite.execute_all()

        test_report = TestReport(results, TestMetadata())
        test_report.save(self.folder_path)
        return test_report

    # HELPER METHODS
    # --------------

    def load_test_folder_modules(self, test_folder: str):
        # First check if this test folder actually exists
        # assert check_path(test_folder, is_dir=True), 'The given test folder path does not refer to an existing folder!'

        # Dynamically import all the modules in this folder and then use inspect to extract all the classes.
        for root, dirs, files in os.walk(test_folder):
            for file in files:
                file_path = os.path.join(root, file)
                module_name = file.replace('.py', '')

                module = dynamic_import(module_name, file_path)
                self.modules[module_name] = module

            break

    def load_tests_from_module(self, module):
        for name, cls in inspect.getmembers(module, inspect.isclass):
            if issubclass(cls, AbstractTest) and name != 'AbstractTest':
                self.tests[cls.name] = cls

    def load_test_suite(self, suite_name: str):
        assert suite_name in self.config['tests']['suites'].keys(), 'The test suite {} is not known!'.format(suite_name)

        test_names = self.config['tests']['suites'][suite_name]
        tests = [self.tests[test_name] for test_name in test_names]

        test_suite = TestSuite(self, tests, suite_name)
        return test_suite


class AbstractTestResult(AbstractRichOutput, ABC):

    def __init__(self, exit_code: int):
        self.exit_code = exit_code
        self.start_datetime = None
        self.end_datetime = None

    def get_status(self):
        if self.passing:
            return 'passing'
        else:
            return 'error'

    @property
    def passing(self) -> bool:
        return self.exit_code == 0

    @property
    def execution_time(self) -> float:
        time_delta: datetime.timedelta = self.end_datetime - self.start_datetime
        return time_delta.total_seconds()


class MessageTestResult(AbstractTestResult):

    def __init__(self, exit_code: int, message: str):
        AbstractTestResult.__init__(self, exit_code)
        self.message = message

    # IMPLEMENT "AbstractRichOutput"
    # ------------------------------

    def to_string(self) -> str:
        return self.message

    def to_markdown(self) -> str:
        return self.message

    def to_latex(self) -> str:
        return self.message


class AssertionTestResult(AbstractTestResult):

    def __init__(self, detailed: bool = False):
        AbstractTestResult.__init__(self, 0)
        self.detailed = detailed

        self.assertions = []
        self.error_count = 0

    # ASSERTION IMPLEMENTATIONS
    # -------------------------

    def assert_equal(self, expected: Any, actual: Any):
        result = (expected == actual)

        self.assertion_result(
            result,
            '(+) EQUAL "{}" == "{}"'.format(expected, actual),
            '(-) NOT EQUAL "{}" != "{}"'.format(expected, actual)
        )

    def assert_pci_read_ok(self, read_result: str):
        match = re.match('.*:[ ]*000f.*', read_result)
        result = not bool(match)

        self.assertion_result(
            result,
            '(+) PCI READ "{}" IS FINE'.format(read_result),
            '(-) PCI READ "{}" CONTAINS ERROR!'.format(read_result)
        )

    # HELPER METHODS
    # --------------

    def assertion_result(self, result: bool, success_message: str, error_message: str):
        if result:
            self.assertions.append((result, success_message))
        else:
            self.exit_code = 1
            self.error_count += 1
            self.assertions.append((result, error_message))

    # IMPLEMENT "AbstractRichOutput"
    # ------------------------------

    def to_string(self) -> str:
        pass

    def to_markdown(self) -> str:
        template = get_template('assertion_test_result.md')
        return template.render(
            exit_code=self.exit_code,
            assertions=self.assertions,
            detailed=self.detailed,
            error_count=self.error_count
        )

    def to_latex(self) -> str:
        pass


class CombinedTestResult(AbstractTestResult):

    def __init__(self, *test_results):
        self.test_results = test_results
        self.exit_codes = [test_result.exit_code for test_result in self.test_results]
        exit_code = 1 if 1 in self.exit_codes else 0
        AbstractTestResult.__init__(self, exit_code)

    # IMPLEMENT "AbstractRichOutput"
    # ------------------------------

    def to_string(self) -> str:
        return '\n\n'.join(test_result.to_string() for test_result in self.test_results)

    def to_markdown(self) -> str:
        return '\n\n'.join(test_result.to_markdown() for test_result in self.test_results)

    def to_latex(self) -> str:
        return '\\\\ \\\\ \n'.join(test_result.to_latex() for test_result in self.test_results)



class AbstractTest(ABC):

    name = "abstract"

    def __init__(self, test_runner: TestRunner):
        self.test_runner = test_runner
        self.logger = self.test_runner.logger
        self.config = self.test_runner.config

    def execute(self) -> AbstractTestResult:
        start_datetime = datetime.datetime.now()
        try:
            test_result = self.run()
        except Exception as e:
            test_result = MessageTestResult(1, 'Test Execution failed with error "{}"'.format(str(e)))
        end_datetime = datetime.datetime.now()

        test_result.start_datetime = start_datetime
        test_result.end_start_time = end_datetime
        return test_result

    def get_name(self):
        return self.name

    @abstractmethod
    def run(self) -> AbstractTestResult:
        raise NotImplementedError()


class TestSuite(object):

    def __init__(self, test_runner: TestRunner, tests: List[Type[AbstractTest]], name: str):
        self.test_runner = test_runner
        self.tests = tests
        self.suite_name = name

        self.results = {}

    def execute_all(self):
        for test_class in self.tests:
            test = test_class(self.test_runner)
            self.results[test.name] = test.execute()

        return self.results

    def get_name(self):
        return 'suite:{}'.format(self.suite_name)


class TestMetadata(AbstractRichOutput):

    def __init__(self, config: Config = Config()):
        self.config = config

        self.date_time = datetime.datetime.now()
        self.platform = platform.platform()
        self.version = get_version()

    def get_date(self):
        date_format = self.config.get_date_format()
        return self.date_time.strftime(date_format)

    def get_time(self):
        time_format = self.config.get_time_format()
        return self.date_time.strftime(time_format)

    # IMPLEMENT "AbstractRichOutput"
    # ------------------------------

    def to_string(self) -> str:
        return ""

    def to_markdown(self) -> str:
        template = get_template('test_meta.md')
        return template.render(
            date=self.get_date(),
            time=self.get_time(),
            platform=self.platform,
            config=self.config,
            version=self.version
        )

    def to_latex(self) -> str:
        return ""


class TestReport(AbstractRichOutput):

    def __init__(self, test_results: Dict[str, AbstractTestResult], test_meta: TestMetadata):
        self.results = test_results
        self.meta = test_meta

        # COMPUTED ATTRIBUTES
        self.test_count = len(self.results)
        self.passing_count = sum(1 for result in self.results.values() if result.passing)
        self.error_count = sum(1 for result in self.results.values() if not result.passing)
        self.success_ratio = round(self.passing_count / self.test_count, ndigits=5)

    def save(self, path: str):
        """Saves the test report into the folder with the given *path*

        At the current time, the test report will be saved as both a markdown file and an html file which was generated
        from the markdown file. Using a simple web server to serve the archives folder, the test report in the form of
        this html file could then be viewed using a web browser.

        All generated files will have the same base name 'report' but different file endings dependings based on their
        type.

        :param path: the path of the folder into which to save the report
        """
        # Save the report as an markdown file
        markdown_path = os.path.join(path, 'report.md')
        with open(markdown_path, mode='w+') as file:
            file.write(self.to_markdown())

        # Converting the file to a simple html file
        html_path = os.path.join(path, 'report.html')
        markdown_to_html(markdown_path, html_path, [])


    # HELPER METHODS
    # --------------

    def get_file_name(self):
        return

    # IMPLEMENT "AbstractRichOutput"
    # ------------------------------

    def to_string(self) -> str:
        return self.to_markdown()

    def to_markdown(self) -> str:
        template = get_template('test_report.md')
        return template.render(
            report=self,
            meta=self.meta,
            results=self.results
        )

    def to_latex(self) -> str:
        return ""
