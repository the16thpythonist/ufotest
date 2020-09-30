from ufotest.testing import AbstractTest, TestRunner
from ufotest.testing import MessageTestResult


class AcquireSingleFrame(AbstractTest):

    name = 'single_frame'

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):
        return MessageTestResult(0, 'to be implemented')
