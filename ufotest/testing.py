from __future__ import annotations
import os
import re
import json
import inspect
import platform
import datetime
import logging
from abc import ABC, abstractmethod
from typing import Tuple, Dict, List, Type, Any, Optional
from contextlib import AbstractContextManager

import matplotlib.pyplot as plt

from ufotest.config import PATH, Config, get_path
from ufotest.util import (markdown_to_html,
                          dynamic_import,
                          create_folder,
                          get_template,
                          get_version,
                          AbstractRichOutput,
                          random_string)
from ufotest.camera import UfoCamera
from ufotest.util import csubtitle, cprint, cresult


class TestContext(AbstractContextManager):
    """
    Represents the context for the execution of a test run.

    This is the reasoning behind the design choice: The original system was that there was a test runner which would
    then produce a test report. Now the problem is, that the construction of a test report needed *a lot* of parameters.
    Too many parameters to funnel through the constructor. So the alternative would have been to use a wrapper object
    which contains all the important data. That is what this class does. But it does more: In fact this test context
    class wraps all the information which is required by the test runner. During the tests, the test runner writes
    all the relevant results into the context object. Afterwards it gets passed to the constructor of the test report.

    **EXAMPLE**

    Since this is a context manager, it should be used with the "with" syntax, where both the test runner and the
    test report are handled within the context:

    .. code-block:: python

        with TestContext() as test_context:
            test_runner = TestRunner(test_context)
            # Run the tests.
            test_report = TestReport(test_context)

    :ivar results: A dictionary whose keys are the string (unique) names of the individual test cases and the values
        are the test result objects, which those tests have produced as results.
    """
    ARCHIVE_FOLDER_FORMAT = 'test_run_%d_%m_%Y__%H_%M_%S'

    def __init__(self, *additional_test_folders, config=Config()):
        # constructed attributes
        self.additional_test_folders = additional_test_folders

        # calculated attributes
        self.config = config
        self.archive_folder_path = self.config.get_archive_path()
        self.creation_datetime = datetime.datetime.now()
        self.folder_name = self.creation_datetime.strftime(self.ARCHIVE_FOLDER_FORMAT)
        self.folder_path = os.path.join(self.archive_folder_path, self.folder_name)
        # I have added this, because I realized, that the test result objects have to access this value for
        # correctly creating html links to additional resources saved within the test's folder.
        self.relative_url = os.path.join('archive', self.folder_name)
        self.folder_url = self.config.url(self.relative_url)
        # This general information, about the platform and version on which the test was executed, was previously
        # encapsulated by the TestMetadata class. But now all of this information os combined into the context. This
        # is because the responsibility of the context essentially is to provide such "contextual" information
        self.platform = platform.platform()
        self.version = get_version()  # the version of this software

        static_test_folder = os.path.join(PATH, 'tests')
        dynamic_test_folder = self.config.get_test_folder()
        self.test_folders = [
            static_test_folder,
            dynamic_test_folder,
            *self.additional_test_folders
        ]

        # -- The logging is supposed to be saved into a file within the correct archive folder for this test execution.
        self.logger = logging.Logger('TestContext')
        self.logger.setLevel(logging.DEBUG)
        self.logger_path = os.path.join(self.folder_path, 'context.log')

        # Non initialized attributes
        # So the way this context object works is that a new context object is being created for every testing process
        # the instance of this class will ultimately be passed to the TestRunner object which actually executes the
        # the test process. The responsibility of the context is to provide all the information which is required to
        # specify an individual process. But the responsibility is more than that. The context will also save the
        # results of the test runner. It does that to then later be passed to a TestReport. So for this purpose it has
        # to have some empty properties which are only later being set by the TestRunner.
        self.start_datetime: Optional[datetime.datetime] = None
        self.end_datetime: Optional[datetime.datetime] = None
        self.results: Dict[str, AbstractTestResult] = {}
        self.tests = {}
        self.name: Optional[str] = None

    def start(self, name: str):
        """
        Sets the start time for the test run.
        """
        self.name = name
        self.start_datetime = datetime.datetime.now()

    def end(self, name: str):
        """
        Sets the end time for the test run
        """
        self.end_datetime = datetime.datetime.now()

    def get_path(self, *sub_paths):
        return get_path('archive', self.folder_name, *sub_paths)

    # -- AbstractContextManager --

    def __enter__(self) -> TestContext:
        # ~ CREATING THE ARCHIVE FOLDER
        create_folder(self.folder_path)

        # ~ INIT LOGGING
        logger_handler = logging.FileHandler(self.logger_path, mode='w', encoding=None, delay=False)
        self.logger.addHandler(logger_handler)

        # ~ LOGGING START MESSAGE
        self.logger.debug('Enter test context')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # ~ LOGGING END MESSAGE
        self.logger.debug('Exit test context')


