import time

from ufotest.testing import AbstractTest, MessageTestResult, TestRunner
from ufotest.camera import pci_read, pci_write


class PowerUpTest(AbstractTest):

    name = 'power_up'

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):

        pci_write('9000', 'DFFF')
        result1 = pci_read('9010', '1')
        print(result1)
        time.sleep(0.2)

        pci_write('9000', 'E0FF')
        result2 = pci_read('9010', '1')
        print(result2)
        time.sleep(0.2)

        pci_write('9000', 'E10F')
        result3 = pci_read('9010', '1')
        print(result3)
        time.sleep(0.2)

        return MessageTestResult(0, 'RESULT: {}'.format(result1))

