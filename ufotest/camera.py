"""
A module containing the functionality related to interacting with the camera
"""
import os
import time

import shutil
import click
import numpy as np

from ufotest.config import CONFIG
from ufotest.util import execute_command, get_command_output, execute_script, run_command
from ufotest.util import cprint, cresult, cparams
from ufotest.exceptions import PciError, FrameDecodingError


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
    image = np.fromfile(path, dtype=np.uint16, count=2 * sensor_width * sensor_height * n)
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
