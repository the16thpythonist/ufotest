from unittest import TestCase
import matplotlib.pyplot as plt

from ufotest.tests.basic import RepeatedResetTest, RepeatedFrameTest


# == MOCK DATA ==

RESET_SCRIPT_OUTPUT = """
--------------------------------------------------------------------
--------------------------- S T A R T  -----------------------------
-------------------- C O N F I G U R A T I O N  --------------------
---------------------- ( UFO 6 - 20 MPixel ) -----------------------
--------------------------- Normal Mode ----------------------------
--------------------------------------------------------------------
    9010:  000fd400

    9010:  000fd600

    9010:  000bd700

    9010:  000fe100

    9010:  000fde00

    9010:  000be740

    9010:  000be866

    9010:  000be944

    9010:  000bece4

    9010:  000bedd2

    9010:  000bf45b

    9010:  000bf55b

    9010:  000bf92f

    9010:  000bfb66

Set the start single of line to 0 ...
    9010:  000b9800

    9010:  000b9900

Set the number of line to 3840 ...
    9010:  000b9a00

    9010:  000f9b00

Set the subsampling to 0 ...
    9010:  000b9c00

    9010:  000b9d00

    9010:  000b9e00

    9010:  000b9f00

Set the min. value of exp time ... 96 us
    9010:  000fa000

    9010:  000ba100

Enable test pattern ...
    9010:  000bd300

FPGA Reset ...
---------- R E S E T ------------------
---------- ENABLE R/W ------------------
Set all IODEAL to Default..
finish ..
Set DMA timeout
Set the number of frame on CMOS internal frame generator
    9010:  000f9600

--------------------------------------------------------------------
finish ..
--------------------------------------------------------------------
status ...
    9050:  8449efff  00003001    00001111  00000000
    9060:  00000000  00000000    00000000  00000000
"""


# == TEST CASE CLASSES ==

# Strictly speaking, we cannot test this test completely, because part of it's functionality obviously relies on the
# interaction with the camera itself. But many of its helper methods were written as simple input-output functions and
# these can be tested independently

class TestRepeatedResetTest(TestCase):

    def test_clean_reset_output(self):
        """
        If the basic functionality of "clean_reset_output" method works at all. Tested with a snippet of exemplary
        output, but not the whole thing.
        """
        output = (
            "Set the min. value of exp time ... 96 us\n"
            "   9010:  000fa000  \n"
            "\n"
            "   9010:  000ba100  \n"
            "\n"
            "Enable test pattern ...\n"
            "   9010:  000bd300  \n"
            "\n"
            "FPGA Reset ...\n"
        )
        expected = [
            "9010:  000fa000",
            "9010:  000ba100",
            "9010:  000bd300"
        ]

        self.assertListEqual(
            RepeatedResetTest.clean_reset_output(output),
            expected
        )

    def test_segment_reset_output(self):
        output_lines = [
            "9010:  000fa000",
            "9010:  000ba100",
            "9010:  000bd300",
            "9050:  8449efff  00003001    00001111  00000000"
        ]
        expected = {
            "9010": ["000fa000", "000ba100", "000bd300"],
            "9050": ["8449efff  00003001    00001111  00000000"]
        }

        self.assertDictEqual(
            RepeatedResetTest.segment_reset_output(output_lines),
            expected
        )

    def test_register_contains_error(self):
        register_value1 = "000ba100"
        self.assertFalse(RepeatedResetTest.register_contains_error(register_value1))

        register_value2 = "000fa000"
        self.assertTrue(RepeatedResetTest.register_contains_error(register_value2))

    def test_state_contains_error(self):
        state_value1 = "8449ffff  00003001    00001111  00000000"
        self.assertFalse(RepeatedResetTest.state_contains_error(state_value1))

        state_value2 = "8449efff  00003001    00001111  00000000"
        self.assertTrue(RepeatedResetTest.state_contains_error(state_value2))

        state_value3 = "8449ffff  00003001    00001001  00000000"
        self.assertTrue(RepeatedResetTest.state_contains_error(state_value3))

    def test_create_figure(self):
        """
        If the method to actually create the matplotlib Figure object works
        """
        error_counts = [2, 3, 5, 2, 1]
        state_errors = [False, True, True, False, False]
        max_error_count = 10

        fig = RepeatedResetTest.create_figure(error_counts, state_errors, max_error_count)

        self.assertIsInstance(fig, plt.Figure)


class TestRepeatedFrameTest(TestCase):

    def test_create_figure(self):
        counters = {
            'success': {
                'name': 'Success',
                'color': 'green',
                'count': 2
            },
            'pci_error': {
                'name': 'PCI Err',
                'color': 'red',
                'count': 5
            },
            'decoding_error': {
                'name': 'Dec. Err',
                'color': 'red',
                'count': 4
            }
        }
        fig = RepeatedFrameTest.create_figure(counters)
        # fig.show()
        self.assertIsInstance(fig, plt.Figure)
