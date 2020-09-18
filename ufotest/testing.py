import os
import inspect
import time
import datetime
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Dict, List, Type

from ufotest.config import PATH, Config
from ufotest.util import check_path, dynamic_import, create_folder


class TestRunner(object):

    # STATIC LOGGER CONFIG

    def __init__(self, config: Config = Config()):
        self.config = config
        self.modules = {}
        self.tests = {}

        self.archive_folder_path = self.config.get_archive_folder()
        self.start_time = datetime.datetime.now()
        self.folder_path = os.path.join(self.archive_folder_path, self.start_time.strftime('%d_%m_%Y__%H_%M_%S'))
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
        return test_report

    def run_suite(self, suite_name: str):
        test_suite = self.load_test_suite(suite_name)
        results = test_suite.execute_all()

        test_report = TestReport(results, TestMetadata())
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


class AbstractTestResult(ABC):

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

    @abstractmethod
    def to_string(self) -> str:
        raise NotImplementedError()


class MessageTestResult(AbstractTestResult):

    def __init__(self, exit_code: int, message: str):
        AbstractTestResult.__init__(self, exit_code)
        self.message = message

    def to_string(self) -> str:
        return self.message


class AbstractTest(ABC):

    name = "abstract"

    def __init__(self, test_runner: TestRunner):
        self.test_runner = test_runner
        self.logger = self.test_runner.logger
        self.config = self.test_runner.config

    def execute(self) -> AbstractTestResult:
        start_datetime = datetime.datetime.now()
        test_result = self.run()
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


# TODO: Add some meta data.
class TestMetadata(object):

    def __init__(self):
        pass


class TestReport(object):

    def __init__(self, test_results: Dict[str, AbstractTestResult], test_meta: TestMetadata):
        self.results = test_results
        self.meta = test_meta

    def to_markdown(self):
        string = '# Test Report \n\n'
        string += '## Individual Test Outputs\n\n'

        for name, result in self.results.items():
            string += '### {name} ({status})\n'.format(
                name=name,
                status=result.get_status()
            )
            string += result.to_string()
            string += '\n'

        return string

    def to_string(self):
        return self.to_markdown()
