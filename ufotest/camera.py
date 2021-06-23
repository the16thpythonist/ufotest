"""
A module containing the functionality related to interacting with the camera
"""
import os
import time
import copy
import functools
import subprocess
from abc import abstractmethod
from typing import Optional, Any

import shutil
import click
import numpy as np
from PIL import Image

from ufotest.config import CONFIG, Config, get_path
from ufotest.util import execute_command, get_command_output, execute_script, run_command
from ufotest.util import cprint, cresult, cparams
from ufotest.exceptions import PciError, FrameDecodingError


class AbstractCamera(object):
    """
    This is the abstract base class for wrapping access to a specific camera.

    **DESIGN CHOICE**

    Here is the reasoning for why this is necessary: Previously the access to the camera was managed by a few isolated
    functions in this module. That was a simpler and less bloated version, but it also was not sub optimal for the
    following reasons:

    (1) There is the desire to be able to actually use different cameras with the ufotest framework. The isolated
    functions only implemented access to one specific model. So the reasonable alternative is to defines a set of
    methods which have to be implemented by every camera and other than that leave room for individual requirements.
    This needs an interface (this very class in other words)

    (2) Representing the camera by a class has a secondary advantage: A class has a state. This leaves the option to
    potentially cache certain values from the camera interaction and thus be more efficient. Or some functionality
    inherently requires an external state management.
    """
    def __init__(self, config: Config):
        self.config = config

    # -- state management

    @abstractmethod
    def poll(self) -> bool:
        """
        This method should return a boolean value of whether or not the camera is currently *usable*. This will most
        likely be false before a init sequence has established a connection to the camera and true afterwards. But it
        can also be used to indicate a possible temporary blocking during a readout operation or the like.
        """
        raise NotImplementedError

    @abstractmethod
    def set_up(self) -> None:
        """
        This method is supposed to execute all necessary interactions with the camera to ensure that afterwards the
        camera can be used -> return frames, manipulate properties
        """
        raise NotImplementedError

    @abstractmethod
    def tear_down(self) -> None:
        """
        This method is supposed to execute all code which is needed to properly terminate the connection with the
        camera. All cleanup operations so to say.
        It should NOT permanently disable the camera though. Subsequently calling set_up and tear_down should be
        possible
        """
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """
        This method is supposed to reset the camera into it's default internal state. It would be important that this
        also works in case the camera has issues and might not communicate correctly. Thus, this should be a hard reset
        to tear down the entire connection and then set it up from scratch would be best.
        """
        raise NotImplementedError

    # -- actual camera stuff

    @abstractmethod
    def get_frame(self) -> np.array:
        """
        This method should wrap all interaction which is required to obtain a single frame from the camera. The frame
        should then be converted into a simple two dimensional numpy array and returned.
        """
        raise NotImplementedError

    # -- manipulating internal properties

    @abstractmethod
    def set_prop(self, key: str, value: Any) -> None:
        """
        This method is supposed to set the internal property of the camera with the name *key* to the new *value*
        """
        raise NotImplementedError

    @abstractmethod
    def get_prop(self, key: str) -> Any:
        """
        This method is supposed to return the currently configured value of the internal property with the name *key*
        """
        raise NotImplementedError

    @abstractmethod
    def supports_prop(self, key: str) -> bool:
        """
        This method should return the boolean value of whether or not, the specific camera implementation supports a
        a property of the given name.
        """
        raise NotImplementedError


