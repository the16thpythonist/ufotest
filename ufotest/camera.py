"""
A module containing the functionality related to interacting with the camera
"""
import os
import time

import shutil
import click
import numpy as np

from ufotest.config import CONFIG
from ufotest.util import execute_command, get_command_output, execute_script


def pci_write(addr: str, value: str):
    pci_command = 'pci -w {} {}'.format(addr, value)
    exit_code = execute_command(pci_command, False)
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
    execute_script('pcie_init', verbose=verbose)
    # Reset all the parameters for the camera
    execute_script('reset_fpga', verbose=verbose)
    # Enable the sensor power supply
    execute_script('power_up', verbose=verbose)
    # ?
    execute_script('reset', verbose=verbose)
    # Display the status just to be save
    execute_script('status', verbose=verbose)

    click.secho('Camera set up finished\n', bold=True)


def tear_down_camera(verbose: bool = False):
    # Disable the sensor power supply
    execute_script('power_down', verbose=verbose)
    # Display the status just to be save
    execute_script('status', verbose=verbose)

    click.secho('camera tear down finished\n', bold=True)


def get_frame(path: str = '/tmp/frame.raw', verbose: bool = False):
    exit_code = save_frame(path, verbose)

    if not exit_code:
        # read the data of the frame and return it
        with open(path, mode='rb+') as file:
            return file.read()
    else:
        return b''


def save_frame(path: str, verbose: bool, tmp_path='/tmp'):
    # Requesting the frame from the camera
    if verbose:
        click.secho('Sending frame request')
    pci_write('0x9040', '0x80000201')
    pci_write('0x9040', '0x80000209')
    # time.sleep(0.1)
    pci_read('9070', '4')
    pci_write('0x9040', '0x80000201')
    time.sleep(0.01)

    # Taking all the raw data of the frame
    if verbose:
        click.secho('Receiving raw data')
    data_path = os.path.join(tmp_path, 'frame.out')
    receive_command = 'pci -r dma0 --multipacket -o {}'.format(data_path)
    execute_command(receive_command, verbose)
    time.sleep(0.1)
    pci_read('9050', '12')
    time.sleep(0.1)

    # Decoding the frame into the RAW format
    if verbose:
        click.secho('Decoding the image, with the following settings:')
        click.secho('-- Camera height:   {}'.format(CONFIG['camera']['camera_height']))
        click.secho('-- Camera width:    {}'.format(CONFIG['camera']['camera_width']))
    decode_command = 'ipedec -r {height} --num-columns {width} {path} {verbose}'.format(
        height=CONFIG['camera']['camera_height'],
        width=CONFIG['camera']['camera_width'],
        path=data_path,
        verbose='-v' if verbose else ''
    )
    exit_code = execute_command(decode_command, verbose)
    # Saving the frame to the correct position
    if not exit_code:
        decoded_path = '{}.raw'.format(data_path)
        shutil.move(decoded_path, path)
        if verbose:
            click.secho('Saved frame to "{}"'.format(path), fg='green')
    else:
        click.secho('Error saving frame!', fg='red')

    return exit_code
