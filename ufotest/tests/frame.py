import os
import time
from typing import Optional, Tuple

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from ufotest.util import cprint, cresult
from ufotest.util import setup_environment, random_string, force_aspect
from ufotest.camera import save_frame, import_raw, get_frame, UfoCamera
from ufotest.config import CONFIG
from ufotest.exceptions import PciError, FrameDecodingError

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

    LOW_PERCENTILE = 1
    HIGH_PERCENTILE = 99

    name = 'single_frame'
    description = (
        'Requests a single frame from the camera. The contents of this frame are not tested in any way. '
        'The test is simply meant to test if a frame can be requested from the camera at all. If the frame was '
        'successfully taken, this frame is being converted into an image and this image is then also displayed in the '
        'test report. Additionally, the histogram of the frame will be plotted.'
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

        self.frame: Optional[np.array] = None
        self.frame_flat: Optional[np.array] = None

        self.histogram_values: Optional[np.array] = None
        self.histogram_x: Optional[np.array] = None

        self.top_percentile: Optional[int] = None
        self.top_x: Optional[int] = None

        self.bottom_percentile: Optional[int] = None
        self.bottom_x: Optional[int] = None

    def run(self):
        # -- SETTING UP ENV VARIABLES
        setup_environment()

        # -- REQUESTING FRAME FROM CAMERA
        # The "capture_frame" method will query the camera object to get a frame in the format of a numpy 2D array and
        # then save this into the self.frame property and a flattened 1D version of the frame to the self.frame_flat
        # variable
        self.capture_frame()
        cprint(f'captured frame with {len(self.frame_flat)} pixels')

        # -- CREATING THE HISTOGRAM
        self.calculate_histogram()
        cprint(f'created histogram')

        fig_frame = self.create_frame_figure()
        fig_frame_description = (
            f'A single frame acquired from the camera. (left) The image as it was taken from the camera. The image '
            f'itself is not colored, but the pixel range is converted into a color map, where 0 corresponds to dark '
            f'blue colors and the maximum pixel value {self.MAX_PIXEL_VALUE} to bright yellow. (right) The frame with '
            f'a contrast increasing algorithm applied to it, which will stretch the histogram to take up all the '
            f'available space up to the max pixel value.'
        )

        fig_hist = self.create_histogram_figure()
        fig_hist_description = (
            f'The histogram of the frame. (left) Shows the histogram, where the bounds of the plot are set to the  '
            f'minimum and maximum possible pixel values with the currently used detector. (right) Shows the zoomed '
            f'version of the histogram, where the borders of the plot are adjusted to start at the 1st percentile and '
            f'end at the 99th percentile.'
        )

        cprint('saved final figures')

        return CombinedTestResult(
            FigureTestResult(0, self.context, fig_frame, fig_frame_description),
            FigureTestResult(0, self.context, fig_hist, fig_hist_description)
        )

    def capture_frame(self):
        self.frame = self.camera.get_frame()
        self.frame_flat = self.frame.flatten()

    def calculate_histogram(self):
        self.histogram_values, self.histogram_x = np.histogram(self.frame_flat, bins=range(0, self.MAX_PIXEL_VALUE))
        self.histogram_x = self.histogram_x[:-1]
        histogram_cumsum = np.cumsum(self.histogram_values)
        histogram_sum = np.sum(self.histogram_values)

        self.bottom_x = max(x
                            for x, val in zip(self.histogram_x, histogram_cumsum)
                            if val <= (self.LOW_PERCENTILE / 100) * histogram_sum)

        self.top_x = min(x
                         for x, val in zip(self.histogram_x, histogram_cumsum)
                         if val >= (self.HIGH_PERCENTILE / 100) * histogram_sum)

    def create_frame_figure(self) -> plt.Figure:
        fig, (ax_frame, ax_frame_mod) = plt.subplots(nrows=1, ncols=2, figsize=(20, 15))
        norm = mcolors.Normalize(vmin=0, vmax=self.MAX_PIXEL_VALUE)

        # ~ plotting the frame as an image
        ax_frame.imshow(self.frame, norm=norm)
        ax_frame.set_title('Captured Frame')

        # ~ plotting the frame with increased contrast
        frame_mod = self.increase_frame_contrast(self.frame)
        ax_frame_mod.imshow(frame_mod, norm=norm)
        ax_frame_mod.set_title('Captured Frame - Increased Contrast')

        return fig

    def create_histogram_figure(self) -> plt.Figure:
        fig, (ax_hist, ax_hist_zoom) = plt.subplots(nrows=1, ncols=2, figsize=(20, 15))

        hist_bins = list(range(0, self.MAX_PIXEL_VALUE))
        ax_hist.hist(self.frame_flat, bins=hist_bins)
        ax_hist.set_title('Captured Frame - Histogram')
        ax_hist.set_xlabel('Pixel Values')
        ax_hist.set_ylabel('Occurrences')
        self.force_aspect(ax_hist, aspect=0.9)

        ax_hist_zoom.hist(self.frame_flat, bins=hist_bins)
        ax_hist_zoom.set_title('Captured Frame - Zoomed Histogram')
        ax_hist_zoom.set_xlabel('Pixel Values')
        ax_hist_zoom.set_ylabel('Occurrences')
        ax_hist_zoom.set_xlim([self.bottom_x, self.top_x])
        self.force_aspect(ax_hist_zoom, aspect=0.9)

        return fig

    def increase_frame_contrast(self, frame: np.ndarray) -> np.ndarray:
        low_value = self.bottom_x
        high_value = self.top_x
        difference = high_value - low_value

        # The absence of this section caused an error before. There is quite a reasonable probability, that this
        # difference is actually 0 because the image just is so homogeneous. If that is the case we do not perform
        # the procedure to increase the contrast (Division by zero!) and instead return the original frame
        if difference == 0:
            return frame

        frame_result = np.zeros(shape=self.frame.shape, dtype=np.int32)
        for i in range(len(frame_result)):
            for j in range(len(frame_result[i])):
                new_value = (self.MAX_PIXEL_VALUE / difference) * self.frame[i][j] - \
                            (self.MAX_PIXEL_VALUE / difference) * low_value
                frame_result[i][j] = min(new_value, self.MAX_PIXEL_VALUE)

        return frame_result

    @classmethod
    def force_aspect(cls, ax, aspect: float = 1):
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()
        base = abs(x_max - x_min) / abs(y_max - y_min)
        ax.set_aspect(aspect * base)


class FrameAcquisitionTime(AbstractTest):
    """
    Acquires multiple frames to determine the average time needed to per frame acquisition.
    """

    FRAME_COUNT = 25
    BATCH_COUNT = 5

    name = 'frame_time'
    description = (
        'This test case acquires multiple frames from the camera and records the time needed for this process. It '
        'then calculates the average time required to fetch a frame. This is done for multiple batches and the average '
        'times for all these batches is plotted. Individual errors during frame acquisition are ignored, but if more '
        'than half of the frame requests fail, the test is declared as not passed.'
    )

    def __init__(self, test_runner: TestRunner, frame_count=FRAME_COUNT, batch_count=BATCH_COUNT):
        AbstractTest.__init__(self, test_runner)

        self.frame_count = frame_count
        self.batch_count = batch_count

        self.times = np.zeros(shape=(self.batch_count, self.frame_count), dtype=np.float32)
        self.errors = np.zeros(shape=(self.batch_count, self.frame_count), dtype=np.bool)

    def run(self):
        # This method will actually request all the frames from the camera and save each individual time into the
        # self.times matrix and also fills out the self.errors matrix to true at that location if a frame request
        # results in an error. Generally, this takes some time.
        self.acquire_frames()

        # This test case will be declared a failure if more than half the frames could not be acquired due to error.
        total_errors = np.sum(self.errors)
        exit_code = bool(total_errors >= 0.5 * self.batch_count * self.frame_count)

        fig = self.create_figure()
        fig_description = (
            f'A total of {self.batch_count} batches recorded, each consisting of {self.frame_count} independent frames. '
            f'(left) The plot shows the average acquisition time in milliseconds for every batch as well as the '
            f'standard deviation within that batch. (right) This bar chart shows how many frames in each batch could'
            f'not be acquired due to some error.'
        )
        figure_result = FigureTestResult(exit_code, self.context, fig, fig_description)

        return figure_result

    def acquire_frames(self):
        for b in range(self.batch_count):
            for n in range(self.frame_count):
                try:
                    start_time = time.time()
                    self.camera.get_frame()
                    # time is a measure in seconds, but we want to measure in milli seconds, so we multiply by 1000
                    total_time = time.time() - start_time
                    self.times[b][n] = total_time * 1000
                except (PciError, FrameDecodingError) as e:
                    self.errors[b][n] = True
                    self.logger.warning(f'Batch {b}, frame {n} failed with error: {e.__class__}')

    def create_figure(self):
        fig, (ax_times, ax_errors) = plt.subplots(1, 2, figsize=(15, 20))

        masked_times = np.ma.masked_array(self.times, self.errors)

        batch_indices = np.array(range(self.batch_count))
        batch_times = np.mean(masked_times, axis=1)
        batch_stds = np.std(masked_times, axis=1)

        # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.errorbar.html
        ax_times.plot(batch_indices, batch_times, color='blue')
        ax_times.errorbar(batch_indices, batch_times, yerr=batch_stds, capsize=4.0)
        ax_times.set_title('Average acquisition time per batch')
        ax_times.set_ylim(0)
        ax_times.set_xticks(batch_indices)
        ax_times.set_ylabel('Avg. time [ms]')
        ax_times.set_xlabel('Batch index')
        force_aspect(ax_times, aspect=1)

        # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.bar.html
        batch_errors = np.sum(self.errors, axis=1)
        ax_errors.bar(batch_indices, batch_errors, color='red')
        ax_errors.set_title('Failed errors per batch')
        ax_errors.set_ylim([0, 10])
        ax_errors.set_xlabel('Batch index')
        force_aspect(ax_errors, aspect=1)

        return fig


class SingleFrameStatistics(AbstractTest):
    """
    Acquires a single frame from the camera and calculates some simple statistics for this frame. Such as the
    mean, min and max value and the standard deviation. It also creates a histogram for the frame and that plot is
    displayed in the test report.
    """

    NDIGITS = 3

    name = 'frame_statistics'
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


