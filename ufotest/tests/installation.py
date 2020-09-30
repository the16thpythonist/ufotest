from ufotest.testing import AbstractTest, TestRunner
from ufotest.testing import MessageTestResult


class LibucaInstalledTest(AbstractTest):

    name = 'libuca_installed'

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):
        return MessageTestResult(0, 'to be implemented')