class TestRunner(object):
    """
    The TestRunner manages the loading and the execution of test cases.

    **EXAMPLE**

    A new test runner has to be instantiated with a reference to a valid TestContext object. After creating a new test
    runner, the "load" method has to be called. This will trigger the dynamic import of all python modules within the
    valid test folders (defined in the test context). From those modules all test cases (all subclasses of AbstractTest)
    are loaded as available tests. Only then can a test case or a test suite be invoked.

    .. code-block:: python

        with TestContext() as test_context:
            test_runner = TestRunner(test_context)
            test_runner.load()

            test_runner.run_test()
            test_runner.run_suite()

    **EXECUTION OF A TEST**

    Through the "load" method all tests are part of the internal self.test dict, where their string names are the
    keys and the classes are the values. When a test is supposed to be executed, a new instance of that class is being
    created. The only thing, which is passed to the constructor of each test case is the test runner instance itself.
    This test runner contains all other important references such as the config singleton, the test context and an
    instance of th camera interface. Finally, the "run" method of this test is invoked and the resulting TestResult
    object is added to the TestReport instance. This test report is not returned but instead added to the context from
    where it can be accessed and further processed.
    """

    def __init__(self, test_context: TestContext):
        # constructed attributes
        self.context = test_context

        # derived attributes from context
        self.config = self.context.config
        self.logger = self.context.logger

        self.tests = {}
        self.modules = {}

        # 1.3.0
        # The whole system of interfacing with the camera has been reworked to the point where all interaction should
        # be funneled through a single camera instance of a class which implements the "AbstractCamera" interface.
        # This camera instance will be the most important value to which each test case will have to have access to.
        self.camera_class = self.config.pm.apply_filter('camera_class', UfoCamera)
        self.camera = self.camera_class(self.config)
        self.camera.set_up()

    def load_modules(self) -> None:
        """
        This method loads all the test modules (not test cases yet) by iterating all the test folders which are defined
        in the test context and importing all modules from these folders. These modules are then stored in the internal
        self.modules dict, where the key is name of the module and the value the reference to the imported module.

        :return: void
        """
        for test_folder in self.context.test_folders:
            self.load_module_from_test_folder(test_folder)

    def load_module_from_test_folder(self, test_folder: str) -> None:
        """
        Given the string path of a *test_folder* this method dynamically imports all the python modules in this folder
        (interpreting them as python modules containing UfoTest test cases) and saved the reference to those module and
        thus all their contents in the internal self.modules dict.

        :param test_folder: The string absolute path to a folder which contains python modules which in turn contain
            classes that define UfoTest test cases.

        :return: void
        """
        # All the modules within the test folder have to be dynamically imported to access the TestCase classes within
        # them. This loop iterates all the python modules in the given folder path and then adds the dynamic import to
        # the "modules" dict.
        counter = 0
        for root, dirs, files in os.walk(test_folder):
            for file_name in (file_name for file_name in files if '.py' in file_name):
                file_path = os.path.join(root, file_name)
                module_name = file_name.replace('.py', '')

                module = dynamic_import(module_name, file_path)
                self.modules[module_name] = module
                counter += 1

            # We break here because we dont really want to iterate the whole tree structure. We really only wanted all
            # the modules from the top most folder.
            break

        self.logger.info('loaded {} test modules from folder: {}'.format(counter, test_folder))

    def load_tests(self) -> None:
        """
        Based on the modules already imported into the internal self.modules dict, this method will iterate all of
        those methods extract all UfoTest test cases and store them in the internal self.tests dict, where the keys are
        defined by the test cases static "name" attribute and the values are the according classes.py

        :return: void
        """
        for module_name, module in self.modules.items():
            self.load_tests_from_module(module)

        self.context.tests = self.tests

    def load_tests_from_module(self, module: Any) -> None:
        """
        Given the reference to an imported module *module* this method will extract all UfoTest test case classes from
        this module and store them in the internal self.tests dict. A class within the module will only be
        interpreted as a test case if it directly inherits from "AbstractTest".

        Note that this method can only be called when the module have previously already been imported and thus the
        self.modules dict is already populated.

        :param module: A reference to the dynamically imported module object.

        :return: void
        """
        counter = 1
        # Now we have a dynamically imported module and want to extract the classes from it in a similarly dynamic
        # fashion. Luckily, the "inspect" module provides exactly such functionality.
        # INFO: The second argument to of the "get_members" function takes a function, which essentially acts as a
        # filter for which member exactly to include in the final list.
        for name, cls in inspect.getmembers(module, inspect.isclass):
            # We only want to use those classes, which are subclasses of the AbstractTest base class. This way we are
            # excluding all the possible helper classes which are possibly within those test modules.
            if issubclass(cls, AbstractTest):
                # Now these test modules obviously have to import the abstract base class to make the actual test
                # inherit from them. This is a problem because the previous if statement would also accept these
                # imported duplicates of the base class itself.
                if name != 'AbstractTest':
                    # NOTE: here we are not using the class name as the key of the dict, but the class "property"
                    # "name" which has to be defined by every test case.
                    self.tests[cls.name] = cls
                    counter += 1

        self.logger.info('imported {} tests from the module: {}'.format(counter, module.__name__))

    def load(self) -> None:
        """
        Dynamically loads all the test cases from the folder locations given in the test context which was passed to
        this runner. Only after this method was called, test cases are actually known to the runner and can be executed

        :return: void
        """
        self.load_modules()
        self.load_tests()

        self.logger.info('All tests loaded')

    def get_test_suite(self, suite_name: str) -> TestSuite:
        """
        Return a TestSuite wrapper object which represents the suite identified by the given *suite_name*.

        :param str suite_name: The unique string name, which identifies the suite

        :raises KeyError: If the given suite name does not exist

        :return TestSuite: The test suite wrapper object
        """
        suites = self.config.get_test_suites()

        if suite_name not in suites.keys():
            raise KeyError((f'You are attempting to run a test suite with the name "{suite_name}", but a suite with '
                            f'this name is not known to the system. Please check for eventual typos!'))

        test_names = suites[suite_name]
        # suite_tests = [test for test_name, test in self.tests.items() if test_name in test_names]
        suite_tests = [self.tests[test_name] for test_name in test_names]
        test_suite = TestSuite(self, suite_tests, suite_name)

        return test_suite

    def run_test(self, test_name: str) -> None:
        """
        Executes a single test case which is identified by *test_name*.

        :param str test_name: The unique string name which identifies the test case

        :return: void
        """
        if test_name not in self.tests.keys():
            raise KeyError((f'You are attempting to run a test case with the name {test_name}, but a test case '
                            f'with this name does not exist. Please check for typo, or if the test case is placed in a '
                            f'valid test folder!'))

        self.context.start(test_name)
        # A AbstractTest subclass can be instantiated by passing a single argument to the constructor and that is the
        # the test runner object itself.
        test_class = self.tests[test_name]
        test_instance: AbstractTest = test_class(self)
        test_result: AbstractTestResult = test_instance.execute()

        self.context.results[test_name] = test_result
        self.context.end(test_name)

    def run_suite(self, suite_name: str):
        """
        Executes multiple tests which are part of the suite identified by *suite_name*

        :return: void
        """
        self.context.start(suite_name)
        test_suite = self.get_test_suite(suite_name)

        results = test_suite.execute_all()
        self.context.results.update(results)
        self.context.end(suite_name)


