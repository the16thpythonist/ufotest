import time
from typing import List, Dict, Any
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

from ufotest.testing import AbstractTest, FigureTestResult, MessageTestResult, CombinedTestResult, TestRunner
from ufotest.camera import get_frame
from ufotest.util import run_script
from ufotest.exceptions import PciError, FrameDecodingError


class RepeatedResetTest(AbstractTest):
    """
    **THE IDEA**

    The following observation could be made when working with the camera: Sometimes the reset script would not leave
    the camera properly initialized, but instead indicate some errors. Heuristic testing of this behaviour did not
    reveal any conditions for this occurrence. It seems to appear sometimes at random.
    Now this test case is supposed to quantify this behaviour, by repeatedly repeating the reset sequence and checking
    how often the camera is left with errors.
    """

    REPETITIONS = 5
    FIGURE_DESCRIPTION = (
        'This figure shows the amount of register errors for each repetition. The horizontal axis shows the index of '
        'each new repetition of the reset script. The vertical axis shows the amount of register errors which have '
        'occurred for that run of the reset script. The color blue indicates, that the final state register contained '
        'the expected bits which indicate an operational state, while the color red indicates that the final state '
        'register deviated from what it should be.'
    )

    name = 'repeated_reset'
    description = (
        f'In essence, this test runs the "reset" script {REPETITIONS} consecutive times. For each execution of the '
        'script, the test checks the output which is produced. The output of the script contains the status readouts '
        'of some registers which are manipulated in the process of resetting the camera. The classification of whether '
        'these register readouts imply a problem with the setup process or not is based on a heuristical rul given by '
        'Michele: If the third position of the 9010 register is an "f" that indicates an error, whereas a "b" '
        'indicates a success. For each repetition of the reset script, the test keeps track of how many such errors '
        'occurred in the output of the 9010 registers. An additional factor which is also considered by this test '
        'is the state of the 9050 register which is printed at the very end of the reset script. The evaluation of '
        'this is based on another heuristical rule given by Michele. If the status register looks something like this: '
        '"xxxxffff  xxxxxxx     xxxx1111  xxxxxxxx", it indicates that the camera is ready for communication and '
        'frame transmission. If this is not the case there may be an error with the camera. This test fails if even '
        'one of the repetitions does not match the before mentioned format of the 9050 register.'
    )

    def __init__(self, test_runner: TestRunner):
        super(RepeatedResetTest, self).__init__(test_runner)

        self.register_error_counts: List[int] = []
        self.state_errors: List[bool] = []
        self.register_data = {}

    def run(self):

        for i in range(self.REPETITIONS):
            # For each repetition we want to execute the reset script and analyse the output for possible errors.
            exit_code, stdout = run_script('reset')

            lines = self.clean_reset_output(stdout)
            self.register_data = self.segment_reset_output(lines)
            error_count = sum(self.register_contains_error(value) for value in self.register_data['9010'])
            state_error = self.state_contains_error(self.register_data['9050'][0])

            self.register_error_counts.append(error_count)
            self.state_errors.append(state_error)

            time.sleep(1)

        exit_code = any(self.state_errors)

        # ~ Creating the plot for visualization
        fig = self.create_figure(self.register_error_counts, self.state_errors, len(self.register_data['9010']))
        figure_result = FigureTestResult(exit_code, self.context, fig, self.FIGURE_DESCRIPTION)

        return figure_result

    # -- Helper methods --

    # So one important step is to clean up the output. The output of the script is designed to be semi human readable
    # which means it contains some text and empty lines for formatting. But it also contains some actual information
    # about the state of the camera. This information should be extracted. The information I really want would be for
    # one thing the individual results for the status registers and the second important information would be the
    # final overview.

    @classmethod
    def clean_reset_output(cls, output: str, filter_substrings: list = ['9010', '9050', '9060']) -> List[str]:
        lines = output.splitlines()
        lines = [line.lstrip().rstrip() for line in lines if any(substring in line for substring in filter_substrings)]
        return lines

    @classmethod
    def segment_reset_output(cls, output_lines: List[str]) -> Dict[str, List[str]]:
        segmented_lines = defaultdict(list)
        for line in output_lines:
            front, back = line.split(':')
            segmented_lines[front.replace(' ', '')].append(back.lstrip().rstrip())

        return segmented_lines

    @classmethod
    def register_contains_error(cls, value: str) -> bool:
        return value[3] == 'f'

    @classmethod
    def state_contains_error(cls, value: str) -> bool:
        register_values = [item for item in value.split(' ') if item]
        first, _, third, _ = register_values

        state_first = first[4:]
        state_third = third[4:]

        return not (state_first == 'ffff' and state_third == '1111')

    @classmethod
    def create_figure(cls, error_counts: List[int], state_errors: List[bool], maximum_errors: int) -> plt.Figure:
        count = len(error_counts)
        fig, ax = plt.subplots(ncols=1, nrows=1)
        ax: plt.Axes = ax
        ax.set_title('Bar Chart: Register errors for each repetition')
        ax.set_ylabel('error count')
        ax.set_xlabel('repetition index')
        ax.set_xlim(left=0, right=count + 1)
        ax.set_ylim(bottom=0, top=maximum_errors + 1)

        x = list(range(1, count + 1))
        heights = [error_count if error_count else 0.5 for error_count in error_counts]
        color = ['red' if state_error else 'blue' for state_error in state_errors]
        ax.bar(x=x, height=heights, color=color)

        ax.plot([0, count + 1], [maximum_errors, maximum_errors], color='gray')

        return fig


class RepeatedFrameTest(AbstractTest):

    REPETITIONS = 5

    name = 'repeated_frames'
    description = (
        f'Attempts to capture a frame {REPETITIONS} times.'
    )

    def __init__(self, test_runner: TestRunner):
        super(RepeatedFrameTest, self).__init__(test_runner)
        self.counters = {
            'success': {
                'name': 'Success',
                'color': 'green',
                'count': 0
            },
            'pci_error': {
                'name': 'PCI Err',
                'color': 'red',
                'count': 0
            },
            'decoding_error': {
                'name': 'Dec. Err',
                'color': 'red',
                'count': 0
            }
        }

    def run(self):

        for i in range(self.REPETITIONS):
            try:
                frame_path = get_frame()
                self.counters['success']['count'] += 1
                time.sleep(1)
            except PciError:
                self.counters['pci_error']['count'] += 1
            except FrameDecodingError:
                self.counters['decoding_error']['count'] += 1

        exit_code = self.counters['pci_error']['count'] > 0 or self.counters['decoding_error']['count'] > 0

        # ~ Creating the figure
        fig = self.create_figure(self.counters)
        figure_result = FigureTestResult(exit_code, self.context, fig, 'some description')

        return figure_result

    @classmethod
    def create_figure(cls, counters: Dict[str, Dict[str, Any]]) -> plt.Figure:
        fig, ax = plt.subplots(nrows=1, ncols=1)
        ax: plt.Axes = ax

        count = len(counters)
        ax.set_title('Bar chart: Errors during repeated execution of "frame" script')
        ax.set_ylabel('')
        ax.set_yticks(list(range(1, count + 1)))
        ax.set_ylim(0, count + 1)
        ax.set_yticklabels([data['name'] for data in counters.values()])
        ax.set_xlabel('Number of occurrences over all repetitions')

        ax.barh(
            y=list(range(1, count + 1)),
            width=[data['count'] for data in counters.values()],
            color=[data['color'] for data in counters.values()])

        return fig


