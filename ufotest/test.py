import os
from abc import ABC, abstractmethod

from ufotest.config import PATH, CONFIG

STATIC_TESTS_FOLDER = os.path.join(PATH, 'tests')
DYNAMIC_TESTS_FOLDER = CONFIG['tests']['folder']


class TestRunner(object):

    test_folders = [
        STATIC_TESTS_FOLDER,
        DYNAMIC_TESTS_FOLDER
    ]

    def __init__(self):
        self.config = CONFIG
        self.tests = {}

    def load(self):
        for test_folder in self.test_folders:
            # Dynamically import all the modules in this folder and then use inspect to extract all the classes.
            pass

    def _load_test_folder(self, test_folder: str):
        pass

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
