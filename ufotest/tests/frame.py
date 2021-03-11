import os
import math
import datetime
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt

from ufotest.util import setup_environment, random_string
from ufotest.camera import save_frame, import_raw, get_frame

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

        creation_datetime = datetime.datetime.now()
        description = 'Frame taken from the camera @ {}'.format(creation_datetime.strftime('%d.%m.%Y, %H:%M'))

        fig, ax = plt.subplots(nrows=1, ncols=1)
        ax.imshow(frames[0])

        figure_result = FigureTestResult(0, self.context, fig, description)
        return figure_result


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

        self.file_name = random_string(16)
        self.file_path = '/tmp/{}.raw'.format(self.file_name)

        self.histogram_name = 'single_frame_statistics.png'
        self.histogram_path = os.path.join(self.context.folder_path, self.histogram_name)

    def run(self):
        setup_environment()

        # -- ACQUIRE FRAME AS MATRIX
        save_frame(self.file_path)
        frames = import_raw(self.file_path, 1, self.config.get_sensor_width(), self.config.get_sensor_height())
        frame = frames[0]

        stats = self.create_frame_statistics(frame)
        dict_result = DictTestResult(0, stats)
        fig = self.create_histogram_figure(frame)
        figure_result = FigureTestResult(0, self.context, fig, description='')

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

    name = 'calculate_pair_noise'
    description = (
        'Calculates the noise for a pair of frames.'
    )

    def __init__(self, test_runner):
        AbstractTest.__init__(self, test_runner)

    def run(self):

        frame1_path = get_frame()
        frame1 = import_raw(frame1_path, 1, self.config.get_sensor_width(), self.config.get_sensor_height())[0]
        frame1_mean = np.mean(frame1)

        frame2_path = get_frame()
        frame2 = import_raw(frame2_path, 1, self.config.get_sensor_width(), self.config.get_sensor_height())[0]
        frame2_mean = np.mean(frame2)

        row_count = len(frame1)
        column_count = len(frame1[0])
        squared_sum = 0
        for i in range(row_count):
            for j in range(column_count):
                squared_sum += ((frame1[i][j] - frame1_mean) - (frame2[i][j] - frame2_mean))**2

        variance = squared_sum / (2 * row_count * column_count)
        standard_deviation = math.sqrt(variance)

        dict_result = DictTestResult(0, {
            'variance': round(variance, ndigits=self.NDIGITS),
            'standard deviation': round(standard_deviation, ndigits=self.NDIGITS)
        })

        return dict_result


class CalculateSeriesNoiseTest(AbstractTest):

    name = 'calculate_series_noise'
    description = 'Calculates the camera noise from a series of images'

    def __init__(self, test_runner: TestRunner):
        AbstractTest.__init__(self, test_runner)

    def run(self):
        pass