class _TestRunner(object):
    """
    :deprecated:
    """

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


class ImageTestResult(AbstractTestResult):
    """Represents an image as the result of a test case.

    **Path issues**

    So ultimately this object is supposed to be converted into a MARKDOWN and a HTML snippet. This creates a little bit
    of an issue with the fact that the very purpose of this class: It relies on an external resource (the image).
    Passing the path of this image is fine for the MD version. But for the HTML file just having the absolute file
    system path does not solve anything. For this we would need to know the equivalent URL path.

    This is why the constructor needs the additional argument "url_base". It is supposed to define the base url at
    which this image asset can be found.

    **Example**

    THe most likely use case of this result type is the following: A test case generates some sort of image. This can
    be either an info graphic or just simply the image of a camera frame. It will then save this image into the test
    folder (which it knows from the test context). The test context then provides the base url like so:

    .. code-block:: python
        # "run" of "ExampleTest"

        file_name = 'image.png'
        file_path = os.path.join(self.context.folder_path, file_name)

        result = ImageTestResult(0, file_path, self.context.folder_url)
    """

    def __init__(self, exit_code: int, file_path: str, description: str, url_base: str = '/static'):
        AbstractTestResult.__init__(self, exit_code)

        self.file_path = file_path
        self.url_base = url_base
        self.description = description
        self.config = Config()

        # The file name is important here because ultimately this object also has to be converted into an HTML file and
        # within an html file the file system path is not so important. More important is the URL path. So to make this
        # work at all.
        self.file_name = os.path.basename(self.file_path)
        self.file_url = os.path.join(url_base, self.file_name)

    # == AbstractRichOutput

    def to_string(self) -> str:
        return 'Image "{}" ({}): {}'.format(self.file_name, self.file_path, self.description)

    def to_markdown(self) -> str:
        return '[{}]({})\n\n{}'.format(self.file_name, self.file_path, self.description)

    def to_latex(self) -> str:
        return ''

    def to_html(self) -> str:
        return '\n'.join([
            '<div class="image-test-result">',
            '<img src="{}" alt="{}">'.format(self.file_url, self.file_name),
            '<p>',
            '{}'.format(self.description),
            '</p>',
            '</div>'
        ])


