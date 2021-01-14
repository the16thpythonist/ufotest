from ufotest.testing import AbstractTest, TestRunner, MessageTestResult


class MockTest(AbstractTest):

    name = "mock"

    description = (
        "This test case is simply a mock, which is used to test the ufotest software tools. The test case does "
        "absolutely nothing and returns a simple MessageTestResult."
    )

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):
        return MessageTestResult(0, 'Mock returned 0')
