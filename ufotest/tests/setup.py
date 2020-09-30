import time

from ufotest.testing import AbstractTest, MessageTestResult, TestRunner
from ufotest.camera import pci_read, pci_write
from ufotest.util import clean_pci_read_output


class PowerUpTest(AbstractTest):

    name = 'power_up'

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):

        writes = [
            ('9000', 'DFFF'),
            ('9000', 'E0FF'),
            ('9000', 'E10F')
        ]

        results = []

        for address, value in writes:
            pci_write(address, value)
            result = pci_read('9010', '1')
            results.append(clean_pci_read_output(result))
            time.sleep(0.2)

        return MessageTestResult(0, '\n'.join(results))

