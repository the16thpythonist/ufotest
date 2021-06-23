import statistics
from typing import List

import numpy as np
import matplotlib.pyplot as plt

from ufotest.testing import AbstractTest, TestRunner, FigureTestResult, MessageTestResult, CombinedTestResult
from ufotest.exceptions import PciError, FrameDecodingError


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

    def __init__(self, test_runner: TestRunner, start: int = 1, end: int = 3, step: int = 1, reps: int = 4):
        AbstractTest.__init__(self, test_runner)

        self.start = start
        self.end = end
        self.step = step
        self.reps = reps

        self.exposure_times = list(range(self.start, self.end, self.step))

    def run(self):
        error_count = 0
        noises = []
        for exposure_time in self.exposure_times:
            _noises = []
            for i in range(self.reps):
                try:
                    noise = self.measure_noise()
                    _noises.append(noise)
                except (PciError, FrameDecodingError):
                    error_count += 1

            noises.append(_noises)

        ptc_fig = self.create_ptc_figure(self.exposure_times, noises)

        description = 'photon transfer curve'

        return CombinedTestResult(
            FigureTestResult(0, self.context, ptc_fig, description),
            MessageTestResult(0, f'A total of *{error_count}* noise measurements failed')
        )

    def measure_noise(self):
        frame1 = self.camera.get_frame()
        frame2 = self.camera.get_frame()

        var = calculate_pair_variance(frame1, frame2)
        noise = np.sqrt(var)

        return noise

    @classmethod
    def create_ptc_figure(cls, exposure_times: List[int], noises_list: List[List[float]]):
        fig, (ax_ptc) = plt.subplots(nrows=1, ncols=1, figsize=(20, 15))

        noise_means = [statistics.mean(noises) for noises in noises_list]
        noise_stdevs = [statistics.stdev(noises) for noises in noises_list]

        ax_ptc.set_title('Dark Photon Transfer Curve')
        ax_ptc.set_xlabel('Exposure time')
        ax_ptc.set_ylabel('Noise')
        ax_ptc.plot(exposure_times, noise_means)
        ax_ptc.errorbar(exposure_times, noise_means, yerr=noise_stdevs)

        return fig