class InternalDictMixin:
    """
    This is a mixin which can be used for subclasses of AbstractCamera. This abstract camera interface expects the
    ability to manipulate internal camera properties using three distinct functions. This mixin offers a default
    implementation for these methods, which will manage these internal camera properties in an internal dict
    "self.values". The default implementation will simple read and write these values to this internal dict. But this
    mixin also allows to implement overwrite getter and setter methods for each prop to customize the behavior.

    **EXAMPLE**

    In the order of the multiple inheritance, the mixins are best placed first. This mixin furthermore expects the
    subclass to define a static attribute "default_values", which is a dict and contains the default values for all the
    props. This dict should contain all (and only) entries for each prop which is supported by the camera, because the
    outcome of "supports_prop" is defined by whether or not the prop is defined in this default dict.

    The behavior of the get / set operation for a specific prop can be customized by simply implementing a method which
    is called get_{prop name} / set_{prop name}

    .. code-block: python

        class ExampleCamera(InternalDictMixin, AbstractCamera):

            default_values = {'exposure_time': 100}

            def set_exposure_time(value):
                # You only have to implement the instructions to actually modify the camera here.
                # At this point the value is already saved in the internal self.values dict!

    **WHAT IT EXPECTS**

    - static attribute dict *default_dict*
    - no instance attribute named *values*
    """
    # default_values = {...}

    def __init__(self):
        if not hasattr(self, 'default_values'):
            raise NotImplementedError((f'You are attempting to instantiate a subclass of "InternalDictMixin" without '
                                       f'having defined a static attribute "default_values". This mixin expects this '
                                       f'attribute to exists. Please add this static dict to the subclass!'))

        self.values = copy.deepcopy(self.default_values)

    def supports_prop(self, key: str) -> bool:
        """
        Returns whether or not the prop with the name *key* is supported. This is determined by it's existence as a key
        within default_values.

        :param str key: The string name of the prop

        :returns bool:
        """
        return key in self.default_values.keys()

    def set_prop(self, key: str, value: Any) -> None:
        """
        Sets the new value of the prop with the name *key* to *value*

        :param str key: The string name of the prop
        :param value: The new value

        :returns: void
        """
        self.values[key] = value

        method_name = f'set_{key}'
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            method(value)

    def get_prop(self, key: str) -> Any:
        """
        Returns the current value of the prop with the name *prop*

        :param str key: The string name of the prop

        :returns: The value of the prop
        """
        value = self.values[key]

        method_name = f'get_{key}'
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            value = method()

        return value

# TODO: CommandHistoryMixin


