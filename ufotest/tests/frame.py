import os
import math
import datetime
import statistics
from typing import Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt

from ufotest.util import setup_environment, random_string
from ufotest.camera import save_frame, import_raw, get_frame, UfoCamera
from ufotest.config import CONFIG

from ufotest.testing import (AbstractTest,
                             TestRunner,
                             ImageTestResult,
                             CombinedTestResult,
                             DictTestResult,
                             FigureTestResult)
from ufotest.testing import MessageTestResult

# This test case is essentially supposed to capture a single frame and potentially even display this frame inside of
# the test report. Obviously this is not a very methodical test. It's purpose is more to heuristically check if
# anything is working at all at first. If I can manage to display the image, this might even serve for a human operator
# checking the report to get a feeling for how the camera is doing.


class AcquireSingleFrame(AbstractTest):
    """
    Acquires a single frame from the camera and puts the image into the test report.
    """

    MAX_PIXEL_VALUE = 4095

    name = 'single_frame'
    description = (
        'Requests a single frame from the camera. The contents of this frame are not tested in any way. '
        'The test is simply meant to test if a frame can be requested from the camera at all. If the frame was '
        'successfully taken, this frame is being converted into an image and this image is then also displayed in the '
        'test report. This test relies on the assumption, that the camera has been properly setup previously and is '
        'now accepting frame requests.'
    )

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

        # So the intention is to somehow include the frame image into the test report. For that purpose we will have
        # to save the image into the folder for this test run first.
        # So this is actually pretty easy since I reworked the testing system: Each test case gets passed the test
        # runner object which will ultimately execute the test. Thus, the test case also has access to the test context
        # which contains all the information we could wish for!
        self.file_name = 'single_frame.png'
        self.frame_path = os.path.join(self.context.folder_path, self.file_name)

    def run(self):
        # -- SETTING UP ENV VARIABLES
        setup_environment()

        # -- REQUESTING FRAME FROM CAMERA
        frame_path = get_frame()
        frames = import_raw(frame_path, 1, self.config.get_sensor_width(), self.config.get_sensor_height())
        frame = frames[0]

        fig_frame = self.create_frame_figure(frame)
        description = (
            'This figure shows a single frame, which was captured from the camera. The first subplot shows the frame '
            'image exactly as it is. All pixel values are exactly as returned by the camera. The second subplot shows '
            'the same frame but with an increased contrast. The contrast has been increased through an algorithm which '
            'stretches the histogram of the image to its 0.1 and 0.9 quantile. The third subplot shows the histogram '
            'of the image with increased contrast. This roughly equates to zooming into the "interesting region" of '
            'the histogram.'
        )

        fig_hist = self.create_histogram_figure(frame)

        return CombinedTestResult(
            FigureTestResult(0, self.context, fig_frame, ''),
            FigureTestResult(0, self.context, fig_hist, '')
        )

    @classmethod
    def create_frame_figure(cls, frame: np.ndarray) -> plt.Figure:
        fig, (ax_frame, ax_frame_mod, ax_hist) = plt.subplots(nrows=1, ncols=3, figsize=(20, 15))

        # ~ plotting the frame as an image
        ax_frame.imshow(frame)
        ax_frame.set_title('Captured Frame')

        # ~ plotting the frame with increased contrast
        frame_mod = cls.increase_frame_contrast(frame)
        ax_frame_mod.imshow(frame_mod)
        ax_frame_mod.set_title('Captured Frame - Increased Contrast')

        return fig

    @classmethod
    def create_histogram_figure(cls, frame: np.ndarray) -> plt.Figure:
        fig, (ax_hist, ax_hist_zoom) = plt.subplots(nrows=1, ncols=2, figsize=(20, 15))

        frame_flat = frame.flatten()
        hist, _ = np.histogram(frame_flat, bins=list(range(0, cls.MAX_PIXEL_VALUE)))
        bottom_quantile = np.quantile(hist, 0.1)
        top_quantile = np.quantile(hist, 0.9)

        hist_bins = list(range(min(frame_flat), max(frame_flat)))
        ax_hist.hist(frame_flat, bins=hist_bins)
        ax_hist.set_title('Captured Frame - Histogram')
        ax_hist.set_xlabel('Pixel Values')
        ax_hist.set_ylabel('Occurrences')

        hist_zoom_bins = list(range(bottom_quantile, top_quantile))
        ax_hist_zoom.hist(frame_flat, bins=hist_zoom_bins)
        ax_hist_zoom.set_title('Captured Frame - Zoomed Histogram')
        ax_hist_zoom.set_xlabel('Pixel Values')
        ax_hist_zoom.set_ylabel('Occurrences')

        return fig

    @classmethod
    def increase_frame_contrast(cls, frame: np.ndarray) -> np.ndarray:
        frame_flat = frame.flatten()
        hist, _ = np.histogram(frame_flat, bins=list(range(0, cls.MAX_PIXEL_VALUE)))
        min_value = np.quantile(hist, 0.1)
        max_value = np.quantile(hist, 0.9)
        difference = max_value - min_value

        # The absence of this section caused an error before. There is quite a reasonable probability, that this
        # difference is actually 0 because the image just is so homogeneous. If that is the case we do not perform
        # the procedure to increase the contrast (Division by zero!) and instead return the original frame
        if difference == 0:
            return frame

        frame_result = frame.copy()
        for i in range(len(frame_result)):
            for j in range(len(frame_result[i])):
                new_value = (cls.MAX_PIXEL_VALUE / difference) * frame_result[i][j] - \
                            (cls.MAX_PIXEL_VALUE / difference) * min_value
                frame_result[i][j] = min(new_value, cls.MAX_PIXEL_VALUE)

        return frame_result


