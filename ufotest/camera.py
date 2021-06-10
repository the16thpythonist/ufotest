"""
A module containing the functionality related to interacting with the camera
"""
import os
import time
import subprocess
from abc import abstractmethod
from typing import Optional

import shutil
import click
import numpy as np

from ufotest.config import CONFIG, Config
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

    @abstractmethod
    def get_frame(self) -> np.array:
        raise NotImplementedError

    @abstractmethod
    def poll(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_up(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def tear_down(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        raise NotImplementedError


# TODO: CommandHistoryMixin


class UfoCamera(AbstractCamera):

    def __init__(self, config: Config):
        AbstractCamera.__init__(self, config)

        self.tmp_path = self.config.pm.apply_filter('ufo_camera_tmp_path', value='/tmp')

        # These paths are required for the method of how frames are retrieved from the camera. This works by using a
        # system command "pci" this command will require the received data to be written to files. In a first stage the
        # raw received bytes are written to the .out file. This data is then decoded to produce image in a .raw format.
        self.data_path = os.path.join(self.tmp_path, 'frame')
        self.frame_path = self.data_path + '.raw'

    # -- AbstractCamera --
    # The following methods are the abstract methods which have to be implemented for AbstractCamera

    def get_frame(self) -> np.array:
        self.request_frame()
        self.receive_frame()
        self.decode_frame()

        # At this point, if everything worked out as it should, the frame data resides in the file references by
        # self.frame_path as a .raw file. Now we only need to interpret this file as a numpy array and return that.
        frame_array = import_raw(self.frame_path, 1, self.config.get_sensor_width(), self.config.get_sensor_height())
        return frame_array

    def poll(self) -> bool:
        pass

    def set_up(self):
        pass

    def tear_down(self):
        pass

    def reset(self):
        pass

    # -- Helper methods --
    # These methods wrap camera specific functionality which is required to implement the more top level behavior

    def decode_frame(self):

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
        # At this point I have no clue, what these instructions specifically do. I just imitated the relevant
        # section from micheles bash script for requesting frames.
        pci_write('0x9040', '0x80000201')
        pci_write('0x9040', '0x80000209')
        time.sleep(0.1)
        pci_read('9070', '4')
        pci_write('0x9040', '0x80000201')
        time.sleep(0.01)

    def pci_write(self, addr: str, value: str) -> bool:
        pci_command = f'pci -w {addr} {value}'
        result = self.execute_command(pci_command)
        return not bool(result['exit_code'])

    def pci_read(self, addr: str, size: int) -> str:
        pci_command = 'pci -r {} -s {}'.format(addr, str(size))
        result = self.execute_command(pci_command)
        return result['stdout']

    def execute_command(self, command: str, cwd: Optional[str] = None) -> dict:
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


class MockCamera(AbstractCamera):

    def __init__(self, config: Config):
        AbstractCamera.__init__(self, config)

        self.enabled = False

    def get_frame(self) -> np.array:
        width = self.config.get_sensor_width()
        height = self.config.get_sensor_height()

        frame_array = np.random.rand(height, width)
        return frame_array

    def poll(self):
        return self.enabled

    def set_up(self):
        self.enabled = True

    def tear_down(self):
        self.enabled = False

    def reset(self):
        pass


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
