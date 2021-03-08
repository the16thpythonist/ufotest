import time
from typing import List, Dict
from collections import defaultdict

import numpy as np
import matplotlib.pyplot as plt

from ufotest.testing import AbstractTest, FigureTestResult, MessageTestResult, AssertionTestResult, TestRunner
from ufotest.util import run_script


class RepeatedResetTest(AbstractTest):
    """
    **THE IDEA**

    The following observation could be made when working with the camera: Sometimes the reset script would not leave
    the camera properly initialized, but instead indicate some errors. Heuristic testing of this behaviour did not
    reveal any conditions for this occurrence. It seems to appear sometimes at random.
    Now this test case is supposed to quantify this behaviour, by repeatedly repeating the reset sequence and checking
    how often the camera is left with errors.
    """

    name = 'repeated_reset'
    description = (
        'this is a description'
    )

    REPETITIONS = 5

    def __init__(self, test_runner: TestRunner):
        super(RepeatedResetTest, self).__init__(test_runner)

        self.register_error_counts: List[int] = []
        self.state_errors: List[bool] = []

    def run(self):

        for i in range(self.REPETITIONS):
            # For each repetition we want to execute the reset script and analyse the output for possible errors.
            exit_code, stdout = run_script('reset')

            lines = self.clean_reset_output(stdout)
            register_data = self.segment_reset_output(lines)
            error_count = sum(self.register_contains_error(value) for value in register_data['9010'])
            state_error = self.state_contains_error(register_data['9050'][0])

            self.register_error_counts.append(error_count)
            self.state_errors.append(state_error)

            time.sleep(1)

        exit_code = any(self.state_errors)

        # ~ Creating the plot for visualization
        fig = self.create_figure(self.register_error_counts, self.state_errors)
        figure_result = FigureTestResult(exit_code, self.context, fig)

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
    def create_figure(cls, error_counts: List[int], state_errors: List[bool]) -> plt.Figure:
        fig, ax = plt.subplots(ncols=1, nrows=1)
        ax: plt.Axes = ax
        ax.set_title('Register errors for each repetition')
        ax.set_ylabel('error count')
        ax.set_xlabel('repetition index')

        x = list(range(1, len(error_counts) + 1))
        heights = error_counts
        color = ['red' if state_error else 'blue' for state_error in state_errors]

        ax.bar(x=x, height=heights, color=color)

        return fig