class FigureTestResult(ImageTestResult):

    def __init__(self, exit_code: int, test_context: TestContext, figure: plt.Figure, description: str):
        self.test_context = test_context

        # ~ SAVE IMAGE INTO TEST FOLDER
        self.figure_name = f'{random_string(10, additional_letters="")}.png'
        self.figure_path = self.test_context.get_path(self.figure_name)
        # https://stackoverflow.com/questions/11837979/removing-white-space-around-a-saved-image-in-matplotlib
        # The parameters "bbox_inches" and "pad_inches" are supposed to reduce the whitespace around the plot.
        figure.savefig(self.figure_path, bbox_inches='tight', pad_inches=0.0)

        ImageTestResult.__init__(self, exit_code, self.figure_path, description, url_base=self.test_context.folder_url)


class DictTestResult(AbstractTestResult):

    def __init__(self, exit_code: int, data: dict, message: str = ''):
        AbstractTestResult.__init__(self, exit_code)
        self.data = data
        self.message = message

    # == AbstractRichOutput

    def to_string(self) -> str:
        row_format = '{:>20}{:>20}'
        rows = [row_format.format(str(key), str(value)) for key, value in self.data.items()]
        return '\n'.join(rows)

    def to_html(self) -> str:
        row_format = '<div class="row"><div class="key">{}</div><div class="value">{}</div></div>'
        rows = [row_format.format(str(key), str(value)) for key, value in self.data.items()]
        return '\n'.join([
            '<div class="dict-test-result">',
            '{}'.format('\n'.join(rows)),
            '</div>'
        ])

    def to_latex(self) -> str:
        return ''

    def to_markdown(self) -> str:
        row_format = '- *'
        rows = [row_format.format(str(key), str(value)) for key, value in self.data.items()]
        return '\n'.join(rows)


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

    def to_html(self) -> str:
        return '<div class="message-test-result">{}</div>'.format(self.message)


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

    def to_html(self) -> str:
        return ""


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

    def to_html(self) -> str:
        return '\n\n'.join(test_result.to_html() for test_result in self.test_results)