class SingleFrameStatistics(AbstractTest):
    """
    Acquires a single frame from the camera and calculates some simple statistics for this frame. Such as the
    mean, min and max value and the standard deviation. It also creates a histogram for the frame and that plot is
    displayed in the test report.
    """

    NDIGITS = 3

    name = 'single_frame_statistics'
    description = (
        'Requests a single frame from the camera. This frame is then used to compute some simple statistical '
        'properties. These are the mean grayscale value, the min value, the max value, the variance and the '
        'standard deviation. Additionally, a histogram of the grayscale values within the camera is computed. '
        'This histogram is saved as a plot and displayed in the test report. This test relies on the assumption, '
        'that the camera is properly setup and ready to accept frame requests.'
    )

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):
        setup_environment()

        # -- ACQUIRE FRAME AS MATRIX
        file_path = get_frame()
        frames = import_raw(file_path, 1, self.config.get_sensor_width(), self.config.get_sensor_height())
        frame = frames[0]

        stats = self.create_frame_statistics(frame)
        dict_result = DictTestResult(0, stats)
        fig = self.create_histogram_figure(frame)
        figure_description = (
            'This figure shows a histogram of the pixel values within the captured frame.'
        )
        figure_result = FigureTestResult(0, self.context, fig, figure_description)

        return CombinedTestResult(
            dict_result,
            figure_result
        )

    def create_frame_statistics(self, frame: np.ndarray) -> dict:
        return {
            'average':                      round(float(np.mean(frame)), ndigits=self.NDIGITS),
            'variance':                     round(float(np.var(frame)), ndigits=self.NDIGITS),
            'standard deviation':           round(float(np.std(frame)), ndigits=self.NDIGITS),
            'min value':                    np.min(frame),
            'max value':                    np.max(frame)
        }

    @classmethod
    def create_histogram_figure(cls, frame: np.ndarray) -> plt.Figure:
        fig, ax = plt.subplots(nrows=1, ncols=1)
        frame_data = frame.flatten()
        ax.hist(frame_data, bins=list(range(0, 4096)))
        ax.set_title('Histogram of frame values')
        ax.set_xlabel('Pixel value')
        ax.set_ylabel('Number of occurrences')

        return fig


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

        frame1, frame2 = self.get_frames()
        variance = self.calculate_pair_variance(frame1, frame2)
        rmsnoise = math.sqrt(variance)

        dict_result = DictTestResult(self.exit_code, {
            'variance': round(variance, ndigits=self.NDIGITS),
            'rmsnoise': round(rmsnoise, ndigits=self.NDIGITS)
        })

        fig = self.create_figure(frame1, frame2)
        figure_description = (
            'This figure shows the two frames which were captured for the purpose of calculating the noise '
            'The first subplot shows the first frame, the second subplot shows the second frame and the third subplot '
            'shows the image which results when subtracting all the pixel values of the first frame from those of the '
            'second frame.'
        )
        figure_result = FigureTestResult(self.exit_code, self.context, fig, figure_description)

        return CombinedTestResult(
            message_result,
            figure_result,
            dict_result
        )

    def get_frames(self) -> Tuple[np.ndarray, np.ndarray]:
        frame1_path = get_frame()
        frame1 = import_raw(frame1_path, 1, self.config.get_sensor_width(), self.config.get_sensor_height())[0]

        frame2_path = get_frame()
        frame2 = import_raw(frame2_path, 1, self.config.get_sensor_width(), self.config.get_sensor_height())[0]

        return frame1, frame2

    @classmethod
    def calculate_pair_variance(cls, frame1: np.ndarray, frame2: np.ndarray) -> float:
        frame1_mean = np.mean(frame1)
        frame2_mean = np.mean(frame2)

        row_count = len(frame1)
        column_count = len(frame1[0])
        squared_sum = 0
        for i in range(row_count):
            for j in range(column_count):
                squared_sum += ((frame1[i][j] - frame1_mean) - (frame2[i][j] - frame2_mean)) ** 2

        variance = squared_sum / (2 * row_count * column_count)
        return round(variance, ndigits=cls.NDIGITS)

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


class RepeatedCalculatePairNoise(CalculatePairNoiseTest):

    REPETITIONS = 5

    name = 'repeated_calculate_pair_noise'
    description = (
        'Repeatedly calculates the noise by acquiring two separate frames, subtracting them and using the square root '
        f'of the variance. Executes {REPETITIONS} times and displays the average and'
    )

    def __init__(self, test_runner: TestRunner):
        CalculatePairNoiseTest.__init__(self, test_runner)

    def run(self):
        noise_values = []
        for i in range(self.REPETITIONS):
            frame1, frame2 = self.get_frames()
            variance = self.calculate_pair_variance(frame1, frame2)
            rmsnoise = math.sqrt(variance)
            noise_values.append(rmsnoise)

        stats = {
            'mean noise': round(statistics.mean(noise_values), ndigits=self.NDIGITS),
            'stdev noise': round(statistics.stdev(noise_values), ndigits=self.NDIGITS)
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


class CalculateSeriesNoiseTest(AbstractTest):

    name = 'calculate_series_noise'
    description = 'Calculates the camera noise from a series of images'

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):
        pass

