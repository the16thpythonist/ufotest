from ufotest.testing import AbstractTest, TestRunner, MessageTestResult


class MockTest(AbstractTest):

    name = "mock"

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):
        return MessageTestResult(0, 'Hello World')