class AbstractTest(ABC):

    name = "abstract"
    description = ""

    def __init__(self, test_runner: TestRunner):
        self.test_runner = test_runner
        self.logger = self.test_runner.logger
        self.config = self.test_runner.config
        self.context = self.test_runner.context
        self.camera = self.test_runner.camera

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
        self.config = Config()

        self.results = {}

    def execute_all(self):
        """
        Executes all all test cases which are part of this suite.
        """
        for test_class in self.tests:
            test = test_class(self.test_runner)
            csubtitle(f'TEST: {test.name}')
            self.results[test.name] = test.execute()
            cresult(f'{test.name} DONE')

        return self.results

    def get_name(self):
        return 'suite:{}'.format(self.suite_name)


class TestMetadata(AbstractRichOutput):
    """
    :deprecated:
    """
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

    def to_html(self) -> str:
        return ""


class TestReport(AbstractRichOutput):

    DATETIME_FORMAT = '%d.%m.%Y %H:%M'

    def __init__(self, test_context: TestContext):
        assert test_context.start_datetime is not None, \
            "The test context has to have been started before attempting to construct a test report from it"

        assert test_context.end_datetime is not None, \
            "The test context has to have been ended before attempting to construct a test report from it"

        assert len(test_context.results) > 0, \
            "The test context has to have at least on test (!= 0) to construct a test report from it"

        # constructed attributes
        self.context = test_context

        # derived attributes from context
        self.config = self.context.config
        self.platform = str(self.context.platform)
        self.version = self.context.version
        self.results = self.context.results
        self.name = self.context.name
        self.folder_name = self.context.folder_name
        self.folder_path = self.context.folder_path
        self.start = self.context.start_datetime.strftime(self.DATETIME_FORMAT)
        self.end = self.context.end_datetime.strftime(self.DATETIME_FORMAT)
        self.duration = int((self.context.end_datetime - self.context.start_datetime).seconds / 60)
        self.tests = self.context.tests

        # derived attributes from config
        self.repository_url = self.config.get_repository_url()
        self.documentation_url = self.config.get_documentation_url()
        self.sensor = "{} x {} pixels".format(self.config.get_sensor_height(), self.config.get_sensor_width())

        # calculated attributes
        self.test_count = len(self.results)
        self.successful_results = {test_name: result for test_name, result in self.results.items() if result.passing}
        self.successful_count = len(self.successful_results)
        self.error_count = self.test_count - self.successful_count
        self.success_ratio = round(self.successful_count / self.test_count, 2)

    def save(self, folder_path: str):
        # 1 -- SAVE MARKDOWN FILE
        markdown_path = os.path.join(folder_path, 'report.md')
        with open(markdown_path, mode='w') as markdown_file:
            markdown_file.write(self.to_markdown())

        # 2 -- SAVE HTML FILE
        html_path = os.path.join(folder_path, 'report.html')
        with open(html_path, mode='w') as html_file:
            html_file.write(self.to_html())

        # 3 -- SAVE JSON FILE
        json_path = os.path.join(folder_path, 'report.json')
        with open(json_path, mode='w') as json_file:
            json_file.write(self.to_json())

    # == UTILITY FUNCTIONS

    def get_test_description(self, test_name: str) -> str:
        return self.tests[test_name].description

    # == JSON SAVING

    def to_dict(self) -> dict:
        return {
            'platform':             self.platform,
            'version':              self.version,
            'sensor':               self.sensor,
            'name':                 self.name,
            'folder_name':          self.folder_name,
            'folder_path':          self.folder_path,
            'start':                self.start,
            'start_iso':            self.context.start_datetime.isoformat(),
            'end':                  self.end,
            'end_iso':              self.context.end_datetime.isoformat(),
            'duration':             self.duration,
            'test_count':           self.test_count,
            'successful_count':     self.successful_count,
            'success_ratio':        self.success_ratio
        }

    def to_json(self) -> str:
        data = self.to_dict()
        return json.dumps(data, sort_keys=True, indent=4)

    # == ABSTRACT RICH OUTPUT

    def to_html(self) -> str:
        template = get_template('test_report.html')
        return template.render({'report': self})

    def to_markdown(self) -> str:
        template = get_template('test_report.md')
        return template.render({'report': self})

    def to_string(self) -> str:
        # Not important right now
        pass

    def to_latex(self) -> str:
        # Not important right now
        pass


class _TestReport(AbstractRichOutput):
    """
    :deprecated:
    """
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

    def to_html(self) -> str:
        return ""

