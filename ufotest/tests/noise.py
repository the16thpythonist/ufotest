import math
import time
import random
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


class CalculateMultiNoiseTest(AbstractTest):

    FRAME_COUNT = 10
    name = 'calculate_multi_noise'
    description = (
        f'Calculates the noise with a slightly different procedure: Takes {FRAME_COUNT} frames from the camera '
        f'and then calculates the variance for every pixel. The final variance and thus noise is calculated as the '
        f'mean over all those pixel specific variances'
    )

    def __init__(self, test_runner: TestRunner):
        super(CalculateMultiNoiseTest, self).__init__(test_runner)
        self.frames = []
        self.frame_array = None

        self.variance_frame = np.zeros(shape=(self.config.get_sensor_height(), self.config.get_sensor_width()))
        self.noise_frame = np.zeros(shape=(self.config.get_sensor_height(), self.config.get_sensor_width()))

    def run(self):
        # ~ Getting the frames from the camera
        for i in range(self.FRAME_COUNT):
            try:
                frame = self.camera.get_frame()
                self.frames.append(frame)
            except (FrameDecodingError, PciError) as e:
                cprint(f'Failed to acquire frame {i + 1}')

        # ~ Calculating the noise
        self.frame_array = np.zeros(shape=(
            self.config.get_sensor_height(),
            self.config.get_sensor_width(),
            len(self.frames)
        ))
        for index, frame in enumerate(self.frames):
            self.frame_array[:, :, index] = frame

        cprint(f'Assembled {len(self.frames)} frames into a 3d numpy array')
        cprint(f'max: {np.max(self.frame_array)} - min: {np.min(self.frame_array)}')

        self.variance_frame = np.var(self.frame_array, axis=2)
        self.noise_frame = np.sqrt(self.variance_frame)

        variance = np.mean(self.variance_frame)
        noise = np.sqrt(variance)

        fig = self.create_variance_figure()

        return CombinedTestResult(
            FigureTestResult(0, self.test_runner.context, fig, ''),
            DictTestResult(0, {
                'variance': f'{variance:0.2f}',
                'noise': f'{noise:0.2f}'
            })
        )

    def create_variance_figure(self):
        fig, (variance_ax, noise_ax) = plt.subplots(nrows=1, ncols=2, figsize=(10, 15))

        variance_ax.imshow(self.variance_frame, vmin=0, vmax=500)
        variance_ax.set_title('Pixel specific variance')

        variance_ax.text(500, 500, f'min: {np.min(self.variance_frame):0.2f} - max: {np.max(self.variance_frame):0.2f}',
                         bbox={'facecolor': 'white', 'alpha': 0.5, 'pad': 10})

        noise_ax.imshow(self.noise_frame, vmin=0, vmax=30)
        noise_ax.set_title('Pixel specific noise')

        return fig


class CalculateNoiseWorker(mp.Process):

    def __init__(self, task_queue: mp.Queue, result_queue: mp.Queue):
        super(CalculateNoiseWorker, self).__init__()
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self):
        while not self.task_queue.empty():
            # The elements of the task queue are tuples, where the first element is the exposure time which was used
            # for that experiment and the remaining two elements are the np arrays frame objects which were taken from
            # the camera at that exposure time.
            exposure_time, frame1, frame2 = self.task_queue.get()

            variance = calculate_pair_variance(frame1, frame2)
            print(f"variance {variance}")
            noise = np.sqrt(variance)

            # The result will be a tuple whose first element is again the exposure time and the second element is the
            # resulting noise value which was calculated
            result = (exposure_time, noise)
            self.result_queue.put(result)


