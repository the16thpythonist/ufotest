import time

from ufotest.testing import AbstractTest, MessageTestResult, AssertionTestResult, TestRunner
from ufotest.camera import pci_read, pci_write
from ufotest.util import clean_pci_read_output


class PowerUpTest(AbstractTest):

    name = 'power_up'

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):
        test_result = AssertionTestResult()

        writes = [
            ('9000', 'DFFF'),
            ('9000', 'E0FF'),
            ('9000', 'E10F')
        ]

        for address, value in writes:
            pci_write(address, value)
            read = pci_read('9010', '1')
            cleaned_read = clean_pci_read_output(read)
            test_result.assert_pci_read_ok('write {}, {} --> {}'.format(address, value, cleaned_read))
            time.sleep(0.2)

        return test_result