class UfoCamera(InternalDictMixin, AbstractCamera):
    """
    Implements the interface to interact with the UFO camera.
    """

    default_values = {
        'exposure_time': 1
    }

    def __init__(self, config: Config):
        # The InternalDictMixin provides a default implementation for the property management of the camera class. On
        # default getting and setting will modify the values of the internal "values" dict. For specific properties
        # behavior can be overwritten by providing special getter and setter methods following the naming convention
        # of the property
        InternalDictMixin.__init__(self)
        AbstractCamera.__init__(self, config)

        self.tmp_path = self.config.pm.apply_filter('ufo_camera_tmp_path', value='/tmp')

        # These paths are required for the method of how frames are retrieved from the camera. This works by using a
        # system command "pci" this command will require the received data to be written to files. In a first stage the
        # raw received bytes are written to the .out file. This data is then decoded to produce image in a .raw format.
        self.data_path = os.path.join(self.tmp_path, 'frame')
        self.frame_path = self.data_path + '.raw'

    # -- AbstractCamera --
    # The following methods are the abstract methods which have to be implemented for AbstractCamera

    def get_frame(self) -> np.ndarray:
        """
        Returns a frame from the camera as a numpy array. The dimensions of this array are dependent on the camera
        sensor / the configuration of the camera sensor selected in the config file of the project.

        The process of retrieving a frame can be roughly outlined like this. Using the command line interface of
        "pcitool" specific registers are set, which instruct the camera to acquire a frame. The data of this frame is
        then saved as a raw bytestream. By using the command line interface of ipedecode this frame is decoded into the
        RAW image format, which is then loaded into a numpy array and returned.

        :return: np.ndarray
        """
        self.request_frame()
        self.receive_frame()
        self.decode_frame()

        # At this point, if everything worked out as it should, the frame data resides in the file references by
        # self.frame_path as a .raw file. Now we only need to interpret this file as a numpy array and return that.
        frames = import_raw(self.frame_path, 1, self.config.get_sensor_width(), self.config.get_sensor_height())
        frame_array = frames[0]
        return frame_array

    def poll(self) -> bool:
        """
        Returns whether or not the camera can be used.

        :return: bool
        """
        result = self.config.sm.invoke('status')
        if self.config.verbose():
            cprint(result['stdout'])

        return result['exit_code']

    def set_up(self):
        """
        Executes the routine to set up the camera for subsequent operations.

        Specifically this involves the following series of scripts:
        - pcie_init
        - reset_fpga
        - power_up
        - reset

        :return: void
        """
        self.config.sm.invoke('pcie_init', args={'prefix': 'sudo', 'postfix': ''})
        time.sleep(0.5)
        self.config.sm.invoke('reset_fpga')
        time.sleep(0.5)
        self.config.sm.invoke('power_up')
        time.sleep(0.5)
        self.config.sm.invoke('reset')

    def tear_down(self):
        pass

    def reset(self):
        pass

    def set_exposure_time(self, value: int):
        """
        *KIND OF* sets the exposure time of the camera. At the current point in time, this method does modify the
        exposure time of the camera, but which value in ms it actually is, is unclear. Supported are int values up to
        12. Generally the higher the value the higher the exposure time.

        :return void:
        """
        self.pci_write('9000', 'a001')
        time.sleep(0.2)
        self.pci_read('9010', 1)
        time.sleep(0.2)

        hex_value = hex(41216 + 2 ** value).lstrip('0x')
        self.pci_write('9000', hex_value)
        time.sleep(0.2)
        self.pci_read('9010', 1)
        time.sleep(0.2)

    # -- Helper methods --
    # These methods wrap camera specific functionality which is required to implement the more top level behavior

    def decode_frame(self):
        """
        Uses the raw frame data stored in the file at "data_path" to decode it into an actual image of the
        RAW format, which is stored at the path "frame_path"

        :raises FrameDecodingError: If there is any problem during the decoding process
        :return: void
        """
        # This command will decode the raw data which should have previously been written as the file
        # referenced by self.data_path and decode it into an actual picture in the .raw format. The resulting file
        # is written to the same folder and has the same filename as the input file but with a .raw appended.
        # Its important to note that this operation needs to be supplied with the camera dimensions. So it is
        # instrumental that the correct dimensions are set in the config file which fit the uses sensor.
        decode_command = 'ipedec -r {height} --num-columns {width} {path} {verbose}'.format(
            height=self.config.get_sensor_height(),
            width=self.config.get_sensor_width(),
            path=self.data_path,
            verbose='-v' if self.config.verbose() else ''
        )
        result = self.execute_command(decode_command)

        # If this step fails, it is usually because not enough bytes could be received. Wrong data vs no data at all.
        if result['exit_code']:
            stdout = result['stdout']
            raise FrameDecodingError(stdout[:stdout.find('\n')])

    def receive_frame(self, force=True):
        """
        Reads out the raw byte data of the previously requested frames and stores it into a temporary file
        whose path is defined in the "data_path" property of this class.

        :param force: Boolean flag of whether or not to forcefully delete the previous data file. Default is True

        :raises PciError: If there is any problem with receiving the frame
        :return: void
        """
        if force and os.path.exists(self.data_path):
            os.remove(self.data_path)

        # This command will trigger a continuous readout of the camera (this is for larger data chunks). The data is
        # written into a file. This data is not yet usable! It is in a special transfer format and still needs decoding!
        receive_command = f'pci -r dma0 --multipacket -o {self.data_path}'
        result = self.execute_command(receive_command)

        # A PciError is used when the data transfer itself fails and a DecodingError if the receive itself is successful
        # but the data is wrong.
        if result['exit_code']:
            stdout = result['stdout']
            raise PciError(stdout[:stdout.find('\n')])

        # I have no clue what this does, but it is also done in micheles script.
        time.sleep(0.1)
        pci_read('9050', '12')
        time.sleep(0.1)

    def request_frame(self):
        """
        Writes the necessary registers of the camera to indicate that a new frame is requested

        :return: void
        """
        # At this point I have no clue, what these instructions specifically do. I just imitated the relevant
        # section from micheles bash script for requesting frames.
        pci_write('0x9040', '0x80000201')
        pci_write('0x9040', '0x80000209')
        time.sleep(0.1)
        pci_read('9070', '4')
        pci_write('0x9040', '0x80000201')
        time.sleep(0.01)

    def pci_write(self, addr: str, value: str) -> bool:
        """
        Uses the "pci" command to write a new value to the given register address of the FPGA. Returns the boolean
        value of whether or not the write operation was successful.

        :param addr: The string representation of the register address to write to
        :param value: The actual value to write to the register

        :return: boolean
        """
        pci_command = f'pci -w {addr} {value}'
        result = self.execute_command(pci_command)
        return not bool(result['exit_code'])

    def pci_read(self, addr: str, size: int) -> str:
        """
        Uses the "pci" command to perform a register readout operation of the FPGA at the given address and with the
        given size. Returns the string output of the console command.

        :return: string
        """
        pci_command = 'pci -r {} -s {}'.format(addr, str(size))
        result = self.execute_command(pci_command)
        return result['stdout']

    def execute_command(self, command: str, cwd: Optional[str] = None) -> dict:
        """
        Executes a terminal command in a separate shell process and returns a dict which contains the information about
        the outcome of the command.

        The returned dict contains the following fields:
        - stdout: A string which contains the entire console output of the command
        - stderr: A string which contains the entire error output of the command
        - exit_code: The int exit code of the command

        :param command: The bash string to be executed in the terminal
        :param cwd: An optional string to define the absolute path of the folder in which the command should be
            executed in.

        :return: dict
        """
        completed_process = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return {
            'exit_code': completed_process.returncode,
            'stdout': completed_process.stdout.decode(),
            'stderr': completed_process.stderr.decode()
        }


