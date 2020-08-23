"""
A module containing the code related to actually capturing images from the camera.
"""
import os
import time
import shutil

import click

from ufotest.util import pci_read, pci_write, execute_command
from ufotest.config import CONFIG


def get_frame(path: str = '/tmp/frame.raw', verbose: bool = False):
    exit_code = save_frame(path, verbose)
    # read the data of the frame and return it
    with open(path, mode='rb+') as file:
        return file.read()


def save_frame(path: str, verbose: bool, tmp_path='/tmp'):
    # Requesting the frame from the camera
    if verbose:
        click.secho('Sending frame request')
    pci_write('0x9040', '0x80000201')
    pci_write('0x9040', '0x80000209')
    time.sleep(0.2)
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
