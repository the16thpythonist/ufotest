import math
import statistics
from collections import defaultdict
from typing import List, Dict
from multiprocessing import Pool
import multiprocessing as mp
#from pathos.multiprocessing import ProcessingPool as Pool

import numpy as np
import matplotlib.pyplot as plt

from ufotest.util import cprint, cerror
from ufotest.config import CONFIG
from ufotest.testing import (AbstractTest,
                             TestRunner,
                             FigureTestResult,
                             MessageTestResult,
                             CombinedTestResult,
                             DictTestResult)
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


class MeasureNoiseMixin:

    def __init__(self):
        self.noise_measurement = {
            'frame1':       None,
            'frame2':       None,
            'variance':     0,
            'rmsnoise':     0
        }

    def measure_noise(self) -> float:
        """
        Captures two independent frames from the camera and proceeds to calculate the noise as the square root of the
        variance of the difference between those frames. This final noise value is then returned

        :return: float
        """
        frame1 = self.camera.get_frame()
        self.noise_measurement['frame1'] = frame1
        frame2 = self.camera.get_frame()
        self.noise_measurement['frame2'] = frame2

        variance = calculate_pair_variance(frame1, frame2)
        self.noise_measurement['variance'] = variance
        rmsnoise = np.sqrt(variance)
        self.noise_measurement['rmsnoise'] = rmsnoise

        return rmsnoise


class CalculatePairNoiseTest(AbstractTest):

    NDIGITS = 3
    INFO_MESSAGE = (
        'The calculation of the noise is based on the description in the following PDF document: '
        f'<a href="{CONFIG.static("photon_transfer_method.pdf")}">Photon Transfer Method</a>.'
    )

    name = 'calculate_pair_noise'
    description = (
        'This test calculates the noise of the camera. The procedure is based on a description of the measurement for '
        'the "Photon Transfer Curve (PTC)". A link to a PDF document describing this procedure can be found in the '
        'content below. A rough explanation of the procedure goes like this: Two frames are captures from the camera '
        'in short succession of each other and with the same settings. These two images are subtracted from each other '
        'to cancel out the influence of the fixed pattern noise. The variance is calculates like this:  '
        'var = \\sum_{i}^{N} (I_1i - M1) - (I_2i - M2) / 2 N'
        'where N is the total number of pixels, I_i the value of pixel at index i and M is the average pixel value of '
        'the respective image. The noise measure "rmsnoise" is then calculated as the square root of this variance:  '
        'rmsnoise = \\sqrt{var}.'
    )

    def __init__(self, test_runner):
        AbstractTest.__init__(self, test_runner)
        self.exit_code = 0

    def run(self):

        message_result = MessageTestResult(self.exit_code, self.INFO_MESSAGE)

        frame1 = self.camera.get_frame()
        cprint('Captured frame 1')
        frame2 = self.camera.get_frame()
        cprint('Captured frame 2')

        variance = calculate_pair_variance(frame1, frame2)
        rmsnoise = math.sqrt(variance)

        dict_result = DictTestResult(self.exit_code, {
            'variance': round(variance, ndigits=self.NDIGITS),
            'rmsnoise': round(rmsnoise, ndigits=self.NDIGITS)
        })
        cprint('Calculated noise')

        fig = self.create_figure(frame1, frame2)
        figure_description = (
            'This figure shows the two frames which were captured for the purpose of calculating the noise '
            'The first subplot shows the first frame, the second subplot shows the second frame and the third subplot '
            'shows the image which results when subtracting all the pixel values of the first frame from those of the '
            'second frame.'
        )
        figure_result = FigureTestResult(self.exit_code, self.context, fig, figure_description)
        cprint('Created figures')

        return CombinedTestResult(
            message_result,
            figure_result,
            dict_result
        )

    @classmethod
    def create_figure(cls, frame1: np.ndarray, frame2: np.ndarray) -> plt.Figure:
        fig, (ax_frame1, ax_frame2, ax_diff) = plt.subplots(nrows=1, ncols=3, figsize=(20, 15))

        ax_frame1.imshow(frame1)
        ax_frame1.set_title('Frame 1')

        ax_frame2.imshow(frame2)
        ax_frame2.set_title('Frame 2')

        frame_difference = frame2 - frame1
        ax_diff.imshow(frame_difference)
        ax_diff.set_title('Frame Difference (Frame2 - Frame1)')

        return fig


