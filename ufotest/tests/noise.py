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
    description = (
        'This test case does the following: Starting from a base value, the exposure time of the camera is '
        'incrementally increased until it reaches a maximum value. For each exposure time value, the noise of the '
        'camera is measured in multiple repetitions. This is done by capturing two independent frames from the camera '
        'and calculating the variance over the difference of these frames. After all measurements are done, the mean '
        'noise value for each exposure time is plotted in a diagram. This diagram should contain some information '
        'about the noise characteristics of the camera. Note that for this measurement, no light should be getting '
        'to the sensor at all. The entire idea of it relies on the assumption that each frame only captures an image '
        'of the "noise" without any external image information.'
    )

    def __init__(self, test_runner: TestRunner, start: int = 1, end: int = 10, step: int = 1, reps: int = 3):
        AbstractTest.__init__(self, test_runner)

        self.start = start
        self.end = end
        self.step = step
        self.reps = reps

        self.exposure_times = list(range(self.start, self.end + 1, self.step))

    def run(self):
        error_count = 0
        noises = []
        for exposure_time in self.exposure_times:
            self.camera.set_prop('exposure_time', exposure_time)
            _noises = []
            for i in range(self.reps):
                try:
                    noise = self.measure_noise()
                    _noises.append(noise)
                except (PciError, FrameDecodingError):
                    error_count += 1

            noises.append(_noises)

        ptc_fig = self.create_ptc_figure(self.exposure_times, noises)

        description = (
            f'Mean noise measurements. The exposure time was varied from {self.start}ms to a maximum of {self.end} ms '
            f'in increments of {self.step}. For each exposure time, the noise was measured a total of {self.reps} '
            f'independent times. This implies that each exposure time required the capturing of {self.reps * 2} '
            f'independent frames.'
        )

        return CombinedTestResult(
            FigureTestResult(0, self.context, ptc_fig, description),
            MessageTestResult(0, f'A total of *{error_count}* noise measurements failed')
        )

    def measure_noise(self) -> float:
        """
        Captures two independent frames from the camera and proceeds to calculate the noise as the square root of the
        variance of the difference between those frames. This final noise value is then returned

        :return: float
        """
        frame1 = self.camera.get_frame()
        frame2 = self.camera.get_frame()

        var = calculate_pair_variance(frame1, frame2)
        noise = np.sqrt(var)

        return noise

    @classmethod
    def create_ptc_figure(cls, exposure_times: List[int], noises_list: List[List[float]]):
        """
        Creates the actual matplotlib figure for the curve, given the exposure time and the list of the noise
        measurements. Returns the matplotlib.Figure object.

        This is a rather straightforward figure: On the x axis is the exposure time and the plot shows the development
        of the MEAN noise measurements over these exposure times. Additionally for each exposure time there is an
        error bar displayed, which represents the STDEV of noise measurements.

        :return: Figure
        """
        fig, (ax_ptc) = plt.subplots(nrows=1, ncols=1, figsize=(20, 15))

        noise_means = [statistics.mean(noises) if noises else 0 for noises in noises_list]
        noise_stdevs = [statistics.stdev(noises) if noises else 0 for noises in noises_list]

        ax_ptc.set_title('Dark Photon Transfer Curve')
        ax_ptc.set_xlabel('Exposure time')
        ax_ptc.set_ylabel('Noise')
        ax_ptc.plot(exposure_times, noise_means, color='#E82E00')
        ax_ptc.errorbar(exposure_times, noise_means, yerr=noise_stdevs, color='#FF5328')

        return fig
