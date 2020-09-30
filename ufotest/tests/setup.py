from ufotest.testing import AbstractTest, MessageTestResult, TestRunner
from ufotest.camera import pci_read, pci_write


class PowerUpTest(AbstractTest):

    name = 'power_up'

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):

        pci_write('9000', 'DFFF')
        result = pci_read('9000', '1')

        return MessageTestResult(0, 'RESULT: {}'.format(result))
