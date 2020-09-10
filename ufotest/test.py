import os
from abc import ABC, abstractmethod

from ufotest.config import PATH, CONFIG
from ufotest.util import check_path, dynamic_import

STATIC_TESTS_FOLDER = os.path.join(PATH, 'tests')
DYNAMIC_TESTS_FOLDER = CONFIG['tests']['folder']


class TestRunner(object):

    test_folders = [
        STATIC_TESTS_FOLDER,
        DYNAMIC_TESTS_FOLDER
    ]

    def __init__(self):
        self.config = CONFIG
        self.modules = {}
        self.tests = {}

    def load(self):
        for test_folder in self.test_folders:
            # Dynamically import all the modules in this folder and then use inspect to extract all the classes.
            pass

    def _load_test_folder_modules(self, test_folder: str):
        # First check if this test folder actually exists
        path_exists = check_path(test_folder, is_dir=True)

        # Dynamically import all the modules in this folder and then use inspect to extract all the classes.
        for root, dirs, files in os.walk(test_folder):
            for file in files:
                file_path = os.path.join(root, file)
                module_name = file.replace('.py', '')

                module = dynamic_import(module_name, file_path)
                self.modules[module_name] = module

            break

    def run_test(self):
        pass

    def run_suite(self):
        pass


class AbstractClass(ABC):

    name = "abstract"

    def __init__(self, test_runner: TestRunner):
        self.test_runner = test_runner

    @abstractmethod
    def run(self):
        raise NotImplementedError()

    def get_name(self):
        return self.name