class MockCamera(InternalDictMixin, AbstractCamera):
    """
    This is a mock implementation of the AbstractCamera interface. It does not actually interface with any real
    hardware, it only simulates camera behavior testing purposes.

    **FRAMES**

    As expected by the AbstractCamera interface, this class implements a functional "get_frame" method. This method
    returns a static picture which is based on the "sample.png" image from the static folder of the ufotest
    installation. The image itself displays some kind of landscape.

    **SET UP**

    The camera does indeed require the "set_up" method to be called before any frames can be captured. This is however
    not due to any specific reason. The setup status is internally simple represented as a boolean flag. This is to
    simulate camera behavior as well as possible.

    **EXPOSURE TIME**

    This class supports the "exposure_time" prop. It can be set as int values between 1 and 100. This class actually
    attempts to simulate the effects of exposure time somewhat. With higher values the static image becomes (1)
    brighter, as in higher pixel values overall and (2) there is more noise: The magnitude of the additive gaussian
    noise gets more with higher exposure time.
    """
    default_values = {
        'exposure_time': 1,
        'min_exposure_time': 1,
        'max_exposure_time': 100
    }

    def __init__(self, config: Config):
        AbstractCamera.__init__(self, config)
        InternalDictMixin.__init__(self)

        self.enabled = False

        # -- loading the sample image
        self.image_path = get_path('static', 'mock.jpg')
        self.image = self.load_image(self.image_path)

    @functools.lru_cache
    def load_image(self, image_path: str):
        """
        Uses pillow to load the image with the given *image_path* as a grayscale image object.

        **DESIGN CHOICE**

        One could say that this method is redundant, because the little code within I could have just called within the
        constructor as it is. That is true, but the important thing is that this method is cached. The loading of the
        image is relatively time intensive. This is not a problem were this class be used in the normal ufotest routine
        the camera class is only instantiated once. But the mock implementation is mainly for testing and for testing
        the camera class is instantiated many more times, such that this runtime becomes an issue...

        :param image_path: The str absolute path to the image file

        :returns Image: the image object
        """
        return Image.open(image_path).convert('L')

    @functools.lru_cache
    def resize_image(self, width, height):
        image = self.image.resize((width, height))
        frame_array = np.array(image, dtype=np.float64)
        return frame_array

    def get_frame(self) -> np.array:
        # ~ Resizing the image to fit the given geometry constraints
        width = self.config.get_sensor_width()
        height = self.config.get_sensor_height()
        frame_array = self.resize_image(width, height)

        # ~ Applying the exposure time to the image
        # The first effect of a higher exposure time is that the image gets brighter
        exposure_time = self.get_prop('exposure_time')
        frame_array *= np.sqrt(exposure_time / self.get_prop('min_exposure_time'))
        # The other effect is that there is more noise
        frame_array = self.add_gaussian_noise(frame_array, exposure_time)

        return frame_array.astype(np.uint16)

    def poll(self):
        return self.enabled

    def set_up(self):
        self.enabled = True

    def tear_down(self):
        self.enabled = False

    def reset(self):
        pass

    # -- utility methods

    @classmethod
    def add_gaussian_noise(cls, frame_array: np.ndarray, intensity: float) -> np.ndarray:
        """
        Given a base frame *frame_array* this method generates a random gaussian noise centered around 0 and with a
        standard deviation of *intensity* with the original frames shape and then adds the noise array to this base
        frame and returns the result.

        :returns: The modified frame array
        """
        noise_array = np.random.normal(loc=0.0, scale=intensity, size=frame_array.shape)
        return frame_array + noise_array

