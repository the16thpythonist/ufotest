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
    LOW_PERCENTILE = 0.05
    HIGH_PERCENTILE = 0.95

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
        frame = self.camera.get_frame()

        fig_frame = self.create_frame_figure(frame)
        frame_description = ('')

        fig_hist = self.create_histogram_figure(frame)
        hist_description = ('')

        return CombinedTestResult(
            FigureTestResult(0, self.context, fig_frame, ''),
            FigureTestResult(0, self.context, fig_hist, '')
        )

    @classmethod
    def create_frame_figure(cls, frame: np.ndarray) -> plt.Figure:
        fig, (ax_frame, ax_frame_mod) = plt.subplots(nrows=1, ncols=2, figsize=(20, 15))

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
        bottom_quantile = int(np.quantile(hist, cls.LOW_PERCENTILE))
        top_quantile = int(np.quantile(hist, cls.HIGH_PERCENTILE))

        hist_bins = list(range(int(np.min(frame_flat)) + 1, int(np.max(frame_flat)) + 100))
        ax_hist.hist(frame_flat, bins=hist_bins)
        ax_hist.set_title('Captured Frame - Histogram')
        ax_hist.set_xlabel('Pixel Values')
        ax_hist.set_ylabel('Occurrences')
        ax_hist.set_ylim()

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
        min_value = np.quantile(hist, cls.LOW_PERCENTILE)
        max_value = np.quantile(hist, cls.HIGH_PERCENTILE)
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


