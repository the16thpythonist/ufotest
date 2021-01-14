import os
import datetime

import numpy as np
import matplotlib.pyplot as plt

from ufotest.util import setup_environment, random_string
from ufotest.camera import save_frame, import_raw

from ufotest.testing import AbstractTest, TestRunner, ImageTestResult, CombinedTestResult, DictTestResult
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
        save_frame(self.frame_path, verbose=False)

        creation_datetime = datetime.datetime.now()
        description = 'Frame taken from the camera @ {}'.format(creation_datetime.strftime('%d.%m.%Y, %H:%M'))

        return ImageTestResult(0, self.frame_path, description, url_base=self.context.folder_url)


class SingleFrameStatistics(AbstractTest):
    """
    Acquires a single frame from the camera and calculates some simple statistics for this frame. Such as the
    mean, min and max value and the standard deviation. It also creates a histogram for the frame and that plot is
    displayed in the test report.
    """

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
        save_frame(self.file_path, verbose=False)
        frame = import_raw(self.file_path, 1, self.config.get_sensor_width(), self.config.get_sensor_height())

        statistics_result = self.calc_statistics_result(frame)
        histogram_result = self.calc_histogram_result(frame)

        return CombinedTestResult(
            statistics_result,
            histogram_result
        )

    def calc_statistics_result(self, frame: np.ndarray) -> DictTestResult:
        statistics = {
            'average':                      round(float(np.mean(frame)), 4),
            'variance':                     round(float(np.var(frame)), 4),
            'standard deviation':           round(float(np.std(frame)), 4),
            'min value':                    np.min(frame),
            'max value':                    np.max(frame)
        }
        return DictTestResult(0, statistics)

    def calc_histogram_result(self, frame: np.ndarray) -> ImageTestResult:
        image_hist = np.empty(shape=(2048,))
        for row in frame:
            for value in row:
                image_hist[value] += 1
        plt.hist(image_hist)
        plt.title('Histogram of grayscale values')
        plt.ylabel('grayscale values')
        plt.imsave(self.histogram_path, dpi=100)
        result = ImageTestResult(
            0,
            self.histogram_path,
            'A histogram of the frame.',
            url_base=self.context.folder_url
        )

        plt.clf()

        return result