# == DEPRECATED ==


def pci_write(addr: str, value: str):
    pci_command = 'pci -w {} {}'.format(addr, value)
    exit_code = execute_command(pci_command, verbose=False)
    if exit_code:
        click.secho('Command "{}" failed!'.format(pci_command), fg='red')


def pci_read(addr: str, size):
    pci_command = 'pci -r {} -s {}'.format(addr, str(size))
    value = get_command_output(pci_command)
    return value


def import_raw(path: str, n: int, sensor_width: int, sensor_height: int):
    image = np.fromfile(path, dtype=np.uint16, count=sensor_width * sensor_height * n)
    image = image.reshape((n, sensor_height, sensor_width))
    return image


def set_up_camera(verbose: bool = False):
    # enable the drivers and stuff
    execute_script('pcie_init', verbose=verbose, prefix='sudo ')
    time.sleep(1)
    # Reset all the parameters for the camera
    execute_script('reset_fpga', verbose=verbose)
    time.sleep(1)
    # Enable the sensor power supply
    execute_script('power_up', verbose=verbose)
    time.sleep(1)
    # ?
    execute_script('reset_tp', verbose=verbose)
    time.sleep(1)
    # Display the status just to be save
    execute_script('status', verbose=verbose)

    click.secho('Camera set up finished\n', bold=True)


def tear_down_camera(verbose: bool = False):
    # Disable the sensor power supply
    execute_script('power_down', verbose=verbose)
    # Display the status just to be save
    execute_script('status', verbose=verbose)

    click.secho('camera tear down finished\n', bold=True)


# def get_frame(path: str = '/tmp/frame.raw', verbose: bool = False):
#     exit_code = save_frame(path, verbose)
#
#     if not exit_code:
#         # read the data of the frame and return it
#         with open(path, mode='rb+') as file:
#             return file.read()
#     else:
#         return b''


def save_frame(path: str, tmp_path: str = '/tmp') -> int:
    """
    :deprecated:
    """
    # ~ REQUESTING FRAME FROM CAMERA
    # This function sends the necessary PCI instructions, which tell the camera to start sending frame data
    request_frame()

    # ~ RECEIVING FRAME DATA
    data_path = os.path.join(tmp_path, 'frame.out')
    receive_frame(data_path)

    # ~ DECODING FRAME DATA
    frame_path = decode_frame(data_path)

    # Saving the frame to the correct position
    if True:
        shutil.move(frame_path, path)
        if True:
            click.secho('Saved frame to "{}"'.format(path), fg='green')
    else:
        click.secho('Error saving frame!', fg='red')

    return 1