class CalculateNoiseMultiProcessing(AbstractTest):

    MEASUREMENT_COUNT = 10
    WORKER_COUNT = 4

    name ='calculate_noise_parallel'
    description = (
        f'This test case simply investigates the advantages of the multiprocessing implementation of the noise '
        f'calculation. The operation of calculating the noise for a pair of frames is very costly. If many such '
        f'calculations have to be made, multiprocessing may be an appropriate means of speeding up the process.'
        f'This test compares a purely sequential calculation of {MEASUREMENT_COUNT} noise values with using '
        f'{WORKER_COUNT} worker processes instead'
    )

    def __init__(self, test_runner: TestRunner):
        super(CalculateNoiseMultiProcessing, self).__init__(test_runner)

        # Now I think requesting all the frames for the calculation from the camera would be kind of a waste of time,
        # because in the end this test is not about the actual noise values but the calculation. But on the other hand
        # I also dont want to use the same two frames for all of the experiments, because I fear that could influence
        # the speed, due to favorably filled computation caches or something like that.
        # Thus we will request TEN frames from the camera and then pick two at random for each calculation
        self.frames = []

        # This will be the list with the task tuples.
        self.tasks = []

        self.sequential_time = 0
        self.parallel_time = 0

    def run(self):
        # At first we request the frames from the camera and then we do the random picking to assemble them into as many
        # frame pairs as we need.
        for i in range(10):
            try:
                frame = self.camera.get_frame()
                self.frames.append(frame)
            # It does not matter if it is less than 10 frames by a few
            except:
                pass

        for i in range(self.MEASUREMENT_COUNT):
            frame1 = random.choice(self.frames)
            frame2 = random.choice(self.frames)
            self.tasks.append((0, frame1, frame2))

        cprint(f'Acquired {len(self.frames)} frames from the camera')

        self.calculate_sequential()
        self.calculate_parallel()

        improvement = (self.parallel_time / self.sequential_time) * 100
        average = self.parallel_time / self.MEASUREMENT_COUNT

        message = (
            f'Sequential processing of {self.MEASUREMENT_COUNT} noise calculations took <strong>'
            f'{self.sequential_time:0.2f}</strong> seconds and parallel processing took <strong>'
            f'{self.parallel_time:0.2f}</strong> seconds. That is {improvement:0.2f} percent of the time. For '
            f'a parallel processing with {self.WORKER_COUNT} this makes an average time of <strong>'
            f'{average:0.2f}</strong> seconds per noise calculation.'
        )

        return MessageTestResult(0, message)

    def calculate_sequential(self):
        start_time = time.time()
        for exp, frame1, frame2 in self.tasks:
            variance = calculate_pair_variance(frame1, frame2)
            noise = np.sqrt(variance)

        end_time = time.time()
        self.sequential_time = end_time - start_time
        cprint(f'Sequential time: {self.sequential_time}')

    def calculate_parallel(self):
        start_time = time.time()

        task_queue = mp.Queue()
        [task_queue.put(task) for task in self.tasks]
        result_queue = mp.Queue()

        workers = []
        for i in range(self.WORKER_COUNT):
            worker = CalculateNoiseWorker(task_queue, result_queue)
            worker.start()
            workers.append(worker)
            cprint(f'Started worker {i + 1}')

        [worker.join() for worker in workers]
        end_time = time.time()

        self.parallel_time = end_time - start_time
        cprint(f'Parallel time: {self.parallel_time}')


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

    def __init__(self, test_runner: TestRunner, start: int = 3, end: int = 100, step: int = 5, reps: int = 10):
        MeasureNoiseMixin.__init__(self)
        AbstractTest.__init__(self, test_runner)

        self.start = start
        self.end = end
        self.step = step
        self.reps = reps

        self.exposure_times = list(range(self.start, self.end + 1, self.step))
        self.tasks = []

        self.noises = defaultdict(list)

    def run(self):
        # ~ Fetching all the images from the camera first
        error_count = 0
        for exposure_time in self.exposure_times:
            self.camera.set_prop('exposure_time', exposure_time)
            cprint(f'set exposure time: {exposure_time}')

            for i in range(self.reps):
                try:
                    frame1 = self.camera.get_frame()
                    frame2 = self.camera.get_frame()
                    self.tasks.append((exposure_time, frame1, frame2))
                    cprint(f'Acquired two frames for exp time: {exposure_time}')

                except (PciError, FrameDecodingError):
                    error_count += 1
                    cprint(f'Failed to acquire frames for exp time: {exposure_time}')

        # ~ Calculating the noises in parallel
        task_queue = mp.Queue()
        [task_queue.put(task) for task in self.tasks]
        result_queue = mp.Queue()

        worker_count = 4
        workers = []
        for i in range(worker_count):
            worker = CalculateNoiseWorker(task_queue, result_queue)
            worker.start()
            workers.append(worker)

        [worker.join() for worker in workers]

        while not result_queue.empty():
            exposure_time, noise = result_queue.get()
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


class CalculateDarkPhotonTransferCurve2(AbstractTest):

    name = 'dark_photon_transfer_curve_alt'
    description = '---'

    def __init__(self, test_runner: TestRunner):
        super(CalculateDarkPhotonTransferCurve2, self).__init__(test_runner)

    def run(self):

        for exposure_time in [3, 7, 9, 22, 45, 53]:
            self.camera.set_prop('exposure_time', exposure_time)
            frames = []
            for i in range(30):
                try:
                    frames.append(self.camera.get_frame())
                except (PciError, FrameDecodingError) as e:
                    print(e.__class__)

            frame_array = np.zeros(shape=(
                self.config.get_sensor_height(),
                self.config.get_sensor_width(),
                len(frames)
            ))
            for index, frame in enumerate(frames):
                frame_array[:, :, index] = frame

            variance = np.mean(np.var(frame_array, axis=2) / len(frames))
            noise = np.sqrt(variance)
            cprint(f'{variance} - {noise}')

        return MessageTestResult(0, "a")

# TODO: Why do I get PCIErrors with higher exposure times
# TODO: Make the device manager better.