class RepeatedCalculatePairNoise(MeasureNoiseMixin, AbstractTest):

    REPETITIONS = 5

    def __init__(self, test_runner):
        MeasureNoiseMixin.__init__(self)
        AbstractTest.__init__(self, test_runner)

    def run(self):
        noise_values = []
        for i in range(self.REPETITIONS):
            rmsnoise = self.measure_noise()
            noise_values.append(rmsnoise)

        stats = {
            'mean noise': round(statistics.mean(noise_values), ndigits=3),
            'stdev noise': round(statistics.stdev(noise_values), ndigits=3)
        }
        dict_result = DictTestResult(0, stats)

        message_result = MessageTestResult(0, (
            f'These results show the average noise measurement and the standard deviation of this noise value for a '
            f'total of {self.REPETITIONS} measurements of the noise out of pairs of frames:'
        ))

        return CombinedTestResult(
            message_result,
            dict_result
        )


def calculate_noise(measurement_tuple):

    _exposure_time, _frame1, _frame2 = measurement_tuple
    _variance = calculate_pair_variance(_frame1, _frame2)
    _noise = np.sqrt(_variance)

    return _exposure_time, _noise


calculate_noise.__module__ = 'ufotest.tests.noise'
calculate_noise.__qualname__ = 'calculate_noise'


class CalculateDarkPhotonTransferCurve(MeasureNoiseMixin, AbstractTest):

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

    def __init__(self, test_runner: TestRunner, start: int = 1, end: int = 100, step: int = 10, reps: int = 3):
        MeasureNoiseMixin.__init__(self)
        AbstractTest.__init__(self, test_runner)

        self.start = start
        self.end = end
        self.step = step
        self.reps = reps

        self.exposure_times = list(range(self.start, self.end + 1, self.step))
        self.frames = []

        self.noises = defaultdict(list)

    def run(self):
        error_count = 0

        p = mp.Process(target=calculate_noise)
        p.start()

        for exposure_time in self.exposure_times:
            self.camera.set_prop('exposure_time', exposure_time)
            cprint(f'set exposure time: {exposure_time}')

            for i in range(self.reps):
                try:
                    frame1 = self.camera.get_frame()
                    frame2 = self.camera.get_frame()
                    self.frames.append((exposure_time, frame1, frame2))
                    cprint(f'Acquired two frames for exp time: {exposure_time}')

                except (PciError, FrameDecodingError):
                    error_count += 1
                    cprint(f'Failed to acquire frames for exp time: {exposure_time}')

        # TODO: Some weird problem with pickle and imporing. Does not work. I think Ill have to design a worker object
        #       manually
        # https://zetcode.com/python/multiprocessing/ unten use Queue and worker
        with Pool(4) as pool:
            noises = pool.map(calculate_noise, self.frames)
            for (exposure_time, noise) in noises:
                self.noises[exposure_time].append(noise)

        cprint('Calculated noises in parallel')

        ptc_fig = self.create_ptc_figure(self.exposure_times, self.noises)

        description = (
            f'Mean noise measurements. The exposure time was varied from {self.start}ms to a maximum of {self.end} ms '
            f'in increments of {self.step}. For each exposure time, the noise was measured a total of {self.reps} '
            f'independent times. This implies that each exposure time required the capturing of {self.reps * 2} '
            f'independent frames.'
        )

        return CombinedTestResult(
            FigureTestResult(0, self.context, ptc_fig, description),
            MessageTestResult(0, f'A total of <strong>{error_count}</strong> noise measurements failed')
        )

    @classmethod
    def create_ptc_figure(cls, exposure_times: List[int], noises_dict: Dict[int, List[float]]):
        """
        Creates the actual matplotlib figure for the curve, given the exposure time and the list of the noise
        measurements. Returns the matplotlib.Figure object.

        This is a rather straightforward figure: On the x axis is the exposure time and the plot shows the development
        of the MEAN noise measurements over these exposure times. Additionally for each exposure time there is an
        error bar displayed, which represents the STDEV of noise measurements.

        :return: Figure
        """
        fig, (ax_ptc) = plt.subplots(nrows=1, ncols=1, figsize=(20, 15))

        noises_list = [noises_dict[e] for e in exposure_times]
        noise_means = [statistics.mean(noises) if len(noises) > 0 else 0 for noises in noises_list]
        noise_stdevs = [statistics.stdev(noises) if len(noises) > 1 else 0 for noises in noises_list]

        ax_ptc.set_title('Dark Photon Transfer Curve')
        ax_ptc.set_xlabel('Exposure time')
        ax_ptc.set_ylabel('Noise')
        ax_ptc.plot(exposure_times, noise_means, color='#E82E00')
        ax_ptc.errorbar(exposure_times, noise_means, yerr=noise_stdevs, color='#FF5328')

        return fig