# TODO: If I wanted to be platform independent I would have to replace the default value here.
def get_frame(tmp_path: str = '/tmp') -> str:
    """Requests a frame from the camera, receives the data, decodes it into a '.raw' image and saves it.

    :param tmp_path: A string path to a temporary folder, which is used to store the intermediate files which are
        produced during the reception and decoding process. The final image file will also be saved to this folder.
        Defaults to '/tmp'

    :raises PciError: Whenever anything goes wrong with the PCI communication with the camera.
    :raises FrameDecodingError: Whenever anything goes wrong during the decoding process of the camera.

    :returns: The string path of the final '.raw' file.
    """
    # ~ REQUESTING FRAME FROM CAMERA
    # This function sends the necessary PCI instructions, which tell the camera to start sending frame data
    request_frame()

    # ~ RECEIVING FRAME DATA
    data_path = os.path.join(tmp_path, 'frame.out')
    # We explicitly remove the temporary file here for the following reason: It turns out that the pci read command
    # which is used in "receive_frame" does not overwrite but append to the end! But we really want to replace temporary
    # file so that it always just contains the data for a single frame.
    if os.path.exists(data_path):
        os.remove(data_path)
    receive_frame(data_path)  # raises: PciError

    # ~ DECODING FRAME DATA
    frame_path = decode_frame(data_path)  # raises: FrameDecodingError

    return frame_path


def request_frame() -> None:
    """Sends the necessary PCI instructions to request a frame from the camera

    This function is based on one of Michele's scripts called "frame.sh"
    """
    # At this point I have no clue, what these instructions specifically do. I just imitated the relevant section from
    # Micheles bash script for requesting frames.
    pci_write('0x9040', '0x80000201')
    pci_write('0x9040', '0x80000209')
    time.sleep(0.1)
    pci_read('9070', '4')
    pci_write('0x9040', '0x80000201')
    time.sleep(0.01)


def receive_frame(data_path: str) -> None:
    """Receives the raw data for a frame over the PCI interface and saves it into the file *data_path*

    This function can only be called when a request for frame data has previously been sent to the camera!
    This function is based on one of Michele's scripts called "frame.sh"

    :raises PciError: When the data reception command exits with exit code 1. The error message contains some of the
        output of the command.

    :param data_path: The string path of the *file* into which to save the frame data. Does not have to exist yet.
    """
    receive_command = 'pci -r dma0 --multipacket -o {}'.format(data_path)
    exit_code, stdout = run_command(receive_command)
    if exit_code:
        raise PciError(stdout[:stdout.find('\n')])
    time.sleep(0.1)
    pci_read('9050', '12')
    time.sleep(0.1)


def decode_frame(data_path: str) -> str:
    """Decodes the frame data given at *data_path* and returns the path to the .raw image file

    This function can only be called, after the actual frame data has been received from the camera. The file with the
    raw data has to already exist.
    This function is based on one of Michele's scripts called "frame.sh"

    :param data_path: The string path of the file which contains the raw frame data.

    :raises FrameDecodingError: When the decode command fails. The error message contains some part of the commands
        output.

    :returns: The string path to the decoded .raw image file
    """
    frame_path = f'{data_path}.raw'

    if CONFIG.verbose():
        cprint('Decoding the image, with the following settings:')
        cparams({
            'camera sensor width': CONFIG.get_sensor_width(),
            'camera sensor height': CONFIG.get_sensor_height(),
            'input data path': data_path,
            'output frame path': frame_path
        })

    decode_command = 'ipedec -r {height} --num-columns {width} {path} {verbose}'.format(
        height=CONFIG.get_sensor_height(),
        width=CONFIG.get_sensor_width(),
        path=data_path,
        verbose='-v' if CONFIG.verbose() else ''
    )

    exit_code, stdout = run_command(decode_command)
    if exit_code:
        raise FrameDecodingError(stdout[:stdout.find('\n')])

    return frame_path
