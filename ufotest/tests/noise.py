import statistics
from typing import List

import numpy as np
import matplotlib.pyplot as plt

from ufotest.testing import AbstractTest, TestRunner, FigureTestResult, MessageTestResult


# == UTILITY FUNCTIONS

def calculate_pair_variance(frame1: np.ndarray, frame2: np.ndarray) -> float:
    """
    Given two frame arrays of the same dimensions and from the same camera under the same conditions *frame1* and
    *frame2*, this method calculates the variance of the difference of those frames. This measure of variance is the
    necessary value to determine the noise of the camera.

    :param frame1: The first of the two independent(!) frames
    :param frame2: The second frame

    :returns float: The variance
    """
    frame1_mean = np.mean(frame1)
    frame2_mean = np.mean(frame2)

    row_count = len(frame1)
    column_count = len(frame1[0])
    squared_sum = 0
    for i in range(row_count):
        for j in range(column_count):
            squared_sum += ((frame1[i][j] - frame1_mean) - (frame2[i][j] - frame2_mean)) ** 2

    variance = squared_sum / (2 * row_count * column_count)
    return variance


# == ACTUAL TEST CASES

class CalculateDarkPhotonTransferCurve(AbstractTest):

    name = 'dark_photon_transfer_curve'
    description = 'blub'

    def __init__(self, test_runner: TestRunner, start: int = 1, end: int = 10, step: int = 5, reps: int = 1):
        AbstractTest.__init__(self, test_runner)

        self.start = start
        self.end = end
        self.step = step
        self.reps = reps

    def run(self):
        noises = []
        for exposure_time in range(self.start, self.end, self.step):
            self.camera.set_prop('exposure_time', exposure_time)
            noise = statistics.mean([self.measure_noise() in range(self.reps)])
            noises.append(noise)

        ptc_fig = self.create_ptc_figure(noises)
        ptc_fig.show()

        description = 'photon transfer curve'

        return FigureTestResult(0, self.context, ptc_fig, description)

    def measure_noise(self):
        frame1 = self.camera.get_frame()
        frame2 = self.camera.get_frame()

        var = calculate_pair_variance(frame1, frame2)
        noise = np.sqrt(var)

        return noise

    @classmethod
    def create_ptc_figure(cls, noises: List[float]):
        fig, (ax_ptc) = plt.subplots(nrows=1, ncols=1, figsize=(20, 15))

        ax_ptc.plot(noises)

        return fig
